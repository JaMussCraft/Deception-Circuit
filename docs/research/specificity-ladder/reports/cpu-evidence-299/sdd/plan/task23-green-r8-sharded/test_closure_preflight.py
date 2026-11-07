"""Tiny stdlib dependency regression; no native imports."""
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from closure_preflight import check_context

class ClosureTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.pins = {}
        self.write('docs/research/held_out.json', {'schema': 1, 'sets': []})
        self.write('docs/research/directions.json', {'directions': [
            {'id': 'specificity-ladder', 'frozen_grader_sha256':
             '866fd15dd30b695e46ffe955b09894fb831af92e2b9015eafbd7f0eee151d2f9'}]})

    def write(self, name, value):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(value))
        self.pins[name] = hashlib.sha256(path.read_bytes()).hexdigest()

    def test_complete_empty_registry(self):
        self.assertEqual(len(check_context(self.root, self.pins)['files']), 2)

    def test_each_missing_registry_rejects(self):
        for name in ('held_out.json', 'directions.json'):
            with self.subTest(name=name):
                path = self.root / 'docs/research' / name
                data = path.read_bytes()
                path.unlink()
                with self.assertRaisesRegex(ValueError, 'missing context'):
                    check_context(self.root, self.pins)
                path.write_bytes(data)

    def test_omitted_path_dependency_rejects_then_complete_passes(self):
        digest = hashlib.sha256(b'["protected"]\n').hexdigest()
        self.write('docs/research/held_out.json', {'schema': 1, 'sets': [
            {'path': 'data/protected.json', 'sha256': digest, 'n': 1}]})
        with self.assertRaisesRegex(ValueError, 'missing context'):
            check_context(self.root, self.pins)
        path = self.root / 'data/protected.json'
        path.parent.mkdir()
        path.write_bytes(b'["protected"]\n')
        with self.assertRaisesRegex(ValueError, 'unpinned context'):
            check_context(self.root, self.pins)
        self.pins['data/protected.json'] = digest
        self.assertEqual(len(check_context(self.root, self.pins)['files']), 3)
        path.write_bytes(b'["altered"]\n')
        with self.assertRaisesRegex(ValueError, 'context hash mismatch'):
            check_context(self.root, self.pins)

    def test_escaped_dependency_rejects(self):
        self.write('docs/research/held_out.json', {'schema': 1, 'sets': [
            {'path': '../outside.json', 'sha256': '0' * 64, 'n': 1}]})
        with self.assertRaisesRegex(ValueError, 'escaped context'):
            check_context(self.root, self.pins)

    def test_registry_alias_rejects(self):
        path = self.root / 'docs/research/held_out.json'
        target = path.with_name('ordinary.json')
        path.rename(target)
        path.symlink_to(target.name)
        with self.assertRaisesRegex(ValueError, 'context alias'):
            check_context(self.root, self.pins)

if __name__ == '__main__':
    unittest.main()
