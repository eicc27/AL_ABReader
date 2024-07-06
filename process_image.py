from ImageDecoders.texture import MeshTexture2D
from ImageDecoders.head import Heading
from ImageDecoders.utils import *
from ImageDecoders.head import ssim
from ImageDecoders.alpha_blend import alpha_blend
from functools import partial
from PIL import Image
import numpy as np
import torch
from BSRGAN.models.network_rrdbnet import RRDBNet
from BSRGAN.utils import utils_image
from typing import Literal
from tqdm import tqdm


class ImagePipeline:
    def __init__(self) -> None:
        self.render_output: str = None
        self.faces_output: str = None

    def render(
        self, out_file: str, texture_file: str, mesh_file: str = None, processes=4
    ):
        print(f"Rendering {texture_file} with mesh objects...")
        self.render_output = out_file
        mt2d = MeshTexture2D(texture_file, mesh_file)
        output = mt2d.render(processes)
        Image.fromarray(output.astype(np.uint8)).save(self.render_output)
        print(f"Rendering done written to {out_file}.")
        return self

    def apply_faces(
        self,
        heads_path: str,
        out_dir: str,
        render_output=None,
        **fpn_kwargs,
    ):
        self.faces_output = out_dir
        rm_mkdir(self.faces_output)
        if render_output:
            self.render_output = render_output
        print(
            f"Finding and replacing head(from {heads_path}) to {self.render_output}..."
        )
        heading = Heading(self.render_output, heads_path)
        heading.replace_head(out_path=self.faces_output, **fpn_kwargs)
        print(f"Head replacing done, written to {out_dir}")
        return self

    def super_resolution(
        self,
        output_path: str,
        model_name: Literal["BSRGAN", "BSRGANx2"] = "BSRGAN",
        target_path: str = None,
    ):
        if not torch.cuda.is_available():
            raise RuntimeError("CUDA is not available, cannot perform super-resolution")
        if model_name not in ["BSRGAN", "BSRGANx2"]:
            raise ValueError("Model name must be either 'BSRGAN' or 'BSRGANx2'")
        self.sr_output = output_path
        if not os.path.exists(output_path):
            os.mkdir(output_path)
        if target_path:
            self.faces_output = target_path
        sf = 4 if model_name == "BSRGAN" else 2
        print(
            f"Performing image super-resolution using {model_name} (scaling factor x{sf})..."
        )
        torch.cuda.empty_cache()
        model = RRDBNet(sf=sf)
        model.load_state_dict(
            torch.load(f"BSRGAN/model_zoo/{model_name}.pth"), strict=True
        )
        model.eval()
        for _, v in model.named_parameters():
            v.requires_grad = False
        model = model.to("cuda")
        torch.cuda.empty_cache()
        pbar = tqdm(total=len(self.faces_output))
        for img_path in utils_image.get_image_paths(self.faces_output):
            basename = os.path.basename(img_path)
            # BSRGAN part
            input_img: np.ndarray = utils_image.imread_uint(img_path, n_channels=3)
            input_img = utils_image.uint2tensor4(input_img)
            input_img = input_img.to("cuda")
            output_img = model(input_img)
            output_img: np.ndarray = utils_image.tensor2uint(output_img)
            # alpha blendering part
            sr = output_img / 255.0
            sr = np.concatenate(
                [sr, np.ones_like(sr[..., :1])], axis=-1
            )  # add alpha channel
            lr = Image.open(img_path).resize(
                (sr.shape[1], sr.shape[0]), resample=Image.BICUBIC
            )
            lr = np.array(lr) / 255.0
            # print(lr.shape, sr.shape)
            sr = alpha_blend(sr, lr, lr[..., 3], absolute=True)
            Image.fromarray((sr * 255.0).astype(np.uint8)).save(
                os.path.join(self.sr_output, basename)
            )
            pbar.update(1)
        pbar.close()
        print(f"Super-resolution done, written to {output_path}")
        return self


if __name__ == "__main__":
    # from texture to faces SR
    (
        ImagePipeline()
        .render(
            out_file="assets/feiyun/feiyun_2.png",
            texture_file="assets/feiyun/feiyun_2/Texture2D/feiyun_2.png",
            mesh_file="assets/feiyun/feiyun_2/Mesh/feiyun_2-mesh.obj",
        )
        .apply_faces(
            heads_path="assets/feiyun/heads",
            out_dir="assets/feiyun/feiyun_2_heads",
            layers=6,
            factor=2,
            metric=partial(ssim, abs=True, exps=(1, 1, 2), consts=(1e-4, 3e-4, 1.5e-4)),
        )
        # .super_resolution(
        #     output_path="assets/feiyun/feiyun_2_heads_SR",
        #     model_name="BSRGANx2",
        # )
    )
    # single SR on bg image
    # ImagePipeline().super_resolution(
    #     target_path="assets/bg", model_name="BSRGAN", output_path="assets/output"
    # )
