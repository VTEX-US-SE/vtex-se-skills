#!/usr/bin/env python3
"""Applies an SE's edit to one draft row, from chat, and re-checks the row at once.

    python3 edit_row.py RFP-3-012 coverage=Partial gap="Tiered prices need an external configurator."
    python3 edit_row.py RFP-3-012 response=@new_answer.txt --by "SE name"
    python3 edit_row.py RFP-3-012 owners='["VTEX","SI"]' line_class=shared --dry-run

For reviewing in chat (Claude Code, desktop or terminal) instead of in a spreadsheet. The agent
calls this when the SE says "make RFP-3-012 Partial, the gap is X". Field names are the logical
names from rfp.config.json (coverage, response, gap...) or raw keys. A value starting with `@`
is read from that file; a value that parses as JSON (lists, true/false, numbers) is stored as JSON.

Every edit:
  * is written into the row, which gets `se_edited` updated;
  * is logged to _review/edit_log.jsonl with who, when, before and after, and the same
    VERDICT / SOURCE / FACT / STYLE class the spreadsheet round-trip uses, so the delta report
    reads the same whichever way the SE reviewed;
  * is re-validated immediately, and the result is printed for the SE. The edit is kept even when
    the gate rejects it: the SE decides, the gate informs.

If a review workbook is out with an SE (a _handoff/ folder not reconciled yet), the edit still
goes through, with a warning: the same cell edited in both places will come back as a conflict.
"""
import argparse
import datetime
import json
import pathlib
import sys

import validate_draft
from _common import Row, load_config, load_manifest, load_registry, norm
from handoff import classify

LOG = pathlib.Path('_review') / 'edit_log.jsonl'


def parse_value(v):
    if v.startswith('@'):
        return pathlib.Path(v[1:]).read_text(encoding='utf-8').strip()
    try:
        parsed = json.loads(v)
        if isinstance(parsed, (list, dict, bool, int, float)) or parsed is None:
            return parsed
    except json.JSONDecodeError:
        pass
    return v


def open_handoffs():
    return [d.name for d in sorted(pathlib.Path('_handoff').glob('*'))
            if (d / 'sent.xlsx').exists() and not list(d.glob('reconcile_*.md'))]


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('row_id')
    ap.add_argument('edits', nargs='+', metavar='field=value')
    ap.add_argument('--by', default='SE')
    ap.add_argument('--config')
    ap.add_argument('--drafts', nargs='*', help='draft files (default: _drafts/*.jsonl)')
    ap.add_argument('--dry-run', action='store_true')
    a = ap.parse_args(argv)
    cfg = load_config(a.config)
    id_field = cfg['fields']['id']
    files = [pathlib.Path(p) for p in (a.drafts or sorted(pathlib.Path('_drafts').glob('*.jsonl')))]

    target = None
    contents = {}
    for p in files:
        rows = [json.loads(l) for l in p.read_text(encoding='utf-8').splitlines() if l.strip()]
        contents[p] = rows
        for r in rows:
            if str(r.get(id_field)) == a.row_id:
                if target:
                    raise SystemExit(f'{a.row_id} appears in more than one draft file')
                target = (p, r)
    if not target:
        raise SystemExit(f'{a.row_id} not found in {[str(p) for p in files]}')
    path, raw = target

    now = datetime.datetime.now().isoformat(timespec='seconds')
    entries = []
    for e in a.edits:
        if '=' not in e:
            raise SystemExit(f'expected field=value, got {e!r}')
        field, value = e.split('=', 1)
        key = cfg['fields'].get(field, field)
        before, after = raw.get(key), parse_value(value)
        if json.dumps(before) == json.dumps(after):
            continue
        raw[key] = after
        entries.append({'at': now, 'by': a.by, 'row': a.row_id, 'field': field, 'before': before, 'after': after,
                        'kind': classify(field, norm(str(before or '')), norm(str(after or '')))})
    if not entries:
        print(f'{a.row_id}: nothing changed')
        return 0
    edited = raw.setdefault('se_edited', [])
    for x in entries:
        if x['field'] not in edited:
            edited.append(x['field'])

    for x in entries:
        print(f"{a.row_id} / {x['field']} [{x['kind']}]: {str(x['before'])[:100]!r} -> {str(x['after'])[:100]!r}")
    busy = open_handoffs()
    if busy:
        print(f'  ! a review workbook is still out with an SE ({", ".join(busy)}). If this cell is edited '
              'there too, it will come back as a conflict at reconcile.')

    rows = [Row(r, cfg) for rs in contents.values() for r in rs]
    errs, warns = validate_draft.check(rows, cfg, load_manifest(), load_registry())
    slug = raw.get('capability_slug') or '\0'
    mine = lambda m: m.startswith(a.row_id + ':') or (slug in m and m.startswith('CONTRADICTION'))
    for w in filter(mine, warns):
        print(f'  WARN     {w}')
    for e in filter(mine, errs):
        print(f'  REJECTED {e}')
    if not any(map(mine, errs)):
        print(f'  gates: {a.row_id} passes')

    if a.dry_run:
        print('--dry-run: nothing written')
        return 0
    path.write_text(''.join(json.dumps(r, ensure_ascii=False) + '\n' for r in contents[path]), encoding='utf-8')
    LOG.parent.mkdir(exist_ok=True)
    with LOG.open('a', encoding='utf-8') as f:
        for x in entries:
            f.write(json.dumps(x, ensure_ascii=False) + '\n')
    return 1 if any(map(mine, errs)) else 0


if __name__ == '__main__':
    sys.exit(main())
