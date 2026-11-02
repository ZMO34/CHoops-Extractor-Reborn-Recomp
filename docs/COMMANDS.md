# Commands

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
