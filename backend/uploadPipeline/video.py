import concurrent.futures
import eventlet
import datetime
import json
from uploadPipeline.rabbitmq import VideoQueueManager, createChannel
from flask import (
    Blueprint,
)
import os

from uploadPipeline.uploadPipeline import (
    Video_Quality,
    create_master_playlist,
    resize_video,
)
from uploadPipeline import mongo
import random
import string

video = Blueprint("video", __name__)
queue_manager = VideoQueueManager()


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


def process_single_video(
    original_path,
    final_path,
    quality,
    width,
    height,
    user_id,
    base_name,
    quality_index,
    total_qualities,
):
    base_progress = 5 + (quality_index * 85 // total_qualities)
    send_progress_update(
        user_id=user_id,
        base_name=base_name,
        status="processing_quality",
        progress=base_progress,
        current_quality=quality.name,
        message=f"Starting {quality.name} quality processing",
    )

    resize_video(original_path, final_path, width, height)
    return True


def process_videos(original_path, video_folder, base_name, user_id):
    futures = []
    completed_count = 0
    total_qualities = len(Video_Quality)

    with concurrent.futures.ThreadPoolExecutor(max_workers=total_qualities) as executor:
        for idx, quality in enumerate(Video_Quality):
            quality_path = os.path.join(video_folder, f"{quality.name}@{base_name}")
            hls_folder = os.path.join(quality_path, "hls")
            os.makedirs(hls_folder, exist_ok=True)
            final_path = os.path.join(hls_folder, "stream.m3u8")

            future = executor.submit(
                process_single_video,
                original_path=original_path,
                final_path=final_path,
                quality=quality,
                width=quality.value[0],
                height=quality.value[1],
                user_id=user_id,
                base_name=base_name,
                quality_index=idx,
                total_qualities=total_qualities,
            )
            futures.append((future, quality_path, quality))
        for future, quality_path, quality in futures:
            try:
                future.result(3600)
                completed_count += 1

                progress = 5 + int((completed_count / total_qualities) * 85)

                print(f"{quality.name}, progress = {progress}")
                send_progress_update(
                    user_id=user_id,
                    base_name=base_name,
                    status="quality_processed",
                    progress=progress,
                    current_quality=quality.name,
                    completed_qualities=completed_count,
                    total_qualities=total_qualities,
                )

            except concurrent.futures.TimeoutError:
                print(f"Timeout processing quality: {quality.name}")
                send_progress_update(
                    user_id=user_id,
                    base_name=base_name,
                    status="quality_failed",
                    progress=5 + int((completed_count / total_qualities) * 85),
                    current_quality=quality.name,
                    error=f"Timeout processing {quality.name}",
                )
                return True
            except Exception as e:
                print(f"Error processing video quality {quality.name}: {e}")
                send_progress_update(
                    user_id=user_id,
                    base_name=base_name,
                    status="quality_failed",
                    progress=5 + int((completed_count / total_qualities) * 85),
                    current_quality=quality.name,
                    error=str(e),
                )

                for f, quality_path, _ in futures:
                    f.cancel()
                    if os.path.exists(quality_path):
                        try:
                            import shutil

                            shutil.rmtree(quality_path)
                        except Exception as e:
                            print(f"Error cleaning up quality path {quality_path}: {e}")
                return True
    return False


def upload(ch, method, properties, body):
    job_id = properties.message_id
    user_id = None
    base_name = None
    should_ack = True

    try:
        print(f"[→] Processing job {job_id}")

        message_data = json.loads(body.decode())
        video_data = message_data["data"]
        user_id = video_data.get("user_id")
        base_name = video_data.get("base_name")
        video_path = video_data.get("video_path")

        if not all([user_id, base_name, video_path]):
            print(" [x] Missing required fields in message")
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

        processing_failed = process_videos(
            original_path=original_path,
            video_folder=video_folder,
            base_name=base_name,
            user_id=user_id,
        )
        if os.path.exists(original_path):
            os.remove(original_path)

        if processing_failed:
            send_progress_update(
                user_id=user_id,
                base_name=base_name,
                status="processing_failed",
                progress=100,
                current_quality=None,
                total_qualities=len(Video_Quality),
            )
            print(" [x] Video processing failed")
            should_ack = True
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
            print(e)

        send_progress_update(
            user_id=user_id,
            base_name=base_name,
            status="completed",
            progress=100,
            unique_name=unique_name,
            message="Video processing completed successfully!",
        )

        eventlet.sleep(1)
        print(f" [x] Successfully processed video: {unique_name} for user: {user_id}")

    except json.JSONDecodeError as e:
        print(f" [x] JSON decode error: {e}")
    except Exception as e:
        print(f" [x] Unexpected error in upload processing: {e}")
        should_ack = True

    finally:
        if should_ack:
            ch.basic_ack(delivery_tag=method.delivery_tag)
        print(f"[✓] Job {job_id} acknowledged")


def pop_queue():
    channel = createChannel()
    try:
        channel.basic_qos(prefetch_count=1)
        channel.basic_consume(
            queue="upload", auto_ack=False, on_message_callback=upload
        )
        print(" [*] Video worker ready - waiting for jobs")
        channel.start_consuming()
    except KeyboardInterrupt:
        print("\n[!] Shutting down worker...")
        channel.stop_consuming()

    except Exception as e:
        print(f"[✗] Queue consumption error: {e}")

    finally:
        if channel.is_open:
            channel.close()
        print("[!] Worker stopped")
