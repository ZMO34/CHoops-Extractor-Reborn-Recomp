# User guide

## Security update

Install updated dependencies before launching Studio. When opening a CHMOD project, select a trusted local runtime installation in the runtime picker.

Run `run_studio.py`, then choose File â†’ Open assets folder. Select the installed
recomp's `assets` directory beside `assets.json`. The editor never launches the
game. Restart the game manually through its launcher after saving edits.

There is no asset-archive build step. Save DDS, WAV and individual model/roster
resources in their owning folders. The runtime discovers those files and reads
resource bodies directly; small generated compatibility headers stay inside the
loader. New uniform folders include their own identity metadata. Keep their
`asset.json` and resource files together when moving them between installations.

Models / Courts lists Xbox SCNE records. Select one for textured 3D preview;
orbit/pan/zoom and Fit camera inspect authored geometry. Cutaway hides identified
roof/light-effect meshes. Export DDS or Replace DDS operates on the selected
embedded texture. Unsupported layouts are reported explicitly.

The uniform controls combine an authored Xbox jersey and shorts with the selected
uniform's DDS artwork. Choose a uniform, neckline, top build and shorts build,
then Preview uniform. This is a static rest pose; name/number overlays, the
player's body and runtime cloth simulation are not yet reproduced.

Textures previews individual TXTR records. DDS replacement retains BC1â€“BC5 format and
aspect ratio and permits power-of-two upscales up to 8192 pixels. No automatic
downsizing occurs. This is not yet support for every Xbox texture format.

Preview shoes resolves existing Xbox artwork names and binds their upper/sole
textures to the authored shoe mesh. The static viewer uses neutral lighting and
does not reproduce the game's full palette/material shader.

Audio separates Licensed Music, Band / Fight Songs and Other Audio. Jukebox
titles come from Xbox tables. Play decodes a temporary WAV; Stop ends playback.
Export WAV exports the current replacement when present, otherwise the Xbox XMA2
source. Import WAV writes PCM directly into that resource's folder. Current
imports require matching channels, sample rate and sample count. Export tab
publishes WAV files with an Xbox source-identity manifest in a new folder.
Install the pinned decoder with `tools/setup_audio.py` for source WAV exports.

Roster provides table cells and player appearance/rating panes. Edit confirmed
fields, use Undo/Redo, then Save roster. Unknown neighboring bits remain intact.
Thirty appearance fields use native Xbox caption dropdowns. Existing unusual
values are preserved until edited. Save rejects an externally changed roster.

Export CSV writes the selected roster table and a companion Xbox source-identity
file. Keep the two files together. Import / compare validates the source and
shows every changed cell with field checkboxes before applying anything. Applied
fields form one undoable edit; Save roster writes them to disk. Copy ratings and
Paste ratings to selected support multiple selected player rows.

New uniform creates alternate world/selection asset folders from the selected
school's Home template and saves the edited roster. This feature remains under
integration validation; see the status and parity tracker before using it.

Texture, embedded model texture and album-cover replacement also accept PNG,
JPEG, TGA and BMP. These are encoded to the original BC1–BC5 format at the
supplied dimensions with mipmaps. Supply the original size or a proportional
power-of-two upscale; the editor does not downsize artwork. Covers can be shared
by several tracks; the preview tooltip identifies that relationship.

Select a resource and choose Inspect resource files to view its component bytes.
Choose the component and a hexadecimal offset; each read displays up to 4 KiB
without crossing the component boundary. Legacy paired source components may
still be compressed; the inspector labels that representation explicitly.

Audio: Export tab writes a source-bound WAV folder. Edit its WAVs, then use Import
folder to review changed tracks and select which to save. Unchanged WAVs from
new exports are skipped. Replacements retain original channels, rate and sample
count. Save rechecks the reviewed files and destinations, then applies them to
each owning folder. A write failure restores preceding changes; if a concurrent
edit prevents restoration, recovery files and their target manifest are retained
at the location reported by the editor.

Cloth OBJ: select the cloth SCNE resource in Models / Courts, then Export cloth
OBJ. Keep the OBJ companion JSON beside it. Edit positions in source model space
and retain vertex order/count and exact triangulated faces. Import cloth positions
validates the source and topology, then saves positions directly to its component.
UV, normal, rigging and topology edits are not imported. Shared cloth affects all
uniforms using that resource; this is distinct from editing a uniform DDS.

Roster now includes School relationships and Uniform editor. The first handles
checked school links, player transfers/lineup and conference membership. The
second edits uniform routing, clones private artwork and previews authored player
numbers/surnames. Both use pending roster edits until Save roster; artwork Save
and folder-creation actions explicitly write their owning files. See
[roster relationships](ROSTER_RELATIONSHIPS.md) and [uniforms](UNIFORMS.md).
Indexed uniform atlases also preview/export/import from the Textures library.

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

# Create and export a mod

Use **Mods / Mod Projects → Create Mod**, add source banks and select **Edit
project copies**. Save edits, review differences, then **Export .chmod**. Reopen
the project to continue authoring; change its version for an update. The launcher
installs/enables packages and controls priority. Native saves and compiled DLLs
have separate attachment controls and explicit limits. The source installation
and live saves are never modified in this workflow. Read the
[complete authoring guide](CHMOD_AUTHORING.md) before exporting mixed content.

## C++ native extensions

The SDK is included at `sdk/` and hosted in this repository. Start with sdk/README.md
and sdk/AUTHORING.md. Building an extension needs developer tools; installing a
.chmod needs only the recomp launcher. DLLs are unsandboxed and require explicit
launcher opt-in. Studio exports never load them. Use the source CLI's ABI 2
attachment options for capability-driven DLLs; the existing GUI/default remains
compatible ABI 1. No new Studio authoring UI is implemented here.

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


## Named mod folders

In Mod Projects choose Export mod folder and select a parent directory. Studio creates a folder named for the mod ID with mod.json and assets. Copy it into the runtime mods directory or use Install mod folder.

## Folder mod workflow in 0.2.0

1. In **Mods / Mod Projects**, create a project using a pristine Xbox assets folder and the matching recomp runtime.
2. For existing artwork, find a texture or scene by name or folder path, then use **Copy selected bank into Mod Project**. In the project's Textures tab, drop an image on the selected texture preview and confirm Save. For an embedded texture, select its slot and drop on the scene artwork target.
3. For a one-image court, choose **Build one-image court**, enter the court ID or place the DDS in a folder named for the ID, and drop the DDS. Use the UGA layout at 2048×1024, BC1/DXT1, with 12 mip levels. Use a runtime with the native full-court builder.
4. For a new uniform, choose **Add X/Y/Z jersey**, pick the school and a vacant alternate, then drop the world jersey and shorts artwork. Supply a separate selection jersey when its format or dimensions differ. The launcher links eligible Home-derived artwork; shared or occupied routes require manual roster work.
5. Choose **Export Mod Folder**. Import the generated folder in the recomp launcher and enable its exact version.

3D previews and roster editing still use the existing workspace tools. To edit a roster, attach a compatible native Roster.ROS and its aggregate header in the project. Original installed assets are read-only. Audio preview and export remain available; raw audio and indexed-font edits have no mod folder contract. Compile custom code with the SDK outside Studio. Attach a compiled supported DLL for packaging, or use the mod CLI to declare ABI 2 capabilities.

## Uniform artwork in 0.2.1

In **Add X/Y/Z jersey**, drop the world jersey and shorts artwork and optionally separate selection jersey artwork. Studio generates BC5 bumps and BC4 material maps (green maps) at the Xbox template sizes. Clear **Generate jersey and shorts bump and material maps** to keep the template maps. Dropping jersey or shorts artwork updates the 3D garment preview. Choose the neckline in the wizard or inherit Home. Logos and trim painted into the garment go in the garment artwork.

Drop optional world number, selection number, surname, and world logo artwork. For the number and surname sheets, start from the stock template. Keep the dimensions, glyph cells, and transparent background from the corresponding stock sheet, with at most 256 exact RGBA colors. Export stock sheets from the **Uniforms** artwork selector as PNG templates. Selection banks have a separate, smaller number sheet. Player number assignments remain in the roster editor.

To replace sheets on an existing uniform, copy the corresponding bank into your project, select its artwork in **Uniforms** or **Asset Lookup**, and export the mod folder. Alternate sheet imports and saved necklines require the updated native tools from 0.2.1.

In the **Roster** tab, attach a native `Roster.ROS` and its aggregate header through **Mod Projects**. **Export roster as mod** creates a roster-only mod folder. **Export roster save** creates a fresh folder containing the edited `Roster.ROS` and its portable header. **Choose player shoes** edits brand, style, and Home/Away color for the selected player. The verified roster has no separate alternate shoe fields.

With active mods, the launcher clears unlock codes and makes installed alternate pairs available on supported native roster saves. A new route inherits its Home uniform characteristics, with the alternate wizard's neckline applied if specified. Install a native roster save in the recomp first when using new alternate banks.

## Replace a stock uniform

In **Mods / Mod Projects**, choose **Build or replace uniform**, then select a team and **Home (UH)**, **Away (UA)**, or an alternate. A routed stock uniform is replaced in the mod overlay, including its selection bank. A vacant X/Y/Z slot is built from Home. Drop the artwork you want to change. A replacement can edit just one garment or sheet, while a new alternate needs world jersey and shorts artwork. Automatic BC5 bumps and BC4 material maps are enabled for each supplied garment. Use the roster editor for stock neckline changes.

Export the mod folder and install it in the launcher with the matching 0.2.2 native tools. When multiple teams share the same bank or roster route, use an independently routed bank for a team-specific replacement.

## Where texture mods are installed

The recomp launcher reads texture replacements from installed mod packages
under `mods/`. For a loose texture override, the `assets/` path in the
package mirrors the vanilla bank and record path. The launcher reads the
replacement bytes from the package and creates a separate runtime cache.
Vanilla files are the read-only source. Disable the mod to load vanilla textures.

This applies to supported standalone and embedded texture slots in courts,
arenas, menus, uniforms, shoes, and other banks. For an existing texture,
copy the owning bank into a Studio project, replace the selected artwork, and
export a mod folder. The exported package includes the selected overrides.
Packed or unrecognized layouts still need a verified codec and an exportable
slot before Studio can produce a replacement.

## Open, combine, and separate mod folders

Studio remembers the installed assets path and the Mods folder. Use **Set Mods Folder** to change the default location for package pickers and exports.

Choose **Open Project or Mod Folder** to open an author project or bring an existing `mod.json` package into a new working folder. Named texture paths and registered XYZ world and selection banks are available in the project browser. Other package payloads can be carried through export according to their existing manifest contract.

**Combine with Mod Folder** makes a new project containing the current project and another package. An overlap on the same resource requires a choice of input. **Separate Content** makes a new project containing the selected bank, uniform pair, roster, or code group. Give combined and separated projects a new mod ID. Export a new folder for launcher import.

## Browse a mod collection

Choose **Open Project or Mod Folder**, select the collection folder, and choose
a child package to edit. Export separate packages into the appropriate
collection folders for use in the launcher. The collection root holds
categories and child packages. Each child has its own `mod.json`.

Choose **Import scorebug artwork** inside an open project to convert a supported
PS3 bottom-bar ZIP into Xbox texture overrides. The conversion uses the Xbox
scene layout. Export the textures as a mod folder.
