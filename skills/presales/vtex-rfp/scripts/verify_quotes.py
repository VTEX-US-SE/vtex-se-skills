#!/usr/bin/env python3
"""Checks each row's provenance_quote against the LIVE public page at its evidence_url.

    python3 verify_quotes.py _drafts/*.jsonl

validate_draft.py checks the quote against the local corpus copy. This checks what the evaluator
will actually open: the corpus is pulled from branch `main`, which can be ahead of what is
published, and a page can exist in the repo without rendering. Every verification must end at
the artefact the recipient opens.

HOST INTERCEPTION. Some environments (sandboxes, corporate proxies) serve one cached body for
every path on a host. Measured: every help.vtex.com doc path, including invented slugs, returned
the same payload. So each host is probed with a slug that cannot exist; if a real URL returns the
same body as that canary, the row is UNVERIFIABLE here, not FAILED. Verify those with the
vtex-developer connector's fetch_document instead. Exit code 1 only on real FAILED rows.
"""
import argparse
import hashlib
import html
import json
import pathlib
import re
import subprocess
import sys
import tempfile
from urllib.parse import urlparse

from _common import load_config

TMP = pathlib.Path(tempfile.mkdtemp(prefix='vtex-rfp-verify-'))


def normalize(s):
    s = re.sub(r'\[([^\]]+)\]\([^)]*\)', r'\1', s or '')
    # '_' is kept: it is part of identifiers such as vtex_session, and stripping it produced
    # false FAILED verdicts on correctly cited rows.
    s = html.unescape(re.sub(r'[*`>#]', '', s))
    for a, b in [('’', "'"), ('‘', "'"), ('“', '"'), ('”', '"'), ('—', '-'), ('–', '-')]:
        s = s.replace(a, b)
    s = re.sub(r'\s+', ' ', s).strip()
    return re.sub(r'\s+([,.;:)])', r'\1', s)     # inline links leave a space before punctuation


def fetch(url, tries=3):
    """A single un-retried fetch of a ~1 MB page came back truncated often enough to produce false
    FAILED verdicts, so short bodies are retried and, if still short, reported as a fetch error."""
    dest = TMP / hashlib.sha1(url.encode()).hexdigest()
    best = b''
    for _ in range(tries):
        subprocess.run(['curl', '-sS', '-L', '--retry', '2', '--max-time', '60', '-o', str(dest), url],
                       capture_output=True)
        body = dest.read_bytes() if dest.exists() else b''
        if len(body) > len(best):
            best = body
        if len(best) > 50_000:
            break
    return best


def to_text(raw):
    t = raw.decode('utf-8', 'ignore')
    t = re.sub(r'<script.*?</script>|<style.*?</style>', ' ', t, flags=re.S)
    return normalize(re.sub(r'<[^>]+>', ' ', t))


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('files', nargs='+')
    ap.add_argument('--config')
    a = ap.parse_args(argv)
    id_field = load_config(a.config)['fields']['id']
    rows = []
    for f in a.files:
        rows += [json.loads(l) for l in pathlib.Path(f).read_text(encoding='utf-8').splitlines() if l.strip()]

    canaries, pages, bad, unver = {}, {}, [], []
    for r in rows:
        url, q, rid = r.get('evidence_url'), r.get('provenance_quote'), r.get(id_field, '?')
        if not url or not q:
            continue
        p = urlparse(url)
        base = f'{p.scheme}://{p.netloc}{p.path.rsplit("/", 1)[0]}'
        if base not in canaries:
            canaries[base] = fetch(f'{base}/verify-quotes-canary-does-not-exist-9z9z9z')
        if url not in pages:
            pages[url] = fetch(url)
        raw = pages[url]
        if raw and raw == canaries[base]:
            unver.append(rid)
            continue
        if len(raw) < 5_000:
            print(f'FETCH?  {rid:<14} {url}  (body {len(raw)}B, treated as a fetch error)')
            unver.append(rid)
            continue
        ok = normalize(q) in to_text(raw)
        print(f'{"OK    " if ok else "FAILED"}  {rid:<14} {url}')
        if not ok:
            bad.append(rid)
            print(f'          quote: {normalize(q)[:110]}')

    print()
    if unver:
        print(f'{len(unver)} row(s) UNVERIFIABLE from this environment (not broken): {sorted(set(unver))}')
    if bad:
        print(f'{len(bad)} row(s) whose quote is NOT on the rendered page: {bad}')
        return 1
    print('OK: every checkable quote was found on its rendered page.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
