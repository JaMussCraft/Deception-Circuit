# Final selected calibration CPU operator readiness

PASS for committed29492146127f56c05a4087b1bfdeea0e63a4d24a. Exactly one finalselected mgnpCPUwrapper route completed100.906s,exit0, with13plannedcalibrationbatches (6forced+7natural), no outputdirectory or runmutation. Allfrozen sources/protocol/operations stayed exact. GPU numericalpass is false because this was CPUonly; it is not calibrationorGPUrelease.

The exacttested operations file here requests1200s,A100 with60/180/60/60sbuffers,360stotal. Its48hproposaladmissionhorizon is2026-10-27T16:31:25UTC (exactfractioninJSON); a queuewaitapproachingexpiryrequiresrootreassessment/freshrelease. Do not extendthishorizon silently. Livewrapper bindsactualSlurmStart/End; runnerreplacesdeadlinewithactualEnd, capsrequestatmin1200actualduration and rechecksremainingbuffers. The rejected2099candidate outside thisdirectory is neverselected.

Read scheduler-readiness-snapshot.json: noactiveuserjobs at snapshot, A100x4-interactive slotempty,beto.142340fairshare,1200stest-onlystartimmediate. Recheck userownership immediatelybefore actualsubmission. NoA100x8concurrentjob and nootheragentjobmutation. Rootexplicitcalibrationrelease plus finalmanifestrebindPASS are stillrequired; main remainsunreleased. Exactreviewablesbatchargv is saved without executing it. Noreservation/submission;GPUreserved/actual/API costs0.
