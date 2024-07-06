from typing import Callable, Literal
from data import Image_Types, ImageData
import os


class FramesReader:
    def __init__(
        self,
        folder: str,
        sort_fn: Callable[[any], any] = None,
        processes=1,
        read_method: Literal["torch", "torch_cuda", "pil", "cv"] = "pil",
        output_format: Image_Types = "numpy",
        tqdm: bool = False,
    ) -> None:
        self.folder = folder
        self.sort_fn = sort_fn
        self.read_method = read_method
        self.output_format = output_format
        self.tqdm = tqdm
        if processes > 1:
            from concurrent.futures import ThreadPoolExecutor as TPE

            self.pool = TPE(processes)
        if self.tqdm:
            from tqdm import tqdm

            self.tqdm = tqdm

    def read(self) -> list[any]:
        files = os.listdir(self.folder)
        files = sorted(files, key=self.sort_fn)
        self.result = [0 for _ in range(len(files))]
        self.pbar = self.tqdm(total=len(files)) if self.tqdm else None
        for i, file in enumerate(files):
            file = os.path.join(self.folder, file)
            if "pool" in dir(self):
                self.pool.submit(self._read_and_convert, file, i)
            else:
                self._read_and_convert(file, i)
        if "pool" in dir(self):
            self.pool.shutdown(wait=True)
        return self.result

    def _read_and_convert(self, file: str, index: int):
        data, type = self._read(file)
        self.result[index] = ImageData(data, type, self.output_format).convert()
        self.pbar.update(1) if self.pbar else None

    def _read(self, file: str):
        match self.read_method:
            case "torch":
                return self._read_torch(file)
            case "torch_cuda":
                return self._read_torch_cuda(file)
            case "pil":
                return self._read_pil(file)
            case "cv":
                return self._read_cv(file)
            case _:
                raise ValueError("Invalid read method")

    def _read_torch(self, file: str):
        import torch

        return torch.load(file), "torch"

    def _read_torch_cuda(self, file: str):
        import torch

        return torch.load(file).cuda(), "torch_cuda"

    def _read_pil(self, file: str):
        from PIL import Image

        return Image.open(file), "pil"

    def _read_cv(self, file: str):
        import cv2

        return cv2.imread(file), "numpy"
