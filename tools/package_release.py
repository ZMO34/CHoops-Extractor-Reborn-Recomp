"""Package the already-verified Windows onedir editor, never game assets."""
import hashlib,json,subprocess,zipfile
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from choops_recomp import __version__
from build_windows import collect_licenses


def main():
    root=Path(__file__).resolve().parents[1];package=root/'output/package/CHoops-Recomp-Studio';output=root/'output/releases';output.mkdir(exist_ok=True)
    if not (package/'CHoops-Recomp-Studio.exe').is_file():raise ValueError('Build the Windows editor first')
    collect_licenses(package)
    revision=subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip()
    (package/'release.json').write_text(json.dumps(dict(version=__version__,commit=revision,platform='windows-x64',contains_game_assets=False),indent=2)+'\n',encoding='utf-8')
    files=sorted(p for p in package.rglob('*') if p.is_file())
    forbidden={'.xex','.iso','.iff','.stored','.xma','.pdb'}
    for path in files:
        if path.is_symlink() or path.suffix.lower() in forbidden or 'assets' in path.relative_to(package).parts:raise ValueError('Unexpected game/debug content in release: '+str(path))
    archive=output/f'CHoops-Recomp-Studio-v{__version__}-windows-x64.zip'
    with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as zipped:
        for path in files:zipped.write(path,path.relative_to(package.parent))
    digest=hashlib.sha256(archive.read_bytes()).hexdigest();checksum=archive.with_suffix('.zip.sha256');checksum.write_text(digest+'  '+archive.name+'\n',encoding='ascii')
    with zipfile.ZipFile(archive) as zipped:
        if zipped.testzip() is not None:raise ValueError('Release ZIP integrity check failed')
    print(json.dumps(dict(archive=str(archive),bytes=archive.stat().st_size,sha256=digest,files=len(files),commit=revision),indent=2))


if __name__=='__main__':main()
