"""Private author workspaces and the runtime's canonical CHMOD contract.

Project metadata is editor-only. Only canonical mod.json and declared payloads
enter an archive. No game launch, DLL loading, or live save installation occurs.
"""
import copy
import json
import os
from pathlib import Path
import re
import shutil
import struct
import subprocess
import tempfile
import zipfile

from .workspace import Workspace, atomic_write, sha

DATA = Path(__file__).with_name('data')
XEX = '71e8983d1cc009e485696aad19b5fa4b4661761870e2c8972717b932c1e4be36'
LIMIT = 512 * 1024 * 1024


def parse_json(data):
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result: raise ValueError('Duplicate JSON key: ' + key)
            result[key] = value
        return result
    def invalid(value):raise ValueError('Non-JSON constant: '+value)
    result=json.loads(data.decode('utf-8-sig') if isinstance(data,bytes) else data,object_pairs_hook=unique,parse_constant=invalid)
    def depth(value,level=0):
        if isinstance(value,(dict,list)):
            if level>=32:raise ValueError('JSON nesting exceeds 32 containers')
            for child in (value.values() if isinstance(value,dict) else value):depth(child,level+1)
    depth(result)
    return result


def read_json(path, limit=1024 * 1024):
    if Path(path).stat().st_size > limit: raise ValueError('Metadata exceeds size limit')
    return parse_json(Path(path).read_bytes())


def write_json(path, value, expected=None):
    atomic_write(path, (json.dumps(value, indent=2) + '\n').encode(), expected)


def safe(root, relative):
    if not isinstance(relative, str) or len(relative) > 220 or not re.fullmatch(r'[A-Za-z0-9_./-]+', relative):
        raise ValueError('Unsafe package/project path')
    for part in relative.split('/'):
        if part in ('', '.', '..') or part.endswith('.') or re.match(r'(?i)^(CON|PRN|AUX|NUL|COM[0-9]|LPT[0-9])(\.|$)', part):
            raise ValueError('Unsafe path segment: ' + part)
    root = Path(root).absolute()
    target = root / relative
    cursor = target
    while True:
        if cursor.is_symlink() or (cursor.exists() and cursor.stat().st_file_attributes & 0x400 if os.name == 'nt' else False):
            raise ValueError('Linked project paths are unsupported')
        if cursor == cursor.parent: break
        cursor = cursor.parent
    if not target.resolve().is_relative_to(root.resolve()): raise ValueError('Path escapes project')
    return target


def inventory(root):
    result = {}
    for path in Path(root).rglob('*'):
        relative = path.relative_to(root).as_posix()
        safe(root, relative)
        if path.is_file(): result[relative] = sha(path.read_bytes())
    return result


class RuntimeContract:
    """Invoke shipped validators, never an extension from a package."""
    def __init__(self, root):
        self.root = Path(root).resolve()
        self.backend = self.root / 'tools/chmod.ps1'
        self.tool = next((p for p in (self.root/'ch2k8_tools.exe', self.root/'port/out/build/win-amd64-vulkan/ch2k8_tools.exe') if p.is_file()), None)
        if not self.backend.is_file() or self.tool is None: raise ValueError('Select a complete API 1.2 runtime with tools/chmod.ps1 and ch2k8_tools.exe')
        for name in ('chmod.schema.json', 'hook_registry.json'):
            local = DATA / ('chmod_hooks.json' if name == 'hook_registry.json' else name)
            if read_json(self.root/'docs/formats'/name) != read_json(local):
                raise ValueError('Runtime contract differs from Studio snapshot; update Studio before exporting')

    def native(self, command, *args):
        result = subprocess.run([str(self.tool), command, *map(str, args)], capture_output=True, text=True, timeout=45, creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
        if result.returncode: raise ValueError(result.stderr or result.stdout)
        proof = json.loads(result.stdout)
        if proof.get('ready') is not True: raise ValueError('Native contract did not report ready')
        return proof

    def dll(self, path):
        with tempfile.TemporaryDirectory(prefix='studio-pe-') as temp:
            script=Path(temp)/'check.ps1';script.write_text("param($Backend,$Payload)\n$ErrorActionPreference='Stop'\n. $Backend\nAssert-ChmodDll $Payload\n",encoding='utf-8')
            result=subprocess.run(['powershell.exe','-NoProfile','-ExecutionPolicy','Bypass','-File',str(script),str(self.backend),str(path)],capture_output=True,text=True,timeout=30,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
            if result.returncode:raise ValueError(result.stderr or result.stdout)

    def package(self, folder, game, dependencies=None):
        # Install and resolve only in a disposable directory. AllowCode authorizes
        # metadata validation here; Resolve-Chmods never loads a DLL or saves opt-in.
        with tempfile.TemporaryDirectory(prefix='studio-contract-') as temp:
            script = Path(temp)/'validate.ps1'
            script.write_text("""param($Backend,$Folder,$Game,$Mods,$Deps)
$ErrorActionPreference='Stop'
. $Backend
$m=Read-Chmod $Folder
$null=Install-Chmod $Folder $Mods
$selection=@()
foreach($dep in (Get-Content -Raw -LiteralPath $Deps | ConvertFrom-Json)) {
  $d=Read-Chmod $dep
  $null=Install-Chmod $dep $Mods
  $selection+= [pscustomobject]@{id=$d.id;version=$d.version}
}
$selection+= [pscustomobject]@{id=$m.id;version=$m.version}
$null=Resolve-Chmods $Game $Mods $selection -AllowCode $true
Write-Output 'CHMOD_VALID'
""", encoding='utf-8')
            deps = Path(temp)/'dependencies.json'; write_json(deps, list(map(str, dependencies or [])))
            result = subprocess.run(['powershell.exe', '-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', str(script), str(self.backend), str(folder), str(game), str(Path(temp)/'mods'), str(deps)], capture_output=True, text=True, timeout=120, creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
            if result.returncode or 'CHMOD_VALID' not in result.stdout: raise ValueError(result.stderr or result.stdout)


class ModProject:
    def __init__(self, root, runtime=None):
        self.root = Path(root).resolve()
        self.path = safe(self.root, 'project.json')
        self.state = read_json(self.path,32*1024*1024)
        if self.state.get('project_version') != 1: raise ValueError('Unsupported author project version')
        self.source = Path(self.state['source']).resolve()
        if self.root.is_relative_to(self.source) or self.source.is_relative_to(self.root): raise ValueError('Source and project must be separate')
        self.edit = safe(self.root, 'edit'); self.package_root = safe(self.root, 'package')
        self._contract = RuntimeContract(runtime) if runtime is not None else None
        self.expected = sha(self.path.read_bytes())

    @property
    def contract(self):
        if self._contract is None:
            raise ValueError('Select a trusted runtime explicitly before running native validation')
        return self._contract

    @classmethod
    def create(cls, destination, assets, runtime, mod_id, name, author):
        source = Path(assets).resolve().parent
        destination = Path(destination).resolve()
        if Path(assets).name.casefold() != 'assets': raise ValueError('Select the installed assets folder')
        if destination.exists() or destination.is_relative_to(source) or source.is_relative_to(destination): raise ValueError('Choose a new project directory outside the source installation')
        contract = RuntimeContract(runtime)
        catalog = read_json(source/'assets.json',32*1024*1024)
        if catalog.get('platform') != 'xbox360' or catalog.get('storage') != 'loose-resources': raise ValueError('Requires Xbox direct loose resources')
        manifest = dict(schema_version=1, id=mod_id, name=name, author=author, version='1.0.0', requires=dict(xex_sha256=XEX, recomp='ZMO-beta1', mod_api='1.2.0'), content=['assets'], capabilities=['dds.replace'], dependencies=[], incompatible=[], assets=[])
        # Validate metadata through the canonical schema, before touching disk.
        from jsonschema import Draft202012Validator
        schema = read_json(DATA/'chmod.schema.json')
        for field in ('id','name','author'): Draft202012Validator({'$ref': '#/$defs/'+('id' if field=='id' else 'label'), '$defs':schema['$defs']}).validate(manifest[field])
        destination.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(prefix='.studio-project-', dir=destination.parent) as temp:
            stage=Path(temp)/'project';stage.mkdir();(stage/'edit/assets').mkdir(parents=True);(stage/'package').mkdir()
            empty=copy.deepcopy(catalog);empty['entries']=[];write_json(stage/'edit/assets.json',empty)
            if (source/'runtime_capabilities.json').is_file(): shutil.copyfile(source/'runtime_capabilities.json',stage/'edit/runtime_capabilities.json')
            state=dict(project_version=1, source=str(source), runtime=str(contract.root), description='', manifest=manifest, source_catalog_sha256=sha((source/'assets.json').read_bytes()), baseline={}, banks=[])
            write_json(stage/'project.json',state);os.rename(stage,destination)
        return cls(destination, contract.root)

    def save(self):
        write_json(self.path,self.state,self.expected);self.expected=sha(self.path.read_bytes())

    def add_bank(self, bank):
        self.check_source()
        catalog=read_json(self.source/'assets.json',32*1024*1024)
        matches=[e for e in catalog['entries'] if e['folder']=='assets/'+bank]
        if len(matches)!=1: raise ValueError('Select one existing source bank folder')
        if bank in self.state['banks']: return
        entry=matches[0];source=safe(self.source,entry['folder'])
        layout=read_json(source/'asset.json')
        if not layout.get('blocks') or layout.get('paired_resources'): raise ValueError('Only standard source-bound banks are exportable; paired resources remain gated')
        files=inventory(source)
        with tempfile.TemporaryDirectory(prefix='.bank-',dir=self.root) as temp:
            stage=Path(temp)/bank;shutil.copytree(source,stage)
            if inventory(stage)!=files or inventory(source)!=files: raise ValueError('Source changed during project copy')
            os.rename(stage,safe(self.edit,entry['folder']))
        edit_catalog=read_json(self.edit/'assets.json');edit_catalog['entries'].append(entry);write_json(self.edit/'assets.json',edit_catalog)
        self.state['banks'].append(bank)
        self.state['baseline'].update({entry['folder']+'/'+p:h for p,h in files.items()})
        self.save()

    def check_source(self):
        if sha((self.source/'assets.json').read_bytes())!=self.state['source_catalog_sha256']: raise ValueError('Source catalog changed; create a new project')
        for relative,digest in self.state['baseline'].items():
            if sha(safe(self.source,relative).read_bytes())!=digest: raise ValueError('Source changed: '+relative)

    def review(self):
        self.check_source()
        current=inventory(self.edit/'assets');current={'assets/'+p:h for p,h in current.items()}
        result=[dict(target=p,source_sha256=self.state['baseline'].get(p),sha256=current.get(p)) for p in sorted(current.keys() | self.state['baseline'].keys()) if current.get(p)!=self.state['baseline'].get(p)]
        if self.state.get('native_body_sha256'):
            digest=sha(safe(self.edit,'native-roster-body.dat').read_bytes())
            if digest!=self.state['native_body_sha256']:result.append(dict(target='native-roster-body.dat',source_sha256=self.state['native_body_sha256'],sha256=digest))
        return result

    def workspace(self, assets=None, progress=None):
        workspace=Workspace(self.edit/'assets',progress)
        if self.state.get('native_body_sha256'):
            from types import SimpleNamespace
            path=safe(self.edit,'native-roster-body.dat')
            resource=SimpleNamespace(kind='ROST',key='native-roster',workspace=workspace,blocks=lambda:[path.read_bytes()],component_path=lambda index=0:path)
            workspace.resources=[r for r in workspace.resources if r.kind!='ROST']+[resource]
        return workspace

    def attach_roster(self, payload, header):
        # Validate staged bytes before replacing an earlier project attachment.
        if Path(payload).stat().st_size>64*1024*1024 or Path(header).stat().st_size!=328:raise ValueError('Native roster/header exceeds supported bounds')
        data=Path(payload).read_bytes();head=Path(header).read_bytes()
        with tempfile.TemporaryDirectory(prefix='.roster-',dir=self.root) as temp:
            staged=Path(temp)/'Roster.ROS';staged.write_bytes(data);h=Path(temp)/'Roster.ROS.header';h.write_bytes(head)
            self.contract.native('validate-roster',staged,h)
        body=data[4:]
        from .roster import Roster
        Roster(body)
        changes={safe(self.package_root,'rosters/Roster.ROS'):data,safe(self.package_root,'rosters/Roster.ROS.header'):head,safe(self.edit,'native-roster-body.dat'):body}
        state=copy.deepcopy(self.state);state['manifest']['roster']=dict(file='rosters/Roster.ROS',sha256=sha(data),header='rosters/Roster.ROS.header',header_sha256=sha(head));state['native_body_sha256']=sha(body)
        self._commit_attachment(changes,state)

    def attach_extension(self, payload, hook='player.weight.read'):
        registry=read_json(DATA/'chmod_hooks.json')
        specs=[h for h in registry['package_hooks'] if h['id']==hook]
        if len(specs)!=1: raise ValueError('Hook is unsupported; scorebug/menu/Legacy APIs are not exposed')
        if Path(payload).stat().st_size>64*1024*1024:raise ValueError('DLL exceeds 64 MiB')
        data=Path(payload).read_bytes()
        with tempfile.TemporaryDirectory(prefix='.dll-',dir=self.root) as temp:
            staged=Path(temp)/'extension.dll';staged.write_bytes(data);self.contract.dll(staged)
        relative='code/extension.dll';state=copy.deepcopy(self.state);state['manifest']['extensions']=[dict(file=relative,sha256=sha(data),abi=specs[0]['abi'],hook=hook)]
        self._commit_attachment({safe(self.package_root,relative):data},state)

    def _commit_attachment(self, changes, state):
        before={path:path.read_bytes() if path.exists() else None for path in changes};old=self.state
        try:
            for path,data in changes.items():path.parent.mkdir(parents=True,exist_ok=True);atomic_write(path,data,sha(before[path]) if before[path] is not None else None)
            self.state=state;self.save()
        except BaseException:
            self.state=old
            for path,data in before.items():
                if data is None:path.unlink(missing_ok=True)
                else:atomic_write(path,data)
            raise

    def attach_uniform(self, folder, template_hash):
        folder=Path(folder);name=folder.name
        if not re.fullmatch(r'(sel)?u[haxyz][0-9]{3,4}\.iff',name): raise ValueError('Unsupported uniform bank name')
        catalog=read_json(self.source/'assets.json',32*1024*1024);templates=[e for e in catalog['entries'] if e['hash']==template_hash]
        if len(templates)!=1: raise ValueError('Ambiguous template hash')
        digest=sha(safe(self.source,templates[0]['folder']+'/asset.json').read_bytes())
        relative='uniforms/'+name;target=safe(self.package_root,relative)
        if target.exists(): raise ValueError('Uniform already attached')
        files=inventory(folder)
        with tempfile.TemporaryDirectory(prefix='.uniform-',dir=self.root) as temp:
            stage=Path(temp)/name;shutil.copytree(folder,stage)
            if inventory(stage)!=files:raise ValueError('Uniform changed while attaching')
            self.contract.native('validate-uniform',self.source,stage,template_hash,name,digest)
            target.parent.mkdir(parents=True,exist_ok=True);os.rename(stage,target)
        old=copy.deepcopy(self.state)
        try:
            self.state['manifest'].setdefault('uniforms',[]).append(dict(name=name,template_hash=template_hash,template_layout_sha256=digest,folder=relative,files=[dict(path=p,sha256=h) for p,h in sorted(files.items())]))
            self.save()
        except BaseException:
            self.state=old
            if target.resolve().is_relative_to(self.package_root.resolve()):shutil.rmtree(target)
            raise

    def build(self, destination):
        """Materialize only changed, natively supported payloads into a fresh stage."""
        from jsonschema import Draft202012Validator
        changes=self.review();workspace=Workspace(self.edit/'assets');m=copy.deepcopy(self.state['manifest']);m['assets']=[]
        added={r.entry['folder'] for r in workspace.resources if r.entry.get('added')}
        # Existing uniform editor creates source-bound bank pairs. Validate and
        # package those exact inventories, linked by the edited native roster.
        for folder in sorted(added):
            layout=read_json(safe(self.edit,folder+'/asset.json'));template=layout.get('identity',{}).get('template_hash')
            catalog=read_json(self.source/'assets.json',32*1024*1024);entries=[e for e in catalog['entries'] if e['hash']==template]
            if len(entries)!=1:raise ValueError('New bank has no verified source template')
            name=Path(folder).name;digest=sha(safe(self.source,entries[0]['folder']+'/asset.json').read_bytes())
            self.contract.native('validate-uniform',self.source,safe(self.edit,folder),template,name,digest)
            if any(u['name']==name for u in m.get('uniforms',[])):raise ValueError('Duplicate attached and edited uniform bank')
            files=inventory(safe(self.edit,folder));relative='uniforms/'+name
            for path in files:
                target=safe(destination,relative+'/'+path);target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(safe(self.edit,folder+'/'+path),target)
            m.setdefault('uniforms',[]).append(dict(name=name,template_hash=template,template_layout_sha256=digest,folder=relative,files=[dict(path=p,sha256=h) for p,h in sorted(files.items())],_edited=True))
        targets={}
        for r in workspace.resources:
            prefix=r.entry['folder']+'/'+r.record['folder']
            if r.kind=='TXTR': targets[prefix+'/texture.dds']=(r,'dds.replace')
            elif r.kind=='SCNE' and len(r.components)==1:
                path=r.component_path().relative_to(self.edit).as_posix()
                if path in targets: raise ValueError('Ambiguous component owner')
                targets[path]=(r,'cloth.positions')
        for change in changes:
            path=change['target']
            if path=='native-roster-body.dat' or any(path.startswith(folder+'/') for folder in added):continue
            if path not in targets or not change['source_sha256'] or not change['sha256']: raise ValueError('Unsupported changed file (not silently omitted): '+path)
            r,kind=targets[path];data=safe(self.edit,path).read_bytes()
            if kind=='dds.replace':
                from . import dds
                old=dds.info(safe(self.source,path).read_bytes());new=dds.info(data);scale=new['width']//old['width']
                if new['fourcc']!=old['fourcc'] or new['width']%old['width'] or not scale or scale&(scale-1) or new['width']*old['height']!=new['height']*old['width']: raise ValueError('Unsupported DDS format/aspect/scale')
                dds.image(data)
            else:self.contract.native('validate-cloth',safe(self.source,path),safe(self.edit,path))
            target=safe(destination,path);target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(data)
            a=dict(bank_hash=r.entry['hash'],record_index=r.record['index'],record_id=r.record['id'],record_type=r.record['type'],target=path,source_sha256=change['source_sha256'],file=path,sha256=sha(data),kind=kind)
            if kind=='cloth.positions':a['component']=0
            m['assets'].append(a)
        for key in ('roster','extensions','uniforms'):
            items=([m[key]] if key=='roster' else m.get(key,[])) if key in m else []
            for item in items:
                if item.pop('_edited',False):continue
                files=([(item['file'],item['sha256']),(item['header'],item['header_sha256'])] if key=='roster' else [(item['file'],item['sha256'])] if key=='extensions' else [(item['folder']+'/'+f['path'],f['sha256']) for f in item['files']])
                for relative,digest in files:
                    source=safe(self.package_root,relative);data=source.read_bytes()
                    if sha(data)!=digest: raise ValueError('Attachment changed; attach again: '+relative)
                    target=safe(destination,relative);target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(data)
        if self.state.get('native_body_sha256'):
            body=safe(self.edit,'native-roster-body.dat').read_bytes()
            from .roster import Roster
            Roster(body)
            payload=struct.pack('>I',len(body))+body;r=m['roster'];target=safe(destination,r['file']);target.write_bytes(payload);r['sha256']=sha(payload)
            self.contract.native('validate-roster',target,safe(destination,r['header']))
        m['content']=[];m['capabilities']=sorted({a['kind'] for a in m['assets']})
        if m['assets'] or m.get('uniforms'):m['content'].append('assets')
        if m.get('roster'):m['content'].append('rosters');m['capabilities'].append('roster.expose')
        if m.get('uniforms'):m['capabilities'].append('uniform.register')
        if m.get('extensions'):m['content'].append('code');m['capabilities'].append('hook.player.weight.read')
        Draft202012Validator(read_json(DATA/'chmod.schema.json')).validate(m)
        write_json(destination/'mod.json',m)
        return m

    def export(self, output, dependencies=None):
        output=Path(output).resolve()
        if output.suffix.lower()!='.chmod' or output.exists(): raise ValueError('Choose a new .chmod destination')
        if output.is_relative_to(self.source) or output.is_relative_to(self.root): raise ValueError('Export outside the source and author project')
        output.parent.mkdir(parents=True,exist_ok=True)
        with tempfile.TemporaryDirectory(prefix='.chmod-',dir=output.parent) as temp:
            stage=Path(temp)/'stage';stage.mkdir();m=self.build(stage)
            self.contract.package(stage,self.source,dependencies)
            archive=Path(temp)/'export.chmod'
            with zipfile.ZipFile(archive,'w',zipfile.ZIP_STORED) as z:
                for path in sorted(stage.rglob('*')):
                    if path.is_file():z.write(path,path.relative_to(stage).as_posix())
            if archive.stat().st_size>LIMIT: raise ValueError('Package exceeds 512 MiB')
            validate_archive(archive)
            reopened=Path(temp)/'reopened';reopened.mkdir()
            with zipfile.ZipFile(archive) as z:z.extractall(reopened)
            self.contract.package(reopened,self.source,dependencies)
            self.check_source()
            # Atomic, no-clobber publication on Windows; never alters enabled state.
            if output.exists(): raise ValueError('Destination appeared during export')
            os.rename(archive,output)
        return m


def validate_archive(path):
    """Bound archive reads before handing a materialized package to the runtime."""
    with Path(path).open('rb') as stream:
        if os.fstat(stream.fileno()).st_size>LIMIT: raise ValueError('Package limit exceeded')
        with zipfile.ZipFile(stream) as archive:
            return _validate_archive_entries(archive, Path(path).parent)


def _validate_archive_entries(z, parent):
    from jsonschema import Draft202012Validator

    entries=z.infolist();seen=set();total=0
    if len(entries)>8192: raise ValueError('Package limit exceeded')
    for entry in entries:
        if entry.compress_type not in (zipfile.ZIP_STORED, zipfile.ZIP_DEFLATED):
            raise ValueError('Unsupported ZIP compression method')
        name=entry.filename;safe(parent,name)
        if name.casefold() in seen: raise ValueError('Duplicate/case-colliding ZIP entry')
        seen.add(name.casefold());total+=entry.file_size
        mode=(entry.external_attr>>16)&0o170000
        if mode not in (0,0o100000) or entry.external_attr & 0x400 or entry.file_size>128*1024*1024 or total>LIMIT or entry.file_size>1024*1024 and entry.file_size>200*max(1,entry.compress_size): raise ValueError('Unsafe ZIP entry/size')
    if 'mod.json' not in z.namelist() or z.getinfo('mod.json').file_size>1024*1024:raise ValueError('Missing/oversize mod.json')
    m=parse_json(z.read('mod.json'))
    Draft202012Validator(read_json(DATA/'chmod.schema.json')).validate(m)
    declared={'mod.json':None}
    for a in m['assets']:declared[a['file']]=a['sha256']
    if m.get('roster'):
        r=m['roster'];declared[r['file']]=r['sha256'];declared[r['header']]=r['header_sha256']
    for e in m.get('extensions',[]):declared[e['file']]=e['sha256']
    for u in m.get('uniforms',[]):
        for f in u['files']:declared[u['folder']+'/'+f['path']]=f['sha256']
    if set(z.namelist())!=set(declared):raise ValueError('Missing or undeclared ZIP payload')
    for name,digest in declared.items():
        if digest and sha(z.read(name))!=digest:raise ValueError('Payload hash mismatch: '+name)
    return m
