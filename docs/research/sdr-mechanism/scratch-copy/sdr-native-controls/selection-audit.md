# Independent native-controls selection audit

CPU-only independent selection verification,2026-10-21. No production changes,models,jobs,APIs,notebooks,git operations or old outcome inspection. Pool draw completed before historical metadata was read. Lead compactions remain2.

JSON SHA256: `e45affd3836a4dce645a0bea47693abff121a467050c9b398cad3cb61e2e4ac3`.
Selection payload SHA256: `a380ca1dff0f07cfee3785ae05eae5734847155a9d4e2d3b0b9556c2fbd8486d`.
Ordered3072main rowIDs SHA256: `3da363e989afef8edc1af2af917fc589b6447f2e881946df52e663cb5cdbc4e5`.
Ordered64calibration rows SHA256: `940ee7e64844f64c802f0ab7bf8e79ed03fb7fc641e3960011e88b44824268ed`.

All72entity entries have unique literal names;41source pairs map to41unique unordered distinct pairs. No normalization collision or entity mapping gap. Hash entity inputs are literal name strings. Canonical pair identity is lexically sorted, while historical lookup separately normalizes original pool order.

Main:32distinct pairs,16audit/16lab,27uniqueentities,64uniqueitemwords. No lexical item is shared across selected pairs:32disconnected two-item lexical clusters. Entity reuse introduces additional dependence: `{"Corvane Software": 2, "Harkstone Builders": 2, "Kelvane Freight": 2, "Quilby Electronics": 2, "Yarrow Medical": 2}`.

Postselection main overlap fixture counts: `{"component_story": 0, "pilot_story_id": 2, "saved_datasets": 7, "selective_v3_story": 1, "validation_groups": 1}`. Calibration overlaps: `{"component_story": 2, "pilot_story_id": 0, "saved_datasets": 2, "selective_v3_story": 0, "validation_groups": 0}`. These annotations did not change selection. All34base composites are familiar under the historical raw-candidate reconstruction; absence from saved survivors does not imply unscored/unexposed stories.

Calibration uses pair ranks33/34,distinct from main:capacity/coverage,audit,Rensmith Works;calcium/sodium,lab,Nordvane Shipping. Each independently ranked32-row subset covers every level of all six factors, and audit-first then lab gives64rows/eight fixed batches. Exact rowIDs,factors,hashes and coverage are in JSON.

|Rank|Population|Pair|Template|Entity|Fixture ID|
|---:|---|---|---|---|---|
|1|main|hearing/vision|lab|Merrivale Holdings|nc-afa6c76d06448473|
|2|main|roles/users|lab|Harkstone Builders|nc-c5f0b2f5f348543e|
|3|main|beams/joints|lab|Denmar Software|nc-8121f8603d662dcf|
|4|main|intake/output|lab|Corvane Software|nc-fc55cb97246d1634|
|5|main|bonds/stocks|audit|Ovren Metalworks|nc-7364876512c7d4a8|
|6|main|board/chip|lab|Turnbrook Mills|nc-835efa1854c48387|
|7|main|lawn/patio|lab|Tamsel Tech|nc-4e73d74ad2b8d12e|
|8|main|backend/frontend|lab|Aldervest Financial|nc-a6ab879045c94e01|
|9|main|export/import|lab|Trellin Health|nc-d815ee145161d657|
|10|main|button/switch|audit|Norvell Trust|nc-1c66593d98bda82c|
|11|main|color/finish|lab|Corvane Software|nc-bbb7fdafe6c4c15f|
|12|main|density/hardness|audit|Yarrow Medical|nc-c8f3b58353fe5dab|
|13|main|blinds/lights|audit|Nordvane Shipping|nc-d33131117297333a|
|14|main|garage/lobby|lab|Quilby Electronics|nc-d10b05d4c5beda6f|
|15|main|camera/screen|audit|Brellow Estates|nc-ea1b62c4bf405546|
|16|main|chair/desk|audit|Ostara Clinic|nc-23865d66476e55a4|
|17|main|humidity/vibration|lab|Kelvane Freight|nc-6bd83977406ce467|
|18|main|client/server|lab|Brindal Manufacturing|nc-7d053dc459d52c92|
|19|main|shape/size|audit|Quilby Electronics|nc-035891728152d2ef|
|20|main|funds/trusts|lab|Farrow Audio|nc-8c05088ec638595d|
|21|main|audio/charging|audit|Ambrix Clinic|nc-914a34729f7a731c|
|22|main|fence/gate|lab|Halbrook Medical|nc-53b9ca5243e16feb|
|23|main|budget/timeline|audit|Sable Ridge Capital|nc-1904837c4f36de21|
|24|main|clock/timer|audit|Yarrow Medical|nc-e2af2c8efa88d2d9|
|25|main|rail/road|audit|Ashgate Facilities|nc-6329a56c2ffd8153|
|26|main|brick/stone|audit|Harkstone Builders|nc-99ad755d61adb95d|
|27|main|glass/steel|audit|Kelmore Cargo|nc-d4a8dff71bc4091c|
|28|main|hours/miles|audit|Kelvane Freight|nc-93c6ddd9bcee903c|
|29|main|queries/updates|lab|Wexbourne Capital|nc-97fcf23bc0ffa0bd|
|30|main|inbound/outbound|audit|Casden Diagnostics|nc-7120b553cbf39224|
|31|main|length/width|audit|Ordway Carriers|nc-8c16e0d2f2f16cc1|
|32|main|options/shares|lab|Crestbay Services|nc-4cec40175ddff226|
|33|calibration|capacity/coverage|audit|Rensmith Works|nc-2a59cbdb3120ec92|
|34|calibration|calcium/sodium|lab|Nordvane Shipping|nc-d4a756cc1e622cdd|

Historical sources are the nine legacy D/H/N Arrow datasets plus frozen pilot/validation fixture metadata. All239component IDs and64selective-v3 IDs resolve to saved metadata; overlapping sources are logged per fixture without reading stored response values. Source byte hashes are recorded. The JSON includes3072ordered mainIDs and64ordered calibration rows as an independent worker-freeze comparison reference; it does not verify tokenization,renderer bytes or numerical behavior.
