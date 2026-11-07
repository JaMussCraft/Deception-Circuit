"""Stdlib readiness rejection checks; never execute a measurement."""
import copy
import unittest
from check_ready import validate

class ReadinessTests(unittest.TestCase):
    def test_template_rejects_every_unbound_actual_reference(self):
        import json
        from pathlib import Path
        template = json.loads(Path(__file__).with_name('producer.template.json').read_text())
        failures = validate(template)
        for key in ('source_commit', 'actual_job', 'source_publication', 'admission', 'resources',
                    'design', 'protocol', 'pilot_inventory'):
            self.assertTrue(any(key in failure for failure in failures), key)

    def test_digest_reference_is_required_not_a_path_string(self):
        self.assertTrue(any('actual_job' in error for error in validate({'actual_job': '/tmp/job.json'})))

    def test_template_cannot_self_enable_execution(self):
        self.assertTrue(validate({'execution_authorized': True}))

if __name__ == '__main__':
    unittest.main()
