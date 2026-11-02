# Continuation handoff

Read AGENTS.md before editing. Work in this repository; do not launch the game.


---

# Current status

The editor is under implementation. Full feature parity is **not complete**.
Loose resource files are authoritative. New imports omit packed block storage;
startup maps component files directly and generates only compatibility metadata.
The supplied installation uses that direct path. All 24 virtual parts pass real
SDK VFS concurrent-read, EOF and read-only checks; its map has no `.stored` or
assembled asset-cache references.
The reference is Extractor Reborn v1.23, commit
`8ed6b90c8907e36dae2a33316294051a0a67db9c`; unfinished upstream research is
distinguished from released functionality in the parity tracker.

Implemented: installed-assets indexing, standard and paired resource discovery,
Xbox DDS previews/replacement, textured scene preview with instance transforms,
Xbox roster names/basic fields/palettes/uniform routing, 33 native player
properties, 30 named ratings, undo/redo, and XMA2 WAV export/native PCM imports.
Licensed music and band/fight songs have separate Audio views. All 87 jukebox
title/index/category mappings were recovered from Xbox native tables and matched
to Xbox localization IDs. Band-bank clips retain their original numeric labels.

Combined authored jersey/shorts and standalone shoe previews resolve Xbox cloth and uniform
artwork by CRC identities. The embedded cloth stream descriptors are 24 bytes,
versus 16 for GPU-backed scenes. Thirty native option lists supply appearance
dropdowns, including hair, tattoos, post and free-throw animations. Name/number
layers, footwear and remaining roster ownership fields are still incomplete.

Windows onedir packaging passes empty and installed-assets startup checks. The
build excludes an unrelated Poppler ICU search path that otherwise introduced
an incompatible same-name DLL. This is an editor startup check, not a game test.

Roster CSV comparison supports field selection and transactional, undoable
application. Ratings can be copied to multiple selected players. New uniform
world/selection folders passed a private-copy test: 989 rows after expansion,
ten independent texture bindings, unchanged source templates, successful reopen.
New folders carry their own identity/texture metadata and require no separate
mod registry. A DDS-only edit produces one native binding while leaving raw
resource bodies and their direct-read map unchanged. Default cloned DDS files
preserve the original mip chain until actually edited.
The virtual sorted-TOC addition test also passes without rebuilding archive chunks.
BC1–BC5 direct uploads pass exact GPU readback checks on the RX 6650 XT and WARP.
The compatible SDK and game executable build and are packaged with previous
runtime binaries backed up. Game assets are unchanged and the game was not
launched. PCM loop/seek behavior and gameplay acceptance remain incomplete.

Do not treat offline preview or structural tests as gameplay confirmation.

Artwork imports accept DDS, PNG, JPEG, TGA and BMP for textures, embedded scene
textures and jukebox covers. Image inputs retain supplied resolution and generate
a complete mip chain. All 87 native song rows now resolve artist/cover groups.
A paired-folder materialization prototype passes source-removal tests; it has
not yet migrated the installed game. The current editor suite passes 67 tests.


---

# Feature parity tracker

The target is the released College Hoops feature set in Extractor Reborn v1.23,
adapted to direct Xbox assets-folder editing. No percentage is claimed while
applicable features remain incomplete. A parser alone does not complete a GUI,
writer, preservation test or integration requirement.

| Feature | Current state | Work remaining |
| --- | --- | --- |
| Open installed assets; search resources | Implemented | Cancelable indexing and diagnostics polish |
| Direct folder loading | Component reads, self-contained additions and natural DDS/WAV discovery implemented | Paired materialization prototype tested synthetically; real-data and gameplay acceptance pending |
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

- Core and Qt suite: **67 passed**, including all 33 player-property neighbor-preservation
  cases, native weight/hand masks, roster growth/undo, uniform table preservation,
  conflicting saves, PCM truncation and jukebox categories.
- CSV selective application and failed-transaction rollback pass.
- Private-copy uniform creation: five banks after addition, 989 roster uniform
  rows, ten independent/pixel-equivalent DDS identities including BC4/5 masks,
  original templates unchanged.
- Fresh direct import has no `_archive`, packed `.stored` files or asset-cache
  dependencies. Thirteen loose-loader tests pass, including compressed-source
  migration with legacy storage deleted, direct edits and repeat-start stability.
- Real SDK VFS checks pass over all 24 direct-resource virtual parts, including
  case-insensitive aliases, four concurrent readers, EOF and denied writes.
- A self-contained new-uniform fixture requires no separate registry. A DDS
  change produces one binding with identical raw resource bodies and direct map.
- Individual Xbox H7A component decoding restores paired texture previews such
  as team-selection logos. Synthetic overlap, bounds and malformed-stream tests pass.
- Standalone native PCM C++ executable passes endian, zero-tail, invalid codec,
  truncation, rate/extent and reset checks.
- Recomp loose-assets and SDK integration subset: **12 passed**.
- Broader owned recomp suite: **86 passed, 20 skipped**. All 13 loose-assets
  tests, including fresh direct import and sorted virtual-TOC addition, pass. Broad default pytest discovery also
  entered unrelated third-party tools and failed on their missing Pillow;
  the owned suite was then explicitly scoped to `tests/`.
- BC1â€“BC5 native D3D12 upload/readback: exact 64Ã—64 seven-mip and 2048Ã—2048
  base-level results on RX 6650 XT and WARP, 20 cases total.
- Qt offscreen startup against the supplied installed assets: passed, four editor
  tabs, no startup error.
- Native invisible OpenGL checks include combined jersey/shorts: two meshes,
  2,726 triangles and two DDS images. Visual inspection caught and fixed the
  overloaded Qt bool/sampler uniform call; explicit integer GL bindings display
  the authored artwork. Multicolor checks now reject flat untextured output.
- Supplied floor parsing after instance-transform support: four parts, 2,098
  triangles, no warnings. Earlier arena audit: 80 parts/44,194 triangles.
- Complete installed catalog: 3,378 banks, 1,584 SCNE, 16,093 TXTR, one ROST,
  77,512 direct/paired/stream AUDO resources.
- Native SDK with PCM and BC4/5 integration: built and installed locally. The game
  executable builds and the folder runtime is packaged with previous binaries
  backed up. Audio/gameplay acceptance remains untested.
- Packaged Windows editor passes empty and supplied-assets offscreen startup
  checks after removal of the incorrectly bundled Poppler ICU DLL. The clean
  build filters that unrelated dependency path.

No game was launched. New uniforms, native audio playback inside the game,
expanded texture layouts and full feature parity are not certified by these tests.

- Paired-folder prototype: source payload removal, decoded component reads,
  descriptor relocation and unknown-gap preservation pass synthetic tests.
  Partial overlaps reject before writes. Installed-game migration is not applied.
- Artwork import supports BC1–BC5 image encoding with complete mipmaps, retains
  supplied upscale dimensions and rejects downsizing/aspect changes.

- Private real-Xbox paired fixture: both records decode identically after
  splitting and deleting the original metadata/data payloads (548,952-byte data
  bank). Editor and shared runtime reader agree. Interrupted commit/retry tests
  retain the old mapping until the owner metadata commits atomically.
