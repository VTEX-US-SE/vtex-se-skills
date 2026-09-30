#!/usr/bin/env python3
"""A gap belongs to the capability where it was proved, and cannot leave it.

    python3 gap_scope.py _drafts/*.jsonl
    python3 gap_scope.py _drafts/*.jsonl --list      # report only, always exits 0

Run it next to validate_draft.py, across the COMBINED output of every worker: one worker's rows
are consistent by construction, two workers' rows together may not be. Exits 1 on any rejection.

THE DEFECT. A real gap is found on one capability and then rewritten into every neighbouring row
that mentions the topic. Measured on 496 rows: 55 rows carried a gap that was a pointer to another
row's gap, all 55 were partial, none full, and 17 inherited from a different capability_slug.

THE RULE. If a row's gap points at another row whose capability_slug differs, the gap does not
belong here: re-derive it for this row's capability, or delete it. A gap that is only a pointer
(marker + row ID, no substance of its own) and whose target leads on to another capability or
section is rejected too.

THE ASYMMETRY. Inheritance that only ever moves downward is not inheritance, it is keyword
contamination. If the rows with a pointed gap contain zero full-coverage rows, that is a hard
failure, not a warning.
"""
import argparse
import collections
import re
import sys

from _common import load_config, load_rows, union

# Inheritance markers. The non-English ones are the literal phrasing found in real rows.
INHERIT = [
    r'inherit', r'the\s+same\s+(?:gap|limitation|constraint)', r'see\s+row', r'as\s+in\s+row',
    r'as\s+per\s+row', r'per\s+row\b', r'described\s+in\s+row', r'answered\s+(?:in|at)\s+row',
    r'scored\s+(?:in|at)\s+row',
    # Polish
    r'dziedzicz', r'ten\s+sam\s+brak', r'to\s+samo\s+ograniczeni', r'jak\s+w\s+wierszu',
    r'zgodnie\s+z\s+(?:odpowiedzi|wierszem)', r'patrz\s+wiersz', r'opisan\w*\s+w\s+wierszu',
    # Spanish / Portuguese
    r'ver\s+(?:la\s+)?fila', r'igual\s+que\s+en\s+la\s+fila', r'mism[oa]\s+(?:brecha|limitaci[oó]n)',
    r'ver\s+(?:a\s+)?linha', r'mesm[oa]\s+(?:lacuna|limita[cç][aã]o)', r'herda',
]
# Deliberately NOT a marker: "priced once in row X". That is legitimate coordination so the same
# build is not counted twice, not an imported gap (4 false positives measured).

FILLER = re.compile(r'\b(?:row|rows|the|in|at|and|a|of|per|see|as|is|it|this|that|same|fila|linha|'
                    r'w|wierszu|wiersz|do|de|que|la|el|o)\b', re.I)
SECTION_REF = re.compile(r'(?:§|section|chapter|secci[oó]n|se[cç][aã]o|rozdz\.)\s*(\d+(?:\.\d+)*)', re.I)


class Refs:
    def __init__(self, cfg, known):
        self.full = re.compile(cfg['row_id_pattern'])
        self.bare = re.compile(cfg['row_id_bare_pattern']) if cfg.get('row_id_bare_pattern') else None
        self.prefix = cfg.get('row_id_prefix') or ''
        self.known = known

    def __call__(self, text):
        """Row IDs cited in text. A bare ID only counts if it resolves to a row that exists,
        so "2-002" is a reference and a date or "30-day" is not, with no exception list."""
        out = list(dict.fromkeys(m.group(0) for m in self.full.finditer(text)))
        if self.bare:
            for m in self.bare.finditer(text):
                cand = self.prefix + m.group(0)
                if cand in self.known and cand not in out:
                    out.append(cand)
        return out


def own_substance(gap, refs, inherit, prefix):
    """Does the gap say something by itself, or only "same as row X"? The 12-word threshold
    was measured: pointer-only gaps had 0 to 9 useful words, the shortest real one had 17."""
    t = gap
    for x in refs:
        t = t.replace(x, ' ')
        if prefix:
            t = t.replace(x[len(prefix):], ' ')
    t = FILLER.sub(' ', inherit.sub(' ', t))
    return len([w for w in re.split(r'[^\w]+', t) if len(w) > 2]) >= 12


def analyse(rows, cfg):
    inherit = union(INHERIT + (cfg.get('extra_inherit_markers') or []))
    by_id = {r.id: r for r in rows}
    refs_in = Refs(cfg, set(by_id))
    slug = {i: (r.raw.get('capability_slug') or '') for i, r in by_id.items()}
    prefix = cfg.get('row_id_prefix') or ''

    def transitive(rid, refs):
        own_sec = by_id[rid].text('section')
        for m in SECTION_REF.finditer(by_id[rid].text('gap')):
            if own_sec and m.group(1) != own_sec and not own_sec.startswith(m.group(1) + '.'):
                return True                      # the gap names another section of the document
        for x in refs:
            t = by_id.get(x)
            if not t:
                continue
            onward = [y for y in refs_in(t.text('gap')) if y not in (x, rid)]
            if any(slug.get(y) and slug[y] != slug[rid] for y in onward):
                return True                      # the target's gap points to another capability
        return False

    cross, hollow, delegated, pointers = [], [], [], []
    for i, r in by_id.items():
        gap = r.text('gap')
        refs = [x for x in refs_in(gap) if x != i]
        if refs:
            pointers.append(i)
        if not refs or not inherit.search(gap):
            continue
        foreign = [x for x in refs if slug.get(x) and slug[x] != slug[i]]
        if foreign:
            cross.append((i, foreign))
        elif not own_substance(gap, refs, inherit, prefix):
            (hollow if transitive(i, refs) else delegated).append((i, refs))
    return by_id, slug, cross, hollow, delegated, pointers


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('files', nargs='+')
    ap.add_argument('--config')
    ap.add_argument('--list', action='store_true', help='report only, exit 0')
    a = ap.parse_args(argv)
    cfg = load_config(a.config)
    by_id, slug, cross, hollow, delegated, pointers = analyse(load_rows(a.files, cfg), cfg)

    print(f'rows: {len(by_id)} | rows whose gap points at another row: {len(pointers)}')
    mix = collections.Counter(by_id[i].role for i in pointers)
    for k, v in mix.most_common():
        print(f'    {v:4}  {k}')

    hard = 0
    if pointers and not mix.get('full'):
        print('\nHARD FAILURE: none of the rows with a pointed gap has full coverage.')
        print('  Inheritance that only moves downward is propagating a keyword, not knowledge.')
        hard = 1
    if delegated:
        print(f'\n{len(delegated)} row(s) delegate their gap to a row with the SAME capability (warning):')
        print('  The verdict is fine, but the committee reads one row. Repeat the clause instead of pointing.')
        for i, refs in sorted(delegated):
            print(f'    {i} -> {", ".join(refs)}')
    for i, refs in sorted(hollow):
        print(f'  REJECTED {i} [{by_id[i].coverage}] gap is only a pointer that leads to another '
              f'capability or section: {", ".join(refs)}')
        print(f'      gap: {by_id[i].text("gap")[:170]}')
    for i, foreign in sorted(cross):
        print(f'  REJECTED {i} [{by_id[i].coverage}] capability {slug[i] or "(none)"} imports a gap from '
              + ', '.join(f'{x} ({slug.get(x)})' for x in foreign))
        print(f'      gap: {by_id[i].text("gap")[:170]}')

    tot = len(cross) + len(hollow)
    print(f'\n{"OK" if not (tot or hard) else "FAILED"}: {len(cross)} cross-capability + '
          f'{len(hollow)} pointer-only rejection(s), {hard} hard failure(s).')
    return 0 if a.list or not (tot or hard) else 1


if __name__ == '__main__':
    sys.exit(main())
