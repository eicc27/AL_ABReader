from pydub import AudioSegment
import os

def segment_audio(input_file: str, output_dir: str, segment_length: float):
    """
    Segment audio in milliseconds and pad the last segment if it's shorter than the segment length.
    """
    # Ensure the output directory exists
    if not os.path.exists(output_dir):
        os.mkdir(output_dir)

    # Load the audio file
    audio: AudioSegment = AudioSegment.from_wav(input_file)
    total_length = len(audio)
    segment_length_ms = int(segment_length * 1000)  # Convert seconds to milliseconds
    # Process each segment
    for i in range(0, total_length, segment_length_ms):
        start = i
        end = i + segment_length_ms
        chunk = audio[start:end]
        
        # Check if the current chunk is the last and if it's shorter than the desired segment length
        if len(chunk) < segment_length_ms:
            # Calculate the needed padding length
            padding_length = segment_length_ms - len(chunk)
            # Create a silence segment
            silence = AudioSegment.silent(duration=padding_length, frame_rate=audio.frame_rate,)
            # Append silence to the chunk
            chunk += silence

        # Export the chunk
        chunk.export(os.path.join(output_dir, f"{i//segment_length_ms}.wav"), format="wav")

if __name__ == "__main__":
    segment_audio("get.wav", "get_segs", 5.12)  # Now expects segment length in seconds
