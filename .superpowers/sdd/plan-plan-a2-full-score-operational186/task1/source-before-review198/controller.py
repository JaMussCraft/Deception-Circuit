"""One original full-score CLI; no bank, pilot, loader injection or retry."""
import json
import os
from pathlib import Path
import signal
import subprocess
import time
import traceback
import common
from common import (C, CONFIG, SOURCE, GPU_NAME, require, read, write, sha, content,
                    validate_config, verify_existing_bank, full_score_command,
                    validate_score_command, entry_release)


def terminate_process_group(child, timeout_seconds=10):
    if child is None or child.poll() is not None:
        return
    os.killpg(child.pid, signal.SIGTERM)
    try:
        child.wait(timeout=timeout_seconds)
    except subprocess.TimeoutExpired:
        os.killpg(child.pid, signal.SIGKILL)
        child.wait(timeout=timeout_seconds)


def protected_inventory(c):
    root = Path(c['main_root'])
    result = {}
    for path in root.rglob('*'):
        rel = path.relative_to(root)
        require(not path.is_symlink(), 'MAIN symlink forbidden')
        if rel.parts[0] == 'score' or rel.parts[0].startswith('.score-'):
            continue
        if path.is_file(): result[str(rel)] = sha(path)
    return result


def _probe(c, name, script, env, work_deadline):
    output = Path(c['evidence_root']) / (name + '.json')
    variable = 'A2_GPU_PROBE_OUTPUT' if script == 'gpu-probe.py' else 'A2_IMPORT_PROBE_OUTPUT'
    child = None
    try:
        left = work_deadline - time.time()
        require(left > 0, 'no remaining read-only probe deadline')
        child = subprocess.Popen([c['python'], str(Path(__file__).resolve().parent / script)],
                                 cwd=c['runtime'], env=dict(env, **{variable: str(output)}), start_new_session=True)
        code = child.wait(timeout=left)
        require(time.time() < work_deadline and code == 0, 'probe failed or observed too late')
    finally:
        terminate_process_group(child)
    return read(output)


def preflight_full_score(c, r):
    """Genuine internal guard chain; no caller-provided success function."""
    require(c == C, 'controller must use exact hash-bound config')
    common.packet()
    before = common.source()
    common.input_closure()
    bank = verify_existing_bank(c)
    common.reviewed_admission()
    common.cache()
    common.protection()
    common.validate_release(r)
    allocation = common.allocation(release=r)
    accounting = common.budget(release=r)
    deadline = common.current_deadlines(c, allocation['facts'])['work_deadline']
    require(deadline - time.time() >= c['resources']['minimum_entry_seconds'], 'preflight entry floor')
    env = common.environment()
    _probe(c, 'imports-before-full-score', 'module-probe.py', env, deadline)
    probe = _probe(c, 'gpu-before-full-score', 'gpu-probe.py', env, deadline)
    device = common.validate_gpu_identity(c, probe)
    # Recheck expensive mutable boundaries after activation/import/probe work.
    common.packet(); common.source(); common.input_closure(); verify_existing_bank(c)
    common.cache(); common.protection(); common.budget(release=r)
    final_allocation = common.allocation(release=r)
    deadline = min(deadline, common.current_deadlines(c, final_allocation['facts'])['work_deadline'])
    out = Path(c['evidence_root'])
    write(out / 'source-before.json', before)
    write(out / 'bank-before.json', bank)
    write(out / 'allocation-before.json', final_allocation)
    write(out / 'accounting-before.json', accounting)
    write(out / 'gpu-identities.json', device)
    inventory = protected_inventory(c)
    write(out / 'MAIN-before.json', inventory)
    return dict(environment=env, work_deadline=deadline, source_before=before,
                bank_before=bank, protected_inventory=inventory)


def _support_rows(p, rows):
    result = []
    for row in rows:
        require(type(row.get('supported')) is bool, 'native support flag must be explicit')
        reason = row.get('unsupported_reason')
        require(row['supported'] or isinstance(reason, str) and reason, 'unsupported diagnostic reason missing')
        result.append(dict(key=list(p.a1.row_key(row)), supported=row['supported'], unsupported_reason=reason))
    return sorted(result, key=lambda row: json.dumps(row['key'], sort_keys=True))


def audit_score_result(c):
    """Native manifest/domain/control/support audit only; no summaries/effects."""
    p, _ = common.imports()
    args = p.parser().parse_args(full_score_command(c)[2:])
    prepared, selected, sidecar = p._load_context(args)
    receipt = p.a1.read_artifact(Path(c['main_root']) / 'groups.json')
    p._validate_live(args, receipt, prepared)
    banks = p.read_stage(Path(c['main_root']) / 'bank', 'banks.json', 'bank', args, receipt)
    p.validate_banks(receipt, prepared, banks)
    scored = p.read_stage(Path(c['main_root']) / 'score', 'score.json', 'score', args, receipt)
    require(scored['kind'] == 'a2_scored' and scored['limit'] == 0 and scored['pilot'] is False
            and scored['injected'] is False and not receipt['injected'] and not banks['injected'], 'genuine full native score only')
    expected = [list(k) for k in p.expected_keys(receipt, 0)]
    require(scored['expected'] == expected and len(expected) == 59652, 'full original expected domain')
    require(scored['bank_artifact_sha256'] == p.hash_content(banks) == c['bank_internal_payload_sha256'], 'score authentic bank link')
    p.validate_a2_scope(receipt, scored['rows'], limit=0, banks=banks, bank_path=Path(c['bank_file']))
    p.a1.validate_positive_controls(scored['positive_controls'], p._prepared_domain(receipt), 0)
    positive = p.a1.positive_keys(p._prepared_domain(receipt), 0)
    require(len(positive) == len(scored['positive_controls']) == 3396, 'full native controls')
    counts = dict(rows=len(scored['rows']), expected=len(expected), positive_controls=len(scored['positive_controls']))
    require(counts == scored['counts'] == {'rows': 59652, 'expected': 59652, 'positive_controls': 3396}, 'native count closure')
    execution = scored['execution_provenance']
    require(execution['gpu_name'] == GPU_NAME and execution['dtype'] == c['dtype']
            and execution['device'].split(':')[0] == 'cuda'
            and str(execution['slurm_job_id']) == c['actual_job_id'], 'actual native score execution identity')
    resource = read(c['resource_proof'])
    reference = resource['full_domain_reference']
    require(sha(reference['path']) == reference['sha256'], 'accepted full domain/support proof changed')
    domain = read(reference['path'])
    require(domain['complete'] is True and domain['source_commit'] == SOURCE
            and domain['groups_file_sha256'] == c['groups_file_sha256'], 'accepted proof181 exact native domain')
    supports = _support_rows(p, scored['rows'])
    want_support = sorted(domain['rows'], key=lambda row: json.dumps(row['key'], sort_keys=True))
    require(supports == want_support and len(want_support) == 59652, 'full support mask/reasons drift')
    control_keys = sorted([list(k) for k in positive], key=lambda row: json.dumps(row))
    require(control_keys == sorted(domain['positive_control_keys'], key=lambda row: json.dumps(row)), 'full control domain drift')
    common._bank_binding(c, allow_score=True)
    source_after = common.source()
    common.input_closure(); common.protection()
    return dict(complete=True, counts=counts, score_manifest_sha256=sha(Path(c['main_root']) / 'score/run_manifest.json'),
                score_execution=execution, source_after=source_after,
                domain_audit=dict(complete=True, expected_keys_sha256=content(expected), positive_keys_sha256=content(control_keys)),
                support_mask_audit=dict(complete=True, support_rows_sha256=content(supports),
                                        unsupported=sum(not row['supported'] for row in supports), reasons_preserved=True),
                bank_after=common._bank_binding(c, allow_score=True), assessment_effects_inspected=False)


def run_full_score(c, r):
    # Cheap real guards also protect callers before any I/O-heavy preflight.
    validate_config(c)
    verify_existing_bank(c)
    common._lease(r)
    command = validate_score_command(c, full_score_command(c))
    context = preflight_full_score(c, r)
    out = Path(c['evidence_root'])
    child = None
    started = time.time()
    record = dict(command=command, cwd=c['runtime'], started_unix=started, original_CLI_entries=0,
                  automatic_retry=False)
    try:
        # Open evidence before consuming permission, then do the one final
        # hash/catalogue/allocation/deadline check immediately at CLI entry.
        with (out / 'full-score.stdout').open('x') as stdout, (out / 'full-score.stderr').open('x') as stderr:
            require(context['work_deadline'] - time.time() > 0, 'work deadline elapsed during costly preflight')
            entry_release(r, 'full_score')
            deadline = min(context['work_deadline'], r.get('_entry_work_deadline', context['work_deadline']),
                           time.time() + c['resources']['child_cap_seconds'])
            remaining = deadline - time.time()
            common._lease(r)
            require(remaining > 0, 'fresh final remaining deadline exhausted')
            child = subprocess.Popen(command, cwd=c['runtime'], env=context['environment'],
                                     stdout=stdout, stderr=stderr, start_new_session=True)
            record['original_CLI_entries'] = 1
            try:
                code = child.wait(timeout=remaining)
            except subprocess.TimeoutExpired:
                terminate_process_group(child)
                raise TimeoutError('original CLI work/child deadline expired; retain partial; no retry')
            record['exit_code'] = code
            require(time.time() < deadline, 'child observed at/after deadline cannot promote COMPLETE')
            require(code == 0, 'original CLI failed; preserve partial; no retry')
        audit = audit_score_result(c)
        require(audit['complete'] is True and audit['domain_audit']['complete'] is True
                and audit['support_mask_audit']['complete'] is True, 'full native completion audit required')
        if 'protected_inventory' in context:
            require(protected_inventory(c) == context['protected_inventory'], 'existing MAIN leaf changed or foreign leaf created')
            for key in ('source_commit', 'snapshot_sha256', 'source_count', 'literal_links'):
                require(audit['source_after'][key] == context['source_before'][key], 'source before-after drift')
            require(audit['bank_after'] == context['bank_before'], 'bank before-after drift')
            accounting_after = common.budget(release=r)
            write(out / 'accounting-after.json', accounting_after)
            write(out / 'source-after.json', audit['source_after'])
            write(out / 'bank-after.json', audit['bank_after'])
            require(accounting_after['ledger_sha256'] == read(out / 'accounting-before.json')['ledger_sha256'],
                    'accounting changed while full-score reader active')
            current = common.current_deadlines(c, common.allocation()['facts'])
            require(time.time() < current['run_deadline'], 'native audit observed after fixed run deadline')
        record['finished_unix'] = time.time()
        record['elapsed_seconds'] = record['finished_unix'] - started
        result = dict(record, complete=True, phase='full_score', audit=audit,
                      source_commit=SOURCE, actual_job_id=c['actual_job_id'], assessment_effects_inspected=False)
        write(out / 'COMPLETE.json', result)
        return result
    finally:
        terminate_process_group(child)
        record['finished_unix'] = time.time()
        record['elapsed_seconds'] = time.time() - started
        write(out / 'full-score-command.json', record)


def main():
    def interrupted(signum, frame):
        raise TimeoutError('controller termination signal ' + str(signum))
    for signum in (signal.SIGTERM, signal.SIGINT): signal.signal(signum, interrupted)
    try:
        validate_config(C)
        require(Path.cwd().resolve() == Path(C['runtime']).resolve(), 'original source cwd')
        release = common.gpu_release('full_score')
        write(Path(C['evidence_root']) / 'root-release.json', release)
        run_full_score(C, release)
    except BaseException as error:
        write(Path(C['evidence_root']) / 'FAILED.json', dict(error=repr(error), traceback=traceback.format_exc(),
                                                          partial_preserved=True, automatic_retry=False))
        raise


if __name__ == '__main__':
    main()
