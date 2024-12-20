# AL AssetBundles Reader

## ABReader

This folder clones part of the functions from [Perfare's Asset Studio](http://github.com/perfare/AssetStudio). To be more specific, the project only needs Texture2D and Mesh decoding functionalities. The Unity version current Azur Lane's using is `2020.3.48f1`. By anchoring this version, many compatibility branches Asset Studio checks are skipped in this implementation. Also, this project ports `ETC2-RGBA8` format decompression from C ([etc.cpp](https://github.com/Perfare/AssetStudio/blob/master/Texture2DDecoderNative/etc.cpp)) to python with almostly irrecognizable performance loss.

It is focused at:

- Read the binary files from `paintings/` and `paintingface/` folders.
- Decode Texture2D and Mesh files with experienced subset of conventions: uncompressed RGBA8 and ETC2-compressed RGBA8.

## BSRGAN

The [**Deep Blind Image Super-Resolution**](https://github.com/cszn/BSRGAN) network implemented by *Kai Zhang, Jingyun Liang, Luc Van Gool and Radu Timofte*. The project truncates exmaple data and utilizes only BSRGAN and BSRGANx2 to enhance different shapes of images. The project also add an interface to integrate BSRGAN process to batch image processing pipeline. Like its predecessor [ESRGAN](https://arxiv.org/abs/1809.00219), it leverages RRDB (Residual-in-Residual Dense Block) to enhance the image quality.

### Performance specs
BSRGANx2 can enhance the whole image to nearly 8K, and BSRGAN to 4K in a single RTX 4090 without much GRAM swapping. For a single character with ~10 face replications, an RTX 4090 can do the job in an accepatble time span.

## ImageDecoders

It is mainly responsible for sealing the 2d texture with its coupled mesh object file. It also has a static-FPN to intelligently and performantly seal the "heads"(or "faces") by searching(convoluting) over the source image to find a most similar location for the head.

### Texture2D Sealing

Azur Lane uses a simple texture 2d sealing method by specifying flipped rectangles with 2 triangle face specs in the mesh object file. e.g.:

```
f 0/0/0 1/1/1 2/2/2
f 2/2/2 3/3/3 0/0/0
```

This specifies a `0-1-2-3` vertice-indexed rectangle.

### Static Pyramidal *Heading*

The baseline of the heading method is given a head, finding the most similar part of the image to the head. By leveraging the concept of convolution, the project features different loss functions to quantize the similarity index.

The project has 3 available loss fns:
1. **MSE** (Measn Squared Error) 
2. **PSNR** (Peak Signal-Noise Ratio)
3. **SSIM** (Structural Similarity Index)

The SSIM implementation is derived from Zhou Wang, A. C. Bovik, H. R. Sheikh and E. P. Simoncelli, ["Image quality assessment: from error visibility to structural similarity,"](https://ieeexplore.ieee.org/document/1284395) in *IEEE Transactions on Image Processing*, vol. 13, no. 4, pp. 600-612, April 2004, doi: 10.1109/TIP.2003.819861.

In this implementation, a pyramidal template matching algorithm is used to narrow down the searching area by first performing a full error conv on low-resolution images. The best location is then upscaled and passed to the higher resolution layers, narrowing down the searching range from each upscaling to `2*upscale_rate`. This provides a huge acceleration over simply performing error conv on the original image, which is 1080p or even 2K (**2~3s on CPU** *vs.* **~10-15mins on a single RTX 4090**).
