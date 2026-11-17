"""Definitions promoted from Xbox registration/getter/setter/localization audits."""
import json
from pathlib import Path
PROFILE=json.loads((Path(__file__).parent/'data/xbox_player_fields.json').read_text())
if PROFILE['platform']!='xbox360':raise ValueError('Xbox player profile required')
FIELDS={row['key']:row for row in PROFILE['fields']}
RATINGS=PROFILE['ratings']
