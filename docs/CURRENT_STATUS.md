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
dropdowns, including hair, tattoos, post and free-throw animations. Authored number/name layers are now implemented. Footwear, eligibility and
remaining player-class fields are still incomplete.

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
