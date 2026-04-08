from concurrent.futures.thread import ThreadPoolExecutor
import logging
import shutil
import concurrent.futures
import datetime
import json
from threading import Event
import ffmpeg
from uploadPipeline.rabbitmq import VideoQueueManager, createChannel
from flask import (
    Blueprint,
)
import os

from uploadPipeline.uploadPipeline import (
    Video_Quality,
    create_master_playlist,
)
from uploadPipeline import mongo
import random
import string

video = Blueprint("video", __name__)
queue_manager = VideoQueueManager()
logger = logging.getLogger(__name__)


env = os.environ.get("FLASK_ENV")
stop_event = Event()


class VideoProcessingError(Exception):
    pass


def send_progress_update(
    user_id,
    base_name,
    status,
    progress,
    current_quality=None,
    total_qualities=None,
    completed_qualities=None,
    error=None,
    unique_name=None,
    message=None,
    **kwargs,
):
    progress_msg = {
        "user_id": user_id,
        "base_name": base_name,
        "status": status,
        "progress": progress,
        "timestamp": datetime.datetime.now().isoformat(),
        "current_quality": current_quality,
        "total_qualities": total_qualities,
        "completed_qualities": completed_qualities,
        "error": error,
        "unique_name": unique_name,
        "message": message,
        **kwargs,
    }

    queue_manager.push_status_updates(progress_msg)
    # sock_upload.emit("send_updates", progress_msg, room=f"userId_{user_id}")


def process_videos(original_path, video_folder, base_name, user_id):
    send_progress_update(
        user_id=user_id,
        base_name=base_name,
        status="processing_qualities",
        progress=5,
        message="Started processing",
    )

    total_quantites = len(Video_Quality)
    qualities = list(Video_Quality)

    probe = ffmpeg.probe(original_path)
    has_audio = any(stream["codec_type"] == "audio" for stream in probe["streams"])
    max_workers = min(3, total_quantites)

    def process_single_video(q):
        if stop_event.is_set():
            return {"quality": q.name, "success": False, "error": "Cancelled"}
        try:
            inp = ffmpeg.input(original_path)

            width, height = q.value[0], q.value[1]
            quality_path = os.path.join(video_folder, f"{q.name}@{base_name}")
            hls_folder = os.path.join(quality_path, "hls")
            os.makedirs(hls_folder, exist_ok=True)
            final_path = os.path.join(hls_folder, "stream.m3u8")
            segment_pattern = os.path.join(hls_folder, "segment_%03d.ts")

            v = inp.video.filter("scale", width, height)

            output_args = dict(
                vcodec="libx264",
                crf=30,
                video_bitrate="1200k",
                f="hls",
                hls_time=4,
                force_key_frames="expr:gte(t,n_forced*4)",
                hls_playlist_type="vod",
                hls_segment_filename=segment_pattern,
                hls_flags="independent_segments",
                movflags="+faststart",
                threads=max(1, os.cpu_count() // max_workers),
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
                out = ffmpeg.output(v, inp.audio, final_path, **output_args)
            else:
                out = ffmpeg.output(v, final_path, **output_args)

            out.run(
                overwrite_output=True,
                capture_stdout=True,
                capture_stderr=True,
                quiet=False if env == "dev" else True,
            )

            return {"quality": q.name, "success": True}

        except ffmpeg.Error as e:
            stop_event.set()
            return {"quality": q.name, "success": False, "error": str(e)}

    completed = 0
    with ThreadPoolExecutor(max_workers=max_workers) as e:
        futures = [e.submit(process_single_video, q) for q in qualities]

        for future in concurrent.futures.as_completed(futures):
            result = future.result()

            if not result["success"]:
                send_progress_update(
                    user_id=user_id,
                    base_name=base_name,
                    status="quality_failed",
                    progress=0,
                    error=result["error"],
                )

                for q in qualities:
                    quality_path = os.path.join(video_folder, f"{q.name}@{base_name}")
                    if os.path.exists(quality_path):
                        shutil.rmtree(quality_path, ignore_errors=True)

                raise VideoProcessingError(result["error"])

            completed += 1

            send_progress_update(
                user_id=user_id,
                base_name=base_name,
                status="quality_progress",
                progress=5 + int((completed / total_quantites) * 90),
                completed_quality=result["quality"],
                completed_count=completed,
                total_qualities=total_quantites,
            )

    send_progress_update(
        user_id=user_id,
        base_name=base_name,
        status="quality_processed",
        progress=100,
        completed_qualities=total_quantites,
        total_qualities=total_quantites,
    )


def upload(ch, method, properties, body):
    job_id = properties.message_id
    user_id = None
    base_name = None
    should_ack = True

    try:
        logger.info(f"[→] Processing job {job_id}")

        message_data = json.loads(body.decode())
        video_data = message_data["data"]
        user_id = video_data.get("user_id")
        base_name = video_data.get("base_name")
        video_path = video_data.get("video_path")

        if not all([user_id, base_name, video_path]):
            logger.error(" [x] Missing required fields in message")
            should_ack = True
            return

        send_progress_update(
            user_id=user_id,
            base_name=base_name,
            status="processing_started",
            progress=5,
            message="Processing started - initializing video conversion...",
        )
        video_folder = os.path.dirname(video_path)
        original_path = video_path

        try:
            process_videos(
                original_path=original_path,
                video_folder=video_folder,
                base_name=base_name,
                user_id=user_id,
            )
        except VideoProcessingError:
            return
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return
        unique_name = "".join(
            random.choice(string.ascii_letters + string.digits) for _ in range(8)
        )

        create_master_playlist(unique_name, video_folder)

        video_doc = {
            "video_title": video_data.get("video_title"),
            "video_desc": video_data.get("video_desc"),
            "file_name": base_name,
            "thumbnail_name": os.path.basename(video_data.get("thumbnail_path", "")),
            "user_id": user_id,
            "unique_name": unique_name,
        }
        try:
            mongo.db.videos.insert_one(video_doc)
        except Exception as e:
            logger.error(e)

        send_progress_update(
            user_id=user_id,
            base_name=base_name,
            status="completed",
            progress=100,
            unique_name=unique_name,
            message="Video processing completed successfully!",
        )

        logger.info(
            f" [x] Successfully processed video: {unique_name} for user: {user_id}"
        )

    except json.JSONDecodeError as e:
        logger.error(f" [x] JSON decode error: {e}")
    except Exception as e:
        logger.error(f" [x] Unexpected error in upload processing: {e}")
        should_ack = True

    finally:
        if should_ack:
            ch.basic_ack(delivery_tag=method.delivery_tag)
        logger.info(f"[✓] Job {job_id} acknowledged")


def pop_queue():
    channel = createChannel()
    try:
        channel.basic_qos(prefetch_count=1)
        channel.basic_consume(
            queue="upload", auto_ack=False, on_message_callback=upload
        )
        logger.info(" [*] Video worker ready - waiting for jobs")
        channel.start_consuming()
    except KeyboardInterrupt:
        logger.error("\n[!] Shutting down worker...")
        channel.stop_consuming()

    finally:
        if channel.is_open:
            channel.close()
        logger.info("[!] Worker stopped")
