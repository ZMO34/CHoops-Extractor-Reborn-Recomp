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
