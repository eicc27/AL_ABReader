import struct


def uint_to_int(i: int, length=2):
    bytes_i = i.to_bytes(length)
    return int.from_bytes(bytes_i, signed=True)


def int_to_float32(i: int):
    h = hex(i)[2:]
    for _ in range(8 - len(h)):
        h = "0" + h
    d = bytes.fromhex(h)
    return struct.unpack("!f", d)[0]


def bytes_to_float32s(bts: list[int]):
    ret = []
    for i in range(0, len(bts), 4):
        d = bytes(bts[i : i + 4][::-1])
        ret.append(struct.unpack("!f", d)[0])
    return ret


def get_bit(val: int, pos: int):
    bit = (val >> pos) & 1
    return bit
