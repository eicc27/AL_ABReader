from ABReader.ab_input import ABInput
from ABReader.ab_exporter import ABExporter
import os
import re


def find_key_by_value(d: dict, value):
    keys = []
    for k, v in d.items():
        if v == value:
            keys.append(k)
    return keys


def mkdir(path):
    if not os.path.exists(path):
        os.mkdir(path)
    return path


class ABCharacterInput:
    """
    Reads input automatically from the source asset bundle folder.
    Specified with a character name, it determines the (possible)
    faces attached to the texture, and calls the input and exporter
    to decode unity-compressed bundles.
    """

    def __init__(self, ab_folder: str, char_name: str) -> None:
        self.paintings_path = os.path.join(ab_folder, "painting")
        self.heads_path = os.path.join(ab_folder, "paintingface")
        # painting - face match
        self.chars = self._search_char(char_name)

    def _search_char(self, char_name: str):
        self.pf_files = []
        pf_kwd = re.compile(rf"{char_name}.*")
        for pf in os.listdir(self.heads_path):
            if pf_kwd.search(pf):
                self.pf_files.append(pf)
        painting_kwd = re.compile(rf"{char_name}.*_tex")
        self.painting_files = []
        for painting in os.listdir(self.paintings_path):
            if painting_kwd.search(painting):
                self.painting_files.append(painting)
        # match face and painting
        chars = {}
        for pf in sorted(self.pf_files):
            segs = pf.split("_")
            if len(segs) == 2:
                name, skin_idx = segs
                kwd = re.compile(rf"{name}.*{skin_idx}.*_tex")
            else:
                name = segs[0]
                kwd = re.compile(rf"{name}.*_tex")
            target_chars = [s for s in self.painting_files if kwd.search(s) != None]
            if not len(target_chars):
                chars[char] = None
                continue
            for char in target_chars:
                chars[char] = pf
        return chars

    def decode(self, out_dir: str):
        # we organize the files with face names, if applicable
        # face_file
        #  - faces
        #  - ...characters
        for face_file in self.pf_files:
            face_path = os.path.join(out_dir, face_file)
            mkdir(face_path)
            self._decode_face_file(
                face_file, mkdir(os.path.join(face_path, "faces"))
            )
            [
                self._decode_painting_file(char, mkdir(os.path.join(face_path, char)))
                for char in find_key_by_value(self.chars, face_file)
            ]
        [
            self._decode_painting_file(char, mkdir(os.path.join(face_path, char)))
            for char in find_key_by_value(self.chars, None)
        ]

    def _decode_painting_file(self, src: str, dst: str):
        src = os.path.join(self.paintings_path, src)
        print(f"Decoding {src} to {dst}")
        ab_input = ABInput(src)
        ab_input.read_assets()
        exporter = ABExporter(ab_input)
        exporter.export(dst)

    def _decode_face_file(self, src: str, dst: str):
        src = os.path.join(self.heads_path, src)
        print(f"Decoding {src} to {dst}")
        ab_input = ABInput(src)
        ab_input.read_assets()
        exporter = ABExporter(ab_input)
        exporter.export(dst)


if __name__ == "__main__":
    char_input = ABCharacterInput("../AssetBundles", "ankeleiqi")
    print(char_input.chars)
    char_input.decode("./decoded")
    # print(input.metadata)
