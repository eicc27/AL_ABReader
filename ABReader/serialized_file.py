from bin_reader import BinaryReader
import json
from utils import uint_to_int

FILE_TYPES = json.load(open("types.json", "r"))


class SerializedFile:
    def __init__(self, content: bytes, path: str) -> None:
        self.path = path
        self.reader = BinaryReader(content)
        self.header = self.read_header()
        self.types = self.read_types()
        self.objs = self.read_objects()

    def read_header(self):
        header = {}
        header["metadata_size"] = self.reader.decode_hex(4 * 16, strip=False)
        header["file_size"] = self.reader.decode_hex(4 * 16, strip=False)
        header["version"] = self.reader.decode_hex(4 * 16, strip=False)
        header["offset"] = self.reader.decode_hex(4 * 16, strip=False)
        if header["version"] >= 9:
            header["endian"] = self.reader.decode_hex(1 * 16, strip=False)
            header["reserved"] = self.reader.decode_hex(3 * 16, strip=False)
        if header["version"] >= 22:
            header["metadata_size"] = self.reader.decode_hex(4 * 16, strip=False)
            header["file_size"] = self.reader.decode_hex(8 * 16, strip=False)
            header["offset"] = self.reader.decode_hex(8 * 16, strip=False)
        assert header["endian"] == 0  # little endian
        if header["version"] >= 7:
            header["unity_version"] = self.reader.decode_str()
        if header["version"] >= 8:
            header["platform"] = self.reader.decode_hex(2 * 16, strip=False)
        if header["version"] >= 13:
            header["enable_typetree"] = self.reader.decode_hex(4 * 16, strip=False) != 0
        return header

    def read_types(self):
        types_num = self.reader.decode_hex(1 * 16, strip=False)
        # print(types_num)
        types = []
        v = self.header["version"]
        enable_typetree = self.header["enable_typetree"]
        for i in range(types_num):
            t = {}
            t["class_id"] = self.reader.decode_hex(
                4 * 16 if i == 0 else 1 * 16, strip=False
            )
            if v >= 16:
                t["is_stripped_type"] = self.reader.decode_hex(4 * 16, strip=False) == 0
            if v >= 17:
                t["script_type_index"] = uint_to_int(
                    self.reader.decode_hex(2 * 16, strip=False)
                )
            if v >= 13:
                t["old_type_hash"] = self.reader.read(16, strip=False)
            if enable_typetree:
                if v >= 12:
                    t["nodes"] = self.read_typetree()
                if v >= 21:
                    t["type_deps"] = []
                    length = uint_to_int(
                        self.reader.decode_hex(4 * 16, strip=False), length=4
                    )
                    for _ in range(length):
                        t["type_deps"].append(
                            uint_to_int(
                                self.reader.decode_hex(4 * 16, strip=False), length=4
                            )
                        )
            types.append(t)
        return types

    def read_typetree(self):
        node_nums = self.reader.decode_hex(4 * 16, strip=False, reverse=True)
        str_bufsize = self.reader.decode_hex(4 * 16, strip=False, reverse=True)
        nodes = []
        v = self.header["version"]
        # print(node_nums, str_bufsize)
        for _ in range(node_nums):
            node = {}
            node["version"] = self.reader.decode_hex(2 * 16, strip=False, reverse=True)
            node["level"] = self.reader.decode_hex(1 * 16, strip=False)
            node["type_flags"] = self.reader.decode_hex(1 * 16, strip=False)
            node["type_str_offset"] = self.reader.decode_hex(
                4 * 16, strip=False, reverse=True
            )
            node["name_str_offset"] = self.reader.decode_hex(
                4 * 16, strip=False, reverse=True
            )
            node["byte_size"] = uint_to_int(
                self.reader.decode_hex(4 * 16, strip=False, reverse=True), length=4
            )
            node["index"] = uint_to_int(
                self.reader.decode_hex(4 * 16, strip=False, reverse=True), length=4
            )
            node["meta_flag"] = uint_to_int(
                self.reader.decode_hex(4 * 16, strip=False, reverse=True), length=4
            )
            if v >= 19:
                node["ref_type_hash"] = self.reader.decode_hex(
                    8 * 16, strip=False, reverse=True
                )
            nodes.append(node)
        string_buf = self.reader.read(str_bufsize)
        # print(self.reader.hexes[self.reader.ptr:self.reader.ptr+10])
        string_buf_reader = BinaryReader(bytes.fromhex("".join(string_buf)))
        for i in range(node_nums):
            node = nodes[i]
            nodes[i]["type"] = SerializedFile.read_str(
                string_buf_reader, node["type_str_offset"]
            )
            nodes[i]["name"] = SerializedFile.read_str(
                string_buf_reader, node["name_str_offset"]
            )
        # print(nodes[-1])
        return nodes

    @staticmethod
    def read_str(reader: BinaryReader, value: int):
        is_offset = value & 0x8000_0000 == 0
        if is_offset:
            reader.moveTo(value)
            return reader.decode_str()
        offset = value & 0x7FFF_FFFF
        return FILE_TYPES[str(int(offset))]

    def read_objects(self):
        object_nums = self.reader.decode_hex(1 * 16, strip=False)
        objs = []
        v = self.header["version"]
        for i in range(object_nums):
            obj = {}
            obj["path_id"] = uint_to_int(
                self.reader.align_nonzero().decode_hex(
                    8 * 16, strip=False, reverse=True
                ),
                length=8,
            )
            if v >= 22:
                obj["byte_start"] = uint_to_int(
                    self.reader.decode_hex(8 * 16, strip=False, reverse=True),
                    length=8,
                )
            obj["byte_start"] += self.header["offset"]
            obj["byte_size"] = self.reader.decode_hex(4 * 16, strip=False, reverse=True)
            obj["type_id"] = uint_to_int(
                self.reader.decode_hex(4 * 16, strip=False, reverse=True), length=4
            )
            # print(obj)
            if v >= 16:
                obj_type = self.types[obj["type_id"]]
                obj["ser_type"] = obj_type
                obj["class_id"] = obj_type["class_id"]
            objs.append(obj)
        # print("".join(self.reader.hexes[self.reader.ptr:self.reader.ptr+20]))
        script_types = []
        if v >= 11:
            script_nums = uint_to_int(
                self.reader.decode_hex(4 * 16, strip=False, reverse=True), length=4
            )
            for _ in range(script_nums):
                script = {}
                script["local_ser_file_idx"] = uint_to_int(
                    self.reader.decode_hex(4 * 16, strip=False, reverse=True), length=4
                )
                script["local_id_in_file"] = uint_to_int(
                    self.reader.move(5).decode_hex(8 * 16, strip=False, reverse=True),
                    length=8,
                )
                script_types.append(script)
        externals = []
        external_nums = uint_to_int(
            self.reader.decode_hex(4 * 16, strip=False, reverse=True), length=4
        )
        assert external_nums == 0
        for _ in range(external_nums):
            ext = {}
            # TODO
            externals.append(ext)
        ref_types = []
        ref_type_nums = uint_to_int(
            self.reader.decode_hex(4 * 16, strip=False, reverse=True), length=4
        )
        # TODO
        assert ref_type_nums == 0
        if v >= 5:
            user_info = self.reader.decode_str()
        return objs
