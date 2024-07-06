from serialized_file import SerializedFile
from bin_reader import BinaryReader
from utils import int_to_float32, get_bit, bytes_to_float32s

VERTEX_FMT = [
    "Float",
    "Float16",
    "UNorm8",
    "SNorm8",
    "UNorm16",
    "SNorm16",
    "UInt8",
    "SInt8",
    "UInt16",
    "SInt16",
    "UInt32",
    "SInt32",
]
VERTEX_FMT_SZ = {
    4: [
        "Float",
        "UInt32",
        "SInt32",
    ],
    2: [
        "Float16",
        "UNorm16",
        "SNorm16",
        "UInt16",
        "SInt16",
    ],
    1: [
        "UNorm8",
        "SNorm8",
        "UInt8",
        "SInt8",
    ],
}


def get_fmt_size(fmt: int):
    fmt_str = VERTEX_FMT[fmt]
    for sz, fmts in VERTEX_FMT_SZ.items():
        if fmt_str in fmts:
            return sz
    raise ValueError(f"Unknown vertex format: {fmt}")


def read_packed_float_vector(reader: BinaryReader):
    ret = {}
    ret["num_items"] = reader.decode_hex(4 * 16, strip=False, reverse=True)
    ret["range"] = int_to_float32(reader.decode_hex(4 * 16, strip=False, reverse=True))
    ret["start"] = int_to_float32(reader.decode_hex(4 * 16, strip=False, reverse=True))
    num_data = reader.decode_hex(4 * 16, strip=False, reverse=True)
    ret["data"] = []
    for _ in range(num_data):
        ret["data"].append(reader.decode_hex(1 * 16, strip=False))
    reader.align()
    ret["bit_size"] = reader.decode_hex(1 * 16, strip=False)
    reader.align()
    return ret


def read_packed_int_vector(reader: BinaryReader):
    ret = {}
    ret["num_items"] = reader.decode_hex(4 * 16, strip=False, reverse=True)
    num_data = reader.decode_hex(4 * 16, strip=False, reverse=True)
    ret["data"] = []
    for _ in range(num_data):
        ret["data"].append(reader.decode_hex(1 * 16, strip=False))
    reader.align()
    ret["bit_size"] = reader.decode_hex(1 * 16, strip=False)
    reader.align()
    return ret


class MeshReader:
    def __init__(self, src: SerializedFile) -> None:
        self.src = src
        self.reader = self.src.reader
        print("Mesh name:", self.reader.decode_aligned_str(reverse=True))
        self.submeshes = self.read_submeshes()
        print("Submeshes:", self.submeshes)
        self.read_shapes_data()
        self.read_bones()
        self.idx_buf = self.read_idx_buf()
        self.vertex_data = self.read_vertex_data()
        self.read_compressed_mesh()
        self.process_data() # vertices, uv0
        self.get_triangles() # indices
        print("Vertices: ", self.vertices[:10])
        print("UV0: ", self.uv0[:10])
        print("Indices: ", self.indices[:10])


    def read_submeshes(self):
        submesh_nums = self.reader.decode_hex(4 * 16, strip=False, reverse=True)
        print("Submesh nums: ", submesh_nums)
        submeshes = []
        for _ in range(submesh_nums):
            submesh = {}
            submesh["first_byte"] = self.reader.decode_hex(
                4 * 16, strip=False, reverse=True
            )
            submesh["index_nums"] = self.reader.decode_hex(
                4 * 16, strip=False, reverse=True
            )
            submesh["topology"] = self.reader.decode_hex(
                4 * 16, strip=False, reverse=True
            )
            assert submesh["topology"] == 0  # triangles
            submesh["base_vertex"] = self.reader.decode_hex(
                4 * 16, strip=False, reverse=True
            )
            submesh["first_vertex"] = self.reader.decode_hex(
                4 * 16, strip=False, reverse=True
            )
            submesh["vertex_nums"] = self.reader.decode_hex(
                4 * 16, strip=False, reverse=True
            )
            submesh["aabb"] = {
                "center": [
                    int_to_float32(
                        self.reader.decode_hex(4 * 16, strip=False, reverse=True)
                    )
                    for _ in range(3)
                ],
                "extent": [
                    int_to_float32(
                        self.reader.decode_hex(4 * 16, strip=False, reverse=True)
                    )
                    for _ in range(3)
                ],
            }
            submeshes.append(submesh)
        return submeshes

    def read_shapes_data(self):
        vertex_nums = self.reader.decode_hex(4 * 16, strip=False, reverse=True)
        assert vertex_nums == 0
        shape_nums = self.reader.decode_hex(4 * 16, strip=False, reverse=True)
        assert shape_nums == 0
        channel_nums = self.reader.decode_hex(4 * 16, strip=False, reverse=True)
        assert channel_nums == 0
        weight_nums = self.reader.decode_hex(4 * 16, strip=False, reverse=True)
        assert weight_nums == 0

    def read_bones(self):
        pose_matrix_size = self.reader.decode_hex(4 * 16, strip=False, reverse=True)
        assert pose_matrix_size == 0
        bone_name_nums = self.reader.decode_hex(4 * 16, strip=False, reverse=True)
        assert bone_name_nums == 0
        self.reader.decode_hex(4 * 16, strip=False, reverse=True)
        bones_aabb_nums = self.reader.decode_hex(4 * 16, strip=False, reverse=True)
        assert bones_aabb_nums == 0
        var_bone_cnt_weights = self.reader.decode_hex(4 * 16, strip=False, reverse=True)
        assert var_bone_cnt_weights == 0
        self.reader.move(4).align()

    def read_idx_buf(self):
        use_16bit_indices = (
            self.reader.decode_hex(4 * 16, strip=False, reverse=True) == 0
        )
        assert use_16bit_indices
        idx_buf_size = self.reader.decode_hex(4 * 16, strip=False, reverse=True)
        idx_buf = []
        for _ in range(idx_buf_size // 2):
            idx_buf.append(self.reader.decode_hex(2 * 16, strip=False, reverse=True))
        self.reader.align()
        # print(idx_buf[-10:])
        return idx_buf

    def read_vertex_data(self):
        vertex_nums = self.reader.decode_hex(4 * 16, strip=False, reverse=True)
        channel_nums = self.reader.decode_hex(4 * 16, strip=False, reverse=True)
        print("Vertices:", vertex_nums, "Channels:", channel_nums)
        channels = []
        for _ in range(channel_nums):
            channels.append(
                {
                    "stream": self.reader.decode_hex(1 * 16, strip=False),
                    "offset": self.reader.decode_hex(1 * 16, strip=False),
                    "format": self.reader.decode_hex(1 * 16, strip=False),
                    "dim": self.reader.decode_hex(1 * 16, strip=False) & 0xF,
                }
            )
        # print(channels)
        stream_nums = max([chn["stream"] for chn in channels]) + 1
        streams = []
        offset = 0
        for s in range(stream_nums):
            mask = 0
            stride = 0
            for i, chn in enumerate(channels):
                if chn["stream"] == s and chn["dim"] > 0:
                    mask |= (1 << i) & 0xFFFF_FFFF
                    stride += chn["dim"] * get_fmt_size(chn["format"])
            streams.append(
                {
                    "channel_mask": mask,
                    "offset": offset,
                    "stride": stride,
                    "divider_op": 0,
                    "freq": 0,
                }
            )
            offset += vertex_nums * stride
            offset = (offset + 15) & ~15 & 0xFFFF_FFFF
        # print(streams)
        data_size = []
        for _ in range(self.reader.decode_hex(4 * 16, strip=False, reverse=True)):
            data_size.append(self.reader.decode_hex(1 * 16, strip=False))
        # print(len(data_size), data_size[:50])
        self.reader.align()
        return {
            "channels": channels,
            "streams": streams,
            "data_size": data_size,
            "vertex_nums": vertex_nums,
        }

    def read_compressed_mesh(self):
        vertices = read_packed_float_vector(self.reader)
        uv = read_packed_float_vector(self.reader)
        normals = read_packed_float_vector(self.reader)
        tangents = read_packed_float_vector(self.reader)
        weights = read_packed_int_vector(self.reader)
        normal_signs = read_packed_int_vector(self.reader)
        tangent_signs = read_packed_int_vector(self.reader)
        float_colors = read_packed_float_vector(self.reader)
        bone_indices = read_packed_int_vector(self.reader)
        triangles = read_packed_int_vector(self.reader)
        uv_info = self.reader.decode_hex(4 * 16, strip=False, reverse=True)
        assert all(
            i["num_items"] == 0
            for i in [
                vertices,
                uv,
                normals,
                tangents,
                weights,
                normal_signs,
                tangent_signs,
                float_colors,
                bone_indices,
                triangles,
            ]
        )
        assert uv_info == 0
        self.reader.move(24)
        # m_MeshUsageFlags, m_BakedConvexCollisionMesh, m_BakedTriangleCollisionMesh
        self.reader.move(4 * 3)
        # m_MeshMetrics[2]
        self.reader.move(4 * 2)
        self.reader.align()
        offset = self.reader.decode_hex(8 * 16, strip=False, reverse=True)
        size = self.reader.decode_hex(4 * 16, strip=False, reverse=True)
        path = self.reader.decode_aligned_str(True)
        assert not path or len(path) == 0
        # print(offset, size, path)

    def process_data(self):
        # read vertex data from self.vertex_data
        vertex_nums = self.vertex_data["vertex_nums"]
        for i, chn in enumerate(self.vertex_data["channels"]):
            if chn["dim"] > 0:
                assert chn["format"] == 0  # float
                stream = self.vertex_data["streams"][chn["stream"]]
                if get_bit(stream["channel_mask"], i):
                    fmt_size = get_fmt_size(chn["format"])
                component_bytes = [
                    None for _ in range(vertex_nums * chn["dim"] * fmt_size)
                ]
                for v in range(vertex_nums):
                    vertex_offset = (
                        stream["offset"] + chn["offset"] + stream["stride"] * v
                    )
                    for d in range(chn["dim"]):
                        component_offset = vertex_offset + d * fmt_size
                        bytes_offset = fmt_size * (d + v * chn["dim"])
                        component_bytes[bytes_offset : bytes_offset + fmt_size] = (
                            self.vertex_data["data_size"][
                                component_offset : component_offset + fmt_size
                            ]
                        )
                component_floats = bytes_to_float32s(component_bytes)
                if i == 0:
                    self.vertices = component_floats
                elif i == 4:
                    self.uv0 = component_floats
                else:
                    raise ValueError(
                        f"Channels other than 0 & 4 (got {i}) should have dim=0"
                    )
        print(self.vertices[:10], self.uv0[:10])
        # at here, we jump all of DecompressCompressedMesh for assertions of empty compressed mesh in self.read_compressed_mesh

    def get_triangles(self):
        self.indices = []
        for sm in self.submeshes:
            first_idx = sm["first_byte"] // 2
            # we use 16 bit indices as asserted before (self.read_idx_buf)
            index_nums = sm["index_nums"]
            # we use triangle topology as asserted before (self.read_submeshes)
            # top = sm["topology"]
            for i in range(0, index_nums, 3):
                self.indices.append(self.idx_buf[first_idx + i])
                self.indices.append(self.idx_buf[first_idx + i + 1])
                self.indices.append(self.idx_buf[first_idx + i + 2])
