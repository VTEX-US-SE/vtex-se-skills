#!/usr/bin/env python3
"""Gate before transposing: rejects any row that cannot prove where it came from.

    python3 validate_draft.py _drafts/*.jsonl
    python3 validate_draft.py --config rfp.config.json _drafts/sec03.jsonl

Exits 1 if any row is rejected. Nothing goes into the client's file until it exits 0.

Why a script and not a prompt: every rule checked here already existed in SKILL.md, and a run
broke them anyway (28 search_documentation calls and zero fetch_document in one measured run).
Advice does not fire; a gate does.

Corpus and registry are OPTIONAL. Without `_corpus/`, the provenance checks are skipped with a
warning and the schema, rule 9 and prose checks still run. Without `_registry/`, the
cross-section consistency is checked only among the rows passed in.
"""
import argparse
import collections
import re
import sys
from urllib.parse import urlparse

from _common import load_config, load_manifest, load_registry, load_rows, norm, union

CAVEAT_OK = {'yes', 'n/a', 'unchecked'}      # 'no' means the invariant was violated
NOT_DELIVERABLE = 'not-deliverable'

# Fact-shaped tokens: versions, standards, numbers with units, percentages. If the answer
# states one, the cited page should contain it.
FACT = re.compile(r'\b(?:PCI\s*DSS\s*v?\d+(?:\.\d+)?|ISO\s*\d{4,5}|SOC\s*[12]|TLS\s*\d\.\d|'
                  r'WCAG\s*\d\.\d|GA4|\d+(?:[.,]\d+)?\s*%|'
                  r'\d+\s*(?:ms|s|sec|seconds|min|minutes|h|hours|days))\b', re.I)

EM_DASH = re.compile(r'—|–|\s--\s')

# Narrating where the answer came from (reported by an SE: it "makes it look AI generated").
PROCESS_NARRATION = [
    r'according to (?:the )?VTEX(?:\'s)? documentation', r'the documentation (?:states|says)',
    r'(?:as )?publicly documented', r'it is documented that', r'VTEX (?:publicly )?documents that',
    r'reclassified \d{4}-\d{2}-\d{2}',
]

# Our own vocabulary leaking into a client column. Extracted from real rows, not imagined.
# Deliberately NOT here: `registry` and `flagged`, which appear legitimately in client prose
# (the client's own systems, a field described as "flagged as active").
OUR_VOCABULARY = [
    r'\badvisor\b', r'\bcitable\b', r'\bcorpus\b', r'\b[\w-]+\.md\b', r'\bcapability_slug\b',
    r'\bslug\b', r'\banchor\s+(?:row|for)\b', r'\binherits?\s+(?:the\s+)?(?:slug|verdict|anchor)',
    r'validate_draft|gap_scope|_drafts|_registry|scratchpad', r'\bwave\s*\d\b', r'\brule\s*\d\b',
    r'\bprovenance\b', r'\bse_note\b', r'\bcoordinator\b', r'\bfor (?:the )?SE\b',
    r'two\s+searches|second\s+search|searched\s+with\s+different',
]

# The answer talking about its own posture instead of the platform. Warning only.
EDITORIAL = re.compile(r'worth (?:being exact|stating|saying|noting)|it is worth\b|rather than hedg'
                       r'|to be (?:precise|honest|exact)\b|consequences? worth', re.I)

RISK = [r'compliance', r'security', r'payment', r'\bSLA\b', r'pric(?:e|ing)', r'personal data',
        r'GDPR', r'PCI', r'WCAG', r'privacy']

COST_DISCLOSED = [r'additional cost', r'extra cost', r'separate(?:ly)?\s+licen[cs]',
                  r'licen[cs]ed\s+separately', r'paid\s+(?:add-?on|product)', r'priced\s+separately',
                  r'\bbilled\b', r'separate\s+VTEX\s+product', r'own\s+commercial\s+terms']

POLARITY_NEG = re.compile(r'\bis not a VTEX feature\b|\bnot a VTEX\b|VTEX (?:does not|doesn\'t) '
                          r'(?:provide|support|offer|host)|\bno native\b', re.I)
POLARITY_POS = re.compile(r'VTEX (?:does )?(?:support|provide|publish|host)s?\b'
                          r'|\bis native\b|natively (?:provided|supported|published)', re.I)


def on_citable_domain(url, domains):
    host = (urlparse(url).hostname or '').lower()
    return any(host == d or host.endswith('.' + d) for d in domains)


def check(rows, cfg, manifest, registry):
    errs, warns = [], []
    corpus_text = {}
    for doc_id, e in manifest.items():
        try:
            with open(e['path'], encoding='utf-8') as f:
                corpus_text[doc_id] = norm(f.read())
        except OSError:
            corpus_text[doc_id] = None
    by_url = {norm(e.get('url')): d for d, e in manifest.items()}

    enum_values = sorted(cfg['coverage'], key=len, reverse=True)
    lead_verdict = re.compile(r'^\s*(?:fully\s+)?(?:' + '|'.join(re.escape(v) for v in enum_values)
                              + r')\b', re.I)
    verdict_phrases = union(cfg.get('extra_verdict_phrases') or [])
    narration = union(PROCESS_NARRATION)
    ours = union(OUR_VOCABULARY)
    risk = union(RISK + (cfg.get('extra_risk_terms') or []))
    paid = union([re.escape(p).replace(r'\ ', r'\s*') for p in cfg.get('paid_products') or []])
    cost = union(COST_DISCLOSED + (cfg.get('extra_cost_disclosure') or []))
    arch = cfg.get('architecture') or {}
    arch_forbidden = union(arch.get('forbidden_terms') or [])

    verdicts = collections.defaultdict(set)
    classes = collections.defaultdict(set)

    for r in rows:
        E = lambda m, r=r: errs.append(f'{r.id}: {m}')
        W = lambda m, r=r: warns.append(f'{r.id}: {m}')
        role = r.role
        klass = r.raw.get('line_class') or r.raw.get('row_class')

        # --- schema ---
        if role is None:
            E(f'coverage {r.coverage!r} is not in the client scale {sorted(cfg["coverage"])}')
        if role != 'na':
            for k in cfg.get('required') or []:
                if not norm(r.text(k)):
                    E(f'{cfg["fields"].get(k, k)!r} is empty')
        cav = r.raw.get('caveat_in_prose')
        if cav == 'no':
            E("caveat_in_prose='no': the invariant was violated, the row is unfinished")
        elif cav not in CAVEAT_OK:
            E(f'caveat_in_prose {cav!r} is invalid (yes | n/a | unchecked)')

        # --- intra-row consistency ---
        if role == 'full' and norm(r.text('gap')):
            E('full coverage with a gap filled in: the row contradicts itself')
        if role == 'partial' and not norm(r.text('gap')):
            E('partial coverage with no gap described')
        if role == 'clarification' and not norm(r.text('assumptions')):
            E('clarification requested but no question in the assumptions field')
        if role == 'none' and klass != NOT_DELIVERABLE:
            E(f"'none' coverage with line_class {klass!r}. None is for a capability with no path at "
              f"all; declare line_class '{NOT_DELIVERABLE}', or use partial and name who builds it")
        if klass == NOT_DELIVERABLE and role != 'none':
            E(f"line_class '{NOT_DELIVERABLE}' with {r.coverage!r}: if there is a path, the class is wrong")
        if klass == 'integrator-build' and role == 'full':
            E('integrator-build marked as full coverage. The committee scores coverage, not our class '
              'column: cap at partial, with the gap naming what is built')
        if role == 'none' and not r.raw.get('se_review_required'):
            E('a negative answer needs se_review_required=true')

        # --- rule 9: two distinct searches before "not supported" ---
        if role == 'none' or r.raw.get('review_flag') == 'not-found':
            s = {norm(x).lower() for x in (r.raw.get('searches') or []) if norm(x)}
            if len(s) < 2:
                E(f'"not supported" / not-found with {len(s)} distinct search(es) recorded; rule 9 needs 2')

        # --- evidence ---
        url = norm(r.raw.get('evidence_url'))
        # A claim needs a source. A 'none' row has nothing to cite; rule 9 covers it instead.
        if role in ('full', 'partial') or url:
            if not url:
                E('no evidence_url (rule 1: one source URL per factual claim)')
            elif not on_citable_domain(url, cfg['citable_domains']):
                E(f'evidence_url is not on a VTEX domain (rule 2): {url}')

        # --- provenance, only with a local corpus ---
        q = norm(r.raw.get('provenance_quote'))
        if manifest and url:
            url_doc = by_url.get(url)
            if not q:
                E('no provenance_quote: nothing proves the page was opened')
            elif len(q) < 40:
                E(f'provenance_quote too short ({len(q)} chars, minimum 40)')
            elif url_doc is None:
                E(f'evidence_url is not in the corpus MANIFEST, so the quote cannot be checked: {url}')
            elif corpus_text.get(url_doc) is None:
                E(f'{url_doc!r} is in the MANIFEST but its file is missing')
            elif q not in corpus_text[url_doc]:
                elsewhere = [d for d, t in corpus_text.items() if t and q in t]
                E(f'provenance_quote is not on the evidence_url page ({url_doc})'
                  + (f'; it is on {elsewhere}, so the URL points at the wrong page' if elsewhere
                     else '; it is on no corpus page, so it was written from a snippet'))
            if url_doc and corpus_text.get(url_doc):
                src = corpus_text[url_doc].lower().replace(' ', '')
                for tok in {m.group(0) for m in FACT.finditer(r.client_text())}:
                    if tok.lower().replace(' ', '') not in src:
                        W(f'fact token {tok!r} does not appear on the cited page, review it')

        # --- prose ---
        if lead_verdict.match(r.text('response')):
            E('the answer opens with the coverage value. The coverage column already carries it, '
              'and the prefix goes stale when the SE changes the dropdown')
        for k in cfg['client_facing']:
            t = r.text(k)
            if EM_DASH.search(t):
                E(f'{cfg["fields"].get(k, k)!r} contains an em dash')
            m = narration.search(t)
            if m:
                E(f'{cfg["fields"].get(k, k)!r} narrates our process ({m.group(0)!r}); say what the platform does')
            m = ours.search(t)
            if m:
                E(f'{cfg["fields"].get(k, k)!r} contains our internal vocabulary ({m.group(0)!r})')
            if verdict_phrases.pattern:
                m = verdict_phrases.search(t)
                if m:
                    E(f'{cfg["fields"].get(k, k)!r} restates the verdict in prose ({m.group(0)!r})')
        client = r.client_text()
        m = EDITORIAL.search(client)
        if m:
            W(f'the prose comments on its own answer ({m.group(0)!r})')
        if paid.pattern:
            m = paid.search(client)
            if m and not cost.search(client):
                E(f'offers {m.group(0)!r} without saying it is a separately licensed VTEX product')
        if arch_forbidden.pattern:
            m = arch_forbidden.search(client)
            if m:
                E(f'contradicts the recorded architecture {arch.get("name")!r} ({m.group(0)!r})')
        if risk.search(client + ' ' + q) and not r.raw.get('se_review_required'):
            W('compliance / security / payment / SLA / pricing row without se_review_required=true')

        # --- capability registry ---
        cap = r.raw.get('capability_slug')
        if cap:
            verdicts[cap].add(r.coverage)
            if klass:
                classes[cap].add(klass)
            reg = registry.get(cap)
            if reg is None:
                if registry:
                    W(f'capability_slug {cap!r} is not in the registry yet')
            elif reg['canonical_verdict'] != r.coverage:
                E(f'registry says {cap} is {reg["canonical_verdict"]!r}, this row says {r.coverage!r}')

    for cap, v in verdicts.items():
        if len(v) > 1:
            errs.append(f'CONTRADICTION: capability {cap!r} answered as {sorted(v)} in different rows')
    for cap, v in classes.items():
        if len(v) > 1:
            errs.append(f'CONTRADICTION: capability {cap!r} has line_class {sorted(v)} in different rows; '
                        'one capability has one owner')

    by_cap = collections.defaultdict(list)
    for r in rows:
        if r.raw.get('capability_slug'):
            by_cap[r.raw['capability_slug']].append(r)
    for cap, rs in by_cap.items():
        neg = [r.id for r in rs if POLARITY_NEG.search(r.client_text())]
        pos = [r.id for r in rs if POLARITY_POS.search(r.client_text())]
        if neg and pos and set(neg) != set(pos):
            warns.append(f'capability {cap!r}: one row denies what another affirms ({neg[:2]} vs {pos[:2]})')

    ids = collections.Counter(r.id for r in rows)
    for rid, n in ids.items():
        if n > 1:
            errs.append(f'{rid}: appears {n} times')
    return errs, warns


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('files', nargs='+')
    ap.add_argument('--config')
    a = ap.parse_args(argv)
    cfg = load_config(a.config)
    rows = load_rows(a.files, cfg)
    manifest, registry = load_manifest(), load_registry()
    if not manifest:
        print('NOTE: no _corpus/MANIFEST*.jsonl, so provenance quotes are not checked against the pages.\n')
    errs, warns = check(rows, cfg, manifest, registry)

    print(f'rows: {len(rows)} | corpus: {len(manifest)} docs | registry: {len(registry)} capabilities')
    tally = collections.Counter()
    for r in rows:
        k = r.raw.get('line_class') or r.raw.get('row_class')
        tally[f'{r.coverage} ({k})' if r.role == 'partial' and k else str(r.coverage)] += 1
    print('coverage:')
    for k, v in sorted(tally.items(), key=lambda kv: -kv[1]):
        print(f'  {v:4d}  {k}')
    for w in warns:
        print(f'  WARN     {w}')
    for e in errs:
        print(f'  REJECTED {e}')
    if errs:
        print(f'\n{len(errs)} rejection(s). Nothing goes into the client file until this is zero.')
        return 1
    print(f'\nOK: {len(rows)} rows passed, {len(warns)} warning(s) for the SE.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
