from ABReader.ab_input import ABInput
from ABReader.texture2d_reader import Texture2DReader
from ABReader.mesh_reader import MeshReader
from ABReader.bin_reader import BinaryReader
from ABReader.etc2_decomp import ETC2A8Decoder
import os
import numpy as np
from PIL import Image

# import texture2ddecoder  # ref file


class ABExporter:
    def __init__(self, ab_input: ABInput) -> None:
        self.files = ab_input.data_files
        self.resources = ab_input.resource_files

    def export(self, path: str = None, processes=1):
        self.texture_nums = 0
        self.path = path
        self.results = []
        if processes > 1:
            from concurrent.futures import ThreadPoolExecutor as TPE

            pool = TPE(processes)
        for file in self.files:
            if processes > 1:
                pool.submit(self._export_single, file)
            else:
                self._export_single(file)
        if processes > 1:
            pool.shutdown(wait=True)
        return None if path else self.results

    def _export_single(self, file):
        if type(file) == Texture2DReader:
            img = self.export_texture2d(file)
            (
                img.save(os.path.join(self.path, f"{self.texture_nums}.png"))
                if self.path
                else self.results.append(img)
            )
        elif type(file) == MeshReader:
            lines = self.export_mesh(file)
            if self.path:
                with open(os.path.join(self.path, "mesh.obj"), "w+") as f:
                    f.writelines(lines)
            else:
                self.results.append(lines)
        else:
            raise NotImplementedError("Unknown file type")

    def export_texture2d(self, file: Texture2DReader):
        img_metadata = file.get_image_data()
        # read data with offset and size
        # reader = BinaryReader(self.resources[])
        path = os.path.basename(file.stream_data["path"])
        print(path, "offset:", img_metadata["offset"])
        reader = BinaryReader(self.resources[path]).moveTo(img_metadata["offset"])
        buf = [int(h, 16) for h in reader.read(img_metadata["size"], strip=False)]
        print(
            "data buffer:",
            buf[:10],
            "format: ",
            file.texture_fmt,
            "size: ",
            img_metadata["size"],
        )
        print(f"Image size: {file.width}x{file.height}")
        # we deal with 2 known formats: ETC2_RGBA8 and RGBA32
        # typically RGBA8 means 8 bits for each channel(RRGGBBAA)
        # resulting in total 32 bits, which is what 32 meaning in RGBA32
        # then we just need to decompress the ETC2 format
        # and save it as PNG
        if file.texture_fmt == "RGBA32":
            assert file.width * file.height * 4 == len(buf)
            img = np.frombuffer(bytes(buf), dtype=np.uint8).reshape(
                (file.height, file.width, 4)
            )
            img = np.flip(img, axis=0)
            img = Image.fromarray(img, "RGBA")
        elif file.texture_fmt == "ETC2_RGBA8":
            assert img_metadata["size"] % 16 == 0
            # img_ = texture2ddecoder.decode_etc2a8(bytes(buf), file.width, file.height)
            # img_ = np.frombuffer(img_, dtype=np.uint32)
            img = ETC2A8Decoder(buf, file.width, file.height).decode()
            # assert np.all(img_ == img)
            # print(colorama.Fore.GREEN, "CHECK PASS")
            img = np.frombuffer(img, dtype=np.uint8).reshape(
                (file.height, file.width, 4)
            )
            img = np.flip(img, axis=0)
            # we turn BGRA into RGBA (0, 1, 2, 3 -> 2, 1, 0, 3)
            img = Image.fromarray(img[..., [2, 1, 0, 3]], "RGBA")
        self.texture_nums += 1
        return img

    def export_mesh(self, file: MeshReader):
        vertices = np.array(file.vertices, dtype=np.int32).reshape(-1, 3)
        uv0 = np.array(file.uv0, dtype=np.float32).reshape(-1, 2)
        indices = np.array(file.indices, dtype=np.int32).reshape(-1, 3)
        lines = []
        for v in vertices:
            v = [str(x) for x in v]
            lines.append(f"v {' '.join(v)}")
        for uv in uv0:
            uv = [str(x) for x in uv]
            lines.append(f"vt {' '.join(uv)}")
        for i in indices:
            i = [f"{x}/{x}/{x}" for x in i]
            lines.append(f"f {' '.join(i)}")
        return lines
