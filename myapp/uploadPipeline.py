import ffmpeg
from flask import current_app
import os
from enum import Enum


class Video_Quality(Enum):
    Q480 = [854, 480]
    Q720 = [1280, 720]
    Q1080 = [1920, 1080]


def get_chunk(file_path, byte1=None, byte2=None):
    file_size = os.stat(file_path).st_size
    start = 0 if byte1 is None else byte1
    end = file_size - 1 if byte2 is None else byte2
    length = end - start + 1

    with open(file_path, "rb") as f:
        f.seek(start)
        chunk = f.read(length)

    return chunk, start, end, file_size


def get_file_path(
    filename,
    quality,
):
    upload_folder = current_app.config["UPLOAD_FOLDER_VIDEO"]
    return os.path.join(upload_folder, filename, f"Q{quality}@{filename}", "hls")


def get_video_path(
    filename,
):
    upload_folder = current_app.config["UPLOAD_FOLDER_VIDEO"]
    return os.path.join(upload_folder, filename)


def resize_video(input_path, output_path, width, height, show_logs):
    segment_dir = os.path.dirname(output_path)
    os.makedirs(segment_dir, exist_ok=True)
    segment_pattern = os.path.join(segment_dir, "segment_%03d.ts")

    inp = ffmpeg.input(input_path)
    v = inp.video.filter("scale", width, height)
    a = inp.audio

    out = ffmpeg.output(
        v,
        a,
        output_path,
        vcodec="libx264",
        crf=30,
        video_bitrate="1200k",
        acodec="aac",
        audio_bitrate="128k",
        ac=2,
        ar=48000,
        f="hls",
        hls_time=4,
        hls_playlist_type="vod",
        hls_segment_filename=segment_pattern,
        hls_flags="independent_segments",
        movflags="+faststart",
        threads=15,
    )
    out = out.overwrite_output()

    if show_logs:
        out.run()
    else:
        out.run(quiet=True, capture_stdout=True, capture_stderr=True)
    print(f"Video resized and saved as HLS at: {output_path}")


def get_bitrate_for_quality(quality: Video_Quality) -> int:
    bitrate_map = {
        Video_Quality.Q480: 1000,
        Video_Quality.Q720: 2500,
        Video_Quality.Q1080: 5000,
    }
    return bitrate_map[quality]


def create_master_playlist(unique_name, output_dir: str):
    master_content = "#EXTM3U\n#EXT-X-VERSION:3\n\n"

    for quality in Video_Quality:
        width, height = quality.value
        bitrate = get_bitrate_for_quality(quality)

        quality_url = f"/watch/{unique_name}/{quality.name}.m3u8"

        total_bandwidth = (bitrate + 128) * 1000
        master_content += f'#EXT-X-STREAM-INF:BANDWIDTH={total_bandwidth},RESOLUTION={width}x{height},CODECS="avc1.64001f,mp4a.40.2"\n'
        master_content += f"{quality_url}\n\n"

    master_path = os.path.join(output_dir, "master.m3u8")
    with open(master_path, "w") as f:
        f.write(master_content)

    return master_path
