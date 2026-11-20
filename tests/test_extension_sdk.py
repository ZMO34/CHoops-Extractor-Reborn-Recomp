"""ABI 2 Studio attachment cases; prepared, not run. No DLL loading."""
import json
import pytest
from test_mod_project import author


def fake_dll():
    import struct
    b=bytearray(512);b[:2]=b'MZ';struct.pack_into('<I',b,60,128)
    b[128:132]=b'PE\0\0';struct.pack_into('<H',b,132,0x8664)
    struct.pack_into('<H',b,150,0x2000);struct.pack_into('<H',b,152,0x20b)
    return b


def test_sdk_attachment_keeps_manifest_capabilities(author,tmp_path):
    project=author[0]
    dll=tmp_path/'neutral.dll';dll.write_bytes(fake_dll())
    project.attach_extension(dll,abi=2,capabilities=['hook.player.weight.read','lifecycle.runtime.ready'],replacements=['player.weight.read'])
    m=project.state['manifest']
    assert m['requires']['mod_api']=='1.3.0'
    assert m['extensions'][0]['abi']==2
    assert m['extensions'][0]['replacements']==['player.weight.read']
    assert m['extensions'][0]['capabilities']==['hook.player.weight.read','lifecycle.runtime.ready']


@pytest.mark.parametrize('capabilities,replacements',[(['simulation.guess'],[]),(['hook.player.weight.read'],['player.weight.write']),(['hook.player.weight.read']*2,[])])
def test_unsupported_attachment_is_non_destructive(author,tmp_path,capabilities,replacements):
    project=author[0]
    before=json.dumps(project.state,sort_keys=True)
    dll=tmp_path/'neutral.dll';dll.write_bytes(fake_dll())
    with pytest.raises(ValueError):project.attach_extension(dll,abi=2,capabilities=capabilities,replacements=replacements)
    assert json.dumps(project.state,sort_keys=True)==before
