"""Build the desktop editor; no game launch or asset packaging."""
import shutil,subprocess,sys
from pathlib import Path

def main():
    root=Path(__file__).resolve().parents[1];output=root/'output/package'
    subprocess.run([sys.executable,'-m','PyInstaller','--noconfirm','--windowed','--name','CHoops-Recomp-Studio','--distpath',str(output),'--workpath',str(root/'output/pyinstaller-work'),'--specpath',str(root/'output'),'--paths',str(root),'--add-data',str(root/'choops_recomp/data')+';choops_recomp/data','--hidden-import','choops_recomp.ui.scene_view',str(root/'run_studio.py')],cwd=root,check=True)
    package=output/'CHoops-Recomp-Studio';decoder=root/'output/tools/vgmstream'
    if not (decoder/'COPYING').is_file():raise ValueError('Install the pinned decoder with tools/setup_audio.py before packaging')
    shutil.copytree(decoder,package/'tools/vgmstream',dirs_exist_ok=True)
    shutil.copytree(root/'docs',package/'docs',dirs_exist_ok=True)
    shutil.copy2(root/'README.md',package/'README.md');print(package)
if __name__=='__main__':main()
