"""Candidate names become labels only after matching actual Xbox CRC identities."""
import zlib

def crc(name):return zlib.crc32(name.encode('ascii'))&0xffffffff

SHAPES=('u','v','vtri','tri','wishbone')
BUILDS=('thin','reg','fat')
BANK_NAMES=['cloth_shorts.iff',*[f'cloth_{shape}{suffix}.iff' for shape in SHAPES for suffix in ('','_thin','_reg','_fat')],*[f'{height}_shoe{i}.iff' for height in ('hi','lo') for i in range(1,5)]]
RECORD_NAMES=['arena','floor','unifregion','unif','shortregion','short','names','jersey_numbers',*[f'jersey_{shape}_{build}' for shape in SHAPES for build in BUILDS],*[f'shorts{build}' for build in BUILDS],*[f'{height}_shoe{i}' for height in ('hi','lo') for i in range(1,5)]]
RECORD_LABELS={crc(name):name for name in RECORD_NAMES}

def bank_labels(entries):
    present={entry['hash'] for entry in entries};return {crc(name.upper()):name for name in BANK_NAMES if crc(name.upper()) in present}
