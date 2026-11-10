import struct
from types import SimpleNamespace
import pytest
from choops_recomp import geometry


def source(tmp_path,monkeypatch):
    path=tmp_path/'cloth.dat';data=bytearray(b'X'*256)
    for i,xyz in enumerate(((0.,0.,0.),(1.,0.,0.),(0.,1.,0.))):struct.pack_into('>3f',data,64+i*20,*xyz)
    path.write_bytes(data)
    resource=SimpleNamespace(key='cloth/0',blocks=lambda:[path.read_bytes()],component_path=lambda:path)
    def preview(blocks,**kwargs):
        points=[struct.unpack_from('>3f',blocks[0],64+i*20)+(0.,0.) for i in range(3)]
        mesh=dict(points=points,indices=[0,1,2],position=dict(format=57,quantized=False,offset=0),stream_start=64,stride=20)
        return dict(warnings=[],source_meshes=[mesh],declared_parts=1)
    monkeypatch.setattr(geometry.scene,'preview',preview)
    return resource,path,bytes(data)


def test_obj_round_trip_and_position_edit_preserve_unknown_bytes(tmp_path,monkeypatch):
    resource,target,original=source(tmp_path,monkeypatch);obj=tmp_path/'cloth.obj';geometry.export_obj(resource,obj)
    assert geometry.import_obj(resource,obj)==3 and target.read_bytes()==original
    obj.write_text(obj.read_text().replace('v 0 0 0','v 0.25 0 0'))
    geometry.import_obj(resource,obj);edited=target.read_bytes()
    assert edited[:64]==original[:64] and edited[68:]==original[68:]
    assert struct.unpack_from('>f',edited,64)[0]==.25


@pytest.mark.parametrize('before,after',[('f 1/1 2/2 3/3','f 2/2 1/1 3/3'),('v 0 0 0','v nan 0 0')])
def test_obj_rejects_topology_and_nonfinite_positions(tmp_path,monkeypatch,before,after):
    resource,target,original=source(tmp_path,monkeypatch);obj=tmp_path/'cloth.obj';geometry.export_obj(resource,obj)
    obj.write_text(obj.read_text().replace(before,after))
    with pytest.raises(ValueError):geometry.import_obj(resource,obj)
    assert target.read_bytes()==original


def test_obj_rejects_stale_source(tmp_path,monkeypatch):
    resource,target,original=source(tmp_path,monkeypatch);obj=tmp_path/'cloth.obj';geometry.export_obj(resource,obj)
    target.write_bytes(original+b'external')
    with pytest.raises(ValueError,match='companion'):geometry.import_obj(resource,obj)
    assert target.read_bytes()==original+b'external'
