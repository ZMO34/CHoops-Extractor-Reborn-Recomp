import importlib.util,json,struct,sys,zlib
from pathlib import Path
import pytest
from choops_recomp import runtime_protocol


def modules(monkeypatch):
    monkeypatch.syspath_prepend(str(Path(__file__).resolve().parents[1]/'runtime'))
    monkeypatch.setitem(sys.modules,'xbox_asset_edits',runtime_protocol)
    import materialize_paired,direct_folder
    return materialize_paired,direct_folder


def fixture(tmp_path,overlap=False):
    root=tmp_path;assets=root/'assets';assets.mkdir()
    name='texturedata.bin';identity=zlib.crc32(name.upper().encode())&0xffffffff
    entries=[dict(hash=1,folder='assets/test.cdf',index=0,size=256),dict(hash=identity,folder='assets/'+name,index=1,size=40)]
    for e in entries:
        p=root/e['folder'];p.mkdir();(p/'asset.json').write_text('{}')
    raw=b'CPU-DATA';packed=b'ZLIB'+struct.pack('>III',len(raw),16+len(zlib.compress(raw)),0)+zlib.compress(raw)
    body=b'GAP!'+packed+b'GPU!'+b'TAIL'
    head=bytearray(256);struct.pack_into('>II',head,0,0xf0985030,256);struct.pack_into('>I',head,24,1)
    for field,target in [(32,112),(36,160),(104,120),(112,144)]:struct.pack_into('>I',head,field,target-field+1)
    struct.pack_into('>II',head,120,0x12345678,0x5c369069)
    struct.pack_into('>4I',head,144,4,len(packed),5 if overlap else 4+len(packed),4)
    head[160:160+len(name.encode('utf-16-be'))]=name.encode('utf-16-be')
    (root/entries[0]['folder']/'payload.dat').write_bytes(head);(root/entries[1]['folder']/'payload.dat').write_bytes(body)
    (root/'assets.json').write_text(json.dumps(dict(version=1,platform='xbox360',storage='loose-resources',entries=entries,total=1024)))
    return entries,bytes(head),body


def test_paired_resources_survive_removal_of_original_payloads(tmp_path,monkeypatch):
    converter,direct=modules(monkeypatch);entries,head,body=fixture(tmp_path)
    assert converter.materialize_pair(tmp_path,*entries)==1
    for e in entries:(tmp_path/e['folder']/'payload.dat').unlink()
    reader=runtime_protocol.SourceReader(tmp_path)
    assert reader.blocks(dict(bank=1,record=0))==(0x5c369069,[b'CPU-DATA',b'GPU!'])
    # Exercise the exact runtime mapper without requiring a synthetic catalog header.
    folder=direct.DirectFolder.__new__(direct.DirectFolder);folder.root=tmp_path
    views=[folder.bank(e) for e in entries]
    outputs=[b''.join((tmp_path/s['path']).read_bytes() for s in v['segments']) for v in views]
    assert outputs[1]==b'GAP!CPU-DATAGPU!TAIL'
    assert struct.unpack_from('>4I',outputs[0],144)==(4,8,12,4)
    assert outputs[0][:144]==head[:144] and outputs[0][160:]==head[160:]
    assert converter.materialize_pair(tmp_path,*entries)==0
    from choops_recomp.workspace import Workspace
    resource=Workspace(tmp_path/'assets').resource('test.cdf/0')
    assert resource.blocks()==[b'CPU-DATA',b'GPU!']


def test_partial_overlap_rejected_before_metadata_or_files_change(tmp_path,monkeypatch):
    converter,_=modules(monkeypatch);entries,head,body=fixture(tmp_path,True)
    with pytest.raises(ValueError,match='overlap'):converter.materialize_pair(tmp_path,*entries)
    assert all(json.loads((tmp_path/e['folder']/'asset.json').read_text())=={} for e in entries)
    assert not (tmp_path/entries[1]['folder']/'_loose').exists()


def test_interrupted_pair_keeps_original_mapping_and_retry_commits(tmp_path,monkeypatch):
    converter,direct=modules(monkeypatch);entries,head,body=fixture(tmp_path)
    publish=converter.publish
    def interrupted(path,data):
        if path==tmp_path/entries[0]['folder']/'asset.json':raise OSError('simulated interruption')
        publish(path,data)
    monkeypatch.setattr(converter,'publish',interrupted)
    with pytest.raises(OSError,match='interruption'):converter.materialize_pair(tmp_path,*entries)
    folder=direct.DirectFolder.__new__(direct.DirectFolder);folder.root=tmp_path
    view=folder.bank(entries[1]);assert len(view['segments'])==1
    assert view['segments'][0]['path'].endswith('/payload.dat')
    monkeypatch.setattr(converter,'publish',publish)
    assert converter.materialize_pair(tmp_path,*entries)==1
    assert all(not s['path'].endswith('/payload.dat') for s in folder.bank(entries[1])['segments'])
