from serialized_file import SerializedFile
import json

IMG_TYPES = json.load(open("image_types.json"))


class Texture2DReader:
    def __init__(self, src: SerializedFile) -> None:
        self.src = src
        self.reader = self.src.reader
        print("Texture 2D name:", self.reader.decode_aligned_str(reverse=True))
        # readInt32, readBoolean * 2, alignStream
        self.reader.move(4 + 1 * 2).align(4)
        (
            self.width,
            self.height,
            _,
            _,
            self.texture_fmt,
            self.mip_count,
        ) = (
            self.reader.decode_hex(4 * 16, strip=False, reverse=True),
            self.reader.decode_hex(4 * 16, strip=False, reverse=True),
            self.reader.decode_hex(4 * 16, strip=False, reverse=True),
            self.reader.decode_hex(4 * 16, strip=False, reverse=True),
            self.reader.decode_hex(4 * 16, strip=False, reverse=True),
            self.reader.decode_hex(4 * 16, strip=False, reverse=True),
        )
        print(f"Image size: {self.width}x{self.height}")
        self.texture_fmt = IMG_TYPES[str(self.texture_fmt)]
        self.reader.move(8)
        self.reader.decode_hex(4 * 16, strip=False, reverse=True)
        self.reader.decode_hex(4 * 16, strip=False, reverse=True)
        self.gl_tex = self.read_gl_texture_settings()
        self.reader.decode_hex(4 * 16, strip=False, reverse=True)
        self.reader.decode_hex(4 * 16, strip=False, reverse=True)
        cnt = self.reader.decode_hex(4 * 16, strip=False, reverse=True)
        for _ in range(cnt):
            self.reader.decode_hex(2 * 16, strip=False, reverse=True)
        self.reader.align()
        image_data_size = self.reader.decode_hex(4 * 16, strip=False, reverse=True)
        if image_data_size == 0:
            self.stream_data = self.read_streaming_info()

    def read_gl_texture_settings(self):
        gl_tex = {}
        gl_tex["filter_mode"] = self.reader.decode_hex(
            4 * 16, strip=False, reverse=True
        )
        gl_tex["af"] = self.reader.decode_hex(4 * 16, strip=False, reverse=True)
        gl_tex["mip_bias"] = self.reader.decode_hex(4 * 16, strip=False, reverse=True)
        gl_tex["wrap_mode"] = self.reader.decode_hex(4 * 16, strip=False, reverse=True)
        self.reader.decode_hex(4 * 16, strip=False, reverse=True)
        self.reader.decode_hex(4 * 16, strip=False, reverse=True)
        return gl_tex

    def read_streaming_info(self):
        streaming_info = {}
        streaming_info["offset"] = self.reader.decode_hex(
            8 * 16, strip=False, reverse=True
        )
        streaming_info["size"] = self.reader.decode_hex(
            4 * 16, strip=False, reverse=True
        )
        strlen = self.reader.decode_hex(4 * 16, strip=False, reverse=True)
        streaming_info["path"] = bytes.fromhex(
            "".join(self.reader.read(strlen, strip=False))
        ).decode()
        self.reader.align(4)
        # print(self.reader.hexes[self.reader.ptr:self.reader.ptr + 10])
        return streaming_info

    def get_image_data(self):
        return {
            "path": self.stream_data["path"],
            "file": self.src,
            "offset": self.stream_data["offset"],
            "size": self.stream_data["size"],
        }
