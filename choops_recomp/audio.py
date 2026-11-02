"""Xbox 44-byte AUDO/XMA2 resources and native PCM WAV replacements."""
from pathlib import Path
import json
import os
import shutil
import struct
import subprocess
import tempfile
import wave
import io
import sys
from .workspace import atomic_write,sha
from .dds import fnv64


def info(blocks):
    if len(blocks)!=2 or len(blocks[0])!=44:raise ValueError('Xbox audio requires the confirmed 44-byte header and payload')
    version,codec,fmt,samples,rate,flags,size,*unknown=struct.unpack('>11I',blocks[0])
    if version!=1 or codec!=5 or fmt not in (2,5) or not 1000<=rate<=192000 or not 0<size<=len(blocks[1]) or size%2048 or not samples:raise ValueError('Unsupported Xbox AUDO/XMA2 layout')
    return dict(codec='XMA2',channels=1 if fmt==2 else 2,sample_rate=rate,samples=samples,encoded_bytes=size,seconds=samples/rate,source_identity=fnv64(blocks[1][:2048]),opaque_words=[flags,*unknown])


def wav_info(path):
    with wave.open(str(path),'rb') as stream:
        if stream.getcomptype()!='NONE' or stream.getsampwidth()!=2:raise ValueError('Import uncompressed signed 16-bit PCM WAV')
        return dict(channels=stream.getnchannels(),sample_rate=stream.getframerate(),samples=stream.getnframes())


def decoder_path():
    configured=os.environ.get('CHOOPS_VGMSTREAM')
    candidates=[Path(configured)] if configured else []
    candidates += [Path(__file__).resolve().parents[1]/'output/tools/vgmstream/vgmstream-cli.exe',Path(__file__).resolve().parents[1]/'tools/vgmstream/vgmstream-cli.exe']
    if getattr(sys,'frozen',False):candidates.insert(0,Path(sys.executable).parent/'tools/vgmstream/vgmstream-cli.exe')
    found=shutil.which('vgmstream-cli')
    if found:candidates.append(Path(found))
    for p in candidates:
        if p.is_file():return p
    raise ValueError('Install the pinned open-source decoder with tools/setup_audio.py or set CHOOPS_VGMSTREAM')


def export_wav(resource,destination,original=False):
    blocks=resource.blocks();meta=info(blocks);destination=Path(destination)
    if destination.exists():raise ValueError('Choose a new WAV destination')
    destination.parent.mkdir(parents=True,exist_ok=True)
    current=resource.folder/'audio.wav'
    if not original and current.is_file():
        check=wav_info(current)
        if any(check[k]!=meta[k] for k in ('channels','sample_rate','samples')):raise ValueError('Edited WAV no longer matches its Xbox resource')
        with destination.open('xb') as stream:stream.write(current.read_bytes())
        return dict(meta,edited=True)
    with tempfile.TemporaryDirectory(prefix='choops-xma-') as tmp:
        work=Path(tmp);raw=work/'input.xma';raw.write_bytes(blocks[1][:meta['encoded_bytes']])
        raw.with_suffix('.xma.txth').write_text('\n'.join(['codec = XMA2',f"channels = {meta['channels']}",f"sample_rate = {meta['sample_rate']}",f"num_samples = {meta['samples']}",'start_offset = 0',f"data_size = {meta['encoded_bytes']}"])+'\n',encoding='ascii')
        out=work/'decoded.wav'
        result=subprocess.run([str(decoder_path()),'-i','-W','1','-o',str(out),str(raw)],capture_output=True,text=True,timeout=300,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
        if result.returncode or not out.exists():raise ValueError('Xbox XMA decode failed: '+result.stderr[-1500:])
        check=wav_info(out)
        if any(check[k]!=meta[k] for k in ('channels','sample_rate','samples')):raise ValueError('Decoded WAV differs from declared Xbox stream parameters')
        with destination.open('xb') as stream:stream.write(out.read_bytes())
    return meta


def import_wav(resource,source):
    meta=info(resource.blocks());check=wav_info(source)
    if any(check[k]!=meta[k] for k in ('channels','sample_rate','samples')):raise ValueError('Native WAV replacement must match original channel count, sample rate and sample count; no automatic resampling or trimming is performed')
    folder=resource.folder;folder.mkdir(parents=True,exist_ok=True)
    # Canonical PCM container: Python also reads extensible WAVs, whereas the
    # runtime deliberately accepts only the small, standard PCM representation.
    with wave.open(str(source),'rb') as incoming:
        frames=incoming.readframes(incoming.getnframes())
    if len(frames)!=check['samples']*check['channels']*2:raise ValueError('Truncated PCM samples')
    buffer=io.BytesIO()
    with wave.open(buffer,'wb') as outgoing:
        outgoing.setnchannels(check['channels']);outgoing.setsampwidth(2);outgoing.setframerate(check['sample_rate']);outgoing.writeframes(frames)
    target=folder/'audio.wav';payload=buffer.getvalue()
    atomic_write(target,payload,sha(target.read_bytes()) if target.exists() else None)
    marker=dict(version=1,platform='xbox360',resource=resource.record['index'],file='audio.wav',kind='native-pcm',source_identity=meta['source_identity'],channels=meta['channels'],sample_rate=meta['sample_rate'],samples=meta['samples'])
    if 'stream' in resource.record:marker['stream']=resource.record['stream']
    atomic_write(folder/'audio.json',(json.dumps(marker,indent=2)+'\n').encode())
    return marker


def export_batch(resources,destination,progress=None):
    """Publish a complete WAV folder only after every selected track succeeds."""
    import uuid
    destination=Path(destination)
    if destination.exists():raise ValueError('Choose a new audio export folder')
    destination.parent.mkdir(parents=True,exist_ok=True)
    scratch=destination.with_name('.studio-audio-'+uuid.uuid4().hex);scratch.mkdir();rows=[]
    try:
        for i,resource in enumerate(resources):
            if progress:progress(i,len(resources),resource.label)
            filename=f'{i:05d}.wav';meta=export_wav(resource,scratch/filename)
            rows.append(dict(resource=resource.key,file=filename,label=resource.label,source_identity=meta['source_identity'],channels=meta['channels'],sample_rate=meta['sample_rate'],samples=meta['samples']))
        (scratch/'audio_manifest.json').write_text(json.dumps(dict(version=1,platform='xbox360',tracks=rows),indent=2)+'\n')
        scratch.rename(destination)
    except BaseException:
        if scratch.exists() and scratch.parent==destination.parent and scratch.name.startswith('.studio-audio-'):shutil.rmtree(scratch)
        raise
    return rows


def validate_batch(workspace,folder):
    """Review all source identities and PCM parameters before applying any track."""
    folder=Path(folder).resolve();manifest=json.loads((folder/'audio_manifest.json').read_text())
    if manifest.get('version')!=1 or manifest.get('platform')!='xbox360':raise ValueError('An Xbox audio export manifest is required')
    result=[];seen=set()
    for row in manifest['tracks']:
        key=row['resource']
        if key in seen:raise ValueError('Duplicate audio replacement target')
        seen.add(key);resource=workspace.resource(key);source=(folder/row['file']).resolve()
        if not source.is_relative_to(folder):raise ValueError('Audio import path escapes selected folder')
        meta=info(resource.blocks());check=wav_info(source)
        if meta['source_identity']!=row['source_identity'] or any(check[k]!=meta[k] for k in ('channels','sample_rate','samples')):raise ValueError('Audio import differs from its Xbox source: '+key)
        with wave.open(str(source),'rb') as incoming:
            if len(incoming.readframes(check['samples']))!=check['samples']*check['channels']*2:raise ValueError('Truncated batch PCM samples')
        result.append((resource,source))
    return result
