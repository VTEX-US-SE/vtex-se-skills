"""The solution set in scope, and mechanical detection of documentation outside it.

Imported by corpus.py; not run on its own.

Default solution set (SKILL.md, "Declare the solution set at Step 0"):
    storefront -> FastStore + its CMS
    B2B        -> Buyer Portal

Why this exists: a run answered from CMS Portal (Legacy) documentation. The page was real,
published, VTEX-owned and correctly quoted, so it passed every other check. None of them asks
whether the page describes the platform generation the client would actually receive.

    OUT  CMS Portal (Legacy): "no longer available for new accounts".
    OUT  Site Editor: the CMS for Store Framework, so it leaves with it.
    OUT  Store Framework FRONTEND apps (blocks, components). Rebuilt as FastStore sections.
    IN   VTEX IO BACKEND apps and integrations: reusable with FastStore through the BFF.

The distinction that matters most in practice: an IO backend capability such as Assembly Options
is IN; its `assembly-option-item-*` blocks are OUT. That is rendering, not capability. So a Store
Framework frontend page is a WARNING (answer the capability via the API/BFF), not a rejection.

Rejecting is not enough on its own. A legacy page usually names its replacement, so the hint is
returned for the caller to follow.
"""
import json
import pathlib
import re

SLUG_OUT = re.compile(r'legacy|cms-portal-legacy|legacy-cms', re.I)
TITLE_OUT = re.compile(r'\(Legacy\)', re.I)
BODY_OUT = (
    ('stores using the Legacy Portal technology', 'body says it is for the Legacy Portal'),
    ('no longer available for new accounts', 'body says it is unavailable for new accounts'),
)

SF_FRONTEND = re.compile(
    r'\bstore framework\b|\bsite editor\b|\bstore theme\b'
    r'|\bvtex\.store-|\bstore-components\b|\bassembly-option-item'
    r'|\bblocks?\.jsonc?\b|\binterfaces\.json\b|\bstorefront\s+blocks?\b', re.I)

IO_BACKEND = re.compile(
    r'\bservice\.json\b|\bGraphQL\s+(?:resolver|schema)|\bmasterdata\b|\bREST\s+API'
    r'|\bwebhook\b|\bevent\b|\bAPI\s+endpoint', re.I)

REPLACEMENT_HINT = re.compile(
    r'(?:use|replaced by|instead,? use|migrat\w+ to|new(?:er)? version)[^.]{0,120}', re.I)

FINDINGS = pathlib.Path('_findings') / 'out_of_scope_pages.jsonl'


def classify(doc_id='', title='', repo_path='', body='', url=''):
    """Returns (verdict, reason, replacement_hint); verdict is 'in', 'out-of-scope' or 'sf-frontend'."""
    hay_id = f'{doc_id} {repo_path} {url}'
    m = SLUG_OUT.search(hay_id)
    if m:
        return 'out-of-scope', f'slug/path contains {m.group(0)!r}', _hint(body)
    if TITLE_OUT.search(title or ''):
        return 'out-of-scope', 'title is marked (Legacy)', _hint(body)
    for needle, why in BODY_OUT:
        if needle.lower() in (body or '').lower():
            return 'out-of-scope', why, _hint(body)
    hay = f'{hay_id} {title} {body}'
    m = SF_FRONTEND.search(hay)
    if m:
        # An IO backend page can mention Store Framework in passing: frontend signals must
        # outnumber backend ones before the page is classed as frontend.
        nf, nb = len(SF_FRONTEND.findall(hay)), len(IO_BACKEND.findall(body or ''))
        if nf > nb:
            return 'sf-frontend', f'Store Framework frontend signal ({m.group(0)!r}, {nf}x vs {nb}x backend)', ''
    return 'in', '', ''


def _hint(body):
    m = REPLACEMENT_HINT.search(body or '')
    return m.group(0).strip()[:160] if m else ''


def log(entry):
    FINDINGS.parent.mkdir(exist_ok=True)
    with FINDINGS.open('a', encoding='utf-8') as f:
        f.write(json.dumps(entry, ensure_ascii=False) + '\n')
