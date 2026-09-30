#!/usr/bin/env python3
"""Builds a local copy of the cited VTEX pages, so quotes can be checked against the full page.

    python3 corpus.py index                          # once per run: fetch the vtexdocs file trees
    python3 corpus.py add <slug> [<slug> ...]
    python3 corpus.py add --worker w1 <slug> ...     # parallel workers write their own shard

Writes `_corpus/docs/<slug>.md` and one line per page in `_corpus/MANIFEST.jsonl`, with the
canonical public URL (developers.vtex.com / help.vtex.com). That URL is what the answer cites;
the local copy only exists so validate_draft.py can prove the provenance_quote is a literal
substring of the page.

Source: VTEX's public documentation repos on GitHub (vtexdocs/dev-portal-content and
vtexdocs/help-center-content), branch `main`. `main` can be ahead of what is published, which is
why verify_urls.py / verify_quotes.py check the live pages afterwards.

Refused at entry, trying the next candidate with the same slug before giving up:
  * `hidden: true` in frontmatter. The URL answers HTTP 200 but renders nothing, and
    search_documentation ranks such pages first. Logged to _findings/hidden_pages.jsonl.
  * help-center `status:` other than PUBLISHED.
  * pages outside the solution set (scope_guard.py), e.g. CMS Portal (Legacy).
"""
import json
import pathlib
import re
import subprocess
import sys
from urllib.parse import quote

import scope_guard

ROOT = pathlib.Path('.')
CORPUS = ROOT / '_corpus'
DOCS = CORPUS / 'docs'
REPOS = ('dev-portal-content', 'help-center-content')
FINDINGS = ROOT / '_findings' / 'hidden_pages.jsonl'


def paths_file(repo):
    return CORPUS / f'paths_{repo}.txt'


def curl(args):
    return subprocess.run(['curl', '-sSfL', '--max-time', '60'] + args, capture_output=True, text=True)


def index():
    """Fetch the file tree of each docs repo (one GitHub API call per repo)."""
    CORPUS.mkdir(parents=True, exist_ok=True)
    for repo in REPOS:
        r = curl([f'https://api.github.com/repos/vtexdocs/{repo}/git/trees/main?recursive=1'])
        if r.returncode != 0:
            raise SystemExit(f'could not list vtexdocs/{repo}: {r.stderr.strip()}')
        tree = json.loads(r.stdout)
        if tree.get('truncated'):
            print(f'  ! vtexdocs/{repo}: tree listing was truncated by the API; some slugs may be missing')
        paths = [e['path'] for e in tree.get('tree', []) if e['type'] == 'blob' and e['path'].endswith(('.md', '.mdx'))]
        paths_file(repo).write_text('\n'.join(paths) + '\n', encoding='utf-8')
        print(f'  + {repo}: {len(paths)} pages')


def shard(worker=None):
    # Parallel workers cannot share one MANIFEST: two appends interleave. Each worker writes its
    # own shard, and every reader merges MANIFEST*.jsonl.
    return CORPUS / (f'MANIFEST_{worker}.jsonl' if worker else 'MANIFEST.jsonl')


def load_paths():
    idx = {}
    for repo in REPOS:
        f = paths_file(repo)
        if not f.exists():
            raise SystemExit(f'{f} not found. Run `python3 corpus.py index` first.')
        for p in f.read_text(encoding='utf-8').splitlines():
            idx.setdefault(pathlib.PurePosixPath(p).stem, []).append((repo, p))
    return idx


def public_url(repo, path):
    slug = pathlib.PurePosixPath(path).stem
    if repo == 'dev-portal-content':
        if path.startswith('docs/release-notes/'):
            return f'https://developers.vtex.com/updates/release-notes/{slug}'
        for kind in ('api-reference', 'faststore'):
            if path.startswith(f'docs/{kind}/'):
                return f'https://developers.vtex.com/docs/{kind}/{slug}'
        return f'https://developers.vtex.com/docs/guides/{slug}'
    if path.startswith('docs/announcements/'):
        return f'https://help.vtex.com/en/announcements/{slug}'
    m = re.match(r'docs/(\w+)/([\w-]+)/', path + '/')
    locale = m.group(1) if m else 'en'
    kind = path.split('/')[2] if len(path.split('/')) > 3 else 'docs'
    return f'https://help.vtex.com/{locale}/docs/{kind}/{slug}'


def log_hidden(slug, repo, path, reason):
    FINDINGS.parent.mkdir(parents=True, exist_ok=True)
    with FINDINGS.open('a', encoding='utf-8') as f:
        f.write(json.dumps({'doc_id': slug, 'repo': repo, 'repo_path': path,
                            'url': public_url(repo, path), 'reason': reason}, ensure_ascii=False) + '\n')


def load_manifest():
    out = {}
    for f in sorted(CORPUS.glob('MANIFEST*.jsonl')):
        for line in f.read_text(encoding='utf-8').splitlines():
            if line.strip():
                e = json.loads(line)
                out[e['doc_id']] = e
    return out


def frontmatter(text):
    return text.split('---')[1] if text.startswith('---') else ''


def add(slugs, worker=None):
    idx, man = load_paths(), load_manifest()
    DOCS.mkdir(parents=True, exist_ok=True)
    for slug in slugs:
        if slug in man:
            print(f'  = {slug} (already in the manifest)')
            continue
        hits = idx.get(slug)
        if not hits:
            print(f'  ! {slug} not found in the docs repos')
            continue
        # Prefer the dev portal, then the English help-center rendition.
        hits.sort(key=lambda h: (h[0] != 'dev-portal-content', '/en/' not in '/' + h[1]))
        dest = DOCS / f'{slug}.md'
        chosen = None
        # Walk every candidate: a hidden page on one repo must not shadow a published page with
        # the same slug on the other.
        for repo, path in hits:
            r = curl(['-o', str(dest), f'https://raw.githubusercontent.com/vtexdocs/{repo}/main/{quote(path)}'])
            if r.returncode != 0:
                print(f'  ~ {slug}: download failed for {path}: {r.stderr.strip()}')
                continue
            text = dest.read_text(encoding='utf-8')
            fm = frontmatter(text)
            if re.search(r'^hidden:\s*true', fm, re.M):
                dest.unlink()
                print(f'  ~ {slug}: refused in {repo}, hidden: true (unpublished)')
                log_hidden(slug, repo, path, 'hidden: true')
                continue
            m = re.search(r'^status:\s*(\S+)', fm, re.M)
            if m and m.group(1).strip('"\'') != 'PUBLISHED':
                dest.unlink()
                print(f'  ~ {slug}: refused in {repo}, status: {m.group(1)}')
                log_hidden(slug, repo, path, f'status: {m.group(1)}')
                continue
            title = re.search(r'^title:\s*["\']?([^"\'\n]+)', fm, re.M)
            verdict, why, hint = scope_guard.classify(doc_id=slug, title=title.group(1) if title else '',
                                                      repo_path=path, body=text, url=public_url(repo, path))
            entry = {'doc_id': slug, 'repo': repo, 'repo_path': path, 'url': public_url(repo, path),
                     'reason': why, 'verdict': verdict}
            if verdict == 'out-of-scope':
                dest.unlink()
                print(f'  ~ {slug}: OUTSIDE THE SOLUTION SET in {repo}: {why}')
                if hint:
                    print(f'      the page names its replacement: {hint}')
                scope_guard.log(dict(entry, replacement_hint=hint))
                continue
            if verdict == 'sf-frontend':
                print(f'  ! {slug}: describes Store Framework frontend ({why}). Answer the capability '
                      'via the API/BFF; the UI is a FastStore section')
                scope_guard.log(dict(entry, action='usable for capability, not for rendering'))
            chosen = (repo, path, fm)
            break
        if chosen is None:
            print(f'  ! {slug} REFUSED: no published candidate ({len(hits)} tried), not citable (rule 2)')
            continue
        repo, path, fm = chosen
        # slug_en + locale let derive_evidence.py treat /en/, /es/, /pt/ renditions as one article.
        m_slug = re.search(r'^slugEN:\s*["\']?([\w.-]+)', fm, re.M)
        m_loc = re.search(r'^locale:\s*["\']?(\w+)', fm, re.M)
        entry = {'doc_id': slug, 'path': str(dest), 'url': public_url(repo, path), 'repo': repo,
                 'repo_path': path, 'slug_en': m_slug.group(1) if m_slug else slug,
                 'locale': m_loc.group(1) if m_loc else 'en', 'bytes': dest.stat().st_size}
        with shard(worker).open('a', encoding='utf-8') as f:
            f.write(json.dumps(entry, ensure_ascii=False) + '\n')
        print(f'  + {slug} -> {entry["url"]} ({entry["bytes"]}B)')


def main(argv):
    worker = None
    if '--worker' in argv:
        i = argv.index('--worker')
        worker = argv[i + 1]
        del argv[i:i + 2]
    if argv[:1] == ['index']:
        index()
        return 0
    if len(argv) >= 2 and argv[0] == 'add':
        add(argv[1:], worker)
        return 0
    print(__doc__)
    return 0 if argv[:1] in (['-h'], ['--help']) else 2


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
