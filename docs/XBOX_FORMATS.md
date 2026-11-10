# Xbox format evidence

## Security update

Component decoding bounds zlib output by the declared uncompressed extent and copies only the bytes used by each H7A match. CHMOD inspection accepts stored and deflated ZIP entries and checks the archive size before reading its directory.

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

The checked school membership/relationship profile and its entire Xbox corpus
validation are documented in [ROSTER_RELATIONSHIPS.md](ROSTER_RELATIONSHIPS.md).
Indexed uniform palette/mip/metric layouts, authored placement and the new
Recomp-only dormant-row protocol are documented in [UNIFORMS.md](UNIFORMS.md).

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

# CHMOD source-bound export evidence (2026-11-08)

The canonical local runtime API 1.2 schema and hook registry are embedded without
modification in `choops_recomp/data/chmod.schema.json` and `chmod_hooks.json`.
Studio checks these against the selected runtime, then delegates semantic/source
checks to its actual `Read-Chmod`, `Install-Chmod`, `Resolve-Chmods` and native
`validate-cloth`, `validate-roster`, `validate-uniform` implementations. No new
Xbox IDs, offsets, hook points or save layouts are introduced.
Native save edits retain their actual header and researched big-endian 32-bit
body-length wrapper; Studio's existing Xbox roster writer edits only a private
body. Loose ROST components are never converted to native saves. Source identity
comes from original bank/record metadata and hashes, never replacement filenames.
The only DLL hook is the runtime's researched `player.weight.read` ABI 1.
Full provenance, validation levels and exclusions: [CHMOD authoring](CHMOD_AUTHORING.md).

## Extension SDK research boundary

SDK ABI 2 maps only Xbox weight getter 84752968 and setter848425D8 to semantic
callback-scoped interfaces. PPC extraction/insertion and Studio field records agree;
Ghidra read-only disassembly and generated function maps are preserved in the
recomp docs/research/hooks. Host ready/stopping are not guest save lifecycle.
Getter consumers may indirectly persist results; setter modifies a real packed
field. No existing Legacy migration, raw memory interface or gameplay claim is
introduced. Full contracts and available operations are in sdk/hooks.json and
sdk/CONTRACTS.md. No current ABI 2 capability is in-game verified.

## SDK Button Style extension (2026-11-08)

The hosted SDK now includes typed `presentation.button_style` hook 5, its readable
C++ DLL consumer, and `sdk/package_button_style.py` for a mixed DLL + conditional
DDS `.chmod`. ABI 2 host layout is unchanged; capability negotiation rejects older
runtimes. The native Options/Presentation adapter and live D3D12 selection are
implemented and compiled in the recomp. This is a narrow researched Xbox adapter,
not arbitrary UI construction. Source evidence and callback/ownership contracts:
[sdk/BUTTON_STYLE.md](../sdk/BUTTON_STYLE.md). Artwork remains private.

Runtime, extension and synthetic dispatch test executables compiled. No tests,
DLLs or game were executed, and no user saves were changed in this follow-up.
The supplied JPEG alpha is reconstructed; navigation/controller atlases remain
Xbox. Remote acceptance is pending. Source CLI/canonical runtime validation
accepts the new capability; existing GUI/default DLL attachment remains ABI 1.
