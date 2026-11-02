"""Direct owning-resource edits; modern runtimes discover files in place."""
import json
from . import dds,audio,scene
from .workspace import atomic_write,sha


def artwork_payload(path,original):
    """Retain supplied DDS or encode image artwork at its supplied resolution."""
    from pathlib import Path
    path=Path(path)
    return path.read_bytes() if path.suffix.casefold()=='.dds' else dds.from_image(path,original)


def reference(resource):
    result=dict(bank=resource.entry['hash'],record=resource.record['index'])
    if 'stream' in resource.record:result['stream']=resource.record['stream']
    return result


def register(resource,source,path,kind):
    # Modern runtimes discover conventional resource files in their own folders.
    # Keep this compatibility adapter only for pre-migration installations.
    if resource.workspace.manifest.get('storage')=='loose-resources':return
    root=resource.workspace.root;marker=root/'asset_edits.json';before=marker.read_bytes() if marker.exists() else None
    registry=json.loads(before) if before else dict(version=1,platform='xbox360',edits=[])
    if registry.get('version')!=1 or registry.get('platform')!='xbox360':raise ValueError('Unsupported edit registry')
    entry=dict(source=source,file=path.resolve().relative_to(root).as_posix(),kind=kind)
    registry['edits']=[e for e in registry['edits'] if (e['source'],e['kind'])!=(source,kind)]+[entry]
    atomic_write(marker,(json.dumps(registry,indent=2)+'\n').encode(),sha(before) if before is not None else None)


def save_scene_texture(resource,index,payload):
    original=next(t['dds'] for t in scene.textures(resource.blocks()) if t['index']==index and 'dds' in t)
    if 'raw_format' in dds.info(original) or dds.info(original).get('direct_component'):
        from types import SimpleNamespace
        from .raw_texture import save_dds,save_bc_base
        blocks=resource.blocks();header=next(t['header_offset'] for t in scene.textures(blocks) if t['index']==index);proxy=SimpleNamespace(blocks=lambda:[blocks[0][header:header+224],blocks[1]],component_path=resource.component_path,workspace=resource.workspace)
        return (save_dds if 'raw_format' in dds.info(original) else save_bc_base)(proxy,payload)
    resource.workspace.require('native_dds_formats',next(fmt for fmt,(code,size) in dds.FORMATS.items() if code==original[84:88]))
    folder=resource.folder;folder.mkdir(parents=True,exist_ok=True);path=folder/f'texture_{index:04d}.dds'
    if not path.exists():atomic_write(path,original)
    dds.replace(path,payload,original);source=dict(reference(resource),texture=index);register(resource,source,path,'dds');return path


def save_texture(resource,payload):
    blocks=resource.blocks();original=dds.xbox_dds(blocks[0],blocks[1] if len(blocks)>1 else None)
    if 'raw_format' in dds.info(original) or dds.info(original).get('direct_component'):
        from .raw_texture import save_dds,save_bc_base
        return (save_dds if 'raw_format' in dds.info(original) else save_bc_base)(resource,payload)
    resource.workspace.require('native_dds_formats',next(fmt for fmt,(code,size) in dds.FORMATS.items() if code==original[84:88]))
    folder=resource.folder;folder.mkdir(parents=True,exist_ok=True);path=folder/'texture.dds'
    if not path.exists():atomic_write(path,original)
    dds.replace(path,payload,original);register(resource,reference(resource),path,'dds');return path


def save_audio(resource,path):
    resource.workspace.require('native_pcm')
    audio.import_wav(resource,path);register(resource,reference(resource),resource.folder/'audio.wav','pcm')
