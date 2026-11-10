# CHoops Recomp Studio v0.1

First public preview of the Xbox 360 loose-assets editor. Extract the complete
Windows x64 ZIP, keep `_internal` and `tools` beside the executable, then run
`CHoops-Recomp-Studio.exe`. Open the recomp installation's `assets` folder.
No game assets or executable are included. The editor never launches the game.

## Included

- Direct loose-file roster, scene, texture and audio workflows, without archive
  rebuilding, an archive explorer or a PS3 overrides layer.
- 46 Xbox-verified player properties, 30 ratings, eligibility, footwear and shot
  tendencies; school relationships, transfers, lineup ordering, roster CSV,
  search, school/unassigned filters, sorting and undo/redo.
- Conference realignment and four history scalars: founded year, NCAA titles,
  Final Fours and previous-year bids. Unconfirmed history bytes stay protected.
- Combined arena/floor previews and per-resource texture editing; authored
  uniforms/shoes, number/name artwork, private uniform cloning and new alternates.
- BC1–BC5 DDS, indexed team-number/name artwork, L8, RGB565, RGBA8, RG8, RG16F,
  RGBA16F and supported cubemap base editing. Raw DDS preserves channel precision.
- Separate Licensed Music and Band/Fight Songs tabs, WAV export/playback,
  native PCM imports, selective batch import and rollback on ordinary failures.
- Source-bound cloth OBJ position editing, resource inspection and cancellation.

## Validation and remaining work

137 automated tests pass. The descriptor audit recognizes all 16,093 installed
TXTR resources with no layout failures. New raw/indexed/packed-base pixel decodes,
real private-copy write preservation, native invisible GL previews and packaged
startup/dialog checks pass. The installed source assets were not modified.

This is a prerelease, not certified full parity. Raw/indexed edits retain native
dimensions; higher-resolution native DDS substitution remains BC1–BC5 and needs
the recomp's patched runtime. Full raw mip-chain replacement, runtime cloth/body
effects, unconfirmed history semantics, native PCM loop/seek and variable-duration
parity remain open. Offline tests do not certify every edit in gameplay. Consult
`PARITY.md`, `USER_GUIDE.md` and `TEST_REPORT.md` for precise scope.

Third-party library license texts ship in `licenses` and the decoder's `COPYING`.
