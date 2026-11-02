# User guide

Run `run_studio.py`, then choose File → Open assets folder. Select the installed
recomp's `assets` directory beside `assets.json`. The editor never launches the
game. Restart the game manually through its launcher after saving edits.

Models / Courts lists Xbox SCNE records. Select one for textured 3D preview;
orbit/pan/zoom and Fit camera inspect authored geometry. Cutaway hides identified
roof/light-effect meshes. Export DDS or Replace DDS operates on the selected
embedded texture. Unsupported layouts are reported explicitly.

Textures previews individual TXTR records. DDS replacement retains BC format and
aspect ratio and permits power-of-two upscales up to 8192 pixels. No automatic
downsizing occurs. This is not yet support for every Xbox texture format.

Audio separates Licensed Music, Band / Fight Songs and Other Audio. Jukebox
titles come from Xbox tables. Play decodes a temporary WAV; Stop ends playback.
Export WAV exports the current replacement when present, otherwise the Xbox XMA2
source. Import WAV writes PCM directly into that resource's folder. Current
imports require matching channels, sample rate and sample count. Export tab
publishes WAV files with an Xbox source-identity manifest in a new folder.
Install the pinned decoder with `tools/setup_audio.py` for source WAV exports.

Roster provides table cells and player appearance/rating panes. Edit confirmed
fields, use Undo/Redo, then Save roster. Unknown neighboring bits remain intact.
Numeric appearance codes do not yet have every option caption. Existing unusual
values are preserved until edited. Save rejects an externally changed roster.

Export CSV writes the selected roster table and a companion Xbox source-identity
file. Keep the two files together. Import / compare validates the source and
shows every changed cell with field checkboxes before applying anything. Applied
fields form one undoable edit; Save roster writes them to disk. Copy ratings and
Paste ratings to selected support multiple selected player rows.

New uniform creates alternate world/selection asset folders from the selected
school's Home template and saves the edited roster. This feature remains under
integration validation; see the status and parity tracker before using it.
