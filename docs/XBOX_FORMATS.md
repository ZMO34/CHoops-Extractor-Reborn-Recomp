# Xbox format evidence

## Roster

Xbox player stride is **316 bytes**. Header-relative descriptors locate players,
arenas, schools, coaches, conferences and uniforms; fixed source-platform table
addresses are not used. The supplied corpus has 5,685 players, 443 schools,
379 arenas, 1,373 coaches, 39 conferences and 988 uniform rows. All known name
pointers validate. All 988 uniform routes resolve to existing Xbox asset hashes.

Native getter/setter registrations and Xbox localization confirm the 30 scaled
16-bit rating channels and 21 appearance/equipment properties. The promoted
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

Native DDS presently supports 2D BC1/BC2/BC3. GPU payload offsets are stored
plus one and may be nonzero for embedded textures. The editor decodes Xbox tile
and endian layout only for source previews/identity; edited DDS stays native.

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
