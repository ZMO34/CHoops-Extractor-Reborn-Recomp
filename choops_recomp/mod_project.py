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

    def native(self, command, *args, timeout=120):
        result = subprocess.run([str(self.tool), command, *map(str, args)], capture_output=True, text=True, timeout=timeout, creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
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

    @classmethod
    def import_folders(cls, destination, assets, runtime, folders, *,
                       identity=None, groups=None):
        """Create a working project from one or more installed mod packages."""
        from jsonschema import Draft202012Validator

        folders = [Path(folder).absolute() for folder in folders]
        if not folders:
            raise ValueError('Select at least one mod folder')
        manifests = [read_json(safe(folder, 'mod.json')) for folder in folders]
        validator = Draft202012Validator(read_json(DATA/'chmod.schema.json'))
        for manifest in manifests:
            validator.validate(manifest)
        primary = manifests[0]
        destination = Path(destination).resolve()
        source = Path(assets).resolve().parent
        if destination.exists() or destination.is_relative_to(source) or any(
            destination.is_relative_to(folder.resolve()) for folder in folders
        ):
            raise ValueError('Choose a new project folder outside the game assets and input mods')
        if (len(folders) > 1 or groups is not None) and identity is None:
            raise ValueError('Choose a new mod ID for combined or separated projects')
        destination.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(prefix='.studio-import-', dir=destination.parent) as temp:
            project = cls.create(Path(temp)/'project', assets, runtime, *(identity or (
                primary['id'], primary['name'], primary['author'])))
            merged = copy.deepcopy(primary)
            if identity:
                merged.update(zip(('id', 'name', 'author'), identity))
                merged['version'] = '1.0.0'
                merged.pop('update_source', None)
            merged['assets'] = []
            for key in ('roster', 'uniforms', 'extensions'):
                merged.pop(key, None)
            seen = set()
            uniform_names = set()
            stock_catalog = read_json(project.source/'assets.json', 32*1024*1024)
            stock_entries = {e['hash']: e for e in stock_catalog['entries']}
            used = {}
            editable_assets = []
            total = 0

            def checked_file(folder, relative, digest):
                nonlocal total
                path = safe(folder, relative)
                size = path.stat().st_size
                total += size
                if size > 128 * 1024 * 1024 or total > LIMIT:
                    raise ValueError('Selected mod payload exceeds the supported size')
                data = path.read_bytes()
                if sha(data) != digest:
                    raise ValueError('Mod payload digest differs for ' + relative)
                return data

            def attach(relative, data):
                key = relative.casefold()
                if key in used:
                    raise ValueError('Packages use the same payload path: ' + relative)
                used[key] = relative
                path = safe(project.package_root, relative)
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(data)

            for folder, manifest in zip(folders, manifests):
                if manifest['requires']['xex_sha256'] != primary['requires']['xex_sha256']:
                    raise ValueError('The mod folders target different game revisions')
                if manifest['requires']['recomp'] != primary['requires']['recomp']:
                    raise ValueError('The mod folders target different recomp branches')
                for asset in manifest['assets']:
                    group = Path(asset['target']).parts[1]
                    if groups is not None and group not in groups:
                        continue
                    key = (asset['bank_hash'], asset['record_index'], asset.get('texture_slot'),
                           asset.get('component'))
                    if key in seen:
                        raise ValueError('Texture or component conflict: ' + asset['target'])
                    seen.add(key)
                    data = checked_file(folder, asset['file'], asset['sha256'])
                    entry = stock_entries.get(asset['bank_hash'])
                    if entry is None:
                        raise ValueError('The installed catalog lacks ' + group)
                    if asset.get('kind', 'dds.replace') in ('dds.replace', 'cloth.positions', 'court.scene') and asset['target'].startswith(entry['folder']+'/'):
                        pristine = safe(project.source, asset['target'])
                        if pristine.is_file() and sha(pristine.read_bytes()) == asset['source_sha256']:
                            bank_name = Path(entry['folder']).name
                            if bank_name not in project.state['banks']:
                                project.add_bank(bank_name)
                            safe(project.edit, asset['target']).write_bytes(data)
                            editable_assets.append(asset['target'])
                    attach(asset['file'], data)
                    merged['assets'].append(dict(asset, kind=asset.get('kind', 'dds.replace')))
                if manifest.get('roster') and (groups is None or 'Roster' in groups):
                    if merged.get('roster'):
                        raise ValueError('A combined project can contain only one roster')
                    roster = manifest['roster']
                    for field in ('file', 'header'):
                        digest = roster['sha256' if field == 'file' else 'header_sha256']
                        checked_file(folder, roster[field], digest)
                    project.attach_roster(safe(folder, roster['file']), safe(folder, roster['header']))
                    merged['roster'] = project.state['manifest']['roster']
                for uniform in manifest.get('uniforms', []):
                    name = uniform['name']
                    group = name.removeprefix('sel')
                    if groups is not None and group not in groups:
                        continue
                    if name in uniform_names:
                        raise ValueError('Uniform bank conflict: ' + name)
                    uniform_names.add(name)
                    stage = project.edit/'assets'/name
                    if stage.exists():
                        raise ValueError('Loose asset conflicts with uniform bank ' + name)
                    for file in uniform['files']:
                        data = checked_file(folder, uniform['folder']+'/'+file['path'], file['sha256'])
                        target = safe(stage, file['path'])
                        target.parent.mkdir(parents=True, exist_ok=True)
                        target.write_bytes(data)
                    proof = project.contract.native('validate-uniform', project.source, stage,
                                                    uniform['template_hash'], name, uniform['template_layout_sha256'])
                    if proof.get('replacing'):
                        catalog = read_json(project.edit/'assets.json', 32*1024*1024)
                        catalog['entries'].append(stock_entries[proof['hash']])
                        write_json(project.edit/'assets.json', catalog)
                    merged.setdefault('uniforms', []).append(copy.deepcopy(uniform))
                for extension in manifest.get('extensions', []):
                    if groups is None or 'Code' in groups:
                        path = extension['file']
                        attach(path, checked_file(folder, path, extension['sha256']))
                        merged.setdefault('extensions', []).append(copy.deepcopy(extension))
            if not any(merged.get(key) for key in ('assets', 'roster', 'uniforms', 'extensions')):
                raise ValueError('No mod content selected')
            deps = {}
            for manifest in manifests:
                for dep in manifest['dependencies']:
                    if dep['id'] in deps and deps[dep['id']] != dep:
                        raise ValueError('Conflicting dependency versions: ' + dep['id'])
                    deps[dep['id']] = dep
            merged['dependencies'] = list(deps.values())
            merged['incompatible'] = sorted({item for manifest in manifests for item in manifest['incompatible']})
            merged['requires']['mod_api'] = max(m['requires']['mod_api'] for m in manifests)
            project.state.update(manifest=merged, imported_assets=merged['assets'],
                                 imported_editable_assets=editable_assets, imported_uniforms=sorted(uniform_names),
                                 description=merged.get('description', ''))
            project.save()
            project.workspace()
            os.rename(project.root, destination)
        return cls(destination, runtime)

    @staticmethod
    def content_groups(manifest):
        groups = {Path(item['target']).parts[1] for item in manifest['assets']}
        groups.update(item['name'].removeprefix('sel') for item in manifest.get('uniforms', []))
        if manifest.get('roster'):
            groups.add('Roster')
        if manifest.get('extensions'):
            groups.add('Code')
        return sorted(groups)

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
        if not layout.get('blocks') and not layout.get('paired_resources'):
            raise ValueError('Select a source-bound resource bank')
        if any(c['path'] and c['folder']!=entry['folder']
               for record in layout.get('paired_resources',[]) for c in record['component_files']):
            raise ValueError('This paired bank still stores components outside its named folder')
        files=inventory(source)
        with tempfile.TemporaryDirectory(prefix='.bank-',dir=self.root) as temp:
            stage=Path(temp)/bank;shutil.copytree(source,stage)
            if inventory(stage)!=files or inventory(source)!=files: raise ValueError('Source changed during project copy')
            os.rename(stage,safe(self.edit,entry['folder']))
        edit_catalog=read_json(self.edit/'assets.json');edit_catalog['entries'].append(entry);write_json(self.edit/'assets.json',edit_catalog)
        source_textures=self.source/'scene_textures.json'
        if source_textures.is_file():
            catalog=read_json(source_textures,64*1024*1024)
            if catalog.get('version')!=1:raise ValueError('Unsupported named texture catalog')
            marker=self.edit/'scene_textures.json'
            current=read_json(marker,64*1024*1024) if marker.exists() else dict(version=1,scenes=[],unsupported=[])
            for owner in catalog['scenes']:
                if owner['bank']!=entry['hash']:continue
                textures=[item for item in owner['textures'] if item['file'].startswith(entry['folder']+'/')]
                if textures:current['scenes'].append(dict(owner,textures=textures))
            write_json(marker,current)
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
        data = Path(payload).read_bytes()
        source_header = Path(header).read_bytes()
        # The verified aggregate owner field is the only profile-specific field
        # we clear. The native validator checks the remaining save contract.
        owner_offset = 312 if source_header[320:324] == bytes.fromhex('54540818') else 308
        head = source_header[:owner_offset] + bytes(8) + source_header[owner_offset + 8:]
        with tempfile.TemporaryDirectory(prefix='.roster-',dir=self.root) as temp:
            staged=Path(temp)/'Roster.ROS';staged.write_bytes(data);h=Path(temp)/'Roster.ROS.header';h.write_bytes(head)
            self.contract.native('validate-roster',staged,h)
        body=data[4:]
        from .roster import Roster
        Roster(body)
        changes={safe(self.package_root,'rosters/Roster.ROS'):data,safe(self.package_root,'rosters/Roster.ROS.header'):head,safe(self.edit,'native-roster-body.dat'):body}
        state=copy.deepcopy(self.state);state['manifest']['roster']=dict(file='rosters/Roster.ROS',sha256=sha(data),header='rosters/Roster.ROS.header',header_sha256=sha(head));state['native_body_sha256']=sha(body)
        self._commit_attachment(changes,state)

    def export_roster_save(self, output):
        """Publish the validated ROS/header pair into one fresh directory."""
        output = Path(output).resolve()
        if output.exists() or output.is_relative_to(self.root) or output.is_relative_to(self.source):
            raise ValueError('Choose a new roster export folder outside the project and source')
        roster = self.state['manifest'].get('roster')
        if not roster:
            raise ValueError('Attach a native roster and its original header first')
        from .roster import Roster

        body = safe(self.edit, 'native-roster-body.dat').read_bytes()
        Roster(body)
        header = safe(self.package_root, roster['header']).read_bytes()
        if sha(header) != roster['header_sha256']:
            raise ValueError('The attached roster header changed')
        output.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(prefix='.roster-export-', dir=output.parent) as temp:
            stage = Path(temp) / 'roster'
            stage.mkdir()
            save_file = stage / 'Roster.ROS'
            header_file = stage / 'Roster.ROS.header'
            save_file.write_bytes(struct.pack('>I', len(body)) + body)
            header_file.write_bytes(header)
            self.contract.native('validate-roster', save_file, header_file)
            os.rename(stage, output)
        return output

    def attach_extension(self, payload, hook='player.weight.read', abi=1, capabilities=None, replacements=None):
        registry=read_json(DATA/'chmod_hooks.json')
        specs=[h for h in registry['package_hooks'] if h['id']==hook]
        if abi==1:
            if len(specs)!=1 or hook!='player.weight.read': raise ValueError('ABI 1 supports only the legacy weight-read contract')
        elif abi==2:
            capabilities=list(capabilities or []);replacements=list(replacements or [])
            if not capabilities or len(capabilities)!=len(set(capabilities)) or any(c not in registry['capabilities'] for c in capabilities):raise ValueError('Choose supported, unique ABI 2 capabilities from sdk/hooks.json')
            replaceable={h['id'] for h in registry['package_hooks'] if 'replace' in h['operations']}
            if len(replacements)!=len(set(replacements)) or any(r not in replaceable or 'hook.'+r not in capabilities for r in replacements):raise ValueError('Replacement claim requires a supported hook capability')
        else:raise ValueError('Supported native extension ABIs are 1 and 2')
        if Path(payload).stat().st_size>64*1024*1024:raise ValueError('DLL exceeds 64 MiB')
        data=Path(payload).read_bytes()
        with tempfile.TemporaryDirectory(prefix='.dll-',dir=self.root) as temp:
            staged=Path(temp)/'extension.dll';staged.write_bytes(data);self.contract.dll(staged)
        relative='code/extension.dll';state=copy.deepcopy(self.state)
        entry=dict(file=relative,sha256=sha(data),abi=abi)
        if abi==1:entry['hook']=hook
        else:
            entry.update(capabilities=sorted(capabilities),replacements=sorted(replacements))
            state['manifest']['requires']['mod_api']='1.3.0'
        state['manifest']['extensions']=[entry]
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

    def stage_full_court(self, court, artwork):
        """Convert one full-court DDS into the project's private floor components."""
        if not re.fullmatch(r's[0-9]{3}', court):
            raise ValueError('Choose a court ID such as s272')
        artwork = Path(artwork)
        if artwork.suffix.casefold() != '.dds' or artwork.stat().st_size > 4 * 1024 * 1024:
            raise ValueError('Choose a 2048×1024 BC1 DDS with all mip levels')
        self.check_source()
        with tempfile.TemporaryDirectory(prefix='.full-court-', dir=self.root) as tmp:
            stage = Path(tmp)
            image = stage / court / 'floor.dds'
            image.parent.mkdir()
            shutil.copyfile(artwork, image)
            self.contract.native('build-full-floor', self.source, image, stage / 'mods')
            folder = stage / 'mods' / f'full-floor.{court}-1.0.0'
            self.add_bank(court + '.iff')
            manifest = read_json(folder / 'mod.json')
            state = copy.deepcopy(self.state)
            state['manifest']['requires']['mod_api'] = '1.3.0'
            changes = {safe(self.edit, entry['target']): safe(folder, entry['file']).read_bytes()
                       for entry in manifest['assets']}
            self._commit_attachment(changes, state)
        return court

    def create_alternate(self, team, variant, jersey, shorts, selection=None, *,
                         numbers=None, selection_numbers=None, lettering=None, logo=None, generate_bumps=True, neck_shape=None):
        """Create an alternate from the team's Home art."""
        if variant not in (2, 3, 4):
            raise ValueError('Choose X, Y or Z')
        return self.stage_uniform(team, variant, jersey, shorts, selection, numbers=numbers,
                                  selection_numbers=selection_numbers, lettering=lettering, logo=logo,
                                  generate_bumps=generate_bumps, neck_shape=neck_shape, replace_existing=False)

    def stage_uniform(self, team, variant, jersey, shorts, selection=None, *,
                      numbers=None, selection_numbers=None, lettering=None, logo=None,
                      generate_bumps=True, neck_shape=None, replace_existing=True):
        """Replace a routed uniform pair or create a vacant alternate from Home."""
        from . import dds, uniform_fonts, uniforms
        from .edits import artwork_payload
        from .roster import Roster
        import zlib

        if variant not in range(5):
            raise ValueError('Choose Home, Away, X, Y or Z')
        if neck_shape is not None and (type(neck_shape) is not int or not 0 <= neck_shape < 5):
            raise ValueError('Choose a supported Xbox neckline')
        self.check_source()
        stock = Workspace(self.source / 'assets')
        roster, = (resource for resource in stock.of_type('ROST') if resource.bank == 'roster_english.iff')
        model = Roster(roster.blocks()[0])
        owner = uniforms.owner(model, team)
        if uniforms.owners(model, owner) != [team]:
            raise ValueError('This team shares uniform routing. Use a source-bound native roster for independent routing.')
        rows = uniforms.rows(model)
        routed = [row for row in rows if row['owner'] == owner and row['variant'] == variant]
        replacing = bool(routed)
        if replacing and not replace_existing:
            raise ValueError('The alternate slot already exists. Use uniform to replace its artwork.')
        if replacing and not any((jersey, shorts, selection, numbers, selection_numbers, lettering, logo)):
            raise ValueError('Supply at least one artwork file for the replacement')
        if not replacing and (not jersey or not shorts):
            raise ValueError('New alternates require both world jersey and shorts artwork')
        if not replacing and variant < 2:
            raise ValueError('This team has no routed stock uniform for that slot')
        templates = routed or [row for row in rows if row['owner'] == owner and row['variant'] == 0]
        if len(templates) != 1:
            raise ValueError('This team has no unique uniform template')
        template, = templates
        asset = template['asset']
        matching_variants = (variant,) if replacing else (0, 1)
        owners = {row['owner'] for row in rows if row['asset'] == asset and row['variant'] in matching_variants
                  and uniforms.owners(model, row['owner'])}
        if owners != {owner}:
            raise ValueError('This artwork is shared across teams. Use independently routed artwork.')
        if replacing and neck_shape is not None:
            raise ValueError('Use the roster editor to change the neckline of an existing uniform')
        with tempfile.TemporaryDirectory(prefix='.uniform-', dir=self.root) as tmp:
            pair = uniforms.clone_pair(stock, template, asset, variant, Path(tmp), replace=replacing)
            if any(bank.name in self.state.get('imported_uniforms', []) for bank in pair):
                raise ValueError('Edit this imported uniform in the project texture browser')
            state = copy.deepcopy(self.state)
            changes = {}
            for bank, inputs in zip(pair, ((jersey, shorts), (selection or jersey,))):
                layout = read_json(bank / 'asset.json')
                identity = layout['identity']
                previous = next((entry for entry in state['manifest'].get('uniforms', [])
                                 if entry['name'] == bank.name), None)
                if replacing and previous:
                    # A later partial import keeps artwork already saved for this pair.
                    if previous['template_hash'] != identity['template_hash']:
                        raise ValueError('The existing project uniform uses a different template')
                    for file in previous['files']:
                        target = safe(bank, file['path'])
                        source = safe(self.package_root, previous['folder'] + '/' + file['path'])
                        data = source.read_bytes()
                        if sha(data) != file['sha256'] or not target.is_file():
                            raise ValueError('The existing project uniform inventory changed')
                        target.write_bytes(data)
                bound = {texture['record']: texture for texture in layout['textures']}
                is_selection = bank.name.startswith('sel')
                for names, bump, artwork in zip(
                    (('unifregion', 'unif'), ('shortregion', 'short')),
                    ('unifbump', 'shortbump'), inputs,
                ):
                    if artwork is None:
                        continue
                    for name in names:
                        matches = [r for r in layout['records']
                                   if r['id'] == zlib.crc32(name.encode()) and r['index'] in bound]
                        if matches:
                            break
                    if len(matches) > 1:
                        raise ValueError(f'Ambiguous {name} artwork in {bank.name}')
                    if not matches:
                        if bank.name.startswith('sel'):
                            continue
                        raise ValueError(f'Missing {name} artwork in {bank.name}')
                    target = bank / bound[matches[0]['index']]['path']
                    before = target.read_bytes()
                    payload = artwork_payload(artwork, before)
                    if is_selection and dds.info(payload)['fourcc'] != dds.info(before)['fourcc']:
                        payload = dds.encode_image(dds.image(payload), before)
                    dds.replace(target, payload, before)
                    if generate_bumps:
                        bump_slots = [bound[r['index']] for r in layout['records']
                                      if r['id'] == zlib.crc32(bump.encode()) and r['index'] in bound]
                        if len(bump_slots) != 1:
                            raise ValueError(f'Missing or ambiguous {bump} in {bank.name}')
                        normal = bank / bump_slots[0]['path']
                        baseline = normal.read_bytes()
                        from PIL import Image

                        if Path(artwork).suffix.casefold() == '.dds':
                            color = dds.image(payload)
                        else:
                            with Image.open(artwork) as opened:
                                color = opened.convert('RGBA')
                        dds.replace(normal, dds.normal_from_artwork(color, baseline), baseline)
                        material_name = names[-1]
                        material_slots = [bound[r['index']] for r in layout['records']
                                          if r['id'] == zlib.crc32(material_name.encode())
                                          and r['index'] in bound and r['index'] != matches[0]['index']]
                        if len(material_slots) > 1:
                            raise ValueError(f'Ambiguous {material_name} in {bank.name}')
                        if material_slots:
                            material = bank / material_slots[0]['path']
                            template = material.read_bytes()
                            if dds.info(template)['fourcc'] == 'ATI1':
                                result = dds.material_from_artwork(color, template)
                            elif is_selection:
                                result = payload if dds.info(payload)['fourcc'] == dds.info(template)['fourcc'] else dds.encode_image(color, template)
                            else:
                                raise ValueError(f'Unsupported {material_name} material format in {bank.name}')
                            dds.replace(material, result, template)
                if logo is not None and not is_selection:
                    slots = [bound[r['index']] for r in layout['records']
                             if r['id'] == zlib.crc32(b'logo') and r['index'] in bound]
                    if len(slots) != 1:
                        raise ValueError(f'Missing or ambiguous logo in {bank.name}')
                    target = bank / slots[0]['path']
                    baseline = target.read_bytes()
                    dds.replace(target, artwork_payload(logo, baseline), baseline)
                sheets = (('jersey_numbers', selection_numbers),) if is_selection else (
                    ('jersey_numbers', numbers), ('names', lettering))
                for label, artwork in sheets:
                    if artwork is None:
                        continue
                    records = [r for r in layout['records'] if
                               r['id'] == zlib.crc32(label.encode()) and r['type'] == 0x5c369069]
                    if len(records) != 1:
                        raise ValueError(f'Missing or ambiguous {label} in {bank.name}')
                    paths = [bank / c['path']
                             for block, offset in zip(layout['blocks'], records[0]['offsets'])
                             for c in block['components'] if c['start'] == offset]
                    cpu, gpu = paths
                    blocks = [cpu.read_bytes(), gpu.read_bytes()]
                    gpu.write_bytes(uniform_fonts.edited_pixels(blocks, artwork))
                name = bank.name
                relative = 'uniforms/' + name
                template_hash = identity['template_hash']
                source_entry, _ = stock.by_hash[template_hash]
                digest = sha(safe(self.source, source_entry['folder'] + '/asset.json').read_bytes())
                # Loose imports can carry preview DDS files in addition to the
                # native bank pieces and registered standalone DDS templates.
                allowed = {'asset.json'}
                packed = {block['path'] for block in layout['blocks']}
                allowed.update(piece['path'] for piece in layout['pieces'] if piece['path'] not in packed)
                allowed.update(part['path'] for block in layout['blocks'] for part in block['components'])
                allowed.update(record['folder'] + '/record.json' for record in layout['records'])
                allowed.update(texture['path'] for texture in layout['textures'])
                for file in inventory(bank).keys() - allowed:
                    safe(bank, file).unlink()
                self.contract.native('validate-uniform', self.source, bank, template_hash, name, digest)
                files = inventory(bank)
                entries = state['manifest'].setdefault('uniforms', [])
                previous = next((entry for entry in entries if entry['name'] == name), None)
                if previous:
                    if (previous['template_hash'] != template_hash or
                        {file['path'] for file in previous['files']} != set(files)):
                        raise ValueError('The existing project uniform uses a different template or inventory')
                    entries.remove(previous)
                entry = dict(name=name, template_hash=template_hash, template_layout_sha256=digest,
                             folder=relative, files=[dict(path=p, sha256=h) for p,h in sorted(files.items())])
                if neck_shape is not None and not is_selection:
                    entry['neck_shape'] = neck_shape
                entries.append(entry)
                for file in files:
                    changes[safe(self.package_root, relative + '/' + file)] = safe(bank, file).read_bytes()
            self._commit_attachment(changes, state)
        return [bank.name for bank in pair]

    def build(self, destination):
        """Materialize only changed, natively supported payloads into a fresh stage."""
        from jsonschema import Draft202012Validator
        changes=self.review();workspace=Workspace(self.edit/'assets');m=copy.deepcopy(self.state['manifest']);m['assets']=[]
        imported_uniforms = set(self.state.get('imported_uniforms', []))
        added={r.entry['folder'] for r in workspace.resources if r.entry.get('added')
               and r.bank not in imported_uniforms}
        editable = set(self.state.get('imported_editable_assets', []))
        modified = {change['target'] for change in changes if change['sha256']}
        imported = {item['target']: item for item in self.state.get('imported_assets', [])
                    if item['target'] not in editable or item['target'] in modified}
        for path, item in imported.items():
            data = safe(self.package_root, item['file']).read_bytes()
            if sha(data) != item['sha256']:
                raise ValueError('Imported payload changed: ' + path)
            target = safe(destination, item['file'])
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
            m['assets'].append(copy.deepcopy(item))
        for item in m.get('uniforms', []):
            if item['name'] not in imported_uniforms:
                continue
            bank = safe(self.edit, 'assets/'+item['name'])
            self.contract.native('validate-uniform', self.source, bank, item['template_hash'],
                                 item['name'], item['template_layout_sha256'])
            files = inventory(bank)
            for path in files:
                target = safe(destination, item['folder']+'/'+path)
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(safe(bank, path), target)
            item.update(files=[dict(path=p, sha256=h) for p,h in sorted(files.items())], _edited=True)
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
        changed_paths={row['target']:row for row in changes}
        court_paths=set()
        for r in workspace.of_type('SCNE'):
            if r.record['id']!=0xbe45d62e or len(r.components)!=2:
                continue
            paths=[r.component_path(i).relative_to(self.edit).as_posix() for i in range(2)]
            if not any(path in changed_paths for path in paths):continue
            if r.bank in imported_uniforms:
                continue
            original=[safe(self.source,path) for path in paths]
            edited=[safe(self.edit,path) for path in paths]
            self.contract.native('validate-court',*original,*edited)
            for index,(path,src,payload) in enumerate(zip(paths,original,edited)):
                existing = imported.get(path)
                target=safe(destination,existing['file'] if existing else path)
                target.parent.mkdir(parents=True,exist_ok=True)
                data=payload.read_bytes()
                target.write_bytes(data)
                if existing:
                    next(item for item in m['assets'] if item['target']==path)['sha256'] = sha(data)
                    continue
                m['assets'].append(dict(bank_hash=r.entry['hash'],record_index=r.record['index'],
                    record_id=r.record['id'],record_type=r.record['type'],kind='court.scene',
                    component=index,target=path,file=path,source_sha256=sha(src.read_bytes()),
                    sha256=sha(data)))
            court_paths.update(paths)
            m['requires']['mod_api']='1.3.0'
        resources={(r.entry['hash'],r.record['index']):r for r in workspace.resources}
        slots={}
        for (bank,index,slot), file in workspace.texture_catalog.items():
            path=file.relative_to(self.edit).as_posix()
            if path in slots:raise ValueError('Ambiguous named DDS owner: '+path)
            targets[path]=(resources[(bank,index)],'dds.replace')
            slots[path]=slot
        for change in changes:
            path=change['target']
            if path in court_paths or path=='native-roster-body.dat' or Path(path).parts[1] in imported_uniforms or any(path.startswith(folder+'/') for folder in added):continue
            if path not in targets or not change['source_sha256'] or not change['sha256']: raise ValueError('Unsupported changed file (not silently omitted): '+path)
            r,kind=targets[path];data=safe(self.edit,path).read_bytes()
            if kind=='dds.replace':
                from . import dds
                old=dds.info(safe(self.source,path).read_bytes());new=dds.info(data);scale=new['width']//old['width']
                if new['fourcc']!=old['fourcc'] or new['width']%old['width'] or not scale or scale&(scale-1) or new['width']*old['height']!=new['height']*old['width']: raise ValueError('Unsupported DDS format/aspect/scale')
                dds.image(data)
                if path in slots and (new['width']!=old['width'] or new['height']!=old['height'] or new['mips']!=1 or
                                      data[76:108]!=safe(self.source,path).read_bytes()[76:108]):
                    raise ValueError('Named DDS must retain dimensions, channel masks and a single base level')
            else:self.contract.native('validate-cloth',safe(self.source,path),safe(self.edit,path))
            imported_item = imported.get(path)
            target=safe(destination, imported_item['file'] if imported_item else path)
            target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(data)
            if imported_item:
                next(item for item in m['assets'] if item['target']==path)['sha256'] = sha(data)
                continue
            a=dict(bank_hash=r.entry['hash'],record_index=r.record['index'],record_id=r.record['id'],record_type=r.record['type'],target=path,source_sha256=change['source_sha256'],file=path,sha256=sha(data),kind=kind)
            if kind=='cloth.positions':a['component']=0
            if path in slots:a['texture_slot']=slots[path]
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
        if self.state.get('description'):
            m['description']=self.state['description']
        m['content']=[];m['capabilities']=sorted({a['kind'] for a in m['assets']})
        if m['assets'] or m.get('uniforms'):m['content'].append('assets')
        if m.get('roster'):m['content'].append('rosters');m['capabilities'].append('roster.expose')
        if m.get('uniforms'):m['capabilities'].append('uniform.register')
        if m.get('extensions'):
            m['content'].append('code')
            for extension in m['extensions']:
                m['capabilities'].extend(extension['capabilities'] if extension['abi']==2 else ['hook.player.weight.read'])
            m['capabilities']=sorted(set(m['capabilities']))
        Draft202012Validator(read_json(DATA/'chmod.schema.json')).validate(m)
        write_json(destination/'mod.json',m)
        return m

    def build_roster_mod(self, stage):
        from jsonschema import Draft202012Validator

        manifest = copy.deepcopy(self.state['manifest'])
        roster = manifest.get('roster')
        if roster is None:
            raise ValueError('Attach a native roster and its original header first')
        output = self.export_roster_save(stage / 'rosters')
        roster['sha256'] = sha((output / 'Roster.ROS').read_bytes())
        for key in ('uniforms', 'extensions'):
            manifest.pop(key, None)
        manifest.update(assets=[], content=['rosters'], capabilities=['roster.expose'])
        if self.state.get('description'):
            manifest['description'] = self.state['description']
        Draft202012Validator(read_json(DATA/'chmod.schema.json')).validate(manifest)
        write_json(stage/'mod.json', manifest)
        return manifest

    def export_folder(self, output, dependencies=None, *, roster_only=False):
        output=Path(output).resolve()
        if output.exists():raise ValueError('Choose a new mod folder')
        if output.is_relative_to(self.source) or output.is_relative_to(self.root):
            raise ValueError('Export outside the source and author project')
        output.parent.mkdir(parents=True,exist_ok=True)
        with tempfile.TemporaryDirectory(prefix='.mod-folder-',dir=output.parent) as temp:
            stage=Path(temp)/'mod'
            stage.mkdir()
            manifest=self.build_roster_mod(stage) if roster_only else self.build(stage)
            self.contract.package(stage,self.source,dependencies)
            self.check_source()
            if output.exists():raise ValueError('Destination appeared during export')
            os.rename(stage,output)
        return manifest

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
