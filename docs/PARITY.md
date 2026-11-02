# Feature parity tracker

The target is the released College Hoops feature set in Extractor Reborn v1.23,
adapted to direct Xbox assets-folder editing. No percentage is claimed while
applicable features remain incomplete. A parser alone does not complete a GUI,
writer, preservation test or integration requirement.

| Feature | Current state | Work remaining |
| --- | --- | --- |
| Open installed assets; search resources | Implemented | Cancelable indexing and diagnostics polish |
| Direct folder loading | Component reads, self-contained additions and natural DDS/WAV discovery implemented | All 40 paired banks pass private source-removal checks; installed migration and gameplay acceptance pending |
| DDS preview/export/import | BC1–BC5 2D implemented | Other Xbox formats, mip/cubemap parity, batch workflows |
| Native higher-resolution DDS | BC1–BC5 upload/readback passed on hardware and WARP | Runtime acceptance and additional layouts |
| Arena/floor textured 3D preview | Implemented observed layouts | Full source corpus, material/lightmap behavior, combined views |
| Uniform/shoe previews | Authored cloth, front/back numbers, curved surnames, school/player selection and shoe artwork implemented | Runtime cloth/body/material effects and gameplay acceptance |
| Uniform indexed fonts | All 1,976 atlas/metric pairs validated; exact-color image and metric writers, preview implemented | Fixed native dimensions/palette capacity; gameplay acceptance |
| Uniform OBJ workflow | Source-bound float3 cloth OBJ import/export in GUI/CLI; all 33 identified resources pass private preservation checks | Additional vertex layouts, rest/skin deformation parity and gameplay acceptance |
| Court surface controls | Pending | Xbox geometry bindings and preservation tests |
| Roster names, jersey, height, position | Implemented | Search/filter and related side panels |
| Ratings | 30 Xbox-verified channels, copy/paste, selective CSV compare | School filters and richer selection controls |
| Appearance/equipment | 33 Xbox-verified properties, 30 native option lists | Class/redshirt/scholarship, footwear and jump-shot bindings |
| Palette | 31 RGBA slots | Xbox semantic captions and preview bindings |
| School/coach/arena relationships | Checked school dialog and CLI assignments for arena, coach, assistants and rivals | Gameplay/Legacy acceptance; shared arena identity intentionally retained |
| Player transfers / scholarships | Checked 18-slot transfers, unassignment and lineup order implemented | Scholarship/eligibility fields and gameplay acceptance |
| Conference realignment/history | Checked reciprocal realignment in GUI/CLI implemented | Historical statistics editing and gameplay acceptance |
| Roster CSV and selective import | Implemented confirmed fields, source-bound review, one-step undo | Additional Xbox fields as verified |
| Existing uniform asset/shape editing | Checked editor, artwork validation, neckline/slot/unlock, private routing/artwork cloning and alternate availability implemented | Gameplay acceptance of new routing/dormant state |
| New uniforms and asset links | Private Home/Away/alternate artwork and additive folders pass preservation/reopen/direct-map checks | Gameplay acceptance; stadium/menu-logo independence remains separate |
| Licensed Music and Band/Fight Songs tabs | Implemented from Xbox evidence | Shared-cover routing and DDS/image artwork controls implemented; runtime acceptance pending |
| WAV export/import/preview | Implemented | Native loop/seek and duration parity, packaging acceptance |
| Batch WAV | Export, changed-track review, selective GUI/CLI apply and write-failure rollback implemented | Process-interruption recovery polish and gameplay acceptance |
| Raw inspection/diagnostics | Bounded owning-resource hex inspection in GUI/CLI implemented | Richer structured diagnostics |
| Change packages | Pending | Source-bound asset deltas without unchanged game bytes |
| Documentation ecosystem | Established | Update evidence and acceptance records with each feature |

Intentionally removed per owner request: archive/disc explorer, overrides/staging,
disc rebuilding, console codec conversion for native WAV imports, automatic
texture downsizing, other games' profiles and source-platform saved-data adapters.
Their removal does not excuse missing applicable editing functionality.

Upstream draft scorebug, Legacy/recruit and animation-port research is not
represented as a released working feature. Relevant research requires new Xbox
evidence before adoption; incomplete research is not silently marked obsolete.
