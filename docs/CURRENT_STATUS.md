# Current status

2026-11-08: Non-destructive **Mods / Mod Projects** authoring is implemented.
Private bank copies, metadata/reopen/versioning, DDS/cloth changes, native roster
body editing, uniform registration attachments and the catalogued DLL hook use
the local runtime's canonical API 1.2 schema and actual validation backend.
All **158 editor tests pass**, including 21 new authoring cases and native DDS
preparation/disable, cloth preservation, roster rewrapping and mixed-code metadata.
The required API 1.2 runtime changes are currently local/unpublished. Shared DDS
owner validation still occurs at launcher preparation. No game or DLL was run.
See [authoring support and limitations](CHMOD_AUTHORING.md).

The v0.1 Windows preview is packaged from the feature branch. See
`RELEASE_NOTES_v0.1.md` for setup and known limitations. Release artifacts contain
the editor, decoder and documentation, never game assets.

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

## Typed C++ extension SDK (2026-11-08)

The Studio repository now hosts `sdk/`: ABI 2 C headers, readable C++ wrappers,
hook inventory, neutral examples, CMake build project, .chmod packager and author /
adapter / remote-acceptance guides. Studio source CLI can attach ABI 2 DLLs with
capabilities/replacement claims while retaining the ABI 1 GUI/default attachment.
Windows packaging includes the SDK. The current installed editor received the
SDK folder alongside it; its executable was not rebuilt in this task. ABI 2
source CLI/export needs the matching API 1.3 runtime contract snapshot.

Runtime adapters live in the recomp: weight getter/setter plus host ready/stopping
lifecycle. Other gameplay/simulation/presentation/Legacy domains need research.
The runtime, example DLLs and synthetic test executables compile; tests were not
executed. No DLL, game, editor UI or user saves were exercised. Ghidra research
was read-only and saved in the recomp. No performance improvement is claimed.

## SDK Button Style extension (2026-11-08)

The hosted SDK now includes typed `presentation.button_style` hook 5, its readable
C++ DLL consumer, and `sdk/package_button_style.py` for a mixed DLL + conditional
DDS `.chmod`. ABI 2 host layout is unchanged; capability negotiation rejects older
runtimes. The native Options/Presentation adapter and live D3D12 selection are
implemented and compiled in the recomp. This is a narrow researched Xbox adapter,
not arbitrary UI construction. Source evidence and callback/ownership contracts:
[sdk/BUTTON_STYLE.md](../sdk/BUTTON_STYLE.md). Artwork remains private.

Runtime, extension and synthetic dispatch test executables compiled. No tests,
DLLs or game were executed, and no user saves were changed in this follow-up.
The supplied JPEG alpha is reconstructed; navigation/controller atlases remain
Xbox. Remote acceptance is pending. Source CLI/canonical runtime validation
accepts the new capability; existing GUI/default DLL attachment remains ABI 1.
