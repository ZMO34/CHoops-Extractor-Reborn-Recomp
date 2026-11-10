"""Build the desktop editor; no game launch or asset packaging."""
import shutil,subprocess,sys
import argparse
import os
from pathlib import Path
from importlib import metadata


def collect_licenses(package):
    destination=package/'licenses';destination.mkdir(exist_ok=True)
    for name in ('PySide6','PySide6-Essentials','PySide6-Addons','shiboken6','Pillow','PyInstaller','jsonschema','jsonschema-specifications','referencing','rpds-py','attrs'):
        distribution=metadata.distribution(name)
        for entry in distribution.files or []:
            if 'licenses' not in entry.parts:continue
            source=Path(distribution.locate_file(entry))
            if not source.is_file():continue
            relative=Path(*entry.parts[entry.parts.index('licenses')+1:]);target=destination/name/relative;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(source,target)
    python_license=Path(sys.base_prefix)/'LICENSE.txt'
    if python_license.is_file():shutil.copy2(python_license,destination/'Python-LICENSE.txt')

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--console',action='store_true');parser.add_argument('--output',type=Path,help='Separate package directory, e.g. while an existing editor is open');args=parser.parse_args()
    root=Path(__file__).resolve().parents[1];output=args.output.resolve() if args.output else root/'output/package'
    # Qt uses the Windows ICU API. Unrelated Poppler environments can put an
    # incompatible same-name ICU DLL on PATH; keep those out of dependency scan.
    environment=dict(os.environ);environment['PATH']=os.pathsep.join(p for p in environment.get('PATH','').split(os.pathsep) if 'poppler' not in p.casefold())
    subprocess.run([sys.executable,'-m','PyInstaller','--clean','--noconfirm','--console' if args.console else '--windowed','--name','CHoops-Recomp-Studio','--distpath',str(output),'--workpath',str(root/'output/pyinstaller-work'),'--specpath',str(root/'output'),'--paths',str(root),'--add-data',str(root/'choops_recomp/data')+';choops_recomp/data','--hidden-import','choops_recomp.ui.scene_view',str(root/'run_studio.py')],cwd=root,env=environment,check=True)
    package=output/'CHoops-Recomp-Studio';decoder=root/'output/tools/vgmstream'
    if not (decoder/'COPYING').is_file():raise ValueError('Install the pinned decoder with tools/setup_audio.py before packaging')
    shutil.copytree(decoder,package/'tools/vgmstream',dirs_exist_ok=True)
    shutil.copytree(root/'docs',package/'docs',dirs_exist_ok=True)
    shutil.copytree(root/'sdk',package/'sdk',dirs_exist_ok=True)
    shutil.copy2(root/'README.md',package/'README.md');collect_licenses(package);print(package)
if __name__=='__main__':main()
