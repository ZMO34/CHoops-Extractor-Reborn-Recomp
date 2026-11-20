"""Read-only import/export consistency audit for packaged Windows dependencies."""
import argparse,hashlib,json,re,subprocess
from pathlib import Path

def main():
    p=argparse.ArgumentParser();p.add_argument('root',type=Path);p.add_argument('--llvm',default='C:/Program Files/LLVM/bin/llvm-readobj.exe');p.add_argument('--output',required=True);a=p.parse_args();files={};exports={};issues=[]
    for path in a.root.rglob('*'):
        if path.suffix.casefold() in ('.dll','.pyd'):files.setdefault(path.name.casefold(),[]).append(path)
    for name,paths in files.items():
        if len({hashlib.sha256(path.read_bytes()).hexdigest() for path in paths})>1:issues.append(dict(duplicate=name,paths=list(map(str,paths))))
    def inspect(path,flag):return subprocess.check_output([a.llvm,flag,str(path)],text=True,errors='replace')
    for name,paths in files.items():
        for path in paths:
            for block in inspect(path,'--coff-imports').split('Import {')[1:]:
                match=re.search(r'Name: (\S+)',block)
                if not match or match[1].casefold() not in files:continue
                dependency=files[match[1].casefold()][0]
                if dependency not in exports:exports[dependency]=set(re.findall(r'^  Name: (.+)$',inspect(dependency,'--coff-exports'),re.M))
                missing=[symbol for symbol in re.findall(r'^  Symbol: (.+) \(\d+\)$',block,re.M) if symbol and symbol not in exports[dependency]]
                if missing:issues.append(dict(file=str(path),dependency=str(dependency),missing=missing))
    Path(a.output).write_text(json.dumps(issues,indent=2));print(json.dumps(issues,indent=2))
if __name__=='__main__':main()
