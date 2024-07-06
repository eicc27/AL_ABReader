import numpy as np
from PIL import Image
import torch


def alpha_blend(
    source: np.ndarray, target: np.ndarray, alpha: np.ndarray, absolute=False
):
    """
    Blends the source image into the target image based on the alpha mask.
    Typically, the alpha comes from target image, and is masked against source image.

    Args:
    source (np.ndarray): The source image array (H x W x C).
    target (np.ndarray): The target image array (H x W x C).
    alpha (np.ndarray): The alpha mask array (H x W), values between 0 and 1.

    Returns:
    np.ndarray: Blended image array.
    """
    # Ensure alpha is correctly shaped for broadcasting
    if alpha.ndim == 2:
        alpha = alpha[:, :, np.newaxis]
    if absolute:
        # turn all non-1 alpha to 0
        alpha = (alpha == 1.0).astype(np.float32)
    inverse_alpha = 1 - alpha

    # Perform the alpha blending
    blended = alpha * source + inverse_alpha * target

    return blended


def alpha_blend_torch(
    source: torch.Tensor, target: torch.Tensor, alpha: torch.Tensor, absolute=False
):
    """
    Blends the source image into the target image based on the alpha mask using PyTorch.

    Args:
    source (torch.Tensor): The source image tensor (B x C x H x W).
    target (torch.Tensor): The target image tensor (B x C x H x W).
    alpha (torch.Tensor): The alpha mask tensor (B x 1 x H x W), values between 0 and 1.

    Returns:
    torch.Tensor: Blended image tensor.
    """
    # print(source.shape, target.shape, alpha.shape)
    # Ensure alpha is correctly shaped for broadcasting
    if alpha.dim() == 3:
        alpha = alpha.unsqueeze(1)  # Makes alpha (B x 1 x H x W) for broadcasting

    if absolute:
        # Turn all non-1 alpha values to 0
        alpha = (alpha == 1.0).float()

    inverse_alpha = 1 - alpha

    # Perform the alpha blending
    blended = alpha * source + inverse_alpha * target

    return blended


def fill(img: np.ndarray, color: np.ndarray):
    """
    Fills the transparent area of an image with a color.
    """
    if img.shape[-1] == 3:
        return img
    alpha = img[..., 3]
    color = np.array(color).reshape(1, 1, 3)
    color = np.tile(color, (img.shape[0], img.shape[1], 1))
    color = np.concatenate([color, np.ones_like(color[..., :1])], axis=-1)
    return alpha_blend(img, color, alpha)


if __name__ == "__main__":
    sr_ratio = 2
    lr = Image.open("longwu_n/0.png")
    # Image.fromarray(
    #     (fill(np.array(lr) / 255.0, [1, 1, 1]) * 255.0).astype(np.uint8)
    # ).save("0_fill_white.png")
    sr = Image.open("0_fill_white_BSRGAN.png")
    lr = lr.resize(
        (sr.size[0], sr.size[1]),
        resample=Image.BICUBIC,
    )
    # alpha blend lr and sr
    lr = np.array(lr) / 255.0
    sr = np.array(sr) / 255.0
    # extend sr's dim(alpha) if sr has only 3 channels
    if sr.shape[-1] == 3:
        sr = np.concatenate([sr, np.ones_like(sr[..., :1])], axis=-1)
    print(lr.shape, sr.shape)
    alpha = lr[..., 3]
    blended = alpha_blend(sr, lr, alpha, absolute=True)
    Image.fromarray((blended * 255.0).astype(np.uint8)).save("0_alpha_blend_src.png")
