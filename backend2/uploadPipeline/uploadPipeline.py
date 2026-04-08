import os
from enum import Enum


class Video_Quality(Enum):
    Q480 = [854, 480]
    Q720 = [1280, 720]
    Q1080 = [1920, 1080]


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
