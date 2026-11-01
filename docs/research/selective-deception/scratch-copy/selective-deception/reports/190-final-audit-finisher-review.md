# 190 — Independent one-shot finisher review

Code review PASS for the intended root-bound configuration. Beforeactivation, root must bind the full transitive receipt/source union and run the finalizedconfig CPUdryrun below; this review did not activate the watcher or execute its actual auditor child. No runtime/source/input/receipt/guard/cache/budget/job changes were made.

Reviewed189 paths: `transfer-v5/final-eval5-audit/watch-final-audit.py` SHA938275e957102bcb262c51d5ad37b19802870e282f3ae28095e60c27b9c2f9ba; test SHA23190a3ddc676866d1bd4957b9652f8d05cf893c37d2365ed6cdb8aacbd5d264. Independent13mocktests pass mgnp3.06s/base2.81s. No actual subprocess transport ran in these tests.

Completion gate:

- Exact recoverymanifest33ba99c1d08b3aa5aa9c886c820828ba40ce7b1b8bdebf8dcdef35fd5a018d63, rootlaunch command/PID/statepath and orderedfive datasets are required. Finalstate must have one trailingcomplete, exactlyfive unique numeric submittedjobs, orderedmatching validatedjobs and successfulCOMPLETED/0:0 terminalrecords. Submission precedes terminal precedes validation. Barecomplete, stopped, malformed/torn or rewritten/truncated state fails. No scheduler/API calls occur.
- While unresolved, `/proc` command and field22startticks plus non-zombie state prevent PIDreuse/deadprocess confusion. The immediate finalstate reread permits the legitimate appendcomplete→process-exit race. Alreadycomplete evidence intentionally does not require the oldprocess to remain alive.
- TTL is rootcreation≤now<expiry≤creation+24h, checked eachpoll beforedispatch. The child has its own3600second timeout. Expiry/unresolveddeadprocess fails; no restart/retry path exists.

Execution controls:

- Source/config hashes are checked on everypoll. Only the literal reviewed186Python/script/index/JSONoutput/Markdownoutput command is accepted; no shell or other command. Configbytes themselves are pinned by CLIsha and added to runtimebinding checks.
- Both outputpaths must be distinct, absolute and resolveunder the finalaudit directory; pre-existing outputs stop dispatch. A permanent exclusive onceguard is flushed/fsynced before exactlyone subprocess.run. Concurrent/replayedwatchers cannot execute a second child; the auditor's exclusiveoutput creation also prevents an intervening overwrite race. Errors/timeouts consume theguard and stop withoutretry.
- Childenv is an explicit sevenname allowlist plus offline/BLAS1 flags. APIkeys/customtokens and unrelated credentials are absent. Environmentvalues/childtext are not printed; watcher reports only exitstatus/outputpaths and propagates nonzero status. An incomplete technicalaudit is not reported as acquisition success or scientific efficacy.

Root configuration closure requirement (communicated to root and189author): the186inputindex directly binds24files, while the tenreceipts' file_bindings union has129files,119notdirectlylisted in thatindex. Finisher checks every declaredconfigbinding, so root should construct file_bindings as the union of all tenreceipt file_bindings plus allindex immutablebindings plus finisher/test/auditor/index/recoverymanifest/rootlaunchrecord and the choseninterpreter. This satisfies “sourcechange stops beforechild.” If root binds indexonly,186still detects nestedsource changes during its CPUaudit, but that would consume theonceguard afterstarting thechild rather than suppressing dispatch upfront. No codechange is needed for a complete concrete rootconfig.

Required root finalization check (CPU-only; does not wait/probeprocess/startchild/writeguards):

```bash
/u/swong2/.conda/envs/mgnp/bin/python /projects/beto/swong2/Alignment/.scratch/selective-deception/transfer-v5/final-eval5-audit/watch-final-audit.py --config /ABSOLUTE/ROOT-FINAL-CONFIG.json --config-sha256 EXACT_CONFIG_SHA --dry-run
```

Root must verify finalconfig sourceclosure/outputfreshness/processstartticks and retain actual successfuldryrun before activation. This is configuration verification, not additional user permission. Existing recovery remains sole dispatcher; no manual GPU duplication or budget expansion is introduced. The finisher ends after technicalaudit; independent187scientific interpretation remains a separate pending agent task after all data exist.
