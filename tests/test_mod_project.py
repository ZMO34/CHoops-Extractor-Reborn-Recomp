"""Synthetic authoring + actual shipped loader/native contracts; no game launch."""
import json
import os
from pathlib import Path
import shutil
import struct
import subprocess
import sys
import tempfile
import zipfile

import pytest

from choops_recomp.mod_project import ModProject,RuntimeContract,inventory,read_json,safe,sha,validate_archive,write_json,DATA

RUNTIME=Path(os.environ.get('CHMOD_RUNTIME',Path(__file__).resolve().parents[2]/'CH2K8-decomp'))


@pytest.fixture
def author(tmp_path):
    if not (RUNTIME/'ch2k8_tools.exe').is_file():pytest.skip('Set CHMOD_RUNTIME to a complete runtime checkout')
    sys.path[:0]=[str(RUNTIME/'tests'),str(RUNTIME/'tools')]
    from test_native_asset_tools import fixture_disc,IDENTITY
    from loose_assets import import_disc
    disc=tmp_path/'disc';fixture_disc(disc,'texture');game=tmp_path/'game';import_disc(disc,game,direct=True)
    # Isolated synthetic-runtime copy changes ONLY the expected XEX digest.
    # Studio production exposes no bypass of the retail XEX requirement.
    runtime=tmp_path/'runtime';(runtime/'tools').mkdir(parents=True);(runtime/'docs/formats').mkdir(parents=True)
    backend=(RUNTIME/'tools/chmod.ps1').read_text();backend=backend.replace('71e8983d1cc009e485696aad19b5fa4b4661761870e2c8972717b932c1e4be36',IDENTITY)
    (runtime/'tools/chmod.ps1').write_text(backend)
    shutil.copyfile(RUNTIME/'ch2k8_tools.exe',runtime/'ch2k8_tools.exe')
    for name in ('chmod.schema.json','hook_registry.json'):shutil.copyfile(RUNTIME/'docs/formats'/name,runtime/'docs/formats'/name)
    p=ModProject.create(tmp_path/'author',game/'assets',runtime,'test.art','Synthetic','Tests')
    p.state['manifest']['requires']['xex_sha256']=IDENTITY;p.save()
    bank=Path(read_json(game/'assets.json')['entries'][0]['folder']).name;p.add_bank(bank)
    return p,game,runtime


def change_texture(p):
    path=next((p.edit/'assets').rglob('texture.dds'));data=bytearray(path.read_bytes());data[128:136]=bytes.fromhex('00f8e00700000000');path.write_bytes(data)
    return path


def test_export_reopen_update_preserves_source_and_only_changes(author,tmp_path):
    p,game,runtime=author;before=inventory(game);change_texture(p)
    p=ModProject(p.root);rows=p.review();assert len(rows)==1
    out=tmp_path/'art.chmod';manifest=p.export(out)
    assert validate_archive(out)==manifest
    assert inventory(game)==before
    with zipfile.ZipFile(out) as z:assert set(z.namelist())=={'mod.json',rows[0]['target']}
    p.state['manifest']['version']='1.0.1';p.save();p.export(tmp_path/'art-update.chmod')
    assert validate_archive(out)['version']=='1.0.0'
    with pytest.raises(ValueError,match='new .chmod'):p.export(out)


def test_unknown_changes_and_source_mutation_fail_closed(author,tmp_path):
    p,game,runtime=author;change_texture(p)
    unknown=p.edit/'assets/unknown.bin';unknown.write_bytes(b'unsupported')
    with pytest.raises(ValueError,match='Unsupported changed'):p.export(tmp_path/'bad.chmod')
    assert not (tmp_path/'bad.chmod').exists();unknown.unlink()
    source=next((game/'assets').rglob('block0.dat'));source.write_bytes(source.read_bytes()+b'changed')
    with pytest.raises(ValueError,match='Source changed'):p.review()


def test_empty_and_bad_metadata_reject(author,tmp_path):
    p,game,runtime=author
    with pytest.raises(Exception):p.export(tmp_path/'empty.chmod')
    change_texture(p);p.state['manifest']['priority']=99
    with pytest.raises(Exception):p.export(tmp_path/'priority.chmod')


@pytest.mark.parametrize('name',['../escape','assets/CON.dds','assets/a./b','assets//b','C:/escape','assets/a\\b'])
def test_unsafe_paths_reject(tmp_path,name):
    with pytest.raises(ValueError):safe(tmp_path,name)


def test_archive_tamper_and_undeclared_reject(author,tmp_path):
    p,_,_=author;change_texture(p);out=tmp_path/'good.chmod';p.export(out)
    with zipfile.ZipFile(out,'a') as z:z.writestr('extra.txt','unexpected')
    with pytest.raises(ValueError,match='undeclared'):validate_archive(out)


def test_canonical_synthetic_fixture_accepted():
    fixture=RUNTIME/'examples/synthetic-art.chmod'
    if not fixture.is_file():pytest.skip('Runtime example unavailable')
    assert validate_archive(fixture)['id']=='example.synthetic-art'


def test_contract_drift_and_source_project_overlap(author,tmp_path):
    p,game,runtime=author
    with pytest.raises(ValueError,match='outside'):ModProject.create(game/'author',game/'assets',runtime,'test.bad','Bad','Tests')
    path=runtime/'docs/formats/chmod.schema.json';schema=read_json(path);schema['$defs']['label']['maxLength']=119;write_json(path,schema)
    with pytest.raises(ValueError,match='differs'):RuntimeContract(runtime)


def test_native_roster_and_hook_gates(author,tmp_path):
    p,_,_=author
    sys.path[:0]=[str(RUNTIME/'tests')]
    from test_chmod_contracts import synthetic_roster
    payload,header,_=synthetic_roster();save=tmp_path/'Roster.ROS';head=tmp_path/'Roster.ROS.header';save.write_bytes(payload);head.write_bytes(header)
    p.attach_roster(save,head)
    assert p.state['manifest']['roster']['sha256']==sha(payload)
    with pytest.raises(ValueError,match='unsupported'):p.attach_extension(tmp_path/'none.dll','scorebug.draw')
    bogus=tmp_path/'bad.dll';bogus.write_bytes(b'not a DLL')
    with pytest.raises(ValueError):p.attach_extension(bogus)
    assert 'extensions' not in p.state['manifest']


def test_project_tab_available(qtbot):
    from choops_recomp.ui.app import Studio
    window=Studio(offscreen=True);qtbot.addWidget(window)
    assert any(window.tabs.tabText(i)=='Mods / Mod Projects' for i in range(window.tabs.count()))


def test_project_activation_replaces_direct_workspace(author,qtbot):
    from choops_recomp.ui.app import Studio
    from choops_recomp.workspace import Workspace
    p,game,_=author;window=Studio(offscreen=True);qtbot.addWidget(window)
    window.loaded(Workspace(game/'assets'));generation=window.workspace_generation
    window.mod_projects.project=p;window.mod_projects.activate()
    assert window.workspace.root==p.edit
    assert window.workspace_generation>generation


def test_stale_project_metadata_rejected(author):
    p,_,_=author;other=ModProject(p.root);p.state['description']='Changed';p.save()
    with pytest.raises(ValueError,match='changed'):other.save()


def test_real_native_preparation_disable_and_update(author,tmp_path):
    p,game,runtime=author;before=inventory(game);change_texture(p);out=tmp_path/'art.chmod';p.export(out)
    script=tmp_path/'prepare.ps1';script.write_text('''param($Backend,$Package,$Game,$Mods,$Cache,$Tool)
$ErrorActionPreference='Stop'
. $Backend
$m=Install-Chmod $Package $Mods
$selection=@([pscustomobject]@{id=$m.id;version=$m.version})
$plan=Resolve-Chmods $Game $Mods $selection
$prepared=New-ChmodCache $Game $Cache $plan {param($root) $null=& $Tool prepare $root; if($LASTEXITCODE){throw 'Preparation failed'}}
$null=& $Tool validate-runtime $prepared
if($LASTEXITCODE){throw 'Runtime map failed'}
$disabled=Resolve-Chmods $Game $Mods @()
if((New-ChmodCache $Game $Cache $disabled {throw 'Unexpected prepare'}) -ne $Game){throw 'Disable failed'}
''')
    # The current runtime PowerShell cache copier still has MAX_PATH limits.
    # Keep its private cache shallow; do not weaken any resource/path check.
    with tempfile.TemporaryDirectory(prefix='c-',dir=tmp_path.parent) as cache:
        result=subprocess.run(['powershell.exe','-NoProfile','-ExecutionPolicy','Bypass','-File',str(script),str(runtime/'tools/chmod.ps1'),str(out),str(game),str(tmp_path/'mods'),cache,str(runtime/'ch2k8_tools.exe')],capture_output=True,text=True,timeout=90)
    assert result.returncode==0,result.stdout+result.stderr
    assert inventory(game)==before


def test_mixed_assets_and_supported_code_never_loads_dll(author,tmp_path):
    p,game,_=author;change_texture(p)
    from test_chmod_api12 import fake_dll
    dll=tmp_path/'synthetic.dll';dll.write_bytes(fake_dll());p.attach_extension(dll)
    out=tmp_path/'mixed.chmod';m=p.export(out)
    assert m['content']==['assets','code']
    assert set(m['capabilities'])=={'dds.replace','hook.player.weight.read'}
    # The synthetic PE has no executable implementation; acceptance proves only
    # structural declaration/PE validation, never LoadLibrary or hook execution.


def test_native_roster_edit_rewrapped_and_revalidated(author,tmp_path):
    p,_,_=author
    from test_chmod_contracts import synthetic_roster
    from choops_recomp.roster import Roster
    data,header,_=synthetic_roster();save=tmp_path/'Roster.ROS';head=tmp_path/'Roster.ROS.header';save.write_bytes(data);head.write_bytes(header);p.attach_roster(save,head)
    resource=p.workspace().of_type('ROST')[0];model=Roster(resource.blocks()[0]);model.set_player(0,'jersey_number',42);model.save(resource.component_path())
    stage=tmp_path/'stage';stage.mkdir();manifest=p.build(stage)
    exported=(stage/manifest['roster']['file']).read_bytes()
    assert struct.unpack_from('>I',exported)[0]==len(exported)-4
    assert Roster(exported[4:]).rows['players'][0]['jersey_number']==42
    assert save.read_bytes()==data and head.read_bytes()==header
    # Missing uniform routes reject combined activation rather than exporting
    # unrelated jersey filenames as if they were linked.
    with pytest.raises(ValueError,match='unregistered uniform'):p.export(tmp_path/'missing-uniforms.chmod')


def test_cloth_export_uses_native_preservation_contract(author,tmp_path):
    p,_,runtime=author
    from test_chmod_contracts import synthetic_cloth
    from test_native_asset_tools import IDENTITY
    from loose_assets import import_disc
    # Construct an importer-compatible synthetic IFF with one CPU SCNE record.
    body=synthetic_cloth();head=bytearray(96)
    struct.pack_into('>8I',head,0,0xff3bef94,96,96+len(body),0,1,0,1,64-28+1)
    struct.pack_into('>8I',head,32,0,0xbb05a9c1,0,len(body),0,96,len(body),0)
    struct.pack_into('>I',head,64,68-64+1);struct.pack_into('>4I',head,68,0x12345678,0xe26c9b5d,1,0)
    iff=bytes(head)+body;size=(2048+len(iff)+2047)&~2047;archive=bytearray(size)
    struct.pack_into('>6I',archive,0,0xaa00b3bf,2048,1,0,1,0);struct.pack_into('>II8s',archive,24,size//2048,0,'0A'.encode('utf-16-be').ljust(8,b'\0'))
    struct.pack_into('>4I',archive,40,0x11223344,1,0,len(iff));archive[2048:2048+len(iff)]=iff
    disc=tmp_path/'cloth-disc';disc.mkdir();(disc/'default.xex').write_bytes(b'XEX2 fixture');(disc/'0A').write_bytes(archive)
    game=tmp_path/'cloth-game';import_disc(disc,game,direct=True)
    project=ModProject.create(tmp_path/'cloth-author',game/'assets',runtime,'test.cloth','Cloth','Tests');project.state['manifest']['requires']['xex_sha256']=IDENTITY;project.save()
    project.add_bank(Path(read_json(game/'assets.json')['entries'][0]['folder']).name)
    component=next((project.edit/'assets').rglob('block0.dat'));changed=bytearray(component.read_bytes());struct.pack_into('>f',changed,0x200,0.25);component.write_bytes(changed)
    manifest=project.export(tmp_path/'cloth.chmod');assert manifest['assets'][0]['kind']=='cloth.positions'
    changed[0x241]^=1;component.write_bytes(changed)
    with pytest.raises(ValueError):project.export(tmp_path/'bad-cloth.chmod')


def test_authored_native_roster_dummy_hdd_isolation(author,tmp_path):
    p,_,runtime=author
    from test_chmod_contracts import synthetic_roster
    payload,header,_=synthetic_roster();save=tmp_path/'Roster.ROS';head=tmp_path/'Roster.ROS.header';save.write_bytes(payload);head.write_bytes(header);p.attach_roster(save,head)
    stage=tmp_path/'stage';stage.mkdir();m=p.build(stage)
    baseline=tmp_path/'baseline';old=baseline/'B13EBABEBABEBABE/54540818/00000001/Roster.ROS/Roster.ROS';old.parent.mkdir(parents=True);old.write_bytes(b'original user roster')
    legacy=old.parent.parent/'Legacy.LEG/Legacy.LEG';legacy.parent.mkdir();legacy.write_bytes(b'original legacy')
    before=inventory(baseline);script=tmp_path/'profile.ps1';script.write_text('''param($Backend,$Stage,$Baseline,$Profiles)
$ErrorActionPreference='Stop'
. $Backend
$m=Read-Chmod $Stage
$r=[pscustomobject]@{mod=$m.id;version=$m.version;file=(Join-Path $Stage $m.roster.file);header=(Join-Path $Stage $m.roster.header);sha256=$m.roster.sha256;header_sha256=$m.roster.header_sha256}
$p=[pscustomobject]@{active=@([pscustomobject]@{id=$m.id;version=$m.version});replacements=@();roster=$r;extensions=@()}
$first=New-ChmodRosterProfile $Baseline $Profiles $p
if((New-ChmodRosterProfile $Baseline $Profiles $p) -ne $first){throw 'Persistent profile changed'}
$p.roster=$null
if((New-ChmodRosterProfile $Baseline $Profiles $p) -ne $Baseline){throw 'Disable failed'}
Write-Output $first
''')
    with tempfile.TemporaryDirectory(prefix='hdd-',dir=tmp_path.parent) as profiles:
        result=subprocess.run(['powershell.exe','-NoProfile','-ExecutionPolicy','Bypass','-File',str(script),str(runtime/'tools/chmod.ps1'),str(stage),str(baseline),profiles],capture_output=True,text=True,timeout=60)
        assert result.returncode==0,result.stderr
        isolated=Path(result.stdout.strip())
        assert (isolated/old.relative_to(baseline)).read_bytes()==payload
        assert not (isolated/legacy.relative_to(baseline)).exists()
    assert inventory(baseline)==before
