# SDR shared head position findings

**The shared 32 heads transfer donor influence from both context and supplied assistant-prefix positions, with effects that depend on which other positions are also patched.** This constrains shared-core influence while leaving deception unexplained.

We reused eight neutral fixtures and shared heads S=D∩H∩F, plus one layer/count-matched outside set C_S. Donors reversed either answer-example order (E) or factual truth (T). Early replacement covered positions before the assistant header; tail replacement covered the supplied assistant header and answer stem. Full combined both. These are head-output token positions, not attention source tokens or early/late layers. Generated tokens were excluded; all MLPs remained active.

Donor-example choices mean choices of the donor’s first answer example, distinct from copying its emitted answer. Counts show these choices for E and donor-truth choices for T:

| Treatment | Heads | Base | Early | Tail | Full |
|---|---|---:|---:|---:|---:|
| E reporting /256 | S | 46 | 106 | 202 | 206 |
| E reporting /256 | C_S | 46 | 46 | 7 | 3 |
| T reporting /256 | S | 86 | 177 | 141 | 168 |
| T reporting /256 | C_S | 86 | 73 | 71 | 56 |
| T retrieval /128 | S | 0 | 84 | 43 | 99 |
| T retrieval /128 | C_S | 0 | 1 | 0 | 0 |

**Tail replacement carries most of the aggregate example-transfer effect, but context still matters.** For S, early replacement adds 60/256 donor-example choices alone but only 4/256 given tail replacement; tail adds 156/256 alone and 100/256 given early. Tail increases example following in every fixture in both backgrounds. Close aggregate tail/full counts do not imply the same individual answers.

Factual transfer has a different conditional profile. In reporting, tail adds 55/256 donor-truth choices alone but reduces them 9/256 after early replacement. In retrieval, early adds 84/128 alone and 56/128 given tail. Non-additive effects can reflect overwrite and readout nonlinearities. The input changes differ in location and intact responsiveness, so this does not isolate encoding preferences or establish redundancy, competition or a natural route.

All 4,224 responses reached EOS: 4,220 commitments and four contradictions, all retained. All 15,411 main numerical comparisons passed bitwise with zero maximum error; fresh blinded raters agreed across 95 views. Independent arithmetic passed 1,416,357 scalar and 61,566 structural comparisons. Parent replay matched semantic categories in 1,654/1,664 rows across A100/H200; it is descriptive cross-hardware evidence. Phase cost: 1,512 actual A100 GPU-seconds versus 4,500 reserved, $0 API. [Technical evidence](../../.scratch/sdr-cue-followup/analysis.md).

The remaining bottleneck is behavioral identification: this neutral scaffold does not establish pressure mediation, intent, latent knowledge, clean selectivity, deception-specific function or OOD transfer. Earlier failed gates remain closed. No new experiment follows automatically.
