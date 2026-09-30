#!/usr/bin/env python3
"""Records capability_slug -> canonical verdict in _registry/.

    python3 sync_registry.py _drafts/sec06.jsonl                 # central merge
    python3 sync_registry.py --worker w1 _drafts/sec06.jsonl     # a worker's own shard

Run it AFTER a section passes validate_draft.py. From then on, any row answering the same
capability with a different verdict is rejected by validate_draft.py. That is what stops one
capability coming out full in one section and partial in another.

PARALLELISM. Without --worker the script rewrites capabilities.jsonl, which two workers cannot
do at once (the last writer erases the other). With --worker each one appends only its NEW
entries to capabilities_<worker>.jsonl; readers merge every shard, so a conflict is detected
immediately and reported. It is never resolved silently.
"""
import argparse
import json
import pathlib
import sys

from _common import load_config, load_registry, load_rows

REGDIR = pathlib.Path('_registry')


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('files', nargs='+')
    ap.add_argument('--config')
    ap.add_argument('--worker')
    a = ap.parse_args(argv)
    cfg = load_config(a.config)
    REGDIR.mkdir(parents=True, exist_ok=True)
    reg = load_registry()
    fresh, conflicts = {}, []
    for r in load_rows(a.files, cfg):
        cap = r.raw.get('capability_slug')
        if not cap:
            continue
        known = reg.get(cap) or fresh.get(cap)
        if known:
            if known['canonical_verdict'] != r.coverage:
                conflicts.append((cap, known['canonical_verdict'], r.coverage, r.id))
            continue
        fresh[cap] = {'capability_slug': cap, 'canonical_verdict': r.coverage,
                      'line_class': r.raw.get('line_class') or r.raw.get('row_class'),
                      'first_row': r.id, 'section': r.get('section')}
    if a.worker:
        out = REGDIR / f'capabilities_{a.worker}.jsonl'
        with out.open('a', encoding='utf-8') as f:
            for k in sorted(fresh):
                f.write(json.dumps(fresh[k], ensure_ascii=False) + '\n')
        print(f'shard {out.name}: +{len(fresh)} new | union now: {len(reg) + len(fresh)}')
    else:
        reg.update(fresh)
        (REGDIR / 'capabilities.jsonl').write_text(
            ''.join(json.dumps(reg[k], ensure_ascii=False) + '\n' for k in sorted(reg)), encoding='utf-8')
        print(f'registry: {len(reg)} capabilities ({len(fresh)} new)')
    for cap, old, new, rid in conflicts:
        print(f'  CONFLICT {cap}: canonical {old!r} vs {new!r} in {rid}. Resolve before exporting')
    return 1 if conflicts else 0


if __name__ == '__main__':
    sys.exit(main())
