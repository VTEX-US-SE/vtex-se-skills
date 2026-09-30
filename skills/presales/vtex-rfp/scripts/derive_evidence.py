#!/usr/bin/env python3
"""Derives evidence_url from the provenance quote, so the row author never picks the URL.

    python3 derive_evidence.py _drafts/*.jsonl            # rewrite evidence_url in place
    python3 derive_evidence.py --check _drafts/*.jsonl    # report only, exit 1 on problems

WHY. The recurring defect (8 rows in 63) was structural, not careless: the author cites the page
that best EXPLAINS the answer and quotes the page that best PROVES it. At 700 rows discipline does
not beat that pull, so the URL is derived from whichever corpus page literally contains the quote.

Two refusals, both deliberate:
  * quote on ZERO corpus pages: the row was written from a search snippet.
  * quote on MORE THAN ONE article: ambiguity is a defect, not a tie to break. Lengthen the quote.

Ambiguity keys on the ARTICLE (`slug_en`), not the URL: help.vtex.com publishes /en/, /es/ and
/pt/ renditions of one article, and keying on URL would refuse every row of a Spanish run.

The locale comes from rfp.config.json (`locale`): when the article has a rendition in the
client's language, the derived URL points at it. Otherwise it falls back to English.
"""
import argparse
import collections
import json
import pathlib
import sys

from _common import load_config, load_manifest, norm


def pick_rendition(candidates, locale):
    for want in (locale, 'en'):
        for c in candidates:
            if c.get('locale', 'en') == want:
                return c
    return candidates[0]


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('files', nargs='+')
    ap.add_argument('--config')
    ap.add_argument('--check', action='store_true')
    a = ap.parse_args(argv)
    cfg = load_config(a.config)
    locale, id_field = cfg.get('locale') or 'en', cfg['fields']['id']
    docs = load_manifest()
    if not docs:
        raise SystemExit('no _corpus/MANIFEST*.jsonl: build the corpus with corpus.py first')
    for e in docs.values():
        p = pathlib.Path(e['path'])
        e['text'] = norm(p.read_text(encoding='utf-8')) if p.exists() else ''

    problems, changed, localised = [], 0, 0
    for path in map(pathlib.Path, a.files):
        rows = [json.loads(l) for l in path.read_text(encoding='utf-8').splitlines() if l.strip()]
        for r in rows:
            rid = r.get(id_field, '?')
            q = norm(r.get('provenance_quote'))
            if not q:
                problems.append(f'{rid}: no provenance_quote')
                continue
            hits = [e for e in docs.values() if q in e['text']]
            if not hits:
                problems.append(f'{rid}: quote is on ZERO corpus pages, so it was written from a snippet')
                continue
            by_article = collections.defaultdict(list)
            for e in hits:
                by_article[e.get('slug_en', e['doc_id'])].append(e)
            if len(by_article) > 1:
                problems.append(f'{rid}: quote appears in {len(by_article)} articles {sorted(by_article)}; '
                                'lengthen it until it identifies one')
                continue
            chosen = pick_rendition(next(iter(by_article.values())), locale)
            if chosen.get('locale', 'en') == locale != 'en':
                localised += 1
            if r.get('evidence_url') != chosen['url']:
                changed += 1
            r['evidence_url'] = chosen['url']
            r['evidence_doc_id'] = chosen['doc_id']
        if not a.check:
            path.write_text(''.join(json.dumps(x, ensure_ascii=False) + '\n' for x in rows), encoding='utf-8')

    verb = 'would change' if a.check else 'changed'
    print(f'locale={locale} | {len(a.files)} file(s) | evidence_url {verb} on {changed} row(s)'
          + (f' | {localised} pointed at a {locale} rendition' if localised else ''))
    for x in problems:
        print(f'  REJECTED {x}')
    if problems:
        print(f'\n{len(problems)} row(s) cannot have their evidence derived. Fix the quote, not the URL.')
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
