"""Every gate must be SEEN to reject a row that breaks its rule. A gate that has never rejected
anything is not a gate. That was measured three times in one day: checks that passed for reasons
unrelated to what they checked.

    python3 -m unittest discover -s skills/presales/vtex-rfp/scripts/tests -v

Stdlib only. Each test runs the real script in a throwaway opportunity folder.
"""
import copy
import json
import pathlib
import subprocess
import sys
import tempfile
import unittest
import zipfile

SCRIPTS = pathlib.Path(__file__).resolve().parent.parent

URL = 'https://developers.vtex.com/docs/guides/pci-dss'
QUOTE = 'VTEX is certified as a Level 1 service provider under PCI DSS v4.0 for card payments.'
PAGE = f'---\ntitle: PCI DSS\n---\n# PCI DSS\n\n{QUOTE}\n\nMore text about security controls.\n'

GOOD = {
    'rfp_id': 'RFP-1-001', 'section': '1', 'coverage': 'OOTB', 'caveat_in_prose': 'n/a',
    'response': 'VTEX is a PCI DSS v4 Level 1 service provider for card payments.',
    'evidence_url': URL, 'provenance_quote': QUOTE, 'capability_slug': 'pci-dss',
    'line_class': 'platform', 'se_review_required': True,
}


class Folder:
    """A throwaway opportunity folder with a one-page corpus."""

    def __init__(self, rows, config=None, corpus=True, registry=None):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = pathlib.Path(self.tmp.name)
        (self.path / '_drafts').mkdir()
        self.write_rows(rows)
        if config is not None:
            (self.path / 'rfp.config.json').write_text(json.dumps(config))
        if corpus:
            docs = self.path / '_corpus' / 'docs'
            docs.mkdir(parents=True)
            (docs / 'pci-dss.md').write_text(PAGE)
            (self.path / '_corpus' / 'MANIFEST.jsonl').write_text(json.dumps(
                {'doc_id': 'pci-dss', 'path': '_corpus/docs/pci-dss.md', 'url': URL,
                 'slug_en': 'pci-dss', 'locale': 'en'}) + '\n')
        if registry:
            (self.path / '_registry').mkdir()
            (self.path / '_registry' / 'capabilities.jsonl').write_text(
                ''.join(json.dumps(e) + '\n' for e in registry))

    def write_rows(self, rows):
        (self.path / '_drafts' / 'd.jsonl').write_text(''.join(json.dumps(r) + '\n' for r in rows))

    def run(self, script, *args):
        p = subprocess.run([sys.executable, str(SCRIPTS / script), *args], cwd=self.path,
                           capture_output=True, text=True)
        return p.returncode, p.stdout + p.stderr

    def close(self):
        self.tmp.cleanup()


def row(**over):
    r = copy.deepcopy(GOOD)
    for k, v in over.items():
        if v is None:
            r.pop(k, None)
        else:
            r[k] = v
    return r


class ValidateDraft(unittest.TestCase):

    def assertRejects(self, rows, needle, **kw):
        f = Folder(rows, **kw)
        try:
            code, out = f.run('validate_draft.py', '_drafts/d.jsonl')
        finally:
            f.close()
        self.assertEqual(code, 1, out)
        self.assertIn(needle, out)

    def test_good_row_passes(self):
        f = Folder([GOOD])
        code, out = f.run('validate_draft.py', '_drafts/d.jsonl')
        f.close()
        self.assertEqual(code, 0, out)

    def test_coverage_outside_scale(self):
        self.assertRejects([row(coverage='Compliant')], 'not in the client scale')

    def test_empty_response(self):
        self.assertRejects([row(response='')], "'response' is empty")

    def test_caveat_no(self):
        self.assertRejects([row(caveat_in_prose='no')], 'invariant was violated')

    def test_full_with_gap(self):
        self.assertRejects([row(gap='Needs a custom app.')], 'contradicts itself')

    def test_partial_without_gap(self):
        self.assertRejects([row(coverage='Partial')], 'no gap described')

    def test_none_needs_not_deliverable(self):
        self.assertRejects([row(coverage='Gap', searches=['a', 'b'])], "declare line_class 'not-deliverable'")

    def test_rule_9_two_distinct_searches(self):
        self.assertRejects([row(coverage='Gap', line_class='not-deliverable', evidence_url=None,
                                provenance_quote=None, searches=['pci', 'PCI'])], 'rule 9 needs 2')

    def test_no_evidence_url(self):
        self.assertRejects([row(evidence_url=None)], 'no evidence_url')

    def test_non_vtex_domain(self):
        self.assertRejects([row(evidence_url='https://blog.example.com/vtex-pci')], 'not on a VTEX domain')

    def test_quote_not_on_page(self):
        self.assertRejects([row(provenance_quote='VTEX processes all card data in a region of your choice.')],
                           'written from a snippet')

    def test_quote_too_short(self):
        self.assertRejects([row(provenance_quote='Level 1 service provider')], 'too short')

    def test_answer_opens_with_verdict(self):
        self.assertRejects([row(response='OOTB. VTEX is a PCI DSS v4 service provider.')], 'opens with the coverage value')

    def test_em_dash(self):
        self.assertRejects([row(response='VTEX is PCI DSS v4 certified — Level 1.')], 'em dash')

    def test_process_narration(self):
        self.assertRejects([row(response='According to VTEX documentation, the platform is PCI DSS v4 certified.')],
                           'narrates our process')

    def test_internal_vocabulary(self):
        self.assertRejects([row(response='VTEX is PCI DSS v4 certified, see the corpus entry.')], 'internal vocabulary')

    def test_integrator_build_cannot_be_full(self):
        self.assertRejects([row(line_class='integrator-build')], 'integrator-build marked as full')

    def test_paid_product_without_disclosure(self):
        self.assertRejects([row(response='VTEX is PCI DSS v4 certified and CX Platform adds web chat.')],
                           'separately licensed')

    def test_paid_product_with_disclosure_passes(self):
        f = Folder([row(response='VTEX is PCI DSS v4 certified. CX Platform, a paid add-on, adds web chat.')])
        code, out = f.run('validate_draft.py', '_drafts/d.jsonl')
        f.close()
        self.assertEqual(code, 0, out)

    def test_registry_divergence(self):
        self.assertRejects([GOOD], 'registry says', registry=[{'capability_slug': 'pci-dss',
                                                               'canonical_verdict': 'Partial'}])

    def test_same_capability_two_verdicts(self):
        self.assertRejects([GOOD, row(rfp_id='RFP-1-002', coverage='Partial', gap='Only for cards.')],
                           'CONTRADICTION')

    def test_architecture_contradiction(self):
        self.assertRejects([row(response='VTEX is PCI DSS v4 certified; FastStore renders checkout.')],
                           'contradicts the recorded architecture',
                           config={'architecture': {'name': 'headless-external', 'forbidden_terms': ['FastStore']}})

    def test_client_verdict_phrase(self):
        self.assertRejects([row(response='La plataforma cumple totalmente con PCI DSS v4.')], 'restates the verdict',
                           config={'extra_verdict_phrases': ['cumple (?:totalmente|parcialmente)']})

    def test_duplicate_id(self):
        self.assertRejects([GOOD, GOOD], 'appears 2 times')

    def test_custom_scale_and_fields(self):
        cfg = {'coverage': {'Yes': 'full', 'No': 'none'}, 'fields': {'id': 'ID', 'coverage': 'Answer',
                                                                     'response': 'Comment'}}
        r = row(ID='7', Answer='Yes', Comment=GOOD['response'])
        for k in ('rfp_id', 'coverage', 'response'):
            r.pop(k)
        f = Folder([r], config=cfg)
        code, out = f.run('validate_draft.py', '_drafts/d.jsonl')
        f.close()
        self.assertEqual(code, 0, out)


class GapScope(unittest.TestCase):

    def test_cross_capability_gap_rejected(self):
        anchor = row(rfp_id='RFP-5-001', coverage='Partial', capability_slug='price-tiers',
                     gap='Tiered price matrices fed by an external configurator are built by the integrator.')
        bleed = row(rfp_id='RFP-3-012', coverage='Partial', capability_slug='local-menu',
                    gap='The same gap as RFP-5-001, inherited.')
        ok = row(rfp_id='RFP-3-013', capability_slug='local-menu-2', gap='See row RFP-3-014 for context.')
        f = Folder([anchor, bleed, ok])
        code, out = f.run('gap_scope.py', '_drafts/d.jsonl')
        f.close()
        self.assertEqual(code, 1, out)
        self.assertIn('REJECTED RFP-3-012', out)

    def test_bare_id_reference_is_resolved(self):
        anchor = row(rfp_id='RFP-5-001', coverage='Partial', capability_slug='price-tiers', gap='x ' * 20)
        bleed = row(rfp_id='RFP-3-012', coverage='Partial', capability_slug='local-menu',
                    gap='Ten sam brak co w wierszu 5-001, dziedziczy go.')
        f = Folder([anchor, bleed],
                   config={'row_id_pattern': r'\bRFP-\d+-\d{3}\b', 'row_id_bare_pattern': r'\b\d+-\d{3}\b',
                           'row_id_prefix': 'RFP-'})
        code, out = f.run('gap_scope.py', '_drafts/d.jsonl')
        f.close()
        self.assertEqual(code, 1, out)
        self.assertIn('REJECTED RFP-3-012', out)

    def test_asymmetry_is_a_hard_failure(self):
        a = row(rfp_id='RFP-1-001', coverage='Partial', capability_slug='c', gap='Refer to RFP-1-002 for context.')
        b = row(rfp_id='RFP-1-002', coverage='Partial', capability_slug='c', gap='Described alongside RFP-1-001.')
        f = Folder([a, b])
        code, out = f.run('gap_scope.py', '_drafts/d.jsonl')
        f.close()
        self.assertEqual(code, 1, out)
        self.assertIn('HARD FAILURE', out)

    def test_clean_rows_pass(self):
        f = Folder([GOOD, row(rfp_id='RFP-1-002', capability_slug='other')])
        code, out = f.run('gap_scope.py', '_drafts/d.jsonl')
        f.close()
        self.assertEqual(code, 0, out)


class Registry(unittest.TestCase):

    def test_conflict_is_reported(self):
        f = Folder([GOOD])
        self.assertEqual(f.run('sync_registry.py', '_drafts/d.jsonl')[0], 0)
        f.write_rows([row(rfp_id='RFP-2-001', coverage='Partial', gap='g')])
        code, out = f.run('sync_registry.py', '_drafts/d.jsonl')
        f.close()
        self.assertEqual(code, 1, out)
        self.assertIn('CONFLICT pci-dss', out)


class DeriveEvidence(unittest.TestCase):

    def test_url_is_derived_from_the_quote(self):
        f = Folder([row(evidence_url='https://developers.vtex.com/docs/guides/something-else')])
        code, out = f.run('derive_evidence.py', '_drafts/d.jsonl')
        fixed = json.loads((f.path / '_drafts' / 'd.jsonl').read_text())
        f.close()
        self.assertEqual(code, 0, out)
        self.assertEqual(fixed['evidence_url'], URL)

    def test_snippet_quote_rejected(self):
        f = Folder([row(provenance_quote='A sentence that is on no page of the corpus at all, anywhere.')])
        code, out = f.run('derive_evidence.py', '--check', '_drafts/d.jsonl')
        f.close()
        self.assertEqual(code, 1, out)
        self.assertIn('ZERO corpus pages', out)


class Rollup(unittest.TestCase):

    def test_arithmetic(self):
        rows = [GOOD, row(rfp_id='RFP-1-002', coverage='Partial'), row(rfp_id='RFP-1-003', coverage='Gap'),
                row(rfp_id='RFP-1-004', coverage='Contractual')]
        f = Folder(rows)
        code, out = f.run('rollup.py', '_drafts/d.jsonl')
        f.close()
        self.assertEqual(code, 0, out)
        self.assertIn('Gross = (1 + 1) / 3 = 66.7%', out)
        self.assertIn('Net = (1 + 1) / 4 = 50.0%', out)
        self.assertIn('RFP-1-004', out)

    def test_scale_without_no(self):
        f = Folder([row(coverage='Yes')], config={'coverage': {'Yes': 'full', 'Dev': 'partial'}})
        code, out = f.run('rollup.py', '_drafts/d.jsonl')
        f.close()
        self.assertIn('no "not supported" value', out)


def make_xlsx(path):
    """A minimal workbook: shared-string IDs in column A, one drawing that must survive."""
    files = {
        '[Content_Types].xml': '<?xml version="1.0"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"/>',
        'xl/workbook.xml': ('<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
                            'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
                            '<sheets><sheet name="Intro" sheetId="1" r:id="rId1"/>'
                            '<sheet name="Requirements" sheetId="2" r:id="rId2"/></sheets></workbook>'),
        'xl/_rels/workbook.xml.rels': ('<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
                                       '<Relationship Id="rId1" Type="ws" Target="worksheets/sheet1.xml"/>'
                                       '<Relationship Id="rId2" Type="ws" Target="worksheets/sheet2.xml"/></Relationships>'),
        'xl/sharedStrings.xml': '<sst><si><t>ID</t></si><si><t>RFP-1-001</t></si><si><t>RFP-1-002</t></si></sst>',
        'xl/styles.xml': '<styleSheet><cellXfs count="2"><xf numFmtId="0"/><xf numFmtId="0" fontId="1"/></cellXfs></styleSheet>',
        'xl/worksheets/sheet1.xml': '<worksheet><sheetData/></worksheet>',
        'xl/worksheets/sheet2.xml': ('<worksheet><sheetData>'
                                     '<row r="1"><c r="A1" s="1" t="s"><v>0</v></c></row>'
                                     '<row r="2"><c r="A2" t="s"><v>1</v></c><c r="H2"/></row>'
                                     '<row r="3"><c r="A3" t="s"><v>2</v></c></row>'
                                     '</sheetData></worksheet>'),
        'xl/drawings/drawing1.xml': '<xdr:wsDr xmlns:xdr="x"/>',
        'xl/media/image1.png': 'PNG',
    }
    with zipfile.ZipFile(path, 'w') as z:
        for n, c in files.items():
            z.writestr(n, c)


class WriteBack(unittest.TestCase):

    CFG = {'write_back': {'sheet': 'Requirements', 'header_row': 1, 'key_column': 'A',
                          'columns': {'coverage': 'H', 'response': 'I', 'evidence_url': 'J'},
                          'new_headers': {'I': 'Response detail'}}}

    def test_writes_copy_and_preserves_parts(self):
        f = Folder([GOOD], config=self.CFG, corpus=False)
        make_xlsx(f.path / 'client.xlsx')
        code, out = f.run('write_back.py', 'client.xlsx', 'out.xlsx', '_drafts/d.jsonl')
        with zipfile.ZipFile(f.path / 'out.xlsx') as z:
            sheet = z.read('xl/worksheets/sheet2.xml').decode()
            names = z.namelist()
        original = zipfile.ZipFile(f.path / 'client.xlsx').read('xl/worksheets/sheet2.xml').decode()
        f.close()
        self.assertEqual(code, 0, out)
        self.assertIn('<c r="H2" s="2" t="inlineStr"><is><t xml:space="preserve">OOTB</t>', sheet)
        self.assertIn(GOOD['response'], sheet)
        self.assertIn(URL, sheet)
        self.assertIn('Response detail', sheet)
        self.assertIn('xl/drawings/drawing1.xml', names)
        self.assertIn('xl/media/image1.png', names)
        self.assertNotIn('OOTB', original)
        self.assertIn('client row(s) have no draft answer', out)

    def test_refuses_to_overwrite_the_original(self):
        f = Folder([GOOD], config=self.CFG, corpus=False)
        make_xlsx(f.path / 'client.xlsx')
        code, out = f.run('write_back.py', 'client.xlsx', 'client.xlsx', '_drafts/d.jsonl')
        f.close()
        self.assertNotEqual(code, 0)
        self.assertIn('refusing to write into the file the client sent', out)

    def test_unmatched_draft_row_fails(self):
        f = Folder([row(rfp_id='RFP-9-999')], config=self.CFG, corpus=False)
        make_xlsx(f.path / 'client.xlsx')
        code, out = f.run('write_back.py', '--check', 'client.xlsx', 'out.xlsx', '_drafts/d.jsonl')
        f.close()
        self.assertEqual(code, 1, out)
        self.assertIn('no matching ID', out)


if __name__ == '__main__':
    unittest.main()
