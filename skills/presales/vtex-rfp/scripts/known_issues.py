#!/usr/bin/env python3
"""Searches VTEX's published Known Issues for a capability before a row claims it without caveat.

    python3 known_issues.py sync                                  # fetch or refresh the local copy
    python3 known_issues.py search "order editing handling shipping" --module "Order Management"
    python3 known_issues.py search "apple pay" --locale es --json

Source: the public repo vtexdocs/known-issues, the same content as help.vtex.com/<locale>/known-issues.
The copy lives in ~/.cache/vtex-rfp/known-issues (override with VTEX_RFP_KI_DIR) and is refreshed
when older than 24 hours, so a run always reads the current status of each issue.

Only issues that still affect the client are returned by default:
    Backlog, Scheduled   open; the SE decides whether it reaches the client's answer
    No Fix               permanent; a documented limit, so it IS a caveat in the answer
Fixed and Closed are skipped (use --all-statuses to see them).

Record what you checked on the row, even when nothing matched, so the gate can see it ran:
    "known_issues": []                                                       # searched, none found
    "known_issues": [{"url": "...", "status": "No Fix", "title": "..."}]    # from --json output
"""
import argparse
import json
import os
import pathlib
import re
import subprocess
import sys
import time

REPO = 'https://github.com/vtexdocs/known-issues'
OPEN = {'backlog', 'scheduled', 'no fix'}
STOP = set('the a an and or of to in on for with is are be by at from as it this that can not no does do '
           'when which what how client vtex platform support supports should must'.split())


def home():
    return pathlib.Path(os.environ.get('VTEX_RFP_KI_DIR') or pathlib.Path.home() / '.cache' / 'vtex-rfp' / 'known-issues')


def sync(max_age_h=24, quiet=False):
    d = home()
    stamp = d / '.synced'
    if stamp.exists() and time.time() - stamp.stat().st_mtime < max_age_h * 3600:
        return d
    if (d / '.git').exists():
        r = subprocess.run(['git', '-C', str(d), 'pull', '-q', '--depth', '1'], capture_output=True, text=True)
    elif (d / 'docs').exists():
        return d                                     # a plain folder (tests, offline copy): use as is
    else:
        d.parent.mkdir(parents=True, exist_ok=True)
        r = subprocess.run(['git', 'clone', '-q', '--depth', '1', REPO, str(d)], capture_output=True, text=True)
    if r.returncode != 0:
        if (d / 'docs').exists():
            print(f'  ! could not refresh known issues ({r.stderr.strip()}); using the copy from '
                  f'{time.ctime(stamp.stat().st_mtime) if stamp.exists() else "an unknown date"}', file=sys.stderr)
            return d
        raise SystemExit(f'could not fetch {REPO}: {r.stderr.strip()}')
    stamp.touch()
    if not quiet:
        print(f'known issues synced to {d}', file=sys.stderr)
    return d


def parse(path):
    text = path.read_text(encoding='utf-8', errors='ignore')
    fm, body = {}, text
    if text.startswith('---'):
        parts = text.split('---', 2)
        if len(parts) == 3:
            body = parts[2]
            for line in parts[1].splitlines():
                m = re.match(r'^(\w+):\s*(.*)$', line)
                if m:
                    fm[m.group(1)] = m.group(2).strip().strip('"\'')

    def section(name):
        m = re.search(rf'^##\s+{name}\s*$(.*?)(?=^##\s|\Z)', body, re.M | re.S | re.I)
        return re.sub(r'!\[[^\]]*\]\([^)]*\)', '', m.group(1)).strip() if m else ''
    return fm, section('Summary'), section('Workaround')


def words(s):
    return [w for w in re.findall(r'[\w-]+', (s or '').lower()) if len(w) > 2 and w not in STOP]


def search(query, module=None, locale='en', all_statuses=False, limit=5):
    base = sync(quiet=True) / 'docs' / locale / 'known-issues'
    if not base.exists():
        raise SystemExit(f'no known issues for locale {locale!r} at {base}')
    q = set(words(query))
    if not q:
        raise SystemExit('the query has no searchable words')
    hits = []
    for mod in sorted(p for p in base.iterdir() if p.is_dir()):
        if module and module.lower() not in mod.name.lower():
            continue
        for f in mod.glob('*.md'):
            fm, summary, workaround = parse(f)
            status = fm.get('kiStatus', '')
            if not all_statuses and status.lower() not in OPEN:
                continue
            title_w, body_w = set(words(fm.get('title'))), set(words(summary))
            score = 3 * len(q & title_w) + len(q & body_w)
            # Short queries need every term; longer ones at least half, so one common word ("pay")
            # cannot surface an unrelated issue.
            need = len(q) if len(q) <= 2 else (len(q) + 1) // 2
            if score and len(q & (title_w | body_w)) >= need:
                slug = fm.get('slug') or f.stem
                hits.append({'score': score, 'title': fm.get('title', f.stem), 'status': status, 'module': mod.name,
                             'url': f'https://help.vtex.com/{locale}/known-issues/{slug}',
                             'updated': fm.get('updatedAt', '')[:10],
                             'summary': re.sub(r'\s+', ' ', summary)[:300],
                             'workaround': re.sub(r'\s+', ' ', workaround)[:300]})
    hits.sort(key=lambda h: (-h['score'], h['title']))
    return hits[:limit]


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest='cmd', required=True)
    s = sub.add_parser('sync')
    s.add_argument('--force', action='store_true')
    q = sub.add_parser('search')
    q.add_argument('query')
    q.add_argument('--module', help='module folder, e.g. Checkout, "Order Management", Payments')
    q.add_argument('--locale', default='en')
    q.add_argument('--all-statuses', action='store_true')
    q.add_argument('--limit', type=int, default=5)
    q.add_argument('--json', action='store_true')
    a = ap.parse_args(argv)
    if a.cmd == 'sync':
        d = sync(max_age_h=0 if a.force else 24)
        print(f'known issues at {d}')
        return 0
    hits = search(a.query, a.module, a.locale, a.all_statuses, a.limit)
    if a.json:
        print(json.dumps([{k: h[k] for k in ('url', 'status', 'title')} for h in hits], ensure_ascii=False))
        return 0
    if not hits:
        print(f'No open known issue found for {a.query!r}' + (f' in {a.module}' if a.module else '')
              + '. Try one or two other phrasings before recording "known_issues": [].')
        return 0
    for h in hits:
        print(f"[{h['status']}] {h['title']}  ({h['module']}, updated {h['updated']})\n  {h['url']}")
        if h['summary']:
            print(f"  summary: {h['summary']}")
        if h['workaround']:
            print(f"  workaround: {h['workaround']}")
    return 0


if __name__ == '__main__':
    sys.exit(main())
