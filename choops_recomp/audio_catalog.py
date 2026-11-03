"""Audio views retain their separate identities, including uncategorized banks.

Classification uses Xbox bank identity. Mixed jukebox streams stay unclassified
until the Xbox jukebox table establishes each per-track category.
"""
from pathlib import Path
import json
from functools import lru_cache

LICENSED='Licensed Music'
BAND='Band / Fight Songs'
OTHER='Other Audio'
CATEGORIES=(LICENSED,BAND,OTHER)

@lru_cache
def tracks():
    data=json.loads((Path(__file__).parent/'data/xbox_jukebox.json').read_text())
    if data['platform']!='xbox360' or len(data['tracks'])!=87:raise ValueError('Invalid Xbox music catalog')
    return {row['index']:row for row in data['tracks']}


def metadata(resource):
    bank=Path(resource.record.get('stream_bank','')).stem.casefold()
    return tracks().get(resource.record.get('stream'),{}) if bank=='cribmusic' else {}


def category(resource):
    bank=Path(resource.record.get('stream_bank','')).stem.casefold()
    if bank=='band':return BAND
    if bank=='cribmusic':return metadata(resource).get('category',OTHER)
    return OTHER


def group(resources):
    result={name:[] for name in CATEGORIES}
    for resource in resources:result[category(resource)].append(resource)
    return result


def cover_resource(resource):
    row=metadata(resource)
    if not row.get('cover_record'):return None,0
    from .uniform_preview import unique
    cover=unique(resource.workspace,'jukebox.iff','TXTR',row['cover_record'])
    shared=sum(track.get('cover_record')==row['cover_record'] for track in tracks().values())
    return cover,shared
