"""JSON-only derivative of the selected format-control cohort, never a screen.

Only historical full rows determine eligibility. Source loaders read local
CSV/parquet and notebook JSON constants; no model, API, or pickle is loaded.
All used native donor prompts and recipient-to-donor IDs are recovered exactly.
Unused historical pool entries need not be recovered for interchange.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from evaluation.benchmarks import get_benchmark
from evaluation.benchmarks.base import BenchmarkItem, DECEPTIVE, HONEST
from evaluation.benchmarks import sources
from evaluation.frozen_head_masks import binding, check_binding, digest, read_json

IMPORT_VERSION = 'format-control-D_hko__leaf-selected-v1'
SUITES = ('eval5_format_sdr_coarse', 'eval5_format_sdr_coarse_lb')
RELATIVE_RESULT = 'cells/D_hko__leaf/sdr/interchange/benchmarks.json'


def _require(test, message):
    if not test:
        raise ValueError(message)


def _fingerprint(request):
    # Identical to JudgeClient's full-request cache key, including Unicode.
    import hashlib
    return hashlib.sha256(json.dumps(request.cache_payload(), sort_keys=True,
                                    ensure_ascii=False).encode('utf-8')).hexdigest()


def _source_items(bench, cli):
    """Record every parquet file actually consulted by an offline loader."""
    consulted = []
    original = sources.read_parquet
    def tracked(directory, pattern='*.parquet'):
        consulted.extend(sorted(Path(directory).glob(pattern)))
        return original(directory, pattern)
    with patch.object(sources, 'read_parquet', tracked):
        items = bench.load(None, cli)
    if bench.name.startswith('mask:'):
        mask_dir = Path(cli.benchmark_repo_root) / 'mask/mask'
        consulted.extend(sorted((mask_dir / 'csv_data').glob('*.csv')))
        consulted.extend(sorted((mask_dir / 'results').rglob('*.csv')))
        # MASK belief files may live outside results; bind all local CSVs.
        consulted.extend(sorted(mask_dir.rglob('*.csv')))
    consulted.extend(Path(p) for p in bench.rubric_sources(cli))
    consulted.append(Path(__file__).parent / 'benchmarks' /
                     ('mask_bench.py' if bench.name.startswith('mask:') else
                      'liars_bench.py' if bench.name.startswith('lb:') else 'sandbagging.py'))
    return items, [binding(p) for p in sorted(set(consulted)) if p.is_file()]


def import_dataset(name, historical, bench, source_items, source_binding, screen_provenance):
    """Pure offline import; explicit source rows make this easy to audit/test."""
    items = historical['items']
    rows = historical['configs']['full']['labels']
    generations = historical['configs']['full']['generations']
    prompts = historical['prompts']
    partners = historical['partner_ids']
    _require(len(items) == historical['n_items'] == len(rows) == len(generations) == len(prompts) == len(partners),
             'historical row closure failed: ' + name)
    _require(len({r['item_id'] for r in items}) == len(items), 'duplicate selected item')
    by_id = {}
    for item in source_items:
        _require(item.item_id not in by_id, 'duplicate source item ID')
        by_id[item.item_id] = item
    kept, excluded, audit, kept_prompts, donor_ids = [], [], [], [], []
    for index, (record, row, response, prompt, donor_id) in enumerate(zip(items, rows, generations, prompts, partners)):
        item = BenchmarkItem(**record)
        source = by_id.get(item.item_id)
        _require(source is not None and source.messages == item.messages, 'recipient source prompt differs: ' + item.item_id)
        # Source beliefs can evolve; recipient beliefs MUST come from the
        # historical full rows. Keep the full original metadata verbatim.
        _require(row['label'] == DECEPTIVE, 'historical selected row was not deceptive')
        _require(not row.get('judge_error'), 'selected full row has judge error')
        label, raw = bench.parse_judgement(item, response, row.get('judge_text'))
        reason = None if label == DECEPTIVE else 'corrected_historical_intact_not_deceptive:' + str(raw)
        request = bench.judge_request(item, response)
        request_key = _fingerprint(request) if request else None
        if request:
            _require(request.prompt_text == row['judge_prompt'], 'historical judge prompt does not match exact current request')
        entry = dict(item_id=item.item_id, source_row_index=index,
                     original_label=copy.deepcopy(row), historical_generation=response,
                     corrected_label=label, corrected_raw=raw, exclusion_reason=reason,
                     exact_request_fingerprint=request_key, donor_id=donor_id)
        audit.append(entry)
        if reason:
            excluded.append(entry)
            continue
        kept.append(record)
        kept_prompts.append(prompt)
        donor_ids.append(donor_id)
        twin = bench.honest_twin(item)
        if twin is not None:
            _require(twin.item_id == donor_id, 'historical twin donor differs')
            by_id[twin.item_id] = twin
    used_ids = list(dict.fromkeys(donor_ids))
    _require(all(i in by_id for i in used_ids), 'required historical donor prompt absent from safe source')
    pool = []
    for donor_id in used_ids:
        # Honest condition documents the ORIGINAL reference selection, not a
        # new outcome claim. Missing donor beliefs remain None, never invented.
        pool.append(by_id[donor_id].replace(condition=HONEST).to_json())
    partner_index = [used_ids.index(i) for i in donor_ids]
    return dict(items=kept, prompts=kept_prompts, pool_items=pool,
                partner_index=partner_index, pairing=historical['reference']['pairing'],
                new_tokens=historical['new_tokens'], historical_full_audit=audit,
                excluded=excluded, historical_partner_ids=donor_ids,
                selection_provenance=dict(source=source_binding, historical_screen=screen_provenance,
                    historical_reference=historical['reference'],
                    selected_before_correction=len(items), selected_after_correction=len(kept),
                    donor_policy='original-native-used-partner-IDs; fresh same-path full donor generation',
                    unused_pool_items_recovered=False,
                    historical_pool_size=historical['reference']['pool_size'],
                    used_donor_count=len(pool),
                    selection_hardware='historical ' + str(screen_provenance.get('device')),
                    baseline_hardware='new execution; regenerate all intact and donor responses',
                    donor_belief_policy='not reconstructed or judged; recipient beliefs preserved verbatim'))


def import_judge_caches(repo_root, output_path):
    """Two named format-suite copies; last-write within, conflict-exclude across.

    This is an explicit versioned cache import, not an inferred unique original
    judgement. Request keys remain unchanged. Old caches are never modified.
    """
    originals = [Path(repo_root) / 'outputs' / suite / 'judge_cache.jsonl' for suite in SUITES]
    _require(Path(output_path).resolve() not in {p.resolve() for p in originals}, 'refusing to overwrite historical cache')
    copies, manifests = [], []
    for suite in SUITES:
        path = Path(repo_root) / 'outputs' / suite / 'judge_cache.jsonl'
        entries, count, differing = {}, 0, 0
        for line in path.read_text(encoding='utf-8').splitlines():
            if not line.strip():
                continue
            row = json.loads(line)
            _require(set(row) == {'key', 'text'} and isinstance(row['text'], str)
                     and len(row['key']) == 64 and all(c in '0123456789abcdef' for c in row['key']), 'invalid historical cache row')
            count += 1
            if row['key'] in entries and entries[row['key']] != row['text']:
                differing += 1
            entries[row['key']] = row['text']
        copies.append(entries)
        manifests.append(dict(source=binding(path), rows=count, unique_keys=len(entries),
                              differing_duplicate_occurrences=differing))
    all_keys = set().union(*(set(c) for c in copies))
    conflicts = sorted(k for k in all_keys if len({c[k] for c in copies if k in c}) > 1)
    merged = {k: next(c[k] for c in copies if k in c) for k in all_keys if k not in conflicts}
    Path(output_path).write_text(''.join(json.dumps(dict(key=k, text=merged[k]), ensure_ascii=False) + '\n'
                                       for k in sorted(merged)), encoding='utf-8')
    return dict(import_version=IMPORT_VERSION, sources=manifests,
                duplicate_policy='existing JudgeCache last-write-wins within each named source; differing cross-source keys excluded',
                cross_source_conflicting_keys=conflicts, output=binding(output_path),
                imported_bytes=Path(output_path).stat().st_size,
                historical_usage_and_cost='unavailable; never inferred from row count')


def prepare_fixed_cohort(alignment_root, output_path, cache_output_path=None):
    root = Path(alignment_root)
    repo = root / 'Deception-Circuit'
    cli = SimpleNamespace(benchmark_repo_root=str(root), benchmark_pool_size=None,
                          mask_judge_model='openai/gpt-4o', mask_numeric_judge_model='openai/o3-mini')
    datasets, sources_bound = {}, []
    for suite in SUITES:
        path = repo / 'outputs' / suite / RELATIVE_RESULT
        source = binding(path)
        saved = read_json(path)
        _require(saved['resolved']['ref_pool'] == 'honest' and saved['resolved']['ablation'] == 'interchange', 'unsupported historical donor policy')
        sources_bound.append(source)
        for name, historical in saved['datasets'].items():
            _require(name not in datasets, 'duplicate historical dataset')
            bench = get_benchmark(name)
            if hasattr(bench, 'bind'):
                bench.bind(cli)
            source_items, bounds = _source_items(bench, cli)
            sources_bound.extend(bounds)
            datasets[name] = import_dataset(name, historical, bench, source_items, source, saved['screen_cache'][name])
    mask_count = sum(len(d['items']) for k, d in datasets.items() if k.startswith('mask:'))
    _require(mask_count == 171 and sum(len(d['excluded']) for d in datasets.values()) == 2, 'expected exact two MASK exclusions')
    _require(len(datasets['sandbagging']['items']) == 50, 'sandbagging selected50 unavailable')
    _require(sum(len(d['items']) for k, d in datasets.items() if k.startswith('lb:')) == 150, 'LB fixed selected50x3 unavailable')
    _require(sum(len(d['items']) for d in datasets.values()) == 371, 'fixed cohort row closure differs')
    sources_bound.append(binding(__file__))
    unique = {b['path']: b for b in sources_bound}
    result = dict(schema_version=1, import_version=IMPORT_VERSION,
                  purpose='historical_selected_fixed_cohort_not_screen_cache', datasets=datasets,
                  source_bindings=list(unique.values()), no_refill=True, fresh_intact_required=True)
    if cache_output_path:
        result['judge_cache_import'] = import_judge_caches(repo, cache_output_path)
    _require(str(Path(output_path).resolve()) not in unique, 'refusing to overwrite historical cohort source')
    if cache_output_path:
        imported = {r['key']: r['text'] for r in (json.loads(line) for line in Path(cache_output_path).read_text(encoding='utf-8').splitlines())}
        checks = dict(exact_key_hits=0, exact_key_misses=0, historical_saved_text_differs_from_last_write=0)
        for row in datasets.values():
            for entry in row['historical_full_audit']:
                key = entry['exact_request_fingerprint']
                if key is None:
                    continue
                hit = key in imported
                entry['historical_cache_exact_key_hit'] = hit
                checks['exact_key_hits' if hit else 'exact_key_misses'] += 1
                if hit and imported[key] != entry['original_label']['judge_text']:
                    checks['historical_saved_text_differs_from_last_write'] += 1
        result['judge_cache_import']['selected_full_request_audit'] = checks
    result['content_sha256'] = digest(result)
    Path(output_path).write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    for dataset in datasets:
        load_fixed_cohort(output_path, dataset)
    return result


def load_fixed_cohort(path, dataset):
    data = read_json(path)
    _require(data.get('schema_version') == 1 and data.get('import_version') == IMPORT_VERSION
             and data.get('purpose') == 'historical_selected_fixed_cohort_not_screen_cache'
             and data.get('no_refill') is True and data.get('fresh_intact_required') is True,
             'unsupported fixed-cohort manifest')
    _require(data.get('content_sha256') == digest({k: v for k, v in data.items() if k != 'content_sha256'}), 'fixed cohort manifest content hash differs')
    for b in data['source_bindings']:
        check_binding(b)
    if 'judge_cache_import' in data:
        cache_import = data['judge_cache_import']
        imported_bytes = cache_import.get('imported_bytes')
        _require(type(imported_bytes) is int and imported_bytes >= 0, 'invalid or missing imported cache byte count')
        cache_path = Path(cache_import['output']['path'])
        historical_paths = {Path(s['source']['path']).resolve() for s in cache_import['sources']}
        _require(cache_path.resolve() not in historical_paths, 'study cache aliases historical source')
        with cache_path.open('rb') as handle:
            prefix = handle.read(imported_bytes)
        _require(len(prefix) == imported_bytes and hashlib.sha256(prefix).hexdigest() == cache_import['output']['sha256'], 'imported cache prefix differs')
        for source in data['judge_cache_import']['sources']:
            check_binding(source['source'])
        # Runtime cache may append new exact requests after preparation. Its
        # imported copy is bound at freeze; never mutate the historical source.
    _require(dataset in data['datasets'], 'dataset absent from fixed cohort: ' + dataset)
    row = data['datasets'][dataset]
    n = len(row['items'])
    _require(n > 0 and n == len(row['partner_index']) == len(row['prompts']) == len(row['historical_partner_ids']), 'fixed cohort row closure failed')
    _require(type(row['new_tokens']) is int and row['new_tokens'] > 0, 'invalid completion cap')
    items = [BenchmarkItem(**r) for r in row['items']]
    pool = [BenchmarkItem(**r) for r in row['pool_items']]
    _require(len({i.item_id for i in items}) == n and len({i.item_id for i in pool}) == len(pool), 'duplicate cohort/pool IDs')
    for item, p, donor_id in zip(items, row['partner_index'], row['historical_partner_ids']):
        _require(type(p) is int and 0 <= p < len(pool) and pool[p].item_id == donor_id, 'fixed partner mapping differs')
        _require(item.item_id != donor_id, 'identical self donor')
    # Recheck selected identity/prompt/belief/meta against immutable source JSON.
    original = read_json(check_binding(row['selection_provenance']['source']))['datasets'][dataset]
    by_id = {i['item_id']: i for i in original['items']}
    for item in row['items']:
        _require(by_id.get(item['item_id']) == item, 'selected item differs from historical source')
    audit = row['historical_full_audit']
    _require(len(audit) == len(original['items']) and len(row['excluded']) + n == len(audit), 'eligibility audit closure differs')
    kept = {i.item_id for i in items}
    _require(kept == {a['item_id'] for a in audit if a['exclusion_reason'] is None and a['corrected_label'] == DECEPTIVE}, 'eligibility identity closure differs')
    return copy.deepcopy(row)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--alignment-root', required=True)
    parser.add_argument('--output', required=True)
    parser.add_argument('--judge-cache-output')
    cli = parser.parse_args()
    result = prepare_fixed_cohort(cli.alignment_root, cli.output, cli.judge_cache_output)
    print(json.dumps(dict(datasets={k: len(v['items']) for k, v in result['datasets'].items()},
                          output=str(Path(cli.output).resolve())), sort_keys=True))


if __name__ == '__main__':
    main()
