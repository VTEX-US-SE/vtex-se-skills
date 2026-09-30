"""Shared helpers for the vtex-rfp scripts: config loading, JSONL I/O, text normalization.

Every script runs from the opportunity folder (the current directory), not from the script's
own folder. That folder holds the per-RFP config and the working files:

    rfp.config.json          optional; see templates/rfp.config.example.json
    _drafts/*.jsonl          one JSON object per requirement row
    _corpus/MANIFEST*.jsonl  optional local copy of the cited VTEX pages (corpus.py)
    _registry/capabilities*.jsonl   optional canonical verdict per capability (sync_registry.py)

The config exists because every client matrix is different: its coverage scale, its row IDs,
the field names, the language. The first versions of these scripts hardcoded one client's
matrix and could not be reused on the next RFP.
"""
import json
import pathlib
import re

# Roles a coverage value can play. The client's scale maps onto these, so the gates reason
# about "full / partial / none" without knowing the client's words for them.
ROLES = {'full', 'partial', 'none', 'na', 'clarification'}

# Who does the work on a row. `shared` is the real three-way split (VTEX + SI + client) that a
# two-value owner could not express; it carries an explicit `owners` list.
LINE_CLASSES = {'platform', 'integrator-build', 'shared', 'not-deliverable'}
OWNERS = ('VTEX', 'SI', 'client')
# What kind of section a row is in. Decided per SECTION at Step 0, not per document: a large RFP
# often has a functional part, a security annex and a commercial annex.
#   full        functional/technical requirements; the whole workflow
#   security    InfoSec / privacy questionnaires; no architecture step, SE review on every row
#   rfi         capability overviews; coverage optional when the client does not score
#   commercial  pricing, contract, legal: the skill does NOT answer; the SE decides where it goes
PROFILES = {'full', 'security', 'rfi', 'commercial'}

SINGLE_OWNER = {'platform': ['VTEX'], 'integrator-build': ['SI'], 'not-deliverable': []}

DEFAULT_CONFIG = {
    # The skill's own scale, used when the client's matrix defines none. Say so in the
    # roll-up so the SE can remap it.
    'coverage': {
        'OOTB': 'full',
        'Add-on': 'full',
        'Configuration': 'full',
        'Partial': 'partial',
        'Contractual': 'na',
        'Gap': 'none',
    },
    'fields': {
        'id': 'rfp_id',
        'coverage': 'coverage',
        'response': 'response',
        'gap': 'gap',
        'implementation': 'implementation',
        'assumptions': 'assumptions',
        'section': 'section',
        'requirement': 'requirement',
    },
    # Logical names (keys of `fields`) whose text goes into the client's file.
    'client_facing': ['response', 'gap', 'implementation', 'assumptions'],
    # Logical names that must be non-empty on every row whose coverage is not `na`.
    'required': ['response'],
    # How the client numbers their rows. The second pattern is the same ID written bare
    # (e.g. "see row 2-002"); a bare match only counts when it resolves to a known row.
    'row_id_pattern': r'\b[A-Z]{2,5}-\d+(?:\.\d+)*-\d{2,4}\b',
    'row_id_bare_pattern': r'\b\d+(?:\.\d+)*-\d{2,4}\b',
    'row_id_prefix': '',
    'citable_domains': ['vtex.com', 'help.vtex.com', 'developers.vtex.com', 'compliance.vtex.com'],
    'locale': 'en',
    # Extra patterns, in the client's language, for the same checks the English defaults cover.
    'extra_verdict_phrases': [],
    'extra_inherit_markers': [],
    'extra_risk_terms': [],
    'extra_cost_disclosure': [],
    # VTEX products licensed separately. Offering one in client prose without saying it is
    # paid reads as included, and the committee prices what it reads.
    'paid_products': ['CX Platform', 'Agent Builder'],
    'architecture': None,
    # Section -> profile. A key matches its section and every subsection ("13" covers "13.2").
    'profiles': {},
    'default_profile': 'full',
    # How each owner is printed in the client's file (write_back `owner` column).
    'owner_labels': {'VTEX': 'VTEX', 'SI': 'Integrator', 'client': 'Client'},
    'owner_joiner': ' + ',
    # Extra phrases, in the client's language, saying someone other than VTEX builds a part.
    'extra_builder_phrases': [],
}


def load_config(path=None):
    """Merge rfp.config.json (if present) over the defaults."""
    cfg = json.loads(json.dumps(DEFAULT_CONFIG))
    p = pathlib.Path(path) if path else pathlib.Path('rfp.config.json')
    if p.exists():
        user = json.loads(p.read_text(encoding='utf-8'))
        for k, v in user.items():
            if isinstance(v, dict) and isinstance(cfg.get(k), dict) and k != 'coverage':
                cfg[k].update(v)
            else:
                cfg[k] = v
    elif path:
        raise SystemExit(f'config not found: {path}')
    badp = {v for v in list((cfg.get('profiles') or {}).values()) + [cfg.get('default_profile')] if v not in PROFILES}
    if badp:
        raise SystemExit(f'config: unknown profile(s) {sorted(badp)}; use {sorted(PROFILES)}')
    bad = {v for v in cfg['coverage'].values() if v not in ROLES}
    if bad:
        raise SystemExit(f'config: unknown coverage role(s) {sorted(bad)}; use {sorted(ROLES)}')
    return cfg


class Row:
    """A draft row read through the config's field mapping."""

    def __init__(self, raw, cfg):
        self.raw, self.cfg = raw, cfg

    def get(self, logical, default=''):
        return self.raw.get(self.cfg['fields'].get(logical, logical), default)

    @property
    def id(self):
        return str(self.get('id') or '?')

    @property
    def coverage(self):
        return self.get('coverage')

    @property
    def role(self):
        return self.cfg['coverage'].get(self.coverage)

    def text(self, logical):
        return str(self.get(logical) or '')

    @property
    def profile(self):
        sec, best, prof = self.text('section'), -1, None
        for key, value in (self.cfg.get('profiles') or {}).items():
            k = str(key)
            if (sec == k or sec.startswith(k + '.')) and len(k) > best:
                best, prof = len(k), value
        return prof or self.raw.get('profile') or self.cfg.get('default_profile') or 'full'

    @property
    def line_class(self):
        return self.raw.get('line_class') or self.raw.get('row_class')

    def owners(self):
        """Owners derived from line_class; `shared` rows carry their own list."""
        if self.line_class == 'shared':
            return [o for o in OWNERS if o in (self.raw.get('owners') or [])]
        return SINGLE_OWNER.get(self.line_class, [])

    def owner_label(self):
        labels = self.cfg.get('owner_labels') or {}
        return (self.cfg.get('owner_joiner') or ' + ').join(labels.get(o, o) for o in self.owners())

    def client_text(self):
        return ' '.join(self.text(k) for k in self.cfg['client_facing'])


def load_rows(paths, cfg):
    rows = []
    for p in paths:
        for n, line in enumerate(pathlib.Path(p).read_text(encoding='utf-8').splitlines(), 1):
            if line.strip():
                try:
                    rows.append(Row(json.loads(line), cfg))
                except json.JSONDecodeError as e:
                    raise SystemExit(f'{p}:{n}: invalid JSON ({e})')
    return rows


def read_jsonl_glob(folder, pattern):
    out = []
    for f in sorted(pathlib.Path(folder).glob(pattern)):
        for line in f.read_text(encoding='utf-8').splitlines():
            if line.strip():
                out.append(json.loads(line))
    return out


def load_manifest(root='.'):
    """doc_id -> entry, merged across worker shards (MANIFEST_<worker>.jsonl)."""
    return {e['doc_id']: e for e in read_jsonl_glob(pathlib.Path(root) / '_corpus', 'MANIFEST*.jsonl')}


def load_registry(root='.'):
    out = {}
    for e in read_jsonl_glob(pathlib.Path(root) / '_registry', 'capabilities*.jsonl'):
        out.setdefault(e['capability_slug'], e)
    return out


def norm(s):
    """Collapse whitespace and straighten quotes, for substring comparison."""
    s = (s or '').replace('’', "'").replace('‘', "'").replace('“', '"').replace('”', '"')
    return re.sub(r'\s+', ' ', s).strip()


def union(patterns, flags=re.I):
    return re.compile('|'.join(f'(?:{p})' for p in patterns if p), flags)
