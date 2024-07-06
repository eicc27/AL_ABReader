from typing import Literal
import numpy as np

Image_Types = Literal["torch", "torch_cuda", "pil", "numpy"]


class ImageData:
    def __init__(
        self,
        data: any,
        input_type: Image_Types = "numpy",
        output_type: Image_Types = "numpy",
    ) -> None:
        self.input_type, self.output_type = input_type, output_type
        self.data = data
    
    def convert(self):
        if self.input_type == self.output_type:
            return self.data
        data = self._to_numpy()
        return self._to(data)

    def _to_numpy(self):
        match self.input_type:
            case "torch":
                return self._torch_to_numpy()
            case "torch_cuda":
                return self._torch_cuda_to_numpy()
            case "pil":
                return self._pil_to_numpy()
            case _:
                raise ValueError("Invalid input type")

    def _to(self, data: np.ndarray):
        match self.output_type:
            case "torch":
                return self._numpy_to_torch(data)
            case "torch_cuda":
                return self._numpy_to_torch_cuda(data)
            case "pil":
                return self._numpy_to_pil(data)
            case "numpy":
                return data
            case _:
                raise ValueError("Invalid output type")

    def _torch_to_numpy(self):
        import torch

        data: torch.Tensor = self.data
        return data.numpy()

    def _numpy_to_torch(self, data: np.ndarray):
        import torch

        return torch.from_numpy(data)

    def _numpy_to_torch_cuda(self, data: np.ndarray):
        import torch

        return torch.from_numpy(data).cuda()

    def _numpy_to_pil(self, data: np.ndarray):
        from PIL import Image

        return Image.fromarray(data)

    def _torch_cuda_to_numpy(self):
        import torch

        if not torch.cuda.is_available():
            raise Exception("CUDA is not available")
        data: torch.Tensor = self.data
        return data.detach().cpu().numpy()

    def _pil_to_numpy(self):
        from PIL import Image

        data: Image = self.data
        self.out_data = np.array(data)  # H, W, C
