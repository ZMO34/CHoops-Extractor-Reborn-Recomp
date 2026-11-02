# Source and dependency notices

The owner authorized using CHoops Extractor Reborn as the baseline. Host Qt
camera/drawing patterns and shared format ideas were adapted from v1.23 commit
`8ed6b90c8907e36dae2a33316294051a0a67db9c`. Xbox parsers and promoted profiles
were checked against supplied Xbox data and native consumers. No original game
asset payload, console executable or source-platform save profile is distributed.

Python dependencies: PySide6/Qt and Pillow, with their upstream licenses. Native
source audio decoding uses the complete vgmstream r2168 Windows distribution;
retain its COPYING and all dependency notices when packaging. The setup tool pins
the release URL and SHA-256. Its FFmpeg dependencies decode XMA2; this editor does
not claim an XMA encoder. WAV imports use host PCM substitution.

Upstream documentation:
- https://github.com/vgmstream/vgmstream/blob/master/doc/USAGE.md
- https://github.com/vgmstream/vgmstream/blob/master/doc/TXTH.md
- https://github.com/ZMO34/CHoops-Extractor-Reborn
