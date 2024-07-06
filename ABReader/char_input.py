from ab_input import ABInput
from ab_exporter import ABExporter
import os
import re


class ABCharacterInput:
    '''
    Reads input automatically from the source asset bundle folder.
    Specified with a character name, it determines the (possible)
    faces attached to the texture, and calls the input and exporter
    to decode unity-compressed bundles.
    '''
    def __init__(self, ab_folder: str, char_name: str) -> None:
        self.paintings_path = os.path.join(ab_folder, "painting")
        self.heads_path = os.path.join(ab_folder, "paintingface")
        self.chars = self._search_char(char_name)

    def _search_char(self, char_name: str):
        pf_files = []
        pf_kwd = re.compile(rf"{char_name}.*")
        for pf in os.listdir(self.heads_path):
            if pf_kwd.search(pf):
                pf_files.append(pf)
        painting_kwd = re.compile(rf"{char_name}.*_tex")
        painting_files = []
        for painting in os.listdir(self.paintings_path):
            if painting_kwd.search(painting):
                painting_files.append(painting)
        # match face and painting
        chars = {}
        for pf in sorted(pf_files):
            kwd = re.compile(rf"{pf}.*_tex")
            target_chars = [s for s in painting_files if kwd.search(s) != None]
            if not len(target_chars):
                chars[char] = None
                continue
            for char in target_chars:
                chars[char] = pf
        return chars


if __name__ == "__main__":
    ab_input = ABInput("../AssetBundles/painting/aersasi_2_tex")
    ab_input.read_assets()
    ab_output = ABExporter(ab_input)
    ab_output.export()
    # print(input.metadata)
