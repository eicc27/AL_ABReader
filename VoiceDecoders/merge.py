from pydub import AudioSegment
import os

def merge_audios(input_path: str, output_path: str, segment: int = 5120):
    files = os.listdir(input_path)
    files = sorted(files, key=lambda x: int(x.split('.')[0]))
    result = AudioSegment.empty()
    for file in files:
        file = os.path.join(input_path, file)
        audio = AudioSegment.from_wav(file)[:segment]
        result += audio
    result.export(output_path, format="wav")

if __name__ == "__main__":
    merge_audios('get_segs_sr', 'get_sr.wav')