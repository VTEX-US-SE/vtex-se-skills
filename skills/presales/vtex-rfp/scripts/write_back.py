#!/usr/bin/env python3
"""Writes the drafted answers into a COPY of the client's .xlsx, by editing its XML in place.

    python3 write_back.py <client.xlsx> <out.xlsx> _drafts/*.jsonl
    python3 write_back.py --check <client.xlsx> <out.xlsx> _drafts/*.jsonl   # plan only, write nothing

WHY NOT openpyxl. A library rewrite silently drops drawings, images and Excel Tables the client
embedded. Measured: a first attempt filled all 140 cells correctly and destroyed 5 drawings and 1
image without raising anything; the only signal was the file shrinking from 185 KB to 80 KB. So
every zip entry is copied byte for byte and only the target sheet (and styles, for wrap text) is
changed. After writing, the part counts of the output are compared with the original.

NEVER the original. The output path must differ from the input and must not exist yet.

Mapping comes from rfp.config.json, `write_back`:

    "write_back": {
      "sheet": "Requirements",          // sheet NAME as shown in Excel
      "header_row": 1,
      "key_column": "A",                // column whose cell holds the row ID (fields.id)
      "columns": {                      // draft field (logical name or raw key) -> column letter
        "coverage": "H", "response": "I", "evidence_url": "J"
      },
      "new_headers": {"I": "Response detail", "J": "Reference"}   // optional
    }

Run validate_draft.py and gap_scope.py first. This script does not judge content.
"""
import argparse
import collections
import pathlib
import posixpath
import re
import sys
import zipfile
from xml.sax.saxutils import escape

from _common import load_config, load_rows


def esc(s):
    return escape(str(s))


def colnum(letters):
    n = 0
    for ch in letters:
        n = n * 26 + (ord(ch) - 64)
    return n


def sheet_path(z, name):
    wb = z.read('xl/workbook.xml').decode('utf-8')
    rels = z.read('xl/_rels/workbook.xml.rels').decode('utf-8')
    for m in re.finditer(r'<sheet\b[^>]*>', wb):
        tag = m.group(0)
        n = re.search(r'name="([^"]*)"', tag)
        rid = re.search(r'r:id="([^"]*)"', tag)
        if n and rid and n.group(1).replace('&amp;', '&') == name:
            t = re.search(rf'<Relationship\b[^>]*Id="{re.escape(rid.group(1))}"[^>]*>', rels)
            target = re.search(r'Target="([^"]*)"', t.group(0)).group(1)
            return target.lstrip('/') if target.startswith('/') else posixpath.normpath('xl/' + target)
    names = re.findall(r'<sheet\b[^>]*name="([^"]*)"', wb)
    raise SystemExit(f'sheet {name!r} not found; the workbook has {names}')


def shared_strings(z):
    if 'xl/sharedStrings.xml' not in z.namelist():
        return []
    xml = z.read('xl/sharedStrings.xml').decode('utf-8')
    out = []
    for si in re.findall(r'<si>(.*?)</si>', xml, re.S):
        out.append(''.join(re.findall(r'<t[^>]*>(.*?)</t>', si, re.S)))
    return out


def cell_value(sheet, ref, sst):
    m = re.search(rf'<c r="{ref}"([^>]*?)(?:/>|>(.*?)</c>)', sheet, re.S)
    if not m or not m.group(2):
        return ''
    attrs, body = m.group(1), m.group(2)
    if 't="s"' in attrs:
        v = re.search(r'<v>(\d+)</v>', body)
        return sst[int(v.group(1))] if v else ''
    if 't="inlineStr"' in attrs:
        return ''.join(re.findall(r'<t[^>]*>(.*?)</t>', body, re.S))
    v = re.search(r'<v>(.*?)</v>', body, re.S)
    return v.group(1) if v else ''


def add_wrap_style(styles, base):
    """Append a cellXf copying `base` with top alignment and wrap text; return (xml, new index)."""
    m = re.search(r'<cellXfs count="(\d+)">(.*?)</cellXfs>', styles, re.S)
    if not m:
        raise SystemExit('cellXfs not found in styles.xml')
    count, body = int(m.group(1)), m.group(2)
    xfs = re.findall(r'<xf\b.*?(?:/>|</xf>)', body, re.S)
    src = xfs[base] if base < len(xfs) else '<xf numFmtId="0" fontId="0" fillId="0" borderId="0"/>'
    core = re.sub(r'<alignment\b.*?/>', '', src, flags=re.S)
    core = core[:-2].rstrip() + '>' if core.rstrip().endswith('/>') else core.replace('</xf>', '')
    new = core + '<alignment vertical="top" wrapText="1"/></xf>'
    return styles.replace(m.group(0), f'<cellXfs count="{count + 1}">{body}{new}</cellXfs>'), count


def put(sheet, col, row, text, style):
    """Write col+row as an inline string, inserting the cell in column order if it is absent."""
    s = f' s="{style}"' if style is not None else ''
    cell = f'<c r="{col}{row}"{s} t="inlineStr"><is><t xml:space="preserve">{esc(text)}</t></is></c>'
    for pat, flags in ((rf'<c r="{col}{row}"[^>]*/>', 0), (rf'<c r="{col}{row}"[^>]*>.*?</c>', re.S)):
        if re.search(pat, sheet, flags):
            return re.sub(pat, lambda _: cell, sheet, count=1, flags=flags), True
    rm = re.search(rf'<row r="{row}"(?:\s[^>]*)?>(.*?)</row>', sheet, re.S)
    if not rm:
        return sheet, False
    body, pos = rm.group(1), None
    for cm in re.finditer(r'<c r="([A-Z]+)\d+"', body):
        if colnum(cm.group(1)) > colnum(col):
            pos = cm.start()
            break
    body = body + cell if pos is None else body[:pos] + cell + body[pos:]
    return sheet[:rm.start(1)] + body + sheet[rm.end(1):], True


def part_counts(z):
    names = z.namelist()
    return collections.Counter(
        k for n in names for k, p in (('drawings', 'xl/drawings/'), ('media', 'xl/media/'),
                                      ('tables', 'xl/tables/'), ('charts', 'xl/charts/'))
        if n.startswith(p) and not n.endswith('/') and '_rels' not in n)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('original')
    ap.add_argument('out')
    ap.add_argument('drafts', nargs='+')
    ap.add_argument('--config')
    ap.add_argument('--check', action='store_true')
    a = ap.parse_args(argv)
    cfg = load_config(a.config)
    wb_cfg = cfg.get('write_back')
    if not wb_cfg:
        raise SystemExit('rfp.config.json has no "write_back" section; see this script\'s docstring')
    src, out = pathlib.Path(a.original).resolve(), pathlib.Path(a.out).resolve()
    if src == out:
        raise SystemExit('refusing to write into the file the client sent; choose a new output path')
    if out.exists() and not a.check:
        raise SystemExit(f'{out} already exists; choose a name that cannot collide')

    rows = {r.id: r for r in load_rows(a.drafts, cfg)}
    zin = zipfile.ZipFile(src)
    target = sheet_path(zin, wb_cfg['sheet'])
    sheet = zin.read(target).decode('utf-8')
    styles = zin.read('xl/styles.xml').decode('utf-8')
    sst = shared_strings(zin)
    key_col, hdr = wb_cfg['key_column'], int(wb_cfg.get('header_row', 1))
    columns = wb_cfg['columns']

    # Map row ID -> Excel row number, reading the key column of the client's own sheet.
    where = {}
    for m in re.finditer(r'<row r="(\d+)"', sheet):
        n = int(m.group(1))
        if n > hdr:
            v = cell_value(sheet, f'{key_col}{n}', sst).strip()
            if v:
                where[v] = n
    unmatched = sorted(set(rows) - set(where))
    unanswered = sorted(set(where) - set(rows))

    # One wrap-text style per target column, based on the style its first data cell already has.
    first = min((where[i] for i in rows if i in where), default=hdr + 1)
    wrap = {}
    for col in columns.values():
        m = re.search(rf'<c r="{col}{first}"[^>]*?\ss="(\d+)"', sheet)
        styles, wrap[col] = add_wrap_style(styles, int(m.group(1)) if m else 0)

    written, missing = collections.Counter(), []
    for rid, r in rows.items():
        if rid not in where:
            continue
        for field, col in columns.items():
            val = r.raw.get(cfg['fields'].get(field, field))
            if isinstance(val, list):
                val = '\n'.join(map(str, val))
            if val in (None, ''):
                continue
            sheet, ok = put(sheet, col, where[rid], val, wrap[col])
            if ok:
                written[col] += 1
            else:
                missing.append(f'{col}{where[rid]}')
    for col, title in (wb_cfg.get('new_headers') or {}).items():
        hs = re.search(rf'<c r="{key_col}{hdr}"[^>]*?\ss="(\d+)"', sheet)
        sheet, _ = put(sheet, col, hdr, title, hs.group(1) if hs else None)

    print(f'sheet {wb_cfg["sheet"]!r} ({target}) | {len(where)} client rows | {len(rows)} draft rows')
    for col in sorted(set(columns.values()), key=colnum):
        print(f'    column {col}: {written[col]} cell(s)')
    if unmatched:
        print(f'  ! {len(unmatched)} draft row(s) have no matching ID in column {key_col}: {unmatched[:10]}')
    if unanswered:
        print(f'  ! {len(unanswered)} client row(s) have no draft answer: {unanswered[:10]}')
    if missing:
        print(f'  ! cells that could not be placed: {missing[:10]}')
    if a.check:
        print('--check: nothing written')
        return 1 if unmatched else 0

    with zipfile.ZipFile(out, 'w', zipfile.ZIP_DEFLATED) as zout:
        for item in zin.infolist():
            data = {target: sheet, 'xl/styles.xml': styles}.get(item.filename)
            zout.writestr(item, data if data is not None else zin.read(item.filename))
    before = part_counts(zin)
    zin.close()
    with zipfile.ZipFile(out) as zcheck:
        after = part_counts(zcheck)
    if before != after:
        print(f'  ! PART COUNT CHANGED: {dict(before)} -> {dict(after)}. Do not send this file.')
        return 1
    print(f'OK  {out}  (drawings/media/tables preserved: {dict(before) or "none present"})')
    return 1 if unmatched else 0


if __name__ == '__main__':
    sys.exit(main())
