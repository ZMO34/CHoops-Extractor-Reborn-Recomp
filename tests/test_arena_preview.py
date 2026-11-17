from types import SimpleNamespace
from PIL import Image
from choops_recomp import arena_preview as arena


def test_combined_records_keep_distinct_texture_identity_and_source_coordinates(monkeypatch):
    resources=[SimpleNamespace(entry=dict(hash=arena.crc('S000.IFF')),record=dict(id=arena.crc(role)),key=role,folder=SimpleNamespace(__truediv__=lambda *args:None),blocks=lambda role=role:[role.encode(),b'gpu']) for role in ('arena','floor')]
    from pathlib import Path
    for r in resources:r.folder=Path('/nonexistent/private-fixture')
    workspace=SimpleNamespace(of_type=lambda kind:resources)
    monkeypatch.setattr(arena.scene,'preview',lambda blocks:dict(meshes=[dict(name='floor',vertices=[(1,2,3)],batches=[dict(texture_index=0)])],warnings=[],declared_parts=1))
    monkeypatch.setattr(arena.scene,'textures',lambda blocks:[dict(index=0,dds=blocks[0])]);monkeypatch.setattr(arena.dds,'image',lambda payload:Image.new('RGBA',(4,4),'red' if payload==b'arena' else 'blue'))
    monkeypatch.setattr(arena.dds,'info',lambda payload:{})
    result=arena.preview(workspace,0)
    assert len(result['images'])==2 and len(result['meshes'])==2
    assert result['meshes'][0]['batches'][0]['texture_index']!=result['meshes'][1]['batches'][0]['texture_index']
    assert all(m['vertices']==[(1,2,3)] for m in result['meshes'])
