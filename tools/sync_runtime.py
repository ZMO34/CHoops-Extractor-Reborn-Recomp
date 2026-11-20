"""Copy this editor's compatible runtime reference headers from a recomp checkout.

No SDK build, installed game mutation or game launch is performed.
"""
import argparse,shutil
from pathlib import Path

def main():
    p=argparse.ArgumentParser();p.add_argument('--recomp',type=Path,required=True);a=p.parse_args();root=Path(__file__).resolve().parents[1]
    for name in ('native_dds.h','native_dds_upload.h','native_dds_d3d12.inl'):
        source=a.recomp/'port/src'/name
        if not source.is_file():raise ValueError('Required native runtime header missing')
        shutil.copy2(source,root/'runtime'/name)
    shutil.copy2(a.recomp/'port/third_party/XENIA_TEXTURE_LICENSE.txt',root/'docs/XENIA_TEXTURE_LICENSE.txt')
    print('Synchronized compatible native DDS source headers; no game files changed')
if __name__=='__main__':main()
