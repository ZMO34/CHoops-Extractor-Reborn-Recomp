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
