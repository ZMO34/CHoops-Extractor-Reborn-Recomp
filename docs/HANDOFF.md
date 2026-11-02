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
Xbox roster names/basic fields/palettes/uniform routing, 46 native player
properties, 30 named ratings, undo/redo, and XMA2 WAV export/native PCM imports.
Licensed music and band/fight songs have separate Audio views. All 87 jukebox
title/index/category mappings were recovered from Xbox native tables and matched
to Xbox localization IDs. Band-bank clips retain their original numeric labels.

Combined authored jersey/shorts and standalone shoe previews resolve Xbox cloth and uniform
artwork by CRC identities. The embedded cloth stream descriptors are 24 bytes,
versus 16 for GPU-backed scenes. Thirty native option lists supply appearance
dropdowns, including hair, tattoos, post and free-throw animations. Authored number/name layers are now implemented. Footwear, eligibility, class and shot tendencies are now implemented.

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
not yet migrated the installed game. The current editor suite passes 94 tests.

The complete paired corpus (40 pairs / 2,361 records) now passes private
source-removal checks in both reader implementations. Installed migration and
gameplay remain pending. Resource-file inspection is available in each library
and the CLI, with bounded reads confined to a selected component.

Batch WAV folders now support changed-track review and selective saving in the
GUI and CLI. Inputs and destinations are rechecked before commit; write failures
restore preceding edits. Recovery copies and a target manifest are retained if
a concurrent edit prevents rollback. Process interruption is not certified as
an atomic multi-track commit. Licensed and band/fight categories remain separate.
Fresh direct imports materialize paired records and omit their obsolete combined
payloads; existing-install migration retains backups by default.

Embedded Xbox cloth supports source-bound OBJ position import/export in the GUI
and CLI. All 33 identified cloth resources pass private byte-identical round trips
and single-coordinate preservation checks. Files use source model coordinates;
vertex order and exact triangle topology must remain intact. The writer changes
only float3 positions, preserving UVs, weights, rigging, materials and unknown
bytes. It edits shared cloth, not independent per-uniform meshes. Additional
vertex layouts, simulated/rest-pose behavior and gameplay remain unverified.

School relationships and uniform authoring now have dedicated dialogs and shared
CLI backends. All 443 schools / 39 conferences validate, with 5,607 assigned
players. Checked transfers, lineup order, eight team references and reciprocal
conference moves support undo and preserve unrelated fields.

Uniform editing validates artwork folders and provides neckline/slot/unlock
controls, private routing, private Home/Away/alternate artwork clones and alternate
availability with preserved dormant rows. The authored 3D view displays front/back
numbers and curved surnames. All 1,976 Xbox font atlas/metric pairs validate;
exact-color indexed image import and bounded metric editing write owning files.
Static cloth/body/material limitations and gameplay acceptance remain explicit.
See ROSTER_RELATIONSHIPS.md and UNIFORMS.md for evidence and operation details.

## Player, history and texture update

The Xbox player profile now exposes 46 properties plus 30 ratings: class,
scholarship, redshirt status/used, jumper, four footwear controls and four shot
tendencies join the existing fields. Native redshirt exclusions and brand-specific
shoe limits are enforced. Search, school/unassigned filters, numeric sorting and
source-row mapping preserve correct player identity while editing filtered lists.
Player shoes can be previewed using their assigned Home/Away artwork.

Conference history exposes founded year, NCAA championships, NCAA Final Fours
and previous-year bids. Changes preserve membership and all neighboring bytes.
These big-endian scalars were checked across all 39 Xbox conference records;
labels agree with the applicable baseline, but native UI getter bindings have
not all been traced. Unconfirmed ordering/recency fields remain protected.

Models offers combined arena/floor, arena-only and floor-only previews, preserving
authored coordinates and separate material identities. Textures in either owning
resource can be exported/replaced from the combined view. Runtime lighting,
crowds and cloth simulation are outside this authored preview.

All 16,093 installed TXTR descriptors are recognized: 12,016 ordinary BC,
one packed BC base, 1,044 raw 2D, 11 raw cubemaps and 3,021 indexed textures.
Added L8, RGB565, RGBA8, RG8, RG16F and RGBA16F export/import, face previews,
and indexed artwork including team numbers. Raw DDS preserves native channel
precision; PNG is a display-range edit. Indexed PNG requires at most 256 exact
colors. Unrepresentable channel changes are rejected rather than quantized.

Non-BC and packed-base imports update only loose component base pixels at native
dimensions, preserving other mip storage and padding. Indexed edits use the
verified palette/mip writer. No archive/chunk rebuilding is involved. Native GPU
DDS substitution/upscaling remains BC1–BC5; raw upscaling and full raw mip-chain
replacement are not implemented. Unknown future formats are rejected.

Loading is cancellable; interrupted workers do not publish stale results.
Full parity and gameplay certification are not claimed.


---

# Feature parity tracker

The target is the released College Hoops feature set in Extractor Reborn v1.23,
adapted to direct Xbox assets-folder editing. No percentage is claimed while
applicable features remain incomplete. A parser alone does not complete a GUI,
writer, preservation test or integration requirement.

| Feature | Current state | Work remaining |
| --- | --- | --- |
| Open installed assets; search resources | Implemented | Cancelable indexing and diagnostics polish |
| Direct folder loading | Component reads, self-contained additions and natural DDS/WAV discovery implemented | All 40 paired banks pass private source-removal checks; installed migration and gameplay acceptance pending |
| DDS preview/export/import | BC1–BC5, indexed, raw 2D/cubemap base editing implemented | Full raw mip-chain replacement and batch workflows |
| Native higher-resolution DDS | BC1–BC5 upload/readback passed on hardware and WARP | Runtime acceptance and additional layouts |
| Arena/floor textured 3D preview | Implemented observed layouts | Full source corpus, material/lightmap behavior, runtime lighting |
| Uniform/shoe previews | Authored cloth, front/back numbers, curved surnames, school/player selection and shoe artwork implemented | Runtime cloth/body/material effects and gameplay acceptance |
| Uniform indexed fonts | All 1,976 atlas/metric pairs validated; exact-color image and metric writers, preview implemented | Fixed native dimensions/palette capacity; gameplay acceptance |
| Uniform OBJ workflow | Source-bound float3 cloth OBJ import/export in GUI/CLI; all 33 identified resources pass private preservation checks | Additional vertex layouts, rest/skin deformation parity and gameplay acceptance |
| Court surface controls | Pending | Xbox geometry bindings and preservation tests |
| Roster names, jersey, height, position | Implemented | Search/filter and related side panels |
| Ratings | 30 Xbox-verified channels, copy/paste, selective CSV compare | School filters and richer selection controls |
| Appearance/equipment | 46 Xbox-verified properties, native option lists | Runtime acceptance |
| Palette | 31 RGBA slots | Xbox semantic captions and preview bindings |
| School/coach/arena relationships | Checked school dialog and CLI assignments for arena, coach, assistants and rivals | Gameplay/Legacy acceptance; shared arena identity intentionally retained |
| Player transfers / scholarships | Checked 18-slot transfers, unassignment and lineup order implemented | Gameplay acceptance |
| Conference realignment/history | Checked reciprocal realignment in GUI/CLI implemented | Four historical scalars implemented; unknown recency/order semantics and gameplay acceptance |
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

## Player, history and texture update

The Xbox player profile now exposes 46 properties plus 30 ratings: class,
scholarship, redshirt status/used, jumper, four footwear controls and four shot
tendencies join the existing fields. Native redshirt exclusions and brand-specific
shoe limits are enforced. Search, school/unassigned filters, numeric sorting and
source-row mapping preserve correct player identity while editing filtered lists.
Player shoes can be previewed using their assigned Home/Away artwork.

Conference history exposes founded year, NCAA championships, NCAA Final Fours
and previous-year bids. Changes preserve membership and all neighboring bytes.
These big-endian scalars were checked across all 39 Xbox conference records;
labels agree with the applicable baseline, but native UI getter bindings have
not all been traced. Unconfirmed ordering/recency fields remain protected.

Models offers combined arena/floor, arena-only and floor-only previews, preserving
authored coordinates and separate material identities. Textures in either owning
resource can be exported/replaced from the combined view. Runtime lighting,
crowds and cloth simulation are outside this authored preview.

All 16,093 installed TXTR descriptors are recognized: 12,016 ordinary BC,
one packed BC base, 1,044 raw 2D, 11 raw cubemaps and 3,021 indexed textures.
Added L8, RGB565, RGBA8, RG8, RG16F and RGBA16F export/import, face previews,
and indexed artwork including team numbers. Raw DDS preserves native channel
precision; PNG is a display-range edit. Indexed PNG requires at most 256 exact
colors. Unrepresentable channel changes are rejected rather than quantized.

Non-BC and packed-base imports update only loose component base pixels at native
dimensions, preserving other mip storage and padding. Indexed edits use the
verified palette/mip writer. No archive/chunk rebuilding is involved. Native GPU
DDS substitution/upscaling remains BC1–BC5; raw upscaling and full raw mip-chain
replacement are not implemented. Unknown future formats are rejected.

Loading is cancellable; interrupted workers do not publish stale results.
Full parity and gameplay certification are not claimed.


---

# Test report

- Core and Qt suite: **137 passed**, including all 46 player-property neighbor-preservation
  cases, native weight/hand masks, roster growth/undo, uniform table preservation,
  conflicting saves, PCM truncation and jukebox categories.
- CSV selective application and failed-transaction rollback pass.
- Private-copy uniform creation: five banks after addition, 989 roster uniform
  rows, ten independent/pixel-equivalent DDS identities including BC4/5 masks,
  original templates unchanged.
- Fresh direct import has no `_archive`, packed `.stored` files or asset-cache
  dependencies. Fourteen loose-loader tests pass, including compressed-source
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
- Broader owned recomp suite: **87 passed, 20 skipped**. All 14 loose-assets
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

- Full private paired corpus: **40 pairs, 2,361 records** match the shared runtime
  reader and editor after original metadata/data payload removal. All direct
  mapped file extents validate. No installed assets were migrated.
- Bounded resource inspection tests cover component boundaries, EOF, page limits
  and current grown loose-file sizes.
- Latest packaged editor opens the installed assets with all four tabs, 3,378
  banks and no startup error; the game is not launched.

- Batch PCM tests pass for selected-track application, unchanged export detection,
  stale-review rejection, and restoration of both WAV and metadata after an
  injected second-track disk failure. No packed assets or registry are written.
- Fresh paired import omits obsolete metadata/data payloads after successful
  component publication; repeat preparation still reads both components.

- Cloth OBJ: all **33 identified Xbox cloth resources** pass private byte-identical
  round trips. A single X coordinate changes at most its four float bytes, with
  all other source bytes preserved. Synthetic tests reject changed topology,
  nonfinite coordinates and stale source companions before writing.

- Relationship corpus: 443 schools, 39 conferences, 5,607 assigned players, no
  ambiguous membership/backlinks. All eight assignments, transfer, unassignment,
  lineup and realignment/undo pass on a separate in-memory document.
- New tests cover full/shared roster rejection, byte preservation, reciprocal
  conference changes and typed chooser rejection without partial writes.
- All **1,976** uniform atlas/metric pairs validate, including 54 wide atlases.
  Private font PNG round trips are byte-identical; exact-color replacement,
  padding preservation, metric bounds, 00 and surname composition pass.
- Private Home clone, source-template preservation and alternate disable/save/
  reopen/restore pass. Direct runtime preparation sees seven banks and zero stock
  replacement bindings, without rebuilding packed files.
- Native invisible GL front/back renders display authored number 31 and IATI;
  the vertical texture mirror and scalar-float binding issue are fixed.
- Both new dialogs pass offscreen creation and layout inspection with the system
  font explicitly registered for the Windows offscreen plugin.

- Final packaged executable passes `--smoke --smoke-dialogs`: installed catalog,
  eight relationship fields, 13 school members, two uniform routes, nine artwork
  choices and an indexed font decode; no startup error. Existing shoe and court
  native GL checks also pass with the new glyph shader.

Latest offline validation: 137 tests pass; the complete TXTR layout audit has zero
failures and decodes all non-BC/indexed/packed-base pixels. This is not a
16,093-resource write round trip. Combined native invisible GL: 84 meshes,
50 DDS images. Private uniform creation/Home clone/alternate disable-restore
repassed with original templates unchanged. No game or input automation used.
