"""Direct owning-resource file edits and the native binding registry."""
import json
from . import dds,audio,scene
from .workspace import atomic_write,sha


def reference(resource):
    result=dict(bank=resource.entry['hash'],record=resource.record['index'])
    if 'stream' in resource.record:result['stream']=resource.record['stream']
    return result


def register(resource,source,path,kind):
    root=resource.workspace.root;marker=root/'asset_edits.json';before=marker.read_bytes() if marker.exists() else None
    registry=json.loads(before) if before else dict(version=1,platform='xbox360',edits=[])
    if registry.get('version')!=1 or registry.get('platform')!='xbox360':raise ValueError('Unsupported edit registry')
    entry=dict(source=source,file=path.resolve().relative_to(root).as_posix(),kind=kind)
    registry['edits']=[e for e in registry['edits'] if (e['source'],e['kind'])!=(source,kind)]+[entry]
    atomic_write(marker,(json.dumps(registry,indent=2)+'\n').encode(),sha(before) if before is not None else None)


def save_scene_texture(resource,index,payload):
    original=next(t['dds'] for t in scene.textures(resource.blocks()) if t['index']==index and 'dds' in t)
    folder=resource.folder;folder.mkdir(parents=True,exist_ok=True);path=folder/f'texture_{index:04d}.dds'
    if not path.exists():atomic_write(path,original)
    dds.replace(path,payload,original);source=dict(reference(resource),texture=index);register(resource,source,path,'dds');return path


def save_texture(resource,payload):
    blocks=resource.blocks();original=dds.xbox_dds(blocks[0],blocks[1] if len(blocks)>1 else None)
    folder=resource.folder;folder.mkdir(parents=True,exist_ok=True);path=folder/'texture.dds'
    if not path.exists():atomic_write(path,original)
    dds.replace(path,payload,original);register(resource,reference(resource),path,'dds');return path


def save_audio(resource,path):
    audio.import_wav(resource,path);register(resource,reference(resource),resource.folder/'audio.wav','pcm')
