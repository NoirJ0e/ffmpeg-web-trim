import subprocess
import requests
from datetime import datetime
import os
import logging

logging.basicConfig(level=logging.INFO)


# Incase multiple user operate the same time, unique file name would be better than a static file name
def create_unique_file_name(prefix="", extension=".mp4"):
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        logging.info(
            f"create_unique_file_name(): Created unique file name {timestamp}{extension}"
        )
        return f"{prefix}{timestamp}{extension}"

    except Exception as e:
        logging.error(
            f"create_unique_file_name(): Error creating unique file name: {e}"
        )


def download_video(url, output_file):
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()  # handle error response
        with open(output_file, "wb") as file:
            for chunk in response.iter_content(chunk_size=1024):
                file.write(chunk)
        logging.info(f"download_video(): Video download to {output_file} successfully")

    except Exception as e:
        logging.error(f"download_video(): Error downloading video: {e}")


def ffmpeg_process_video(src_file, start_time, end_time, resouce_folder):
    try:
        output_folder = "./output"
        input_file = f"./input/{src_file}"
        # TODO: Path is incorrect right now, maybe use absolute path or full relative path would fix this
        output_file = os.path.join(
            output_folder, create_unique_file_name(prefix="output_video_")
        )
        command = f"ffmpeg -i {input_file} -ss {start_time} -to {end_time} -c copy {output_file}"
        logging.info(f"process_video(): Running command {command}")
        subprocess.run(command, shell=True, cwd=resouce_folder)
        logging.info("process_video(): Video processed successfully")
        return output_file
    except Exception as e:
        logging.error(f"process_video(): Error processing video: {e}")
    finally:
        # Do not store the orignal video for better privacy concern
        if os.path.exists(src_file):
            os.remove(src_file)
