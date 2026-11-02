# Feature parity tracker

The target is the released College Hoops feature set in Extractor Reborn v1.23,
adapted to direct Xbox assets-folder editing. No percentage is claimed while
applicable features remain incomplete. A parser alone does not complete a GUI,
writer, preservation test or integration requirement.

| Feature | Current state | Work remaining |
| --- | --- | --- |
| Open installed assets; search resources | Implemented | Cancelable indexing and diagnostics polish |
| Direct folder loading | Component reads, self-contained additions and natural DDS/WAV discovery implemented | All 40 paired banks pass private source-removal checks; installed migration and gameplay acceptance pending |
| DDS preview/export/import | BC1–BC5, indexed, raw 2D/cubemap base editing implemented | Full raw mip-chain replacement and batch workflows |
| Native higher-resolution DDS | BC1–BC5 upload/readback passed on hardware and WARP | Runtime acceptance and additional layouts |
| Arena/floor textured 3D preview | Implemented observed layouts | Full source corpus, material/lightmap behavior, runtime lighting |
| Uniform/shoe previews | Authored cloth, front/back numbers, curved surnames, school/player selection and shoe artwork implemented | Runtime cloth/body/material effects and gameplay acceptance |
| Uniform indexed fonts | All 1,976 atlas/metric pairs validated; exact-color image and metric writers, preview implemented | Fixed native dimensions/palette capacity; gameplay acceptance |
| Uniform OBJ workflow | Source-bound float3 cloth OBJ import/export in GUI/CLI; all 33 identified resources pass private preservation checks | Additional vertex layouts, rest/skin deformation parity and gameplay acceptance |
| Court surface controls | Pending | Xbox geometry bindings and preservation tests |
| Roster names, jersey, height, position | Implemented | Search/filter and related side panels |
| Ratings | 30 Xbox-verified channels, copy/paste, selective CSV compare | School filters and richer selection controls |
| Appearance/equipment | 46 Xbox-verified properties, native option lists | Runtime acceptance |
| Palette | 31 RGBA slots | Xbox semantic captions and preview bindings |
| School/coach/arena relationships | Checked school dialog and CLI assignments for arena, coach, assistants and rivals | Gameplay/Legacy acceptance; shared arena identity intentionally retained |
| Player transfers / scholarships | Checked 18-slot transfers, unassignment and lineup order implemented | Gameplay acceptance |
| Conference realignment/history | Checked reciprocal realignment in GUI/CLI implemented | Four historical scalars implemented; unknown recency/order semantics and gameplay acceptance |
| Roster CSV and selective import | Implemented confirmed fields, source-bound review, one-step undo | Additional Xbox fields as verified |
| Existing uniform asset/shape editing | Checked editor, artwork validation, neckline/slot/unlock, private routing/artwork cloning and alternate availability implemented | Gameplay acceptance of new routing/dormant state |
| New uniforms and asset links | Private Home/Away/alternate artwork and additive folders pass preservation/reopen/direct-map checks | Gameplay acceptance; stadium/menu-logo independence remains separate |
| Licensed Music and Band/Fight Songs tabs | Implemented from Xbox evidence | Shared-cover routing and DDS/image artwork controls implemented; runtime acceptance pending |
| WAV export/import/preview | Implemented | Native loop/seek and duration parity, packaging acceptance |
| Batch WAV | Export, changed-track review, selective GUI/CLI apply and write-failure rollback implemented | Process-interruption recovery polish and gameplay acceptance |
| Raw inspection/diagnostics | Bounded owning-resource hex inspection in GUI/CLI implemented | Richer structured diagnostics |
| Change packages | Pending | Source-bound asset deltas without unchanged game bytes |
| Documentation ecosystem | Established | Update evidence and acceptance records with each feature |

Intentionally removed per owner request: archive/disc explorer, overrides/staging,
disc rebuilding, console codec conversion for native WAV imports, automatic
texture downsizing, other games' profiles and source-platform saved-data adapters.
Their removal does not excuse missing applicable editing functionality.

Upstream draft scorebug, Legacy/recruit and animation-port research is not
represented as a released working feature. Relevant research requires new Xbox
evidence before adoption; incomplete research is not silently marked obsolete.

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
