# User guide

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
