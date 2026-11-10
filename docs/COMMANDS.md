# Commands

## Security update

Run `python -m pip_audit --strict --skip-editable` after installing the Studio development dependencies and pip-audit. The CHMOD `export`, `attach-roster`, `attach-extension` and `attach-uniform` commands require `--runtime` pointing to a trusted local installation.

After `tools/build_windows.py`, `tools/package_release.py` creates the Windows
release ZIP and SHA-256 sidecar under `output/releases`. It rejects unexpected
game/debug content and includes dependency license texts.

```powershell
python -m venv .venv
.venv/Scripts/python.exe -m pip install -e '.[dev]'
.venv/Scripts/python.exe tools/setup_audio.py
.venv/Scripts/python.exe run_studio.py --assets 'GAME/assets'
.venv/Scripts/python.exe -m choops_recomp --assets 'GAME/assets' info
.venv/Scripts/python.exe -m choops_recomp --assets 'GAME/assets' scene-info s000.iff/9
.venv/Scripts/python.exe -m choops_recomp --assets 'GAME/assets' export-wav 'RESOURCE_KEY' 'new.wav'
.venv/Scripts/python.exe -m choops_recomp --assets 'GAME/assets' import-wav 'RESOURCE_KEY' 'edited.wav'
.venv/Scripts/python.exe -m pytest -q --basetemp=output/pytest-run
```

`RESOURCE_KEY` is the bank/record identity; stream resources include `:INDEX`.
Use CLI `--help` for roster and uniform commands. GUI and CLI share their writers.
Do not infer that a command's presence certifies runtime acceptance.

`runtime/materialize_paired.py` is a development migration prototype. Use only
on private fixtures while full-corpus and gameplay checks remain pending; do not run it against an active game installation.

`import-artwork RESOURCE_KEY image.png` shares the texture writer and supports
DDS, PNG, JPEG, TGA and BMP inputs without chunk rebuilding.

`inspect-resource RESOURCE_KEY --component 0 --offset 0x100 --length 256` reads
only the selected owning component. Pages larger than 64 KiB are rejected.
`tools/paired_smoke.py --assets GAME/assets --output output/NEW_PRIVATE_FOLDER`
validates paired extraction on a private copy and removes only copied payloads.

`review-audio-folder EXPORTED_FOLDER` prints changed tracks and source identities.
`import-audio-folder EXPORTED_FOLDER --resources bank.iff/0,bank.iff/1` applies
selected reviewed identities; omit `--resources` to apply all changed tracks.

`export-cloth-obj RESOURCE_KEY cloth.obj` writes source-bound geometry and JSON.
`import-cloth-obj RESOURCE_KEY cloth.obj` saves supported model-space positions.
`tools/cloth_smoke.py --assets GAME/assets --output output/NEW_PRIVATE_FOLDER`
checks every identified cloth resource on private copies without launching a game.

Relationship commands: `roster-links`, `assign-link TEAM FIELD TARGET`,
`move-player PLAYER TEAM`, `move-conference TEAM CONFERENCE`, and
`reorder-player TEAM PLAYER POSITION`. Use `none` for unassignment.
Uniform commands: `uniform-edit ROW --asset ID --shape CODE --variant CODE
--unlock CODE`, `uniform-detach TEAM`, `uniform-clone TEAM ROW UNUSED_ASSET`,
`uniform-available TEAM SLOT on|off`, `export-font-atlas RESOURCE out.png`, and
`import-font-atlas RESOURCE edited.png`. Writes use the same checked GUI backends.

Private checks: `tools/relationship_smoke.py --assets GAME/assets --output
output/NEW_FOLDER`, `tools/asset_smoke.py --assets GAME/assets --output
output/NEW_FOLDER --full-editor`, and `tools/roster_ui_smoke.py --assets
GAME/assets --output output/NEW_FOLDER`. These do not launch or control a game.

For an automated packaged-editor check, set `QT_QPA_PLATFORM=offscreen` and run
`CHoops-Recomp-Studio.exe --smoke --smoke-dialogs --assets GAME/assets --report
report.json`. It constructs the new dialogs and decodes an indexed atlas without
showing a desktop window, changing assets or launching a game.

Texture corpus audit (read-only):
```powershell
.venv/Scripts/python.exe tools/texture_layout_audit.py --assets GAME/assets --output output/texture-audit.json --pixels
.venv/Scripts/python.exe tools/render_smoke.py --assets GAME/assets --arena 0 --arena-mode combined --expect-textured --output output/arena.png
```
Player fields and conference-history scalars share GUI, roster CSV and CLI
writers. See `roster-set --help`; selected CSV changes form one undoable edit.

# Mod project commands

`python run_studio.py --cli mod --help` lists create, add-bank, review, metadata,
attach-roster, attach-uniform, attach-extension, export and inspect commands.
The existing direct editor commands can target `PROJECT/edit/assets` to edit
private copies, including an attached native roster body. `inspect` checks ZIP,
schema and integrity; export additionally invokes runtime semantic validation.
See [complete command examples](CHMOD_AUTHORING.md#cli).
`python tools/build_windows.py --output output/package-chmod` builds separately
when another packaged editor is open.
