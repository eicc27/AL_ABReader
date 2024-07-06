from texture2d_reader import Texture2DReader
from mesh_reader import MeshReader
from bin_reader import BinaryReader
from serialized_file import SerializedFile
import json

CLASS_ID_TYPES = json.load(open("class_types.json"))


class CompType:
    NONE = 0
    LZMA = 1
    LZ4 = 2
    LZ4HC = 3


class Flags:
    COMP_TYPE = 0x3F
    INFO_COMB = 0x40
    INFO_END = 0x80
    PAD_START = 0x200


def is_serialized(content: bytes):
    if len(content) < 20:
        return False
    reader = BinaryReader(content)
    try:
        t = reader.decode_str()
    except UnicodeDecodeError:
        pass
    else:
        if "unity" in t.lower():
            return False
    metadata = {}
    metadata["metadata_size"] = reader.moveTo(0).decode_hex(4 * 16, strip=False)
    metadata["file_size"] = reader.decode_hex(4 * 16, strip=False)
    metadata["version"] = reader.decode_hex(4 * 16, strip=False)
    metadata["offset"] = reader.decode_hex(4 * 16, strip=False)
    metadata["endian"] = reader.decode_hex(1 * 16, strip=False)
    metadata["reserved"] = reader.decode_hex(3 * 16, strip=False)
    if metadata["version"] >= 22:
        if len(content) < 48:
            return False
        metadata["metadata_size"] = reader.decode_hex(4 * 16, strip=False)
        metadata["file_size"] = reader.decode_hex(8 * 16, strip=False)
        metadata["offset"] = reader.decode_hex(8 * 16, strip=False)
    if metadata["file_size"] != len(content):
        return False
    if metadata["offset"] > len(content):
        return False
    # print(metadata)
    return metadata


class ABInput:
    def __init__(self, path: str) -> None:
        with open(path, "rb") as f:
            self.data: bytes = f.read()
        self.bin_reader = BinaryReader(self.data)
        self.metadata = self.read_metadata()
        self.blks_metadata, self.nodes_metadata = self.read_blk_info()
        self.read_blocks()

    def read_metadata(self):
        metadata = {}
        metadata["type"] = self.bin_reader.decode_str()
        metadata["version"] = self.bin_reader.decode_hex()
        metadata["u_version"] = self.bin_reader.decode_str()
        metadata["u_revision"] = self.bin_reader.decode_str()
        metadata["size"] = self.bin_reader.decode_int()
        metadata["comp_blk_size"] = self.bin_reader.decode_int()
        metadata["ucomp_blk_size"] = self.bin_reader.decode_int()
        metadata["props"] = self.bin_reader.decode_int()
        return metadata

    def read_blk_info(self):
        if self.metadata["props"] & Flags.INFO_COMB:
            data = self.bin_reader.read(self.metadata["comp_blk_size"])
            # print(len(data))
            # print([int(d, 16) for d in data])
        comp_type = self.metadata["props"] & Flags.COMP_TYPE
        # print(comp_type)
        if comp_type in [CompType.LZ4, CompType.LZ4HC]:
            import lz4.block as f

            decomp_data: bytes = f.decompress(
                bytes.fromhex("".join(data)),
                uncompressed_size=self.metadata["ucomp_blk_size"],
            )
            decomp_reader = BinaryReader(decomp_data)
            # print(decomp_reader.hexes)
        _ = decomp_reader.read(16, strip=False)
        blk_num = decomp_reader.decode_int()
        # print(hash, blk_num)
        blks_metadata = [
            {
                "ucomp_size": decomp_reader.decode_hex(4 * 16, strip=False),
                "comp_size": decomp_reader.decode_hex(4 * 16, strip=False),
                "props": decomp_reader.decode_hex(strip=True),
            }
            for _ in range(blk_num)
        ]
        print("Blocks metadata: ", blks_metadata)
        nodes = decomp_reader.decode_hex(4 * 16, strip=False)
        # print(nodes)
        nodes_metadata = [
            {
                "offset": decomp_reader.decode_hex(8 * 16, strip=False),
                "size": decomp_reader.decode_hex(8 * 16, strip=False),
                "props": decomp_reader.decode_hex(4 * 16, strip=False),
                "path": decomp_reader.decode_str(move_after=1),
            }
            for _ in range(nodes)
        ]
        print("Nodes metadata: ", nodes_metadata)
        return blks_metadata, nodes_metadata

    def read_blocks(self):
        blk_data = bytes()
        # read and concat
        for blk_metdata in self.blks_metadata:
            comp_type = blk_metdata["props"] & Flags.COMP_TYPE
            data = self.bin_reader.read(blk_metdata["comp_size"], strip=True)
            if comp_type in [CompType.LZ4, CompType.LZ4HC]:
                import lz4.block as f

                decomp_data: bytes = f.decompress(
                    bytes.fromhex("".join(data)),
                    uncompressed_size=blk_metdata["ucomp_size"],
                )
                blk_data += decomp_data
        assert len(blk_data) == sum([b["ucomp_size"] for b in self.blks_metadata])
        files: list[bytes] = []
        # write into files
        for node_metadata in self.nodes_metadata:
            size = node_metadata["size"]
            offset = node_metadata["offset"]
            path = node_metadata["path"]
            print(path, size, offset)
            files.append((path, blk_data[offset : offset + size]))
        # print(len(files))
        self.asset_files: list[tuple[str, SerializedFile]] = []
        self.resource_files: dict[str, bytes] = {}
        for i, (path, file) in enumerate(files):
            if is_serialized(file):
                with open(f"ser_{i}.bin", "wb") as f:
                    f.write(file)
                sf = SerializedFile(file, path)
                self.asset_files.append(sf)
            else:
                with open(f"src_{i}.bin", "wb") as f:
                    f.write(file)
                self.resource_files[path] = file
        # return files

    def read_assets(self):
        self.data_files = []
        for af in self.asset_files:
            for obj_info in af.objs:
                type = CLASS_ID_TYPES[str(obj_info["class_id"])]
                print(type, obj_info["byte_start"])
                # here, we only deal with Texture2D and Mesh
                # thanks to byte_start, we can directly jump to where the content begins for each section
                af.reader.moveTo(obj_info["byte_start"])
                if type == "Texture2D":
                    self.data_files.append(Texture2DReader(af))
                elif type == "Mesh":
                    self.data_files.append(MeshReader(af))
                    # break
        print(self.data_files)
