# from Texture2DDecoderNative, etc.cpp
import numpy as np
import struct

WRITE_ORDER = [0, 4, 8, 12, 1, 5, 9, 13, 2, 6, 10, 14, 3, 7, 11, 15]

DISTANCE = np.array([3, 6, 11, 16, 23, 32, 41, 64], dtype=np.int32)

ETC1_SUBBLOCK_TABLE = np.array(
    [
        [0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1],
        [0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1],
    ],
    dtype=np.uint8,
)

ETC2_ALPHA_MOD_TABLE = np.array(
    [
        [-3, -6, -9, -15, 2, 5, 8, 14],
        [-3, -7, -10, -13, 2, 6, 9, 12],
        [-2, -5, -8, -13, 1, 4, 7, 12],
        [-2, -4, -6, -13, 1, 3, 5, 12],
        [-3, -6, -8, -12, 2, 5, 7, 11],
        [-3, -7, -9, -11, 2, 6, 8, 10],
        [-4, -7, -8, -11, 3, 6, 7, 10],
        [-3, -5, -8, -11, 2, 4, 7, 10],
        [-2, -6, -8, -10, 1, 5, 7, 9],
        [-2, -5, -8, -10, 1, 4, 7, 9],
        [-2, -4, -8, -10, 1, 3, 7, 9],
        [-2, -5, -7, -10, 1, 4, 6, 9],
        [-3, -4, -7, -10, 2, 3, 6, 9],
        [-1, -2, -3, -10, 0, 1, 2, 9],
        [-4, -6, -8, -9, 3, 5, 7, 8],
        [-3, -5, -7, -9, 2, 4, 6, 8],
    ],
    dtype=np.int32,
)

ETC1_MODIFIER_TABLE = np.array(
    [
        [2, 8],
        [5, 17],
        [9, 29],
        [13, 42],
        [18, 60],
        [24, 80],
        [33, 106],
        [47, 183],
    ],
    dtype=np.int32,
)


def clip_uint8(i: int | list | np.ndarray):
    return np.clip(i, 0, 255)


def uint8(i: int | list):
    return np.array(i).astype(np.uint8)


def argb32(r: int, g: int, b: int, a: int):
    return (((1 * a) << 24) | ((1 * r) << 16) | ((1 * g) << 8) | (1 * b)).astype(
        np.uint32
    )


def array3_to_argb32(color: np.ndarray, bias: int = 0):
    cb = clip_uint8(color + bias)
    cb = cb.astype(np.uint32)
    # print(cb.shape)
    return argb32(cb[:, 0], cb[:, 1], cb[:, 2], 255)


def array8_to_uint64(ab: list[int]):
    packed = struct.pack("<8B", *ab)
    return struct.unpack(">Q", packed)[0]


class ETC2A8Decoder:
    def __init__(self, data: list[int], width: int, height: int) -> None:
        self.data = np.array(data).astype(np.uint8)
        self.width = width
        self.height = height
        self.img = np.zeros((width * height), dtype=np.uint32)
        self.num_blks_x = (width + 3) // 4
        self.num_blks_y = (height + 3) // 4

    def decode(self):
        l = len(self.data)
        print(f"Length of data: {l}")
        # we group data by 16 -> first 8 bytes and last 8 bytes.
        # pad the data to be divided by 16
        data = self.data
        # pad_l = (self.data.size + 15) // 16 * 16
        # print(f"Padding size: {pad_l - l}")
        # data = np.pad(data, (0, pad_l - l))
        data = data.reshape(-1, 8).reshape(-1, 2, 8).transpose(1, 0, 2)
        head_blks: np.ndarray = data[0]
        etc2_blks: np.ndarray = data[1]
        N = etc2_blks.shape[0]
        j = ((etc2_blks[:, 6]).astype(np.int32) << 8 | etc2_blks[:, 7]).astype(
            np.uint16
        )
        k = ((etc2_blks[:, 4]).astype(np.int32) << 8 | etc2_blks[:, 5]).astype(
            np.uint32
        )
        colors = np.zeros((N, 3, 3), dtype=np.uint8)
        buffers = np.zeros((N, 16), dtype=np.uint32)
        mask = (etc2_blks[:, 3] & 2) != 0
        r = (etc2_blks[:, 0] & 0xF8).astype(np.int16)
        dr = (etc2_blks[:, 0] << 3 & 0x18).astype(np.int16) - (
            etc2_blks[:, 0] << 3 & 0x20
        ).astype(np.int16)
        mask_r = mask & (((r + dr) < 0) | ((r + dr) > 255))
        g = (etc2_blks[:, 1] & 0xF8).astype(np.int16)
        dg = (etc2_blks[:, 1] << 3 & 0x18).astype(np.int16) - (
            etc2_blks[:, 1] << 3 & 0x20
        ).astype(np.int16)
        mask_g = mask & ~mask_r & (((g + dg) < 0) | ((g + dg) > 255))
        b = (etc2_blks[:, 2] & 0xF8).astype(np.int16)
        db = (etc2_blks[:, 2] << 3 & 0x18).astype(np.int16) - (
            etc2_blks[:, 2] << 3 & 0x20
        ).astype(np.int16)
        mask_b = mask & ~mask_r & ~mask_g & (((b + db) < 0) | ((b + db) > 255))
        mask_a = mask & ~(mask_r | mask_g | mask_b)
        mask_n = ~mask
        # print(mask_r[:10], mask_g[:10], mask_b[:10], mask_a[:10], mask_n[:10])
        # mask_r
        colors[mask_r, 0] = np.array(
            [
                (etc2_blks[mask_r, 0] << 3 & 0xC0)
                | (etc2_blks[mask_r, 0] << 4 & 0x30)
                | (etc2_blks[mask_r, 0] >> 1 & 0xC)
                | (etc2_blks[mask_r, 0] & 3),
                (etc2_blks[mask_r, 1] & 0xF0) | etc2_blks[mask_r, 1] >> 4,
                (etc2_blks[mask_r, 1] & 0x0F) | etc2_blks[mask_r, 1] << 4,
            ],
            dtype=np.uint8,
        ).T
        colors[mask_r, 1] = np.array(
            [
                (etc2_blks[mask_r, 2] & 0xF0) | etc2_blks[mask_r, 2] >> 4,
                (etc2_blks[mask_r, 2] & 0x0F) | etc2_blks[mask_r, 2] << 4,
                (etc2_blks[mask_r, 3] & 0xF0) | etc2_blks[mask_r, 3] >> 4,
            ],
            dtype=np.uint8,
        ).T
        # mask_g
        colors[mask_g, 0] = np.array(
            [
                (etc2_blks[mask_g, 0] << 1 & 0xF0) | (etc2_blks[mask_g, 0] >> 3 & 0xF),
                (etc2_blks[mask_g, 0] << 5 & 0xE0) | (etc2_blks[mask_g, 1] & 0x10),
                (etc2_blks[mask_g, 1] & 8)
                | (etc2_blks[mask_g, 1] << 1 & 6)
                | etc2_blks[mask_g, 2] >> 7,
            ],
            dtype=np.uint8,
        ).T
        colors[mask_g, 1] = np.array(
            [
                (etc2_blks[mask_g, 2] << 1 & 0xF0) | (etc2_blks[mask_g, 2] >> 3 & 0xF),
                (etc2_blks[mask_g, 2] << 5 & 0xE0) | (etc2_blks[mask_g, 3] >> 3 & 0x10),
                (etc2_blks[mask_g, 3] << 1 & 0xF0) | (etc2_blks[mask_g, 3] >> 3 & 0xF),
            ],
            dtype=np.uint8,
        ).T
        colors[mask_g, 0, 1] |= colors[mask_g, 0, 1] >> 4
        colors[mask_g, 0, 2] |= colors[mask_g, 0, 2] << 4
        colors[mask_g, 1, 1] |= colors[mask_g, 1, 1] >> 4
        # mask_b
        colors[mask_b, 0] = np.array(
            [
                (etc2_blks[mask_b, 0] << 1 & 0xFC) | (etc2_blks[mask_b, 0] >> 5 & 3),
                (etc2_blks[mask_b, 0] << 7 & 0x80)
                | (etc2_blks[mask_b, 1] & 0x7E)
                | (etc2_blks[mask_b, 0] & 1),
                (etc2_blks[mask_b, 1] << 7 & 0x80)
                | (etc2_blks[mask_b, 2] << 2 & 0x60)
                | (etc2_blks[mask_b, 2] << 3 & 0x18)
                | (etc2_blks[mask_b, 3] >> 5 & 4),
            ],
            dtype=np.uint8,
        ).T
        colors[mask_b, 1] = np.array(
            [
                (etc2_blks[mask_b, 3] << 1 & 0xF8)
                | (etc2_blks[mask_b, 3] << 2 & 4)
                | (etc2_blks[mask_b, 3] >> 5 & 3),
                (etc2_blks[mask_b, 4] & 0xFE) | etc2_blks[mask_b, 4] >> 7,
                (etc2_blks[mask_b, 4] << 7 & 0x80) | (etc2_blks[mask_b, 5] >> 1 & 0x7C),
            ],
            dtype=np.uint8,
        ).T
        colors[mask_b, 2] = np.array(
            [
                (etc2_blks[mask_b, 5] << 5 & 0xE0)
                | (etc2_blks[mask_b, 6] >> 3 & 0x1C)
                | (etc2_blks[mask_b, 5] >> 1 & 3),
                (etc2_blks[mask_b, 6] << 3 & 0xF8)
                | (etc2_blks[mask_b, 7] >> 5 & 0x6)
                | (etc2_blks[mask_b, 6] >> 4 & 1),
                etc2_blks[mask_b, 7] << 2 | (etc2_blks[mask_b, 7] >> 4 & 3),
            ],
            dtype=np.uint8,
        ).T
        colors[mask_b, 0, 2] |= colors[mask_b, 0, 2] >> 6
        colors[mask_b, 1, 2] |= colors[mask_b, 1, 2] >> 6
        # print(colors[1])
        # mask_a
        colors[mask_a, 0] = np.array(
            [
                r[mask_a] | r[mask_a] >> 5,
                g[mask_a] | g[mask_a] >> 5,
                b[mask_a] | b[mask_a] >> 5,
            ],
            dtype=np.uint8,
        ).T
        colors[mask_a, 1] = np.array(
            [
                r[mask_a] + dr[mask_a],
                g[mask_a] + dg[mask_a],
                b[mask_a] + db[mask_a],
            ],
            dtype=np.uint8,
        ).T
        colors[mask_a, 1] |= colors[mask_a, 1] >> 5
        # mask_n
        colors[mask_n, 0] = np.array(
            [
                (etc2_blks[mask_n, 0] & 0xF0) | etc2_blks[mask_n, 0] >> 4,
                (etc2_blks[mask_n, 1] & 0xF0) | etc2_blks[mask_n, 1] >> 4,
                (etc2_blks[mask_n, 2] & 0xF0) | etc2_blks[mask_n, 2] >> 4,
            ],
            dtype=np.uint8,
        ).T
        colors[mask_n, 1] = np.array(
            [
                (etc2_blks[mask_n, 0] & 0x0F) | etc2_blks[mask_n, 0] << 4,
                (etc2_blks[mask_n, 1] & 0x0F) | etc2_blks[mask_n, 1] << 4,
                (etc2_blks[mask_n, 2] & 0x0F) | etc2_blks[mask_n, 2] << 4,
            ],
            dtype=np.uint8,
        ).T
        # r transformation
        dist_idx = (etc2_blks[mask_r, 3] >> 1 & 6) | (etc2_blks[mask_r, 3] & 1)
        dist = DISTANCE[dist_idx]
        dist = np.tile(dist[:, np.newaxis], (1, 3))  # align with shape of colors
        color_set = np.array(
            [
                array3_to_argb32(colors[mask_r, 0] * 1),
                array3_to_argb32(colors[mask_r, 1] * 1, dist),
                array3_to_argb32(colors[mask_r, 1] * 1),
                array3_to_argb32(colors[mask_r, 1] * 1, -dist),
            ],
            dtype=np.uint32,
        ).T  # N, 4
        k[mask_r] = k[mask_r] << 1
        for i in range(16):
            buffers[mask_r, WRITE_ORDER[i]] = color_set[
                np.arange(color_set.shape[0]),
                (k[mask_r] & 2) | (j[mask_r] & 1),  # (N,)-shaped indices
            ]
            j[mask_r] = j[mask_r] >> 1
            k[mask_r] = k[mask_r] >> 1
        # g transformation
        dist = (etc2_blks[mask_g, 3] & 4) | (etc2_blks[mask_g, 3] << 1 & 2)
        dist = dist + (
            (colors[mask_g, 0, 0] > colors[mask_g, 1, 0])
            | (
                (colors[mask_g, 0, 0] == colors[mask_g, 1, 0])
                & (colors[mask_g, 0, 1] > colors[mask_g, 1, 1])
            )
            | (
                (colors[mask_g, 0, 0] == colors[mask_g, 1, 0])
                & (colors[mask_g, 0, 1] == colors[mask_g, 1, 1])
                & (colors[mask_g, 0, 2] > colors[mask_g, 1, 2])
            )
        )
        dist = DISTANCE[dist]
        dist = np.tile(dist[:, np.newaxis], (1, 3))  # align with shape of colors
        color_set = np.array(
            [
                array3_to_argb32(colors[mask_g, 0] * 1, dist),
                array3_to_argb32(colors[mask_g, 0] * 1, -dist),
                array3_to_argb32(colors[mask_g, 1] * 1, dist),
                array3_to_argb32(colors[mask_g, 1] * 1, -dist),
            ],
            dtype=np.uint32,
        ).T
        k[mask_g] = k[mask_g] << 1
        for i in range(16):
            buffers[mask_g, WRITE_ORDER[i]] = color_set[
                np.arange(color_set.shape[0]), (k[mask_g] & 2) | (j[mask_g] & 1)
            ]
            j[mask_g] = j[mask_g] >> 1
            k[mask_g] = k[mask_g] >> 1
        # b transformation
        i = 0
        for y in range(4):
            for x in range(4):
                # we promote uint8 to int32 by multiplying each uint8 with a python int
                buffers[mask_b, i] = argb32(
                    clip_uint8(
                        (
                            x * colors[mask_b, 1, 0].astype(np.int32)
                            - x * colors[mask_b, 0, 0].astype(np.int32)
                            + y * colors[mask_b, 2, 0].astype(np.int32)
                            - y * colors[mask_b, 0, 0].astype(np.int32)
                            + 4 * colors[mask_b, 0, 0].astype(np.int32)
                            + 2
                        )
                        >> 2
                    ),
                    clip_uint8(
                        (
                            x * colors[mask_b, 1, 1].astype(np.int32)
                            - x * colors[mask_b, 0, 1].astype(np.int32)
                            + y * colors[mask_b, 2, 1].astype(np.int32)
                            - y * colors[mask_b, 0, 1].astype(np.int32)
                            + 4 * colors[mask_b, 0, 1].astype(np.int32)
                            + 2
                        )
                        >> 2
                    ),
                    clip_uint8(
                        (
                            x * colors[mask_b, 1, 2].astype(np.int32)
                            - x * colors[mask_b, 0, 2].astype(np.int32)
                            + y * colors[mask_b, 2, 2].astype(np.int32)
                            - y * colors[mask_b, 0, 2].astype(np.int32)
                            + 4 * colors[mask_b, 0, 2].astype(np.int32)
                            + 2
                        )
                        >> 2
                    ),
                    255,
                )
                i += 1
        # a & n transformation
        mask_an = mask_a | mask_n
        code = (
            np.array([etc2_blks[mask_an, 3] >> 5, etc2_blks[mask_an, 3] >> 2 & 7])
            .astype(np.uint8)
            .T
        )  # (N, 2)
        table = ETC1_SUBBLOCK_TABLE[etc2_blks[mask_an, 3] & 1]  # (N, 16)
        # print(code.shape, table.shape)
        for i in range(16):
            s = table[:, i]
            m = ETC1_MODIFIER_TABLE[code[np.arange(code.shape[0]), s], j[mask_an] & 1]
            m = m * ((-1) ** (k[mask_an] & 1))
            m = np.tile(m[:, np.newaxis], (1, 3))
            buffers[mask_an, WRITE_ORDER[i]] = array3_to_argb32(colors[mask_an, s], m)
            j[mask_an] = j[mask_an] >> 1
            k[mask_an] = k[mask_an] >> 1
        # decode_etc2a8 part
        mask_head = (head_blks[:, 1] & 0xF0) != 0
        mask_head_n = ~mask_head
        # print([hex(i) for i in buffers[596 // 4]])
        # mask_head
        multp = head_blks[mask_head, 1] >> 4
        table = ETC2_ALPHA_MOD_TABLE[head_blks[mask_head, 1] & 0xF, :]  # (N, 8)
        l = head_blks[mask_head]  # (N, 8)
        l = np.frombuffer(l, dtype=np.uint64).byteswap()  # (N,)
        # print(hex(l[0]))
        WRITE_ORDER_REV = WRITE_ORDER[::-1]
        for i in range(16):
            # print(head_blks[mask_head, 0][0], multp[0], table[0, (l[0]).astype(np.uint8) & 7])
            buffers[mask_head, WRITE_ORDER_REV[i]] = (
                buffers[mask_head, WRITE_ORDER_REV[i]] & 0x00FF_FFFF
            ) + (
                clip_uint8(
                    head_blks[mask_head, 0]
                    + multp * table[np.arange(table.shape[0]), l.astype(np.uint8) & 7]
                ).astype(np.uint32)
                << 24
            )
            l >>= 3
        # mask_head_n
        for i in range(16):
            buffers[mask_head_n, i] = (buffers[mask_head_n, i] & 0x00FF_FFFF) + (
                head_blks[mask_head_n, 0].astype(np.uint32) << 24
            )
        # write buffers into img
        i = 0
        for y in range(self.num_blks_y):
            for x in range(self.num_blks_x):
                self._copy_blk_buf(x, y, 4, 4, buffers[i])
                i += 1
        return self.img

    def _copy_blk_buf(self, bx: int, by: int, bw: int, bh: int, buf: list[int]):
        x = bw * bx
        xl = (self.width - bw * bx) if (bw * (bx + 1) > self.width) else bw
        # xl *= 4 for memcpy
        length = bw * bh
        y = by * bh
        bi = 0
        while y < self.height and bi < length:
            start = y * self.width + x
            # print(start)
            self.img[start : start + xl] = buf[bi : bi + xl]
            y += 1
            bi += bw
