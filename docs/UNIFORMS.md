# Xbox uniform editing and preview

Open Roster → Uniform editor and choose a school. The editor provides:

- Checked artwork-ID, neckline, slot and unlock-code editing. World and selection
  folders must exist; the world folder must contain decodable jersey/shorts art.
- Independent school routing: copies the owner's active and dormant rows to an
  unused owner, preserving every other school's routing and all artwork files.
- Private artwork cloning for Home, Away or an alternate. It creates world and
  selection folders with independent verified texture identities and updates the
  chosen row's artwork ID. Make shared school routing independent first.
- New independent alternate folders and alternate enable/disable checkboxes.
- DDS/image artwork editing, indexed surname/number atlas editing, and glyph
  metric editing. Explicit artwork Save actions write their owning loose files.
- Jersey/shorts preview with the saved neckline, selectable builds and authored
  front/back numbers and curved surnames. Choose a roster player or enter preview
  text and number; 100 represents double-zero. Front/back camera buttons are
  available. Preview text does not modify the player's roster fields.

Routing changes remain in memory until Save roster and support Undo/Redo.
Private folder creation/cloning explicitly saves the current roster too.
Independent routing alone does not make texture artwork private: use the artwork
clone action for that. Existing shared artwork edits intentionally affect users
of that artwork ID. Unlock zero means always available; other native unlock
codes retain their original numeric representation.

## Indexed glyph format

Uniform fonts use an Xbox CPU descriptor with word +8 = `0x24820002`; their GPU
fetch is uninitialized. Dimensions are explicit at +0x60 (width/height halves),
the GPU-relative palette pointer at +0x68 is one-based, and the pixel pointer
at +0x6c is one. Validated layouts are 1024×32, 1024×64 and 2048×32. All mip
indices precede a 16-byte-aligned, 256-entry ARGB palette. Palette+1024 must equal
the component extent. All 1,976 supplied atlas/metric pairs validate, including
54 wide surname atlases. The separate metrics records are type `0x68b693b2`,
with ten number or 28 surname pairs of big-endian 16-bit X/width values.

Font export uses PNG. Import accepts image artwork at the exact native dimensions
and at most 256 distinct RGBA colors; it refuses lossy automatic quantization or
resizing. An unchanged export/import is byte-identical. An edit regenerates the
indexed mip chain using nearest sampling, retains alignment padding and updates
only the owning GPU component. Metrics writes preserve trailing words. General
BC1–BC5 uniform artwork continues to support native DDS upscales.

Number and surname placement comes from Xbox `global.iff/unidata` (96 bytes),
using its front/back rectangles and polar surname transform, with dimensions from
the Xbox jersey-number/name template descriptors. Composition draws the uniform's
authored glyphs; it does not substitute a host font. The shared GL viewer uploads
source rows without an extra vertical mirror and uses explicitly typed sampler,
boolean and float bindings. Front/back native invisible-render checks display
readable artwork, numbers and surname.

## Dormant alternate metadata

Disabled rows are preserved in an editor-owned append-only `XRUFv001` record in
the loose ROST data. This is new Recomp metadata, not a console save schema. The
record contains a big-endian count, complete eight-byte uniform rows, then the
SHA256 digest of its header and rows. The latest marker is authoritative and
invalid digests reject. It can precede later appended strings/tables. Native game
code continues to use only the ordinary active uniform table; enable/disable
publishes a copied active table and updates its count/pointer. Original tables,
unknown row bits and dormant rows remain intact. No archive is rebuilt.

The preview is authored static cloth with glyph layers. Player body rendering,
runtime cloth simulation, skinning and full material/lighting effects are not
reproduced. Indexed-font writes, new owner routing and dormant alternates have
offline preservation/reopen checks; gameplay acceptance remains pending. The
game was not launched during this work.
