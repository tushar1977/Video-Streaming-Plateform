import ffmpeg
from flask import current_app
import os
from enum import Enum


class Video_Quality(Enum):
    Q480 = [854, 480]
    Q720 = [1280, 720]
    Q1080 = [1920, 1080]


def resize_video(input_path, output_path, width, height):
    segment_dir = os.path.dirname(output_path)
    os.makedirs(segment_dir, exist_ok=True)
    segment_pattern = os.path.join(segment_dir, "segment_%03d.ts")

    probe = ffmpeg.probe(input_path)
    has_audio = any(stream["codec_type"] == "audio" for stream in probe["streams"])

    inp = ffmpeg.input(input_path)
    v = inp.video.filter("scale", width, height)

    output_args = dict(
        vcodec="libx264",
        crf=30,
        video_bitrate="1200k",
        f="hls",
        hls_time=4,
        hls_playlist_type="vod",
        hls_segment_filename=segment_pattern,
        hls_flags="independent_segments",
        movflags="+faststart",
        threads=15,
    )

    if has_audio:
        output_args.update(
            {
                "acodec": "aac",
                "audio_bitrate": "128k",
                "ac": 2,
                "ar": 48000,
            }
        )
        out = ffmpeg.output(v, inp.audio, output_path, **output_args)
    else:
        out = ffmpeg.output(v, output_path, **output_args)

    out.run(overwrite_output=True, capture_stdout=True, capture_stderr=True, quiet=True)


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
