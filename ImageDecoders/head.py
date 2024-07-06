from PIL import Image
import torch
import torch.nn.functional as F
import numpy as np
import os
from typing import Callable
from functools import partial
from ImageDecoders.utils import *
from ImageDecoders.alpha_blend import alpha_blend_torch, alpha_blend
from tqdm import tqdm


def psnr(a: torch.tensor, b: torch.tensor):
    """
    Calculate PSNR index between 2 BCHW shaped tensor images.
    """
    I = 255.0
    mse = torch.mean((a - b) ** 2, dim=(-2, -1))  # (B, C)
    return torch.mean(20 * torch.log10(I / torch.sqrt(mse)), dim=-1)  # B


def mse(a: torch.tensor, b: torch.tensor):
    return torch.mean((a - b) ** 2, dim=(-2, -1))


def ssim(
    a: torch.Tensor,
    b: torch.Tensor,
    abs=False,
    exps: tuple[float, float, float] = (1.0, 1.0, 1.0),
    consts: tuple[float, float, float] = (0.01, 0.03, 0.015),
):
    """
    Compute the global SSIM index on image signal a and b,
    both in BCHW format.
    The default parameters (in order: luminance, contrast, structure) are set from the paper:

    Image Quality Assessment: From Error Visibility to Structural Similarity (IEEE 2004).
    """
    C, H, W = a.shape[-3:]
    mu_a = torch.mean(a, dim=(-2, -1))
    mu_b = torch.mean(b, dim=(-2, -1))
    sigma_a = torch.std(a, dim=(-2, -1))
    sigma_b = torch.std(b, dim=(-2, -1))
    sigma_ab = torch.sum(
        (a - mu_a.reshape(-1, C, 1, 1)) * (b - mu_b.reshape(-1, C, 1, 1)), dim=(-2, -1)
    ) / (H * W - 1)
    alpha, beta, gamma = exps
    c1, c2, c3 = consts
    l = (2 * mu_a * mu_b + c1) / (mu_a**2 + mu_b**2 + c1)
    c = (2 * sigma_a * sigma_b + c2) / (sigma_a**2 + sigma_b**2 + c2)
    s = (sigma_ab + c3) / (sigma_a * sigma_b + c3)
    ssim = torch.mean((l**alpha) * (c**beta) * (s**gamma), dim=-1)
    return torch.abs(ssim) if abs else ssim


def image_to_tensor(image: Image.Image, device="cpu"):
    """
    Reshapes the image to (B, C, H, W) tensor.
    """
    t = torch.tensor(np.array(image)).permute(2, 0, 1).float() / 255.0  # (C, H, W)
    return t.reshape(1, *t.shape).to(device)  # (B, C, H, W)


def show_tensor(image: torch.Tensor):
    img = Image.fromarray(
        (image.squeeze(0).permute((1, 2, 0)).detach().cpu().numpy() * 255.0).astype(
            np.uint8
        )
    )
    img.show()


class CustomConv2d(torch.nn.Module):
    def __init__(
        self,
        kernel: torch.Tensor,
        metric: Callable[[torch.Tensor, torch.Tensor], torch.Tensor] = psnr,
    ):
        super(CustomConv2d, self).__init__()
        self.kernel = kernel
        self.metric = metric

    def forward(self, x: torch.Tensor):
        C, H_k, W_k = self.kernel.shape[1:]
        H, W = x.shape[-2:]
        # x shape after unfold: (1, C*H_k*W_k, num_entries)
        x = (
            F.unfold(x, (H_k, W_k))
            .clone()
            .reshape((C, H_k, W_k, -1))
            .permute((3, 0, 1, 2))
        )  # (num_entries, C, Hk, Wk) (BCHW-like)
        kernel = (
            self.kernel.reshape((C, H_k, W_k, 1))
            .repeat(1, 1, 1, x.shape[0])
            .permute((3, 0, 1, 2))
        )
        # apply the alpha channel on the kernel to the image
        x_blended = alpha_blend_torch(x, kernel, kernel[:, 3:, :, :])
        return self.metric(x_blended, kernel).reshape((H - H_k + 1, W - W_k + 1))


class Heading:
    """
    Uses static FPN as backbone to replace heads in the image.

    Attributes:
        src_path (str): Path to the source image.
        picture (Image.Image): Loaded source image.
        heads (list[Image.Image]): List of head images to be used for replacement.
        ref_head (Image.Image): Reference head image set dynamically w.r.t currently processing image. This image is both used in
        comparing with original images in sliding 2d windows in FPN, and the alpha channel masking in final replacement.
        device (str): Device to run computations on, either 'cuda' or 'cpu'. If cuda is available, it will be automatically set.
    """

    def __init__(self, src_path: str, heads_path: str) -> None:
        self.src_path = src_path
        self.picture = Image.open(src_path)
        heads = [os.path.join(heads_path, p) for p in os.listdir(heads_path)]
        self.heads = [Image.open(h) for h in heads]
        self.ref_head = self.heads[0]
        # self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.device = "cpu"

    def _downsample(
        self,
        factor: int,
    ):
        if factor == 1:
            return self.picture, self.ref_head
        return self.picture.resize(
            (self.picture.size[0] // factor, self.picture.size[1] // factor),
            Image.Resampling.BICUBIC,
        ), self.ref_head.resize(
            (self.ref_head.size[0] // factor, self.ref_head.size[1] // factor),
            Image.Resampling.BICUBIC,
        )

    def static_fpn(
        self,
        layers=4,
        factor=2,
        optim_range: list[int] = None,
        metric=psnr,
    ):
        """
        Perform static Feature Pyramid Network (FPN) to locate the best match of the reference head in the source image.

        Args:
            layers (int): Number of downsample layers. Default is 4.
            factor (int): Downsample factor. Default is 2.
            optim_range (list[int]): List of optimization ranges for each layer. Default is None,
            automatically decided by layers and factor.
            metric (Callable): Metric to evaluate the match quality. Default is psnr.

        Returns:
            tuple[int, int]: Coordinates (x, y) of the best match location.
        """
        downsample_rates = [factor**i for i in range(layers)]
        downsample_rates = list(reversed(downsample_rates))
        if not optim_range:
            optim_range = downsample_rates[:-1]
        x: int = None
        y: int = None
        bx1: int = None
        by1: int = None
        for i, rate in enumerate(downsample_rates):
            src, head = self._downsample(rate)
            src, head = image_to_tensor(src, self.device), image_to_tensor(
                head, self.device
            )
            print(f"Downsample rate x{rate}")
            print(f"Src image size {src.size()}, head size {head.size()}")
            if (
                x != None and y != None
            ):  # we narrow down the search range layer by layer
                o = optim_range[i - 1]  # the first loop does not apply
                bx1, by1 = (x - o) * factor, (y - o) * factor
                bx2, by2 = (x + o) * factor, (y + o) * factor
                bx1, bx2 = torch.clamp(
                    bx1, 0, src.shape[-2] - head.shape[-2]
                ), torch.clamp(bx2, 0, src.shape[-2] - head.shape[-2])
                by1, by2 = torch.clamp(
                    by1, 0, src.shape[-1] - head.shape[-1]
                ), torch.clamp(by2, 0, src.shape[-1] - head.shape[-1])
                src = src[:, :, bx1 : bx2 + head.shape[-2], by1 : by2 + head.shape[-1]]
            # show_tensor(src)
            # show_tensor(head)
            # evaluate by convolution
            k: torch.Tensor = CustomConv2d(head, metric=metric)(src)
            # find the best location
            best_loc = torch.argmax(k)
            x, y = best_loc // k.shape[-1], best_loc % k.shape[-1]
            if bx1 != None and by1 != None:  # add bias
                x += bx1
                y += by1
            print(
                f"Best match score: {torch.max(k)}, location: {x.detach().cpu().numpy()}, {y.detach().cpu().numpy()}"
            )
        return x.detach().cpu().numpy(), y.detach().cpu().numpy()

    def replace_head(self, out_path: str, **fpn_kwargs):
        """
        Replace the head in the source image with the best-matched head from the head list.

        Args:
            out_path (str): Path to save the output images.
            **fpn_kwargs: Keyword arguments for the static_fpn method.

        Returns:
            None
        """
        rm_mkdir(out_path)
        # replace the head image into src image at (x, y)
        src = np.array(self.picture) / 255.0
        pbar = tqdm(total=len(self.heads))
        for i, head in enumerate(self.heads):
            # handles for variable head sizes
            self.ref_head = self.heads[i]
            x, y = self.static_fpn(**fpn_kwargs)
            mask = np.array(self.ref_head)[..., -1] / 255.0
            head = np.array(head) / 255.0
            dst = src.copy()
            dst[x : x + head.shape[0], y : y + head.shape[1], :] = alpha_blend(
                head,
                src[x : x + head.shape[0], y : y + head.shape[1], :],
                mask,
            )
            Image.fromarray((dst * 255.0).astype(np.uint8)).save(
                os.path.join(out_path, f"{i}.png")
            )
            pbar.update(1)
        pbar.close()


if __name__ == "__main__":
    heading = Heading("output_bg.png", "heads", kernel_idx=1)
    factor = 2
    layers = 4
    heading.replace_head(
        "longwu_bg",
        layers=layers,
        factor=factor,
        optim_range=[8, 4, 2],
        metric=partial(ssim, abs=True, exps=(1, 1, 2), consts=(1e-4, 3e-4, 1.5e-4)),
    )
