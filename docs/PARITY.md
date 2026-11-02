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
| Uniform/shoe previews | Combined jersey/shorts and authored shoe upper/sole DDS implemented | Numbers/name glyphs, preview selection polish, runtime material effects |
| Uniform OBJ workflow | Pending | Xbox source-bound geometry/rest-position import and export |
| Court surface controls | Pending | Xbox geometry bindings and preservation tests |
| Roster names, jersey, height, position | Implemented | Search/filter and related side panels |
| Ratings | 30 Xbox-verified channels, copy/paste, selective CSV compare | School filters and richer selection controls |
| Appearance/equipment | 33 Xbox-verified properties, 30 native option lists | Class/redshirt/scholarship, footwear and jump-shot bindings |
| Palette | 31 RGBA slots | Xbox semantic captions and preview bindings |
| School/coach/arena relationships | Xbox corpus validated | Checked assignment UI, reciprocal writers |
| Player transfers / scholarships | Pending | Xbox native ownership/count/slot contract |
| Conference realignment/history | Pending | Xbox consumers, reciprocal membership writer |
| Roster CSV and selective import | Implemented confirmed fields, source-bound review, one-step undo | Additional Xbox fields as verified |
| Existing uniform asset/shape editing | Structural writer implemented | Asset-existence validation and preview |
| New uniforms and asset links | Private-copy addition/reopen/pixel identities and sorted virtual TOC tests passed | Gameplay acceptance, stadium/menu-logo independence |
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
