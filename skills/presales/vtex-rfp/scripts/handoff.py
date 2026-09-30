#!/usr/bin/env python3
"""Hands a review workbook to an SE and reads their edits back, with a THREE-sided diff.

    python3 handoff.py freeze <review.xlsx> [--name NAME]
    python3 handoff.py reconcile _handoff/<NAME> <returned.xlsx> _drafts/*.jsonl            # report only
    python3 handoff.py reconcile _handoff/<NAME> <returned.xlsx> _drafts/*.jsonl --apply    # write drafts

WHY THREE SIDES. Detecting "what the SE changed" by diffing their copy against OUR CURRENT drafts
breaks as soon as our drafts move on after the copy was sent: our own later edit then reads as if
the SE had made it, and applying the diff would revert it. So `freeze` keeps the exact workbook
that was sent, and `reconcile` compares, cell by cell:

    sent   (frozen at handoff)   theirs (the SE's returned copy)   ours (current drafts)

    theirs == sent                  -> the SE didn't touch it; keep ours
    theirs != sent, ours == sent    -> the SE's edit; applied with --apply
    theirs != sent, ours == theirs  -> both made the same change; nothing to do
    theirs != sent, ours != sent    -> CONFLICT; nothing is applied for that cell, a human decides

Without this, SE work disappears: regenerating the client file from our drafts silently erases
every edit made in the review copy.

Each applied edit is classified for the delta report. VERDICT = coverage changed. SOURCE =
evidence changed. FACT = the fact-shaped tokens differ (numbers, versions, standards, negations,
product names). STYLE = the same facts, reworded. Fact and style are never counted together: "the
SE rewrote 40 rows" means little until you know how many corrected a fact.

Cells are located with the `write_back` section of rfp.config.json (sheet, key_column, columns),
the same mapping that wrote them. The derived `owner` column is never written back into the drafts:
an SE change there is reported so line_class/owners can be corrected by hand.

After --apply, re-run validate_draft.py, gap_scope.py and, if verdicts changed, update the registry.
"""
import argparse
import datetime
import html
import json
import pathlib
import re
import shutil
import sys
import zipfile

from _common import load_config, norm
from write_back import cell_value, shared_strings, sheet_path

FACT_TOKENS = re.compile(
    r'\b(?:PCI\s*DSS\s*v?\d+(?:\.\d+)?|ISO\s*\d{4,5}|SOC\s*[12]|TLS\s*\d\.\d|WCAG\s*\d\.\d)\b'
    r'|\d+(?:[.,]\d+)?\s*(?:%|ms|s|sec|seconds|min|minutes|h|hours|days)?\b'
    r"|\b(?:not|no|never|cannot|can't|doesn't|does not|without|only)\b", re.I)
# Product and module names: capitalized words not at the start of a sentence. Case-sensitive.
PROPER = re.compile(r'(?<![.!?]\s)(?<!^)\b[A-Z][a-zA-Z0-9]+(?:\s+[A-Z][a-zA-Z0-9]+)*\b', re.M)


def fact_set(text):
    text = text or ''
    return ({norm(m.group(0)).lower() for m in FACT_TOKENS.finditer(text)}
            | {norm(m.group(0)) for m in PROPER.finditer(text)})


def classify(field, before, after):
    if field == 'coverage':
        return 'VERDICT'
    if field in ('evidence_url', 'provenance_quote'):
        return 'SOURCE'
    return 'FACT' if fact_set(before) != fact_set(after) else 'STYLE'


def read_workbook(path, cfg):
    """{row_id: {field: text}} for every mapped column, via the write_back mapping."""
    wb = cfg['write_back']
    with zipfile.ZipFile(path) as z:
        sheet = z.read(sheet_path(z, wb['sheet'])).decode('utf-8')
        sst = shared_strings(z)
    hdr, key = int(wb.get('header_row', 1)), wb['key_column']
    out = {}
    for m in re.finditer(r'<row r="(\d+)"', sheet):
        n = int(m.group(1))
        if n <= hdr:
            continue
        rid = html.unescape(cell_value(sheet, f'{key}{n}', sst)).strip()
        if rid:
            out[rid] = {f: html.unescape(cell_value(sheet, f'{c}{n}', sst)) for f, c in wb['columns'].items()}
    return out


def draft_value(raw, field, cfg):
    v = raw.get(cfg['fields'].get(field, field))
    return '\n'.join(map(str, v)) if isinstance(v, list) else ('' if v is None else str(v))


def freeze(a, cfg):
    if not cfg.get('write_back'):
        raise SystemExit('rfp.config.json needs a "write_back" section (the same mapping write_back.py uses)')
    read_workbook(a.workbook, cfg)                      # fail now, not at reconcile time
    name = a.name or datetime.datetime.now().strftime('%Y%m%d-%H%M%S')
    d = pathlib.Path('_handoff') / name
    if d.exists():
        raise SystemExit(f'{d} already exists; a frozen handoff is never overwritten')
    d.mkdir(parents=True)
    shutil.copy2(a.workbook, d / 'sent.xlsx')
    (d / 'handoff.json').write_text(json.dumps({'sent_at': datetime.datetime.now().isoformat(timespec='seconds'),
                                                'source': str(a.workbook)}, indent=2) + '\n')
    (d / 'sent.xlsx').chmod(0o444)
    print(f'frozen: {d}/sent.xlsx (read-only). Send {a.workbook} to the SE; never edit the frozen copy.')
    return 0


def reconcile(a, cfg):
    d = pathlib.Path(a.handoff)
    sent, theirs = read_workbook(d / 'sent.xlsx', cfg), read_workbook(a.returned, cfg)
    id_field = cfg['fields']['id']
    files = {}
    for p in map(pathlib.Path, a.drafts):
        files[p] = [json.loads(l) for l in p.read_text(encoding='utf-8').splitlines() if l.strip()]
    ours = {str(r.get(id_field)): r for rows in files.values() for r in rows}

    applied, conflicts, owner_changes, missing = [], [], [], []
    for rid, base in sent.items():
        if rid not in theirs:
            missing.append(rid)
            continue
        for field, before in base.items():
            after = theirs[rid].get(field, '')
            if norm(after) == norm(before):
                continue
            if field == 'owner':
                owner_changes.append((rid, before, after))
                continue
            row = ours.get(rid)
            now = draft_value(row, field, cfg) if row else ''
            if norm(now) == norm(after):
                continue
            if row is None or norm(now) != norm(before):
                conflicts.append((rid, field, before, after, now))
                continue
            applied.append((rid, field, before, after, classify(field, before, after)))
            if a.apply:
                row[cfg['fields'].get(field, field)] = after
                row.setdefault('se_edited', [])
                if field not in row['se_edited']:
                    row['se_edited'].append(field)

    if a.apply and applied:
        backup = d / f'drafts_before_reconcile_{datetime.datetime.now():%Y%m%d-%H%M%S}'
        backup.mkdir()
        for p, rows in files.items():
            shutil.copy2(p, backup / p.name)
            p.write_text(''.join(json.dumps(r, ensure_ascii=False) + '\n' for r in rows), encoding='utf-8')

    counts = {k: sum(1 for x in applied if x[4] == k) for k in ('VERDICT', 'SOURCE', 'FACT', 'STYLE')}
    lines = [f'# Reconcile {d.name} ({datetime.date.today()})', '',
             f'SE edits {"applied" if a.apply else "found (not applied, run with --apply)"}: {len(applied)} '
             f'(verdict {counts["VERDICT"]}, source {counts["SOURCE"]}, fact {counts["FACT"]}, style {counts["STYLE"]}). '
             f'Conflicts: {len(conflicts)}. Owner changes to redo by hand: {len(owner_changes)}.', '']
    if conflicts:
        lines += ['## Conflicts (the SE and we both changed the cell since handoff)', '']
        for rid, f, before, after, now in conflicts:
            lines += [f'- **{rid} / {f}**', f'  - sent: {before[:200]}', f'  - SE: {after[:200]}',
                      f'  - ours now: {now[:200]}']
        lines.append('')
    for kind in ('VERDICT', 'SOURCE', 'FACT', 'STYLE'):
        rows = [x for x in applied if x[4] == kind]
        if rows:
            lines += [f'## {kind}', '']
            lines += [f'- {rid} / {f}: {before[:120]!r} -> {after[:120]!r}' for rid, f, before, after, _ in rows]
            lines.append('')
    if owner_changes:
        lines += ['## Owner changed by the SE (update line_class / owners)', '']
        lines += [f'- {rid}: {b!r} -> {x!r}' for rid, b, x in owner_changes] + ['']
    if missing:
        lines += ['## Rows missing from the returned workbook', '', ', '.join(missing), '']
    report = d / f'reconcile_{datetime.datetime.now():%Y%m%d-%H%M%S}.md'
    report.write_text('\n'.join(lines), encoding='utf-8')

    print('\n'.join(lines[:3]))
    print(f'report: {report}')
    if counts['VERDICT']:
        print('Verdicts changed: re-run validate_draft.py; the registry still holds the old verdict for those '
              'capabilities, so update _registry/ to the SE\'s call.')
    if a.apply and applied:
        print('Drafts updated. Re-run validate_draft.py and gap_scope.py before writing the client file.')
    return 1 if conflicts or missing else 0


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('--config')
    sub = ap.add_subparsers(dest='cmd', required=True)
    f = sub.add_parser('freeze')
    f.add_argument('workbook')
    f.add_argument('--name')
    r = sub.add_parser('reconcile')
    r.add_argument('handoff')
    r.add_argument('returned')
    r.add_argument('drafts', nargs='+')
    r.add_argument('--apply', action='store_true')
    a = ap.parse_args(argv)
    cfg = load_config(a.config)
    return freeze(a, cfg) if a.cmd == 'freeze' else reconcile(a, cfg)


if __name__ == '__main__':
    sys.exit(main())
