from types import SimpleNamespace
import pytest
from choops_recomp.inspection import page,hex_text


def test_resource_inspection_cannot_cross_component_extent(tmp_path):
    (tmp_path/'body').write_bytes(b'prefix'+b'ABC\x00'+b'suffix')
    workspace=SimpleNamespace(safe=lambda relative:tmp_path/relative)
    resource=SimpleNamespace(workspace=workspace,components=[dict(file='body',offset=6,size=4)],entry={})
    assert page(resource,length=100)==b'ABC\x00'
    assert page(resource,offset=3)==b'\x00'
    assert page(resource,offset=4)==b''
    with pytest.raises(ValueError,match='exceeds'):page(resource,offset=5)
    with pytest.raises(ValueError,match='64 KiB'):page(resource,length=65537)
    assert hex_text(page(resource)).endswith('ABC.')


def test_loose_inspection_reads_current_component_size(tmp_path):
    (tmp_path/'bank').mkdir();(tmp_path/'bank/body').write_bytes(b'newly grown roster')
    resource=SimpleNamespace(workspace=SimpleNamespace(safe=lambda relative:tmp_path/relative),components=[dict(path='body')],entry=dict(folder='bank'))
    assert page(resource)==b'newly grown roster'
