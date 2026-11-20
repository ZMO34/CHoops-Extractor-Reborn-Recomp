"""Rebuild and verify the College Hoops 2K8 Xbox ROST layout from PS3 data."""

from collections import defaultdict
import struct

from .runtime_protocol import decode_component
from .workspace import sha


PLAYER = 0x271AC
COUNT = 5695  # Includes ten player-format templates.
PS3_STRIDE = 308
XBOX_STRIDE = 316
EXPANSION = COUNT * (XBOX_STRIDE - PS3_STRIDE)
PS3_END = PLAYER + COUNT * PS3_STRIDE + 16
XBOX_END = PS3_END + EXPANSION
PS3_POOL = 0x361D04
TEAM = 0x1D85E0
CONFERENCE = 0x345978
PS3_IFF_SHA = 'fb2fa6b1099e0a13859009eabcc3e1b6b0701169918dcc6e7266d05e66dd78c9'
PS3_ROST_SHA = '3aceb04ac96778e7589c4a197fedb1371376ab01af3d988bf59479620db568b7'
XBOX_ROST_SHA = 'a58c58552f3807061f53a214c47630c90ee30e17fa61d4d878fb2e2a48780a98'


def word(data, offset):
    return struct.unpack_from(">i", data, offset)[0]


def set_word(data, offset, value):
    struct.pack_into(">i", data, offset, value)


def relocate(data, source, source_field, output_field, transform):
    delta = word(source, source_field)
    if delta not in (0, -1):
        target = transform(source_field + delta - 1)
        delta = target - output_field + 1
    set_word(data, output_field, delta)


def signature(data, rows, offset, bit):
    return bytes(data[row + offset] >> bit & 1 for row in rows)


def packed_mapping(ps3, xbox):
    ps3_rows = range(PLAYER, PS3_END - 16, PS3_STRIDE)
    xbox_rows = range(PLAYER, XBOX_END - 16, XBOX_STRIDE)
    signatures = defaultdict(list)
    for offset in range(0x80, 0xBC):
        for bit in range(8):
            values = signature(xbox, xbox_rows, offset, bit)
            if any(values):
                signatures[values].append((offset, bit))
    mapping = {}
    for offset in range(0x80, 0xB6):
        for bit in range(8):
            values = signature(ps3, ps3_rows, offset, bit)
            if any(values):
                destinations = signatures[values]
                if len(destinations) != 1:
                    raise ValueError(f"Ambiguous stock mapping for player bit {offset:#x}.{bit}")
                mapping[offset, bit] = destinations[0]

    # Executable-backed fields include bits that never vary in either stock roster.
    confirmed = {
        (0x85, 0): (0x86, 0),  # Right shoulder, high two bits of the four-bit field.
        (0x86, 7): (0x87, 7),
        # PS3 0x749390/0x7524CC writes intermediate +0x34 bits 3..0.
        # Xbox 0x84D0073C reads the same field into player word +0x90 bits 20..17.
        (0x90, 7): (0x91, 4),
        (0x90, 6): (0x91, 3),
        (0x90, 5): (0x91, 2),
        (0x90, 4): (0x91, 1),
        (0x90, 0): (0x92, 5),  # Eye color.
        (0x90, 1): (0x92, 6),
        (0x91, 0): (0x93, 5),  # T-shirt.
        (0x91, 1): (0x93, 6),
        (0x9B, 0): (0x9C, 2),  # Custom morph gate.
    }
    for bit in range(8):
        confirmed[0x80, bit] = (0x80, bit)  # Confidence.
    for source_bit, target_bit in confirmed.items():
        if mapping.get(source_bit, target_bit) != target_bit:
            raise ValueError(f"Stock mapping conflicts with executable field {source_bit}")
        mapping[source_bit] = target_bit
    if len(mapping) != len(set(mapping.values())):
        raise ValueError("Multiple source player bits target the same Xbox bit")
    return mapping


def transform(source, mapping, unsupported):
    out = bytearray((len(source) + EXPANSION + 31) & ~31)
    out[:PLAYER + 16] = source[:PLAYER + 16]
    out[XBOX_END:len(source) + EXPANSION] = source[PS3_END:]
    for table in range(0x0C, 0xB0, 8):
        if table == 0x0C:
            continue
        movement = (XBOX_STRIDE - PS3_STRIDE) * 5685 if table == 0x14 else EXPANSION
        set_word(out, table, word(source, table) + movement)
    for field in (0xB0, 0xB4, 0xB8):
        set_word(out, field, word(source, field) + EXPANSION)

    def string_target(target):
        if not PS3_POOL <= target < len(source):
            raise ValueError(f"String pointer outside the PS3 text pool at {target:#x}")
        return target + EXPANSION

    def player_target(target):
        index, anchor = divmod(target - PLAYER, PS3_STRIDE)
        if not 0 <= index < 5685 or anchor != 16:
            raise ValueError(f"Invalid player membership pointer at {target:#x}")
        return PLAYER + index * XBOX_STRIDE + anchor

    for field in range(0xBC, PLAYER + 16, 4):
        relocate(out, source, field, field, string_target)

    for index in range(COUNT):
        p = PLAYER + index * PS3_STRIDE
        q = PLAYER + index * XBOX_STRIDE
        for offset in (0x10, 0x14):
            relocate(out, source, p + offset, q + offset, string_target)
        out[q + 0x18:q + 0x80] = source[p + 0x18:p + 0x80]
        out[q + 0xBC:q + 0x13E] = source[p + 0xB6:p + 0x138]
        for offset in range(0x80, 0xB6):
            for bit in range(8):
                if not source[p + offset] >> bit & 1:
                    continue
                target = mapping.get((offset, bit))
                if target is None:
                    unsupported[offset, bit].append(index)
                else:
                    destination, shift = target
                    out[q + destination] |= 1 << shift

    def color(field):
        q = field + EXPANSION
        out[q:q + 4] = source[field + 3:field + 4] + source[field:field + 3]

    for index in range(443):
        p = TEAM + index * 704
        for offset in range(0x6C, 0xB4, 4):
            relocate(out, source, p + offset, p + EXPANSION + offset, player_target)
        for offset in range(0x1A0, 0x224, 4):
            color(p + offset)
    for index in range(39):
        color(CONFERENCE + index * 2964 + 0x20)
    return out


def restore(xbox, source_size, mapping):
    """Recover the full PS3 image independently of the original input bytes."""
    source = bytearray(source_size)
    source[:PLAYER + 16] = xbox[:PLAYER + 16]
    source[PS3_END:] = xbox[XBOX_END:source_size + EXPANSION]
    for field in range(0x14, 0xB0, 8):
        movement = (XBOX_STRIDE - PS3_STRIDE) * 5685 if field == 0x14 else EXPANSION
        set_word(source, field, word(xbox, field) - movement)
    for field in (0xB0, 0xB4, 0xB8):
        set_word(source, field, word(xbox, field) - EXPANSION)

    def string_target(target):
        return target - EXPANSION

    def player_target(target):
        index, anchor = divmod(target - PLAYER, XBOX_STRIDE)
        return PLAYER + index * PS3_STRIDE + anchor

    for field in range(0xBC, PLAYER + 16, 4):
        relocate(source, xbox, field, field, string_target)
    for index in range(COUNT):
        p = PLAYER + index * PS3_STRIDE
        q = PLAYER + index * XBOX_STRIDE
        for offset in (0x10, 0x14):
            relocate(source, xbox, q + offset, p + offset, string_target)
        source[p + 0x18:p + 0x80] = xbox[q + 0x18:q + 0x80]
        source[p + 0xB6:p + 0x138] = xbox[q + 0xBC:q + 0x13E]
        for (offset, bit), (destination, shift) in mapping.items():
            source[p + offset] |= (xbox[q + destination] >> shift & 1) << bit

    def color(field):
        q = field + EXPANSION
        source[field:field + 4] = xbox[q + 1:q + 4] + xbox[q:q + 1]

    for index in range(443):
        p = TEAM + index * 704
        for offset in range(0x6C, 0xB4, 4):
            relocate(source, xbox, p + EXPANSION + offset, p + offset, player_target)
        for offset in range(0x1A0, 0x224, 4):
            color(p + offset)
    for index in range(39):
        color(CONFERENCE + index * 2964 + 0x20)
    return source


def convert_save(saved, ps3_reference, xbox_stock):
    """Return a native length-prefixed save after verifying both directions."""
    if sha(ps3_reference) == PS3_IFF_SHA:
        # Verified single ROST component extent in the USA retail IFF.
        ps3_stock = decode_component(ps3_reference[0x54:0x54 + 0xF8ECB], limit=3981216)
    else:
        ps3_stock = ps3_reference
    if sha(ps3_stock) != PS3_ROST_SHA:
        raise ValueError('Select the unmodified USA PS3 roster_english.iff or decoded ROST')
    if sha(xbox_stock) != XBOX_ROST_SHA:
        raise ValueError('The project source must contain the unmodified USA Xbox roster')
    if not len(ps3_stock) + 4 <= len(saved) <= 64 * 1024 * 1024 or word(saved, 0) != len(saved) - 4:
        raise ValueError('Select a decrypted PS3 USERDATA roster with a valid length prefix')
    source = saved[4:]
    if source[:0xB0] != ps3_stock[:0xB0]:
        raise ValueError('The PS3 save uses a different roster table layout')
    mapping = packed_mapping(ps3_stock, xbox_stock)
    unsupported = defaultdict(list)
    if transform(ps3_stock, mapping, unsupported) != xbox_stock or unsupported:
        raise ValueError('The converter could not reconstruct the stock Xbox roster')
    converted = transform(source, mapping, unsupported)
    if unsupported:
        details = ', '.join(f'{offset:#x}.{bit} in {len(rows)} rows'
                            for (offset, bit), rows in sorted(unsupported.items()))
        raise ValueError(f'The PS3 roster uses unmapped player fields ({details})')
    if restore(converted, len(source), mapping) != source:
        raise ValueError('The converted roster could not reconstruct the PS3 source')
    return struct.pack('>I', len(converted)) + converted
