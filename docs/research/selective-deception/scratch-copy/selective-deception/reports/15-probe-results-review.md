# Probe result review checkpoint

Root records the independently delivered Astra review message; the reviewer completed verification but its turn then hit model capacity before the planned final write. No decision is inferred from that failure.

All24 CPU BF16 vocabulary vectors were independently loaded/hash-checked (128256 values each). For allfour prompts B=C=E=B_repeat=C_repeat bitwise, maximumdifference0. S/C exactly reproduced saved smoke D/H logits, margins and argmaxIDs. S-minus-B changed114168/113990/115020/117995 entries, maxabsolute0.140625/0.25/0.25/0.12890625. SDPA metadata confirms implicitcausal+GQA S versus matching explicit4Dmasks/repeatedKV B/C/E.

This meets report10 first predeclared branch: causal-mask/dispatch path explains observed identity failure; no gateidentity fault. Approved minimal runner-only no-donor dual-self baseline for intactrecipients and donordiagnostics, threshold unchanged, source/runidentity renewed. Focused regression tests and a fresh same-IDsmoke mustpass beforebounded fullrun. Root independently extracted the same numeric comparison summary.

Probe job22994714 completed77sec A100gpuc02. Outputs: ../probes/score-paths-001/. Original sourceef8cc2a; scriptSHA247a9535b149a64503f7519cf3e4ecad813ced6220653c61a4a8c7fffcc3bfeb. CPU-vs-GPU softmax probabilities are secondary; exactlabel-logit reproduction and saved vector comparisons govern.
