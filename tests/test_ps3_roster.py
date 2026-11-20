"""Synthetic checks for the retail roster relocation contract."""
from collections import defaultdict
import struct

import pytest

from choops_recomp import ps3_roster as port


def test_relocates_player_links_and_round_trips_custom_fields():
    source = bytearray(3981216)
    stock_xbox = bytearray(4026784)
    mapping = port.packed_mapping(source, stock_xbox)
    player = port.PLAYER + 7 * port.PS3_STRIDE
    xbox_player = port.PLAYER + 7 * port.XBOX_STRIDE
    field = port.TEAM + 0x6C
    name = port.PS3_POOL + 64
    source[name:name + 4] = b'\x00A\x00\x00'
    port.set_word(source, player + 0x10, name - player - 0x10 + 1)
    port.set_word(source, field, player + 16 - field + 1)
    source[player + 0x85] = 1
    source[player + 0x86] = 128
    source[player + 0x90] = 128
    source[player + 0x9B] = 1
    source[player + 0xB6:player + 0x138] = bytes(range(130))
    color = port.TEAM + 0x220
    source[color:color + 4] = bytes.fromhex('112233ff')

    unsupported = defaultdict(list)
    result = port.transform(source, mapping, unsupported)
    assert not unsupported
    assert result[xbox_player + 0x91] == 0x10
    assert result[xbox_player + 0x9C] == 4
    assert result[xbox_player + 0xBC:xbox_player + 0x13E] == bytes(range(130))
    assert result[color + port.EXPANSION:color + port.EXPANSION + 4] == bytes.fromhex('ff112233')
    assert (field + port.EXPANSION + port.word(result, field + port.EXPANSION) - 1
            == xbox_player + 16)
    assert port.restore(result, len(source), mapping) == source


def test_refuses_an_unverified_reference():
    with pytest.raises(ValueError, match='unmodified USA PS3'):
        port.convert_save(struct.pack('>I', 0), b'bad reference', b'')
