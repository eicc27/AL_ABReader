import cv2
from PIL import Image
import os
import ffmpeg
import torch
from tqdm import tqdm
from torchvision import transforms as T


def extract_frames(video_path, output_folder):
    # Create the output folder if it doesn't exist
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    # Capture the video from the given path
    cap = cv2.VideoCapture(video_path)
    frame_count = 0
    fps = cap.get(cv2.CAP_PROP_FPS)
    print("FPS: ", fps)
    # while True:
    #     # Read the next frame from the video
    #     ret, frame = cap.read()
    #     if not ret:
    #         break

    #     # Convert the frame to RGB (OpenCV uses BGR by default)
    #     frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    #     # Convert the frame to a PIL Image
    #     image = Image.fromarray(frame_rgb)

    #     # Save the frame as a PNG file
    #     output_file = os.path.join(output_folder, f"frame_{frame_count:04d}.png")
    #     image.save(output_file)

    #     frame_count += 1

    # Release the video capture object
    cap.release()


def create_video_from_frames(
    input_folder,
    output_video_path,
    fps=24,
):
    # Get list of all image files in the folder
    image_files = [f for f in os.listdir(input_folder) if f.endswith(".png")]
    image_files.sort()  # Ensure files are in the correct order

    # Read the first image to get the size
    first_image_path = os.path.join(input_folder, image_files[0])
    frame = cv2.imread(first_image_path)
    height, width, layers = frame.shape

    # Define the codec and create VideoWriter object
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")  # Codec for .mp4 file
    video = cv2.VideoWriter(output_video_path, fourcc, fps, (width, height))

    for image_file in image_files:
        image_path = os.path.join(input_folder, image_file)
        frame = cv2.imread(image_path)
        video.write(frame)

    # Release the video writer object
    video.release()


def encode_images_to_video(
    image_pattern="testsets/generated_2_results_x4/%04d_BSRGAN.png",
    output_file="output.mp4",
    fps=144,
    width=7680,
    height=4320,
):
    input_options = {
        "framerate": fps,
        # 'pattern_type': 'glob',
        'hwaccel': 'cuda',
        # 'hwaccel_output_format': 'cuda',
    }

    output_options = {
        "vcodec": "hevc_nvenc",  # Use NVENC for hardware accelerated encoding
        "pix_fmt": "yuv422p",
        "preset": "default",
        # "tune": "psnr",
        "s": f"{width}x{height}",
    }

    # Create the ffmpeg input stream
    input_stream = ffmpeg.input(image_pattern, **input_options)

    # Create the ffmpeg output stream
    output_stream = ffmpeg.output(input_stream, output_file, **output_options)

    # Run the ffmpeg command
    ffmpeg.run(output_stream)


def reshape(file, output_folder, width=3840, height=2160):
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    img = Image.open(file)
    # Apply the transformation
    img_tensor = T.ToTensor()(img).unsqueeze(0).to(device)  # Add batch dimension and move to GPU
    resized_img_tensor = torch.nn.functional.interpolate(img_tensor, size=(height, width), mode='bilinear', antialias=True)
    resized_img = T.ToPILImage()(resized_img_tensor.squeeze(0).cpu())  # Remove batch dimension and move to CPU
    resized_img.save(os.path.join(output_folder, os.path.basename(file)))


if __name__ == "__main__":
    # extract_frames("test.mp4", "testsets/Frames")
    # create_video_from_frames("testsets/generated_2_results_x4", "output.mp4", fps=144)
    # from concurrent.futures import ThreadPoolExecutor
    # pool = ThreadPoolExecutor(max_workers=4)
    # base_path = "testsets/generated_2_results_x4"
    # files = os.listdir(base_path)
    # for file in files:
    #     pool.submit(reshape, os.path.join(base_path, file), "4K")
    # pool.shutdown()
    create_video_from_frames("4K", "output.mp4", fps=144)
    pass
