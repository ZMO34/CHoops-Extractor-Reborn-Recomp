# Continuation handoff

Read AGENTS.md before editing. Work in this repository; do not launch the game.


---

# Current status

The editor is under implementation. Full feature parity is **not complete**.
The reference is Extractor Reborn v1.23, commit
`8ed6b90c8907e36dae2a33316294051a0a67db9c`; unfinished upstream research is
distinguished from released functionality in the parity tracker.

Implemented: installed-assets indexing, standard and paired resource discovery,
Xbox DDS previews/replacement, textured scene preview with instance transforms,
Xbox roster names/basic fields/palettes/uniform routing, 21 native player
properties, 30 named ratings, undo/redo, and XMA2 WAV export/native PCM imports.
Licensed music and band/fight songs have separate Audio views. All 87 jukebox
title/index/category mappings were recovered from Xbox native tables and matched
to Xbox localization IDs. Band-bank clips retain their original numeric labels.

Roster CSV comparison supports field selection and transactional, undoable
application. Ratings can be copied to multiple selected players. New uniform
world/selection folders passed a private-copy test: 989 rows after expansion,
five independent texture bindings, unchanged source templates, successful reopen.
Full runtime integration validation remains. Native PCM SDK integration builds;
loop/seek behavior and runtime acceptance remain incomplete. The installed game
has not been launched or modified for testing this editor.

Do not treat offline preview or structural tests as gameplay confirmation.


---

# Feature parity tracker

The target is the released College Hoops feature set in Extractor Reborn v1.23,
adapted to direct Xbox assets-folder editing. No percentage is claimed while
applicable features remain incomplete. A parser alone does not complete a GUI,
writer, preservation test or integration requirement.

| Feature | Current state | Work remaining |
| --- | --- | --- |
| Open installed assets; search resources | Implemented | Cancelable indexing and diagnostics polish |
| DDS preview/export/import | BC1/2/3 2D implemented | Other Xbox formats, mip/cubemap parity, batch workflows |
| Native higher-resolution DDS | Runtime interface implemented | Editor/runtime acceptance and additional layouts |
| Arena/floor textured 3D preview | Implemented observed layouts | Full source corpus, material/lightmap behavior, combined views |
| Uniform/shoe previews | General SCNE available | Authored cloth/artwork binding, combined jersey/shorts, numbers/name glyphs |
| Uniform OBJ workflow | Pending | Xbox source-bound geometry/rest-position import and export |
| Court surface controls | Pending | Xbox geometry bindings and preservation tests |
| Roster names, jersey, height, position | Implemented | Search/filter and related side panels |
| Ratings | 30 Xbox-verified channels, copy/paste, selective CSV compare | School filters and richer selection controls |
| Appearance/equipment | 21 Xbox-verified properties | Remaining hair/tattoo/animation/class fields, caption choices |
| Palette | 31 RGBA slots | Xbox semantic captions and preview bindings |
| School/coach/arena relationships | Xbox corpus validated | Checked assignment UI, reciprocal writers |
| Player transfers / scholarships | Pending | Xbox native ownership/count/slot contract |
| Conference realignment/history | Pending | Xbox consumers, reciprocal membership writer |
| Roster CSV and selective import | Implemented confirmed fields, source-bound review, one-step undo | Additional Xbox fields as verified |
| Existing uniform asset/shape editing | Structural writer implemented | Asset-existence validation and preview |
| New uniforms and asset links | Private-copy addition/reopen/pixel-identity tests passed | Full runtime TOC tests, stadium/menu-logo independence |
| Licensed Music and Band/Fight Songs tabs | Implemented from Xbox evidence | Shared-cover routing validation and artwork controls |
| WAV export/import/preview | Implemented | Native loop/seek and duration parity, packaging acceptance |
| Batch WAV | Export and import preflight implemented | Transactional batch apply and GUI review |
| Raw inspection/diagnostics | Pending | Bounded asset inspection and actionable failures |
| Change packages | Pending | Source-bound asset deltas without unchanged game bytes |
| Documentation ecosystem | Established | Update evidence and acceptance records with each feature |

Intentionally removed per owner request: archive/disc explorer, overrides/staging,
disc rebuilding, console codec conversion for native WAV imports, automatic
texture downsizing, other games' profiles and source-platform saved-data adapters.
Their removal does not excuse missing applicable editing functionality.

Upstream draft scorebug, Legacy/recruit and animation-port research is not
represented as a released working feature. Relevant research requires new Xbox
evidence before adoption; incomplete research is not silently marked obsolete.


---

# Test report

- Core suite before the new Qt checks: **32 passed**, including all 21 player-property neighbor-preservation
  cases, native weight/hand masks, roster growth/undo, uniform table preservation,
  conflicting saves, PCM truncation and jukebox categories.
- CSV selective application and failed-transaction rollback pass.
- Private-copy uniform creation: five banks after addition, 989 roster uniform
  rows, five independent/pixel-equivalent DDS identities, original templates unchanged.
- Standalone native PCM C++ executable passes endian, zero-tail, invalid codec,
  truncation, rate/extent and reset checks.
- Recomp loose-assets and SDK integration subset: **12 passed**.
- Qt offscreen startup against the supplied installed assets: passed, four editor
  tabs, no startup error.
- Native invisible OpenGL floor render: four meshes/four DDS textures rendered.
- Supplied floor parsing after instance-transform support: four parts, 2,098
  triangles, no warnings. Earlier arena audit: 80 parts/44,194 triangles.
- Complete installed catalog: 3,378 banks, 1,584 SCNE, 16,093 TXTR, one ROST,
  77,512 direct/paired/stream AUDO resources.
- Native SDK with PCM integration: built and installed locally. Updated game
  packaging and audio runtime acceptance are not yet complete.

No game was launched. New uniforms, native audio playback inside the game,
expanded texture layouts and full feature parity are not certified by these tests.
