# Interpretability tooling for head/MLP analysis of Llama-3.1-8B-Instruct

Research date: 2026-09-14. Target environment: HF weights, bf16, `transformers` 5.13.0, `torch` 2.11.0, one A100/A40 per Slurm job, no GPU on the login node (which runs `transformers` 4.57.3), no browser on compute nodes. Consumers: a human (later, with a browser) and a Claude Code agent (terminal only; can read PNG and text files).

Planned analyses: (1) per-head attention patterns aggregated over prompt segments at chosen query positions, split by metadata; (2) direct logit attribution (DLA) of heads and MLPs on a target-minus-distractor logit, plus a differential version across two conditions; (3) path patching (Wang et al. IOI / Goldowsky-Dill et al. 2023) with senders = heads, MLPs, embedding and receivers = head Q/K/V inputs, MLP inputs, logits, position-agnostic and position-specific; (4) per-head knockout ranking; (5) logit lens at one readout position.

All version/date facts below were pulled from the PyPI JSON API and the GitHub REST API on 2026-09-14, and from the installed `transformers` 5.13.0 source. Claims about behaviour were checked in repository source, not READMEs, where the two could differ.

---

## 1. Summary of recommendations

**(a) Compute side: `nnsight==0.7.0` on the raw HF model, with the path-patching inner loop written as plain `torch` forward hooks on the same HF modules. Do not adopt TransformerLens.**
Top reason: every sender and receiver in the planned path patching is an HF module boundary (`embed_tokens` output, `self_attn.o_proj` input for per-head outputs, `q_proj`/`k_proj`/`v_proj`, `mlp`, `lm_head`), so the analyses run against the unmodified HF model, in bf16, under SDPA for everything except pattern extraction, and inside the existing custom wrapper. nnsight is already used elsewhere in the Alignment repo (no version pinned there) and ships agent skills for exactly these recipes. Note that neither nnsight 0.7.0 nor TransformerLens 3.9.0 installs on the login-node base env (Python 3.9.18; both require Python >= 3.10), so environment portability is not a differentiator; only the plain-hook code runs there, which is one more reason to keep the hot loop in plain hooks.
Top risk: nnsight's `main` branch is the 0.8 "pipeline rewrite" (merged 2026-09-09, tag `v0.8.0.rc1`); the docs on `main` already describe 0.8 semantics and `transformers` 5.15. An agent that fetches docs from GitHub will read 0.8 docs while running 0.7.0. Mitigation: pin `nnsight==0.7.0`, vendor the 0.7.0 docs tree (or point the agent at the installed `nnsight` skills), and keep all hook code behind one in-repo adapter so a 0.8 migration touches one file.

**(b) Visualization: JSON/CSV first, then matplotlib PNG for everything, then standalone HTML (JS embedded, no CDN) only for the three analyses where hover or per-head toggling earns its place (attention patterns, DLA/path-patching heatmaps, logit lens).** No notebook in the loop. Do not rely on plotly static-image export on compute nodes; it needs Chrome (kaleido >= 1.0) and that has not been verified on the cluster.

**(c) Agent consumes: PNG (via image read), JSON/CSV/Markdown tables. HTML is only text to the agent; every HTML file must have a JSON twin.** Human-only: circuitsvis attention widgets, plotly hover/zoom.

---

## 2. Facts about the model and `transformers` 5.13 that constrain every tool

Verified by reading the installed `transformers` 5.13.0 source (`transformers/models/llama/modeling_llama.py`, `transformers/integrations/sdpa_attention.py`), mirrored at https://github.com/huggingface/transformers/blob/main/src/transformers/models/llama/modeling_llama.py and https://github.com/huggingface/transformers/blob/main/src/transformers/integrations/sdpa_attention.py.

- `LlamaAttention.forward` returns `(attn_output, attn_weights)`. Under `attn_implementation="sdpa"` the interface returns `attn_weights=None`; under `"eager"` it returns the post-softmax weights (softmax in fp32, cast to query dtype), shape `[batch, n_heads, q, k]`.
- `LlamaModel._can_record_outputs = {"attentions": LlamaAttention}`, so `output_attentions=True` collects whatever the attention module returns; under SDPA that is `None` (nnsight's docs confirm you get an empty tuple with no warning: https://github.com/ndif-team/nnsight/blob/main/docs/patterns/attention-patterns.md).
- `PreTrainedModel.set_attn_implementation` exists in 5.13, so one loaded model can be switched to eager for analysis (1) and back to SDPA for (2)-(5) without reloading (HF docs: https://huggingface.co/docs/transformers/en/attention_interface).
- GQA: 32 query heads, 8 KV heads, `head_dim` 128 (TransformerLens' own config for Llama-3.1-8B lists `n_key_value_heads: 8`, https://github.com/TransformerLensOrg/TransformerLens/blob/main/transformer_lens/loading_from_pretrained.py). `k_proj`/`v_proj` output `[batch, seq, 8*128]`. A "per-head K/V receiver" is therefore a per-KV-group receiver shared by 4 query heads. Any tool that offers 32 K/V heads (TransformerLens `ungroup_grouped_query_attention`, EAP-IG's required setting) is replicating the 8 real ones.
- Per-head output (the "z" / `hook_result` quantity) is the input to `o_proj`, laid out `[batch, seq, 32*128]`; slicing columns of the `o_proj` *output* is not a head (nnsight measured sign disagreement on 71/144 GPT-2 heads: https://github.com/ndif-team/nnsight/blob/main/docs/patterns/per-head-attention.md).

Memory under eager attention (needed only for analysis 1). Attention weights are `[batch, 32, seq, seq]` per layer; at batch 8, seq 1024, that is 512 MB bf16 per layer (1 GB transient fp32 during softmax), 16 GB if all 32 layers are kept. Per-head resid contributions `[batch, seq, 32, 4096]` are 2 GB bf16 per layer at the same batch. Consequence: aggregate patterns and DLA on the fly per layer (reduce over segments/positions inside the hook) instead of caching full tensors; weights alone are 16 GB on a 40 GB A100 or 48 GB A40.

---

## 3. Evidence table

| Package (pip name) | Latest release (PyPI upload date) | Last commit on default branch | `transformers` pin | Llama-3.1-8B | Verdict for this project |
|---|---|---|---|---|---|
| `transformer-lens` | 3.9.0 (2026-09-12) | 2026-09-11 | `>=5.9.0`, `torch>=2.6`, py `>=3.10,<4` | Yes (bridge registry lists `meta-llama/Llama-3.1-8B-Instruct`) | Works on 5.13; forces eager; legacy API deprecated; py >= 3.10 |
| `nnsight` | 0.7.0 (2026-05-05) | 2026-09-09 (0.8 rewrite merged) | unpinned (`transformers`), `torch>=2.4`, py `>=3.10` | Yes (HF model as-is) | Recommended; pin 0.7.0; py >= 3.10 |
| `nnterp` | 1.3.0 (2026-02-28) | 2026-07-02 (repo moved to `ndif-team/nnterp`) | `nnsight>=0.6`, `transformers` unpinned | Yes | Optional sugar over nnsight; not needed for Llama naming |
| `pyvene` | 0.1.8 (2025-05-26) | 2026-03-06 | release `>=4.45.1`; `main` `>=4.55.0.dev0`; no 5.x statement | Yes, with GQA-aware per-head mapping | No release in 16 months; untested on 5.x |
| `circuitsvis` | 1.43.3 (2024-12-18) | 2026-04-30 (housekeeping only) | none (`torch>=2.1.1`, numpy) | n/a (takes tensors) | Usable; pure JS; bundle is inlined for offline HTML |
| `bertviz` | 1.4.1 (2025-06-01) | 2026-01-08 (README) | `transformers>=2.0` | Any attention tuple | HTML output needs cdnjs (require.js, d3); Jupyter-oriented |
| `auto-circuit` | 1.0.1 (2024-08-24) | 2026-08-17 | via `transformer-lens>=1.13`; pins `kaleido==0.2.1` | Only through TL `HookedTransformer` | TL-legacy only; kaleido pin conflicts with plotly >= 6 |
| ACDC (`Automatic-Circuit-Discovery`, git only) | none | 2024-10-01 ("Suggest AutoCircuit") | `transformers ^4.35`, `torch <2.0`, `transformer-lens 1.6.1` | No | Unmaintained; incompatible |
| EAP-IG (`eap`, git only) | 2.0.0 in pyproject, not on PyPI | 2026-05-23 | `transformer-lens>=2.15.0`; imports `HookedTransformer` | Yes, with `ungroup_grouped_query_attention=True` | Reusable ideas (Q/K/V-input edges), not reusable code on HF Llama |
| `inseq` | 0.7.1 (2026-03-06) | 2026-04-25 | `>=4.53.0`, captum | Yes | Feature attribution (captum), not head-level path patching |
| `tuned-lens` | 0.2.0 (2023-07-18) | 2025-08-07 | `>=4.28.1` | Untested | Stale; logit lens is 10 lines by hand |
| `baukit` (git only) | none | 2024-02-22 | none | Any module | Stale; nothing nnsight does not do |
| `plotly` | 7.0.0 (2026-08-25) | active | n/a | n/a | HTML export good; PNG export needs Chrome |
| `kaleido` | 1.4.0 (2026-08-31) | 2026-09-03 | n/a | n/a | Requires Chrome; unverified on cluster |
| `matplotlib` | 3.11.0 (installed) | active | n/a | n/a | Safe headless PNG path |
| Neuronpedia (self-host repo) | v2.6.0 (2026-09-14) | 2026-09-14 | uses TransformerLens/SAELens in its inference server | Base only, SAE features | Not useful for head-level custom circuits |
| `sae-lens` | 6.51.0 (2026-09-11) | 2026-09-11 | `>=4.38.1,<6.0.0` | SAEs only | Out of scope (no SAEs planned) |

Sources for the table: PyPI JSON for each package (`https://pypi.org/pypi/<name>/json`), GitHub `repos/<owner>/<repo>` and `commits?per_page=1` endpoints, plus the repository files cited in the per-tool sections below.

---

## 4. Per-tool findings

### 4.1 TransformerLens 3.9.0

Sources: https://github.com/TransformerLensOrg/TransformerLens (README, `pyproject.toml`, `transformer_lens/HookedTransformer.py`, `transformer_lens/model_bridge/bridge.py`, `transformer_lens/model_bridge/generalized_components/attention.py`, `transformer_lens/loading_from_pretrained.py`, `docs/source/content/migrating_to_v3.md`, `docs/source/content/model_structure.md`), https://TransformerLensOrg.github.io/TransformerLens/content/migrating_to_v3.html, https://pypi.org/project/transformer-lens/.

- **Maintenance:** very active (release 3.9.0 on 2026-09-11; commits on 2026-09-14). `pyproject.toml` requires `transformers>=5.9.0`, `torch>=2.6`. That satisfies the 5.13 job env and excludes the 4.57.3 login env.
- **Two APIs.** `HookedTransformer.from_pretrained` now raises `DeprecationWarning` ("deprecated and will be removed in 4.0. Use `TransformerBridge.boot_transformers(...)`"). The bridge wraps the real HF module graph with adapters and "returns raw HF weights by default — logits/activations match HF, not legacy HookedTransformer".
- **Weight-processing defaults that change numerics.** Legacy `from_pretrained` defaults: `fold_ln=True`, `center_writing_weights=True`, `center_unembed=True`, `fold_value_biases=True`, `refactor_factored_attn_matrices=False`. On the bridge none are applied unless you call `bridge.enable_compatibility_mode()`. The migration guide's table: generated text, CE loss, argmax "identical"; raw logits "differ by per-row constant"; "logit lens, direct logit attribution" "differ" without compat mode; residual norms "differ (grows with depth)". For DLA you must either enable compat mode (and then compare against nothing else) or do the final-norm scaling yourself.
- **Attention implementation is forced to eager.** `boot_transformers` docstring: "Attention implementation is forced to `"eager"` so hooks can capture scores and patterns. ... comparing against the default `"sdpa"` shows ~1e-3 fp32 drift from kernel-level op reordering". `hook_pattern` only fires when the HF attention returns a 4-D weights tensor (`attention.py` lines ~838-845). So every TL run pays the eager memory cost from section 2, even for patching that does not need patterns.
- **Per-head Q/K/V/pattern/result.** Bridge exposes `blocks.{i}.attn.hook_pattern` `(n_heads, pos, pos)`, legacy aliases `hook_q/k/v`, `hook_q_input/k_input/v_input`, and `attn.hook_result` gated by `cfg.use_attn_result`. Llama uses `PositionEmbeddingsAttentionBridge`, which is in the class list that supports `use_attn_result`, `use_split_qkv_input`, `use_attn_in` (`bridge.py` `_validate_attention_fork_supported`). Legacy `set_ungroup_grouped_query_attention` exists on `HookedTransformer`; I found no bridge equivalent, so per-KV-group semantics apply on the bridge (verify before relying on it).
- **Llama-3.1-8B specifics.** The legacy config caps `n_ctx` at 2048 ("capped due to memory issues"). The bridge takes `n_ctx` from the HF config and accepts an override.
- **Memory for 8B bf16.** `dtype=torch.bfloat16` is supported; the weights are the HF weights (16 GB). Eager attention plus optional `use_attn_result` add the tensors quantified in section 2.
- **Verdict.** Feature-complete for the five analyses, but: (i) the supported API is one major version old and still migrating ("every feature is being migrated to TransformerBridge"); (ii) eager everywhere; (iii) compat-mode numerics diverge from HF; (iv) the wrapper cannot host the project's custom HF wrapper. The ecosystem tools that would justify it (EAP-IG, auto-circuit) still target the deprecated `HookedTransformer`. (Its `transformers>=5.9.0` and Python >= 3.10 requirements exclude the login-node env, but nnsight's Python >= 3.10 does too, so that is not a differentiator.)

### 4.2 nnsight 0.7.0

Sources: https://github.com/ndif-team/nnsight (README, `pyproject.toml`, `docs/patterns/attention-patterns.md`, `docs/patterns/per-head-attention.md`, `docs/patterns/activation-patching.md`, `docs/usage/invoke-and-batching.md`, `docs/concepts/source-tracing.md`, `docs/models/transformers-model.md`, tag `v0.7.0` with `0.7.0.md` release notes, `.github/workflows/python-app.yml`), https://pypi.org/project/nnsight/, https://nnsight.net/documentation/.

- **Maintenance:** PyPI 0.7.0 on 2026-05-05; `main` merged "dev into main — the 0.8 pipeline rewrite" on 2026-09-09; tag `v0.8.0.rc1` exists. `transformers` is unpinned; the 0.7.0 CI installs `pip install ./` with whatever `transformers` resolves (5.x by May 2026). Docs on `main` cite "transformers 5.15 on nnsight 0.8".
- **Per-head access on HF Llama.** Documented three ways: reshape `self_attn.output[0]` (post-`o_proj`, *wrong* for ablation), read `.source.attention_interface_1.output[0]` (already `[batch, seq, n_heads, head_dim]`, pre-`o_proj`), or slice `attn.o_proj.input` ("equivalent"). Use `o_proj.input` for senders and knockouts: it is a module boundary and stable across versions. The `.source` op names (`attention_interface_1`, `nn_functional_softmax_0`) are taken from `main` docs that self-identify as "transformers 5.15 on nnsight 0.8"; verify them on 0.7.0 by printing `.source` before relying on them.
- **Attention patterns need eager.** "You need `attn_implementation="eager"` to get attention weights ... `sdpa` ... returns `None` for the weights". Under eager, `model.model.layers[i].self_attn.output[1]` is `[batch, n_heads, q, k]`; `model.output.attentions` gives all layers. `.source` can also reach the raw fp32 softmax before the cast. `attn_implementation` is forwarded to `from_pretrained` (`docs/models/transformers-model.md`), and `set_attn_implementation` on the underlying HF model lets you flip per analysis.
- **Batching interventions.** `with model.trace() as tracer:` with several `tracer.invoke(prompt)` blocks runs one batched forward where each block sees only its rows; cross-invoke hand-off (clean into corrupt) needs `tracer.barrier(n)`. The docs quantify batch-composition drift: ~2e-5 logits in fp32 on Llama-3.2-1B, "in bf16 it is comparable to the metric quantum and can reorder a head ranking, so read a ranking metric through an fp32 head." Apply that to analyses (2)-(4): compute the logit-difference metric in fp32.
- **Agent support.** The README documents Claude Code skills (`ndif-team/skills`), and this workspace already has `nnsight:activation-patching`, `nnsight:attribution-patching`, `nnsight:logit-lens`, `nnsight:nnsight-basics` installed.
- **Verdict.** Best fit: real HF model, SDPA except for (1), batched invokes, remote NDIF path if 70B is needed later. Requires Python >= 3.10, so it runs in the `mgnp` job env (3.12) but not the login-node base env (3.9). Risks: 0.8 churn (pin 0.7.0), deferred-execution error modes (`docs/errors/`) that are harder for an agent to debug than plain hooks, and the eager requirement for patterns (shared with every other tool).

### 4.3 nnterp 1.3.0

Sources: https://github.com/ndif-team/nnterp (README, `pyproject.toml`, `nnterp/standardized_transformer.py`, `docs/model-validation.rst`), https://pypi.org/project/nnterp/, paper https://arxiv.org/abs/2511.14465, https://nnsight.net/blog/2026/02/26/nnterp-integration/.

- Renames any HF model to Llama-style names (`layers`, `self_attn`, `mlp`, `ln_final`, `lm_head`) on top of nnsight and validates shapes on load. `StandardizedTransformer(..., enable_attention_probs=True)` forces `attn_implementation="eager"` and raises if you pass anything else; `attention_probabilities[i]` then returns validated, normalized matrices.
- Since the target already *is* Llama, the renaming adds nothing; the only value is the validated `attention_probabilities` accessor. Optional.

### 4.4 pyvene 0.1.8

Sources: https://github.com/stanfordnlp/pyvene (README, `pyproject.toml`, `pyvene/models/llama/modelings_intervenable_llama.py`), https://pypi.org/project/pyvene/.

- Last PyPI release 2025-05-26 (`transformers>=4.45.1`); `main` requires `>=4.55.0.dev0`; last commit 2026-03-06 "Fix head_dim fallback in per-head dimension mappings for GQA models". No statement of `transformers` 5 support in README, pyproject, or issues (GitHub issue search for "transformers 5" returned nothing relevant).
- Llama mapping is GQA-aware and hits the right module boundaries: `head_attention_value_output` = `o_proj` input split by `n_head`; `head_key_output`/`head_value_output` split by `n_kv_head`; `mlp_input`/`mlp_output`; `attention_input`. Interventions are serialisable dicts, which is nice for agent-written configs.
- Verdict: correct model in principle, but no release in 16 months and no 5.x evidence. Not worth the risk over nnsight.

### 4.5 CircuitsVis 1.43.3

Sources: https://github.com/TransformerLensOrg/CircuitsVis (`python/circuitsvis/utils/render.py`, `python/circuitsvis/attention.py`, `python/pyproject.toml`), https://pypi.org/project/circuitsvis/, wheel contents of `circuitsvis-1.43.3-py3-none-any.whl`.

- **Standalone HTML, headless:** yes. `render_local()` reads the bundled `circuitsvis/dist/cdn/iife.js` (present in the PyPI wheel) and inlines it into a `<script type="module">` with a `<div>`; it is a pure string operation, no notebook or browser needed. `render_cdn()` instead imports `https://unpkg.com/circuitsvis@<ver>/dist/cdn/esm.js`.
- **Trap:** `str(RenderedHTML)` and `.show_code()` return the **CDN** version; `_repr_html_()` picks local only in dev mode or when `internet_on()` fails (it probes `http://google.com` with a 1 s timeout). Write `rendered.local_src` to disk explicitly. The inlined bundle (`dist/cdn/iife.js`) is 1.30 MB in the 1.43.3 wheel, so each standalone HTML file is at least that size plus the attention data; put related widgets in one file to avoid repeating the bundle, or accept ~1.3 MB per file.
- **Widgets:** `attention_patterns(tokens, attention[heads, dest, src])` (per-head selector, token hover), `attention_heads(...)`, `attention_pattern(...)` for one head. All take `list`/`np.ndarray`/`torch.Tensor`.
- **Maintenance:** no release since 2024-12-18; last commit 2026-04-30 (devcontainer removal). Deps are only `numpy` and `torch>=2.1.1`, so nothing to break on `transformers` 5.

### 4.6 bertviz 1.4.1

Sources: https://github.com/jessevig/bertviz (README, `bertviz/head_view.py`, `bertviz/head_view.js`), https://pypi.org/project/bertviz/.

- `head_view(attention, tokens, html_action='return')` returns an `IPython.display.HTML` whose body loads `require.js` from cdnjs and `d3` 5.7.0 from cdnjs (`head_view.js` `require.config`). So the file is standalone but **not offline**, and it needs IPython installed to build. Model view same pattern. Neuron view only supports custom BERT/GPT-2/RoBERTa classes.
- Accepts any tuple of `[batch, heads, q, k]` tensors, so eager Llama attentions work. Last commit 2026-01-08 (README only), release 2025-06-01. Verdict: superseded by circuitsvis for this use; keep out.

### 4.7 Neuronpedia

Sources: https://github.com/hijohnnylin/neuronpedia (README; release v2.6.0 2026-09-14), https://www.neuronpedia.org/llama3.1-8b, https://www.neuronpedia.org/llama-scope.

- Self-hostable: Postgres + Next.js webapp + Python inference server (`make inference-dev MODEL_SOURCESET=...`), plus optional graph server built on `circuit-tracer` (transcoders) and an autointerp server. Runs locally at `localhost:3000/5002`; models load from the HF cache.
- Everything is organised around SAE "sources"; the inference server loads a model plus SAE sets, and the hosted Llama entry is `llama3.1-8b` **Base** with Llama Scope (OpenMOSS) and EleutherAI Multi-TopK SAEs. No Instruct model, no attention-pattern or per-head pages.
- Verdict: no value for head-level circuit work without SAEs. Do not self-host for this project.

### 4.8 auto-circuit, ACDC, EAP-IG

Sources: https://github.com/UFO-101/auto-circuit (`pyproject.toml`, `auto_circuit/utils/graph_utils.py`), https://pypi.org/project/auto-circuit/, https://github.com/ArthurConmy/Automatic-Circuit-Discovery (`pyproject.toml`), https://github.com/hannamw/EAP-IG (README, `pyproject.toml`, `src/eap/graph.py`).

- **auto-circuit 1.0.1:** edge-level patching with a proper sender/receiver graph including Q/K/V receivers, several ablation types, Plotly circuit visualization. But `graph_utils.py` branches on `isinstance(model, HookedTransformer)` (TL legacy, deprecated), and `pyproject.toml` pins `kaleido==0.2.1`, which conflicts with plotly >= 6 (kaleido >= 1 required for image export). Last release 2024-08-24; commits continue (2026-08-17). Reuse the *design* (edge enumeration, position-specific receivers), not the code.
- **ACDC:** pins `torch>=1.10,<2.0`, `transformers ^4.35`, `transformer-lens 1.6.1`; last commit 2024-10-01 points users to auto-circuit. Unmaintained and incompatible with this stack.
- **EAP-IG (`eap` 2.0.0, git-only):** `transformer-lens>=2.15.0`, imports `HookedTransformer`; README says Llama-3 8B works with `model.cfg.ungroup_grouped_query_attention = True` ("this will remove all of the efficiency benefits of GQA"). Its `Graph` models each head with three inputs (Q, K, V) and edges through the residual stream, which is exactly the receiver set planned here; the implementation is TL-bound. Visualization needs system graphviz.

### 4.9 Other visualizers

- **plotly 7.0.0** (https://pypi.org/project/plotly/, https://plotly.com/python-api-reference/generated/plotly.io.write_html.html, https://plotly.com/python/static-image-export/). `write_html(include_plotlyjs=True)` inlines plotly.js ("~3MB ... fully self-contained and can be used offline"); `include_plotlyjs='directory'` writes one `plotly.min.js` next to the files ("can be used offline, but they require a copy of the plotly.min.js bundle"); `'cdn'` needs internet. Static images: "Static image generation requires Kaleido version 1.0.0 or greater" and "Starting with Kaleido version 1.0.0, Chrome is not included in the package itself".
- **kaleido 1.4.0 / choreographer 1.3.0** (https://github.com/plotly/kaleido, https://pypi.org/project/kaleido/, https://github.com/plotly/choreographer, wheel sources). `kaleido_get_chrome` downloads Chrome for Testing into `platformdirs` user data (Linux: `~/.local/share/choreographer/deps/chrome-linux64/chrome`), no root. choreographer launches with `--headless`, `--no-sandbox` and `--disable-gpu` by default (`browsers/chromium.py`; `enable_sandbox` defaults to `False`, `headless` to `True`), and honours `BROWSER_PATH`. Unverified: whether Chrome for Testing's shared-library dependencies exist on the compute-node image. Treat plotly PNG export as optional and test it once on a compute node before depending on it.
- **matplotlib 3.11.0** (installed): `Agg` backend PNG/PDF/SVG, no display. The safe path for every agent-readable figure.
- **inseq 0.7.1** (https://github.com/inseq-team/inseq): captum-based input attribution for HF decoders (transformers >= 4.53), maintained (2026-04-25). Not head/path level; mention only.
- **tuned-lens 0.2.0, baukit:** stale (2023 release; 2024 last commit). Logit lens by hand: apply `model.model.norm` then `lm_head` to the residual at the readout position, as nnsight's README shows.

---

## 5. Recommendation (a): compute-side library

**Choose nnsight 0.7.0 (`pip install "nnsight==0.7.0"`) over TransformerLens 3.9.0.**

Module paths on HF Llama (`model.model.layers[i]`):

| Quantity | Access | Notes |
|---|---|---|
| Embedding output (sender) | `model.model.embed_tokens.output` | |
| Per-head output z (sender, knockout) | `layers[i].self_attn.o_proj.input`, view `[B, S, 32, 128]` | not the `o_proj` output |
| Head Q/K/V inputs (receivers) | `layers[i].self_attn.q_proj.input` etc. (shared normalized residual) | per-head receiver = recompute only head h's slice of `q_proj.output` from the patched input; K/V receivers are per KV group (8) |
| Attention pattern | `layers[i].self_attn.output[1]` under eager; `None` under SDPA | eager only for analysis (1) |
| MLP input / output | `layers[i].mlp.input` / `.output` | |
| Residual for logit lens | `layers[i].output[0]` then `model.model.norm`, `model.lm_head` | |
| Logits | `model.lm_head.output` | for ranking metrics, upcast the final-norm output to fp32 and apply `lm_head` (or `W_U`) in fp32; calling `.float()` on bf16 logits recovers nothing |

Top reason: the analyses run on the unmodified HF model in the project's own wrapper, under SDPA for (2)-(5), with batched invokes for clean/corrupt pairs, and with agent skills already installed. TransformerLens would force eager on every run, deprecates the API the ecosystem tools use, and changes DLA/logit-lens numerics in compat mode. Neither library installs on the login-node env (Python 3.9), so the only code that runs everywhere is plain torch hooks.

Top risk: 0.8 API churn and doc/version skew for the agent. Pin 0.7.0, isolate hook code in one adapter module, and write the path-patching sweep (analysis 3) as plain `register_forward_hook`/`register_forward_pre_hook` calls on the same modules so the hot loop is explicit, batched, and debuggable; validate the plain-hook implementation against nnsight on a handful of (sender, receiver, position) cells before running the full sweep. Second risk: bf16 batch-composition drift can reorder head rankings (nnsight docs); fix the batch composition across conditions and read every ranking metric through an fp32 head (fp32 final norm and unembed), not by upcasting bf16 logits after the fact.

Numerics to record in every run manifest: `attn_implementation`, dtype, batch composition, whether patterns came from eager (they must), and the `nnsight`/`transformers` versions.

---

## 6. Recommendation (b): visualization format per analysis

Principle: emit the data once (JSON/CSV/`.pt`), render PNG for every figure with matplotlib, and add a standalone HTML only where interaction pays. All HTML must embed its JS (no CDN) because the human may open the files from a cluster mount without internet, and the agent never renders them.

| Analysis | Source-of-truth data | Agent view (PNG via matplotlib) | Human view (HTML, JS embedded) |
|---|---|---|---|
| (1) Attention patterns, aggregated by segment / query position / metadata | `attn_agg.json` or parquet: `[layer, head, query_pos_group, segment] -> mean mass`; per-example raw patterns only for a shortlist of prompts | segment x segment heatmap per (layer, head) shortlist; layer x head "mass on segment S" grid | `circuitsvis.attention_patterns(...)` written via `.local_src` for the shortlisted prompts; plotly heatmap with hover for the aggregated grid (`include_plotlyjs='directory'`) |
| (2) DLA and differential DLA | `dla.csv`: `layer, head/mlp, condition, contribution` plus the token pair and readout position | layer x head heatmap (diverging colormap, symmetric limits), separate MLP bar row; differential = A minus B with the same limits | plotly heatmap with hover showing head id, value, per-condition values |
| (3) Path patching | `path_patch.parquet`: `sender, receiver, position, metric_delta, baseline` (position = "all" for agnostic) | one layer x head heatmap per receiver (Q, K, V of a receiver head; MLP input; logits); top-k edge table as Markdown | plotly heatmaps with a receiver dropdown or one file per receiver; optional graph of top-k edges via `graphviz` only if `dot` exists on the node (unverified) |
| (4) Knockout ranking | `knockout.csv`: `layer, head, metric_delta, rank` | horizontal bar chart of top-N and bottom-N; layer x head heatmap | none needed beyond the CSV; plotly optional |
| (5) Logit lens | `logit_lens.json`: per layer top-k tokens, probs, target/distractor logit and rank | layer x top-k text grid (matplotlib table) plus line plot of target minus distractor logit by layer | plotly heatmap with token strings in hover |

Package versions: `matplotlib==3.11.0` (installed), `plotly==7.0.0`, `circuitsvis==1.43.3`. Do not add `kaleido` unless a compute-node test shows Chrome for Testing launches; if it does, `kaleido==1.4.0` plus `kaleido_get_chrome` gives PNG from plotly, but matplotlib already covers the PNG need.

No notebook in the pipeline. Scripts write to `outputs/<run>/` with `json/`, `png/`, `html/` subfolders and a `manifest.json` listing every file, its analysis, and the config. The human opens `html/` in a browser; the agent reads `png/` and `json/`.

---

## 7. Recommendation (c): what the agent consumes versus what only a human needs

Agent (terminal-only, can read images and text):
- PNG figures from matplotlib (heatmaps, bar charts, tables rendered as images). Keep each under ~2000 px wide and label axes with layer/head indices so values can be read back.
- JSON/CSV/parquet tables and Markdown summaries with the top-k rows already sorted. These are what the agent should reason from; PNGs are for sanity checks.
- The run manifest, so it can cite exact files and configs.

Human only:
- circuitsvis attention widgets (per-head toggling, token hover) and plotly heatmaps (hover values, zoom). To the agent these are large text files; it cannot render them and should not try to parse them.

Rule: every HTML file has a JSON twin produced from the same array, so nothing the human sees is unavailable to the agent.

---

## 8. Flags: unmaintained or incompatible with this stack

- **ACDC:** `torch<2.0`, `transformers ^4.35`, `transformer-lens 1.6.1`; last commit 2024-10-01. Do not install.
- **auto-circuit 1.0.1:** `kaleido==0.2.1` pin conflicts with plotly >= 6 image export; requires TL `HookedTransformer` (deprecated in TL 3.x). Design reference only.
- **EAP-IG:** TL `HookedTransformer` only; git install; ungrouped GQA replicates K/V heads.
- **TransformerLens 3.9.0:** forces eager attention; legacy `HookedTransformer` API deprecated; compat-mode weight processing changes DLA/logit-lens numerics relative to HF. Requires `transformers>=5.9.0` and Python >= 3.10.
- **Login-node base env (Python 3.9.18, transformers 4.57.3):** neither `nnsight` 0.7.0 nor `transformer-lens` 3.9.0 installs there (both `requires_python >=3.10`). Library-based analyses run only in the `mgnp` job env; plain-hook code is the only part that runs in both.
- **pyvene 0.1.8:** no release since 2025-05-26; no `transformers` 5 support statement.
- **circuitsvis 1.43.3:** no release since 2024-12; functional, but `str()` of the render object is the CDN variant. Use `.local_src`.
- **bertviz 1.4.1:** HTML depends on cdnjs (require.js, d3); needs IPython to build.
- **tuned-lens 0.2.0 (2023), baukit (2024):** stale; not needed.
- **Neuronpedia:** SAE-centric; hosted Llama-3.1-8B is the base model; no head-level views.
- **kaleido >= 1.0:** needs Chrome; not verified on compute nodes.

---

## 9. Open items to verify on the cluster before building

1. `nnsight==0.7.0` imports and traces Llama-3.1-8B-Instruct under `transformers` 5.13.0 in the `mgnp` env (GPU job). The login node cannot host it (Python 3.9); smoke-test plain-hook code there instead.
2. `model.set_attn_implementation("eager")` then back to `"sdpa"` on the same loaded model gives identical logits up to the ~1e-3 fp32 / bf16-quantum drift documented by TransformerLens and nnsight.
3. Peak memory for one eager forward at the planned batch and sequence length (section 2 estimates), to size analysis (1).
4. Whether `dot` (graphviz) and Chrome for Testing run on a compute node; both are optional.

---

## 10. Source list

- TransformerLens: https://github.com/TransformerLensOrg/TransformerLens ; https://pypi.org/project/transformer-lens/ ; https://TransformerLensOrg.github.io/TransformerLens/content/migrating_to_v3.html ; raw files `pyproject.toml`, `transformer_lens/HookedTransformer.py`, `transformer_lens/loading_from_pretrained.py`, `transformer_lens/model_bridge/bridge.py`, `transformer_lens/model_bridge/generalized_components/attention.py`, `transformer_lens/model_bridge/supported_architectures/llama.py`, `transformer_lens/tools/model_registry/data/supported_models.json`, `docs/source/content/model_structure.md`
- nnsight: https://github.com/ndif-team/nnsight ; https://pypi.org/project/nnsight/ ; https://nnsight.net/documentation/ ; `docs/patterns/attention-patterns.md`, `docs/patterns/per-head-attention.md`, `docs/patterns/activation-patching.md`, `docs/usage/invoke-and-batching.md`, `docs/concepts/source-tracing.md`, `docs/models/transformers-model.md`, tag `v0.7.0` (`0.7.0.md`, `pyproject.toml`, `.github/workflows/python-app.yml`)
- nnterp: https://github.com/ndif-team/nnterp ; https://pypi.org/project/nnterp/ ; https://arxiv.org/abs/2511.14465 ; https://nnsight.net/blog/2026/02/26/nnterp-integration/
- pyvene: https://github.com/stanfordnlp/pyvene ; https://pypi.org/project/pyvene/ ; `pyvene/models/llama/modelings_intervenable_llama.py`
- CircuitsVis: https://github.com/TransformerLensOrg/CircuitsVis ; https://pypi.org/project/circuitsvis/ ; `python/circuitsvis/utils/render.py`, `python/circuitsvis/attention.py`
- bertviz: https://github.com/jessevig/bertviz ; https://pypi.org/project/bertviz/ ; `bertviz/head_view.py`, `bertviz/head_view.js`
- Neuronpedia: https://github.com/hijohnnylin/neuronpedia ; https://www.neuronpedia.org/llama3.1-8b ; https://www.neuronpedia.org/llama-scope
- auto-circuit: https://github.com/UFO-101/auto-circuit ; https://pypi.org/project/auto-circuit/ ; ACDC: https://github.com/ArthurConmy/Automatic-Circuit-Discovery ; EAP-IG: https://github.com/hannamw/EAP-IG
- plotly / kaleido / choreographer: https://pypi.org/project/plotly/ ; https://plotly.com/python-api-reference/generated/plotly.io.write_html.html ; https://plotly.com/python/static-image-export/ ; https://github.com/plotly/kaleido ; https://pypi.org/project/kaleido/ ; https://github.com/plotly/choreographer ; https://pypi.org/project/choreographer/
- transformers: https://huggingface.co/docs/transformers/en/attention_interface ; https://github.com/huggingface/transformers/blob/main/src/transformers/models/llama/modeling_llama.py ; https://github.com/huggingface/transformers/blob/main/src/transformers/integrations/sdpa_attention.py
- Others: https://github.com/inseq-team/inseq ; https://github.com/AlignmentResearch/tuned-lens ; https://github.com/davidbau/baukit ; https://github.com/decoderesearch/SAELens
