#!/usr/bin/env python3
"""Step 4 roll-up: coverage per section and overall, with the arithmetic shown.

    python3 rollup.py _drafts/*.jsonl                 # markdown table to stdout
    python3 rollup.py --json _drafts/*.jsonl          # same numbers as JSON

Gross = (full + partial) / rows scored, where rows whose coverage role is `na` are excluded
from the denominator and listed by ID. Net = the same numerator over every row.

If the client's scale has no value with the role `none`, a clean 100% is an artefact of the
vocabulary, not a result, and the output says so.
"""
import argparse
import collections
import json
import sys

from _common import load_config, load_rows


def pct(n, d):
    return f'{100 * n / d:.1f}%' if d else 'n/a'


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('files', nargs='+')
    ap.add_argument('--config')
    ap.add_argument('--json', action='store_true')
    a = ap.parse_args(argv)
    cfg = load_config(a.config)
    rows = load_rows(a.files, cfg)

    sections = collections.OrderedDict()
    for r in rows:
        sections.setdefault(r.text('section') or '(no section)', []).append(r)

    def summarize(rs):
        c = collections.Counter(r.role for r in rs)
        covered, scored = c['full'] + c['partial'], len(rs) - c['na']
        return {'rows': len(rs), 'full': c['full'], 'partial': c['partial'], 'none': c['none'],
                'clarification': c['clarification'], 'excluded_na': [r.id for r in rs if r.role == 'na'],
                'unknown': [r.id for r in rs if r.role is None],
                'gross': pct(covered, scored), 'net': pct(covered, len(rs)),
                'gross_arithmetic': f'({c["full"]} + {c["partial"]}) / {scored}',
                'net_arithmetic': f'({c["full"]} + {c["partial"]}) / {len(rs)}'}

    result = {'sections': {s: summarize(rs) for s, rs in sections.items()}, 'total': summarize(rows),
              'scale_can_say_no': 'none' in cfg['coverage'].values()}
    if a.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0

    print('| Section | Rows | Full | Partial | None | Clarification | Excluded (na) | Gross | Net |')
    print('|---|---|---|---|---|---|---|---|---|')
    for s, v in list(result['sections'].items()) + [('**Total**', result['total'])]:
        print(f'| {s} | {v["rows"]} | {v["full"]} | {v["partial"]} | {v["none"]} | {v["clarification"]} '
              f'| {len(v["excluded_na"])} | {v["gross"]} | {v["net"]} |')
    t = result['total']
    print(f'\nGross = {t["gross_arithmetic"]} = {t["gross"]}. Net = {t["net_arithmetic"]} = {t["net"]}.')
    if t['excluded_na']:
        print(f'Excluded from the scored denominator: {", ".join(t["excluded_na"])}.')
    if t['unknown']:
        print(f'Rows with a coverage value outside the scale (not counted as covered): {", ".join(t["unknown"])}.')
    if not result['scale_can_say_no']:
        print('\nThe client\'s scale has no "not supported" value, so a high number is partly an artefact '
              'of the vocabulary. Read the distribution, not the percentage.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
