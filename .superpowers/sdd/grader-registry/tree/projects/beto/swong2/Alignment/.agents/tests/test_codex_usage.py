import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / 'codex_usage.py'


class UsageTests(unittest.TestCase):
    def run_check(self, result, *args, mode='ok'):
        with tempfile.TemporaryDirectory() as tmp:
            fake = Path(tmp) / 'codex'
            fake.write_text('#!' + sys.executable + '\n' + '''import json, sys, time
result = json.loads(''' + repr(json.dumps(result)) + ''')
mode = ''' + repr(mode) + '''
for line in sys.stdin:
    msg = json.loads(line)
    if msg['method'] == 'initialize':
        print(json.dumps({'id': msg['id'], 'result': {}}), flush=True)
    elif msg['method'] == 'initialized':
        pass
    elif msg['method'] == 'account/rateLimits/read':
        if mode == 'hang':
            time.sleep(10)
        elif mode == 'error':
            print(json.dumps({'id': msg['id'], 'error': {'message': 'private diagnostic'}}), flush=True)
        else:
            print(json.dumps({'method': 'notification', 'params': {}}), flush=True)
            print(json.dumps({'id': msg['id'], 'result': result}), flush=True)
    else:
        sys.exit(9)
''')
            fake.chmod(0o700)
            p = subprocess.run([sys.executable, str(SCRIPT), '--codex-bin', str(fake), *args],
                               capture_output=True, text=True, timeout=5)
            self.assertTrue(p.stdout.strip(), p.stderr)
            return p.returncode, json.loads(p.stdout)

    def bucket(self, used=25, slot='primary', duration=10080):
        return {'rateLimits': {slot: {'usedPercent': used, 'windowDurationMins': duration,
                                      'resetsAt': 2000000000}}}

    def test_weekly_in_either_slot_and_inclusive_threshold(self):
        for slot in ('primary', 'secondary'):
            code, data = self.run_check(self.bucket(75, slot), '--pause-at', '75')
            self.assertEqual(code, 2)
            self.assertEqual(data['weekly']['used_percent'], 75)
            self.assertEqual(data['weekly']['remaining_percent'], 25)
            self.assertTrue(data['should_pause'])

    def test_under_threshold(self):
        code, data = self.run_check(self.bucket(), '--pause-at', '75')
        self.assertEqual(code, 0)
        self.assertFalse(data['should_pause'])

    def test_missing_weekly_is_unknown_not_zero(self):
        code, data = self.run_check(self.bucket(duration=300), '--pause-at', '75')
        self.assertEqual(code, 1)
        self.assertTrue(data['should_pause'])
        self.assertIsNone(data['weekly'])

    def test_multi_bucket_uses_requested_bucket(self):
        result = self.bucket(10)
        result['rateLimitsByLimitId'] = {'codex': self.bucket(20)['rateLimits'],
                                        'other': self.bucket(90)['rateLimits']}
        code, data = self.run_check(result, '--limit-id', 'other', '--pause-at', '75')
        self.assertEqual(code, 2)
        self.assertEqual(data['weekly']['used_percent'], 90)

    def test_unknown_bucket_does_not_fallback(self):
        code, data = self.run_check(self.bucket(), '--limit-id', 'missing')
        self.assertEqual(code, 1)

    def test_malformed_percentage_and_expired_window_fail_closed(self):
        for value in (-1, 101, None, '75', True, float('nan')):
            code, data = self.run_check(self.bucket(value), '--pause-at', '75')
            self.assertEqual(code, 1)
            self.assertTrue(data['should_pause'])
        result = self.bucket()
        result['rateLimits']['primary']['resetsAt'] = 1
        self.assertEqual(self.run_check(result)[0], 1)

    def test_error_and_timeout_fail_closed_without_private_details(self):
        for mode in ('error', 'hang'):
            code, data = self.run_check({}, '--timeout', '0.2', '--pause-at', '75', mode=mode)
            self.assertEqual(code, 1)
            self.assertTrue(data['should_pause'])
            self.assertNotIn('private diagnostic', json.dumps(data))


if __name__ == '__main__':
    unittest.main()
