import struct
import pytest
from choops_recomp.runtime_protocol import decode_component


def h7(body,size):return struct.pack('>5I',0x0e4837c3,size,20+len(body),0,12)+body


def test_component_literals_and_overlapping_match():
    assert decode_component(h7(b'\0abcdefgh',8))==b'abcdefgh'
    # Literal a, then a distance-one six-byte overlapping match.
    assert decode_component(h7(b'\x02a\x30\x01',7))==b'a'*7


def test_component_bounded_decode_and_invalid_distance():
    with pytest.raises(ValueError,match='header'):decode_component(h7(b'\0a',1),limit=0)
    with pytest.raises(ValueError,match='distance'):decode_component(h7(b'\x01\0\0',3))
    with pytest.raises(ValueError,match='Truncated'):decode_component(h7(b'\0',1))


def test_raw_component_is_already_authoritative():
    value=b'raw resource data';assert decode_component(value) is value
