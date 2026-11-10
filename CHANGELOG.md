# Changes

## Security update

Raised dependency minimums to patched releases, added dependency auditing to CI, and bounded component decompression by the declared size.

## Unreleased

## v0.1 — 2026-11-02

First Windows preview release. Includes the loose-folder editor, player and
conference editing, uniforms, combined arena/floor previews, additional Xbox
texture formats and separate licensed/band audio workflows. Full applicable
parity remains in progress; see `docs/RELEASE_NOTES_v0.1.md`.

- Establish the Xbox assets-folder editor and its documentation ecosystem.
- Add observed Xbox scenes, native DDS, roster and XMA2/PCM workflows.
- Recover jukebox categories/titles and player field masks from Xbox evidence.
- Separate licensed music from band/fight songs; add WAV preview and batch export.
- Track remaining parity requirements explicitly instead of claiming completion.
- Add 12 further Xbox hair/tattoo/signature properties and 30 native option lists.
- Bind authored Xbox cloth to selected uniform DDS artwork in combined previews.
- Fix typed OpenGL sampler/bool bindings and diagnose packaged ICU dependency conflicts.
- Replace runtime asset repacking with direct component-file reads and small loader metadata.
- Discover self-contained added folders and native DDS/WAV files without a separate mod registry.
- Decode individual compressed Xbox paired components and preserve cloned stock mip chains.

- Import image artwork at supplied resolution with complete BC1–BC5 mip chains.
- Resolve all native jukebox artist/cover groups and add shared-cover editing.
- Prototype paired-resource component materialization without source payload dependencies.

- Validate all 40 paired banks without source payloads and add bounded resource inspection.

- Add selective batch WAV import with source review and write-failure rollback.
- Omit obsolete paired payloads from fresh direct imports after component extraction.

- Add source-bound Xbox cloth OBJ position editing and validate all 33 identified resources.

- Add checked school relationship dialogs, player transfers/lineups and reciprocal conference moves.
- Add uniform editing, independent routing/artwork clones and alternate availability.
- Decode/edit Xbox indexed glyphs and metrics; render authored numbers and curved surnames.
- Fix source-row orientation and typed scalar bindings in the 3D preview.

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
