# Runtime integration

The editor writes native DDS/WAV files into the owning assets folders. Modern
runtimes discover conventional resource filenames and each new folder's identity
metadata directly. `asset_edits.json` is accepted only as a compatibility input;
modern edits and additions do not create it. No overrides directory or asset
archive build step is present.

`direct_folder.py` maps decoded component files directly. It never consumes
packed `.stored` bodies and never creates assembled asset-cache binaries. Only
small compatibility headers/padding, the virtual read map and native DDS/audio
binding indices are generated at startup. Fresh imports omit packed storage;
older installations can migrate their loader metadata without changing assets.

The compatible recomp source includes the loose-assets preparer, standard-library
`xbox_asset_edits.py` reader, `native_dds*` headers and native PCM SDK patch. The
reference headers here match the editor's BC1–BC5 DDS and fixed-parameter PCM
interfaces. GPU content identity, guest write tracking and fence-safe retention
remain in force when replacing a host texture.

BC4 maps Xbox DXT5A (59) to ATI1/BC4_UNORM; BC5 maps Xbox DXN (49) to
ATI2/BC5_UNORM. DDS pixel data uploads directly to a host resource and does not
round-trip through Xbox tiled texture memory. Stock guest resources and unknown
bits are retained for compatibility. Signed variants and other dimensions still
require separate validation.

Native PCM replaces assembled decoded XMA frames while preserving the original
decoder's packet/timing progression. Imports currently retain channels, sample
rate and sample count. Loop/seek and variable-duration parity remain open; the
SDK patch disables substitution on unsupported rewind/loop paths.

The folder packager publishes `runtime_capabilities.json` with binary hashes.
The editor refuses new PCM, added-bank or BC4/5 writes when the installed runtime
does not advertise those interfaces. Capabilities establish an interface, not
gameplay acceptance. Previous runtime binaries are backed up before packaging.

No game launch is part of these tools. Source synchronization and SDK rebuilding
must be performed in a compatible recomp checkout; see that repository's build
instructions. `tools/sync_runtime.py` copies reference source headers and the
required Xenia/ReXGlue notice from that checkout into this project.

`materialize_paired.py` is a migration prototype for paired CPU/GPU resources.
It writes decoded component files and preserves unknown gaps, retaining original
payloads as backups. The owner metadata is the atomic pair commit point; interrupted
writes keep the prior mapping and can be retried. Exact shared ranges preserve
identity and partial overlaps reject. Individual source banks currently have a
256 MiB migration limit. Synthetic and all 40 private Xbox pairs (2,361 records) pass source-removal
checks; installed migration and gameplay acceptance are pending. Never migrate while a
game process is running. The supplied installation has not been migrated.
