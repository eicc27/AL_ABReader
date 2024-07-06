import os
import re
import shutil

if __name__ == "__main__":
    path = r"C:\Users\chen\Documents\MuMu共享文件夹\alassetbundles\AssetBundles\cue"
    target_path = "voices/"
    if not os.path.exists(target_path):
        os.makedirs(target_path)
    else:
        for file in os.listdir(target_path):
            os.remove(os.path.join(target_path, file))
    for file in os.listdir(path):
        # find cv5.....
        if re.match(r"cv-5\d{4}\.b", file): # China, Japanese
            # copy to target_path
            shutil.copy(os.path.join(path, file), target_path)
            print(f"copy {file} to {target_path}")
    output_path = "voices_decoded"
    if not os.path.exists(output_path):
        os.makedirs(output_path)
    else:
        for file in os.listdir(output_path):
            os.remove(os.path.join(output_path, file))
    # call exe to decode
    os.system(f"BlhxCueDecoder.exe {target_path} {output_path}")