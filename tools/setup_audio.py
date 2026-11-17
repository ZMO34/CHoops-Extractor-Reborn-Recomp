"""Install the pinned open-source Windows XMA decoder into ignored output/."""
import hashlib,io,os,shutil,tempfile,urllib.request,zipfile
from pathlib import Path

URL='https://github.com/vgmstream/vgmstream/releases/download/r2168/vgmstream-win64.zip'
SHA256='692d45070852a35c1fa42726aa3c9de528e44eec925d37d99b1074256b99a229'

def main():
    root=Path(__file__).resolve().parents[1];target=root/'output/tools/vgmstream'
    if target.exists():raise SystemExit('Decoder directory already exists; preserve or move it before installing again.')
    with urllib.request.urlopen(URL,timeout=60) as response:payload=response.read(64*1024*1024+1)
    if hashlib.sha256(payload).hexdigest()!=SHA256:raise ValueError('Pinned decoder checksum mismatch')
    target.parent.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='.decoder-',dir=target.parent) as temporary:
        temporary=Path(temporary)
        with zipfile.ZipFile(io.BytesIO(payload)) as archive:
            for entry in archive.infolist():
                out=(temporary/entry.filename).resolve()
                if not out.is_relative_to(temporary.resolve()):raise ValueError('Decoder archive path escapes destination')
            archive.extractall(temporary)
        if not (temporary/'vgmstream-cli.exe').is_file() or not (temporary/'COPYING').is_file():raise ValueError('Incomplete decoder distribution')
        shutil.copytree(temporary,target)
    print('Installed vgmstream r2168 with its complete dependency and license files.')
if __name__=='__main__':main()
