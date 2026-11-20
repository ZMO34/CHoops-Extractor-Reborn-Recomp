"""Check real paired-resource extraction using a new private output directory."""
import argparse,json,shutil,struct,sys,zlib,hashlib
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'runtime'))
from choops_recomp import runtime_protocol
sys.modules['xbox_asset_edits']=runtime_protocol
from materialize_paired import materialize_pair
from direct_folder import DirectFolder
from choops_recomp.workspace import Workspace


def main():
    p=argparse.ArgumentParser();p.add_argument('--assets',type=Path,required=True);p.add_argument('--output',type=Path,required=True);args=p.parse_args()
    source=args.assets.resolve().parent;output=args.output.resolve();owned=Path(__file__).resolve().parents[1]/'output'
    if not output.is_relative_to(owned) or output.exists():raise ValueError('Choose a new private output directory under this checkout/output')
    manifest=json.loads((source/'assets.json').read_text());entries={e['hash']:e for e in manifest['entries']};pairs=[];selected={}
    for entry in entries.values():
        folder=source/entry['folder'];layout=json.loads((folder/'asset.json').read_text())
        if 'blocks' in layout or layout.get('loose_segments'):continue
        with (folder/'payload.dat').open('rb') as stream:prefix=stream.read(4)
        if prefix!=bytes.fromhex('f0985030'):continue
        head=(folder/'payload.dat').read_bytes();start=36+struct.unpack_from('>I',head,36)[0]-1;end=start
        while end+2<=len(head) and head[end:end+2]!=b'\0\0':end+=2
        if end+2>len(head):raise ValueError('Unterminated paired name')
        name=head[start:end].decode('utf-16-be');paired=entries[zlib.crc32(name.upper().encode())&0xffffffff]
        pairs.append((entry,paired));selected[entry['hash']]=entry;selected[paired['hash']]=paired
    output.mkdir(parents=True);(output/'assets').mkdir();(output/'private-fixture.txt').write_text('Paired source-removal research fixture\n')
    originals={e['hash']:hashlib.sha256((source/e['folder']/'payload.dat').read_bytes()).hexdigest() for e in selected.values()}
    for entry in selected.values():shutil.copytree(source/entry['folder'],output/entry['folder'])
    (output/'assets.json').write_text(json.dumps(dict(manifest,entries=list(selected.values()))),encoding='utf-8')
    def signature(blocks):return [hashlib.sha256(b).hexdigest() for b in blocks]
    reader=runtime_protocol.SourceReader(output);expected={}
    for entry,paired in pairs:
        for record in reader.records(entry):expected[(entry['hash'],record['index'])]=signature(reader.blocks(dict(bank=entry['hash'],record=record['index']))[1])
    for i,(entry,paired) in enumerate(pairs):
        print(f'{i+1}/{len(pairs)} {Path(entry["folder"]).name}: {materialize_pair(output,entry,paired)} records',flush=True)
    for entry in selected.values():(output/entry['folder']/'payload.dat').unlink()
    reader=runtime_protocol.SourceReader(output);workspace=Workspace(output/'assets');folder=DirectFolder.__new__(DirectFolder);folder.root=output
    for entry in selected.values():folder.bank(entry)
    for (bank,index),hashes in expected.items():
        assert signature(reader.blocks(dict(bank=bank,record=index))[1])==hashes
        key=Path(entries[bank]['folder']).name+'/'+str(index)
        assert signature(workspace.resource(key).blocks())==hashes
    for entry in selected.values():assert hashlib.sha256((source/entry['folder']/'payload.dat').read_bytes()).hexdigest()==originals[entry['hash']]
    report=dict(pairs=len(pairs),records=len(expected),source_payloads_removed=True,editor_and_runtime_equal=True,game_launched=False)
    (output/'report.json').write_text(json.dumps(report,indent=2),encoding='utf-8');print(json.dumps(report))


if __name__=='__main__':main()
