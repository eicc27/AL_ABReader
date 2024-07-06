import json
import os
from random import choice


class Character:
    def __init__(self, config_path: str, with_bg=True):
        with open(config_path) as f:
            self.config = json.load(f)
        self.base_path = self.config["base_path"]
        self.char_config = self.config["char_bg"] if with_bg else self.config["char"]

    def getBackgroundPath(self) -> str:
        return os.path.join(self.base_path, self.config["bg"])

    def getInitCharPath(self) -> str:
        return os.path.join(
            self.base_path, self.char_config["name"], self.config["init"]
        )

    def getNumOfAudios(self):
        return len(self.config["audios"])

    def screenCaliberate(self, ratio: float, dw: int, dh: int):
        h = self.char_config["head"]
        self.char_config["head"] = [
            ratio * h[0] + dw,
            ratio * h[1] + dh,
            ratio * h[2] + dw,
            ratio * h[3] + dh,
        ]
        s = self.char_config["special"]
        self.char_config["special"] = [
            ratio * s[0] + dw,
            ratio * s[1] + dh,
            ratio * s[2] + dw,
            ratio * s[3] + dh,
        ]
        # 1806, 900
        # print(self.char_config["special"])

    def isHead(self, x: int, y: int):
        h = self.char_config["head"]
        return h[0] <= x <= h[2] and h[1] <= y <= h[3]

    def isSpecial(self, x: int, y: int):
        s = self.char_config["special"]
        return s[0] <= x <= s[2] and s[1] <= y <= s[3]

    def getAudioExprs(self, index: int, base=25):
        """
        Gets the audio and expressions with paths joined and converts the decimal part of
        waypoints with base into milliseconds. The default base configuration comes from Adobe Premiere.
        The animation key is also aligned to the waypoint length.
        """
        audio_exprs = self.config["audios"][index]
        result = {}
        result["audio"] = os.path.join(self.base_path, audio_exprs["audio"])
        result["exprs"] = [
            (os.path.join(self.base_path, self.char_config["name"], e))
            for e in audio_exprs["exprs"]
        ]
        result["waypoints"] = [
            (int((int(w) + (w - int(w)) * 100 / base) * 1000))
            for w in audio_exprs["waypoints"]
        ]
        if "anims" not in audio_exprs:
            result["anims"] = [None for _ in range(len(result["exprs"]))]
        else:
            result["anims"] = audio_exprs["anims"]
        for _ in range(len(result["exprs"]) - len(result["anims"])):
            result["anims"].append(None)
        return result

    def getType(self, type: str = None, random_select=True):
        result = []
        for i, audio_expr in enumerate(self.config["audios"]):
            if type is None:
                if "type" not in audio_expr:
                    result.append(i)
                    continue
            if "type" in audio_expr and audio_expr["type"] == type:
                result.append(i)
        return result if not random_select else choice(result)
