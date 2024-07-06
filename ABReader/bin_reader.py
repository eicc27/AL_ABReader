class BinaryReader:
    def __init__(self, data: bytes) -> None:
        self.data = data
        self.hexes: list[str] = self._decode_hex()
        self.len = len(self.hexes)
        self.ptr = 0  # pointing to the next hex to read

    def __len__(self):
        return len(self.hexes)

    def _decode_hex(self):
        hex_data_str = self.data.hex()
        hexes = []
        for i, hd in enumerate(hex_data_str[::2]):
            hexes.append(hd + hex_data_str[2 * i + 1])
        return hexes

    def move(self, bias: int):
        self.ptr += bias
        return self

    def moveTo(self, pos: int):
        self.ptr = pos
        return self

    def align_nonzero(self):
        while int(self.hexes[self.ptr], 16) == 0 and self.ptr < self.len:
            self.ptr += 1
        return self

    def align(self, factor: int = 4):
        while self.ptr % factor != 0:
            self.ptr += 1

    def decode_str(self, move_after: int = 0):
        # strip leading zeros
        while int(self.hexes[self.ptr], 16) == 0 and self.ptr < self.len:
            self.ptr += 1
        # get data
        data = ""
        while int(self.hexes[self.ptr], 16) != 0 and self.ptr < self.len:
            data += self.hexes[self.ptr]
            self.ptr += 1
        self.move(move_after)
        return bytes.fromhex(data).decode()

    def decode_hex(self, size=16, strip=True, reverse=False):
        if strip:
            while int(self.hexes[self.ptr], 16) == 0 and self.ptr < self.len:
                self.ptr += 1
        data = []
        for _ in range(size // 16):
            data.append(self.hexes[self.ptr])
            self.ptr += 1
        if reverse:
            data = data[::-1]
        # print(data)
        return int("".join(data), 16)

    def decode_int(self):
        # strip leading zeros
        while int(self.hexes[self.ptr], 16) == 0 and self.ptr < self.len:
            self.ptr += 1
        # get data
        data = ""
        while int(self.hexes[self.ptr], 16) != 0 and self.ptr < self.len:
            data += self.hexes[self.ptr]
            self.ptr += 1
        return int(data, 16)

    def decode_aligned_str(self, reverse=False):
        # first read a int32 as length
        length = self.decode_hex(4 * 16, strip=False, reverse=reverse)
        str_hexes = self.read(length, strip=False)
        self.align(4)
        return bytes.fromhex("".join(str_hexes)).decode()

    def read(self, size: int, strip=True):
        if strip:
            while int(self.hexes[self.ptr], 16) == 0 and self.ptr < self.len:
                self.ptr += 1
        data = self.hexes[self.ptr : self.ptr + size]
        self.ptr += size
        return data

    def get_data(self, bias=10):
        return " ".join(self.hexes[self.ptr : self.ptr + bias])
