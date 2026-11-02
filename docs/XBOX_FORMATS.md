# Xbox format evidence

## Roster

Xbox player stride is **316 bytes**. Header-relative descriptors locate players,
arenas, schools, coaches, conferences and uniforms; fixed source-platform table
addresses are not used. The supplied corpus has 5,685 players, 443 schools,
379 arenas, 1,373 coaches, 39 conferences and 988 uniform rows. All known name
pointers validate. All 988 uniform routes resolve to existing Xbox asset hashes.

Native getter/setter registrations and Xbox localization confirm the 30 scaled
16-bit rating channels and 33 appearance/equipment properties. Thirty enum
option lists are resolved through their own Xbox localization IDs. The promoted
profile records only Xbox offsets, masks, menu limits and native evidence IDs.
The logical player anchor is raw row +16. For example, native weight getter
`84752968` and setter `848425d8` use anchor+0x8C bits 5..13; handedness uses
anchor+0x84 bit 14. These are different from the source-platform packed layout.

School reference candidates were checked across all 443 Xbox rows: arenas
441 valid/2 null, conferences 443 valid, rivals 339/234/101 valid with remaining
null, head coach and both assistants 443 valid each. No invalid targets were
observed. Reciprocal assignment writers still need separate verification.

## Scenes and textures

Observed Xbox SCNE mesh records are 176 bytes; embedded texture descriptors are
224 bytes. Vertex count is descriptor+8; stream count is the high halfword at+12.
Vertex declarations use Xenos formats. Instance transforms are selected only
when the 128/144-byte candidate layout is unambiguous and homogeneous.

Embedded Xbox cloth retains vertex count at descriptor+8 and stream count in the
high halfword at+12, but uses 24-byte stream descriptors rather than the GPU
scene's 16-byte form. Twenty-one candidate cloth filenames match actual Xbox
CRC identities. The combined U/regular jersey and regular shorts preview resolves
exact SCNE and `unifregion`/`shortregion` TXTR record identities.

Native DDS presently supports 2D BC1/BC2/BC3/BC4/BC5. Xbox DXT5A maps to ATI1/BC4,
and DXN to ATI2/BC5, matching the SDK's native host formats. GPU payload offsets are stored
plus one and may be nonzero for embedded textures. The editor decodes Xbox tile
and endian layout only for source previews/identity; edited DDS stays native.

The observed shoe scene uses Xenos 2/10/10/10 packed positions and a 240-byte
named material table. All eight material names match their stored CRCs. Static
upper/sole routing uses those names, not record order; runtime-only black vertex
lighting is replaced by neutral lighting for the authored-artwork preview.

## Audio and localization

Xbox AUDO has 44 bytes (11 big-endian words), XMA2 codec 5 and 2048-byte packets.
Playback format 2 is mono, 5 stereo. Paired CDF ranges and AUSB stream extents are
resolved through actual embedded Xbox filenames and CRC32 asset identities.

Jukebox native song table `84f983d8` has 23 licensed rows, four bytes of padding,
then 64 fight-song rows, each 36 bytes. The shorter artwork/artist table at
`84f99018` links through pointers; its ordering must not be assumed to match the
song table. All 87 stream indices and title IDs were validated against Xbox
localization. Shared-cover inference beyond explicit links remains unresolved.

Xbox localization uses magic E33E3B9C and a dynamic relative table pointer;
the supplied table begins at 48, not a hard-coded source-platform offset.
Observed literal tokens are 0x01/ASCII pairs. Other token kinds stay opaque.

Reproduction tools under `tools/research` read supplied assets and a read-only
Ghidra project. Private outputs and game data are excluded from version control.

Paired-folder prototype: F0985030 resource descriptors retain their native
record identities and metadata. CPU/GPU extents become individual decoded files;
only the compatibility descriptor offsets and lengths are relocated. Exact
shared extents retain one file, partial overlaps reject, and unclaimed gap/tail
bytes are preserved. Synthetic and all 40 Xbox pairs pass source-removal checks; installed migration and runtime
acceptance remain pending. No packed bank is generated.

Batch native PCM uses source-bound WAV manifests and canonical PCM16 files.
New export manifests include WAV SHA256 values to distinguish unchanged exports.
Application stages each reviewed input, checks source/destination hashes, and
rolls back preceding WAV/metadata writes on ordinary failures. It does not
change XMA packets or rebuild a bank. Interrupted processes may leave a recovery
manifest and backups; multi-track crash atomicity is not claimed.

Embedded cloth OBJ evidence: Xbox CPU stream descriptors use 24-byte rows; the
verified float3 position format is Xenos 57. Source export retains original
vertex indices and triangulates validated strips. Position-only import checks
source SHA256, per-mesh counts and exact live topology, patches only the three
big-endian floats, then reparses. All 33 identified cloth resources pass private
round-trip and single-coordinate checks. Exports use model-space positions;
instance matrices and runtime cloth/skin deformation remain unchanged.
