# import requests
import subprocess
import os
import logging
import uuid
import database
import api

logging.basicConfig(level=logging.INFO)


# Incase multiple user operate the same time, unique file name would be better than a static file name
def create_unique_file(prefix="", extension=".mp4", parent_folder=""):
    """
    Create a unique file name with the given prefix, extension, and parent folder.

    Args:
        prefix (str, optional): Prefix for the file name. Defaults to "".
        extension (str, optional): File extension. Defaults to ".mp4".
        parent_folder (str, optional): Parent folder path. Defaults to "".

    Returns:
        str: The unique file name.

    Raises:
        Exception: If there is an error creating the unique file name.
    """
    try:
        identifier = str(uuid.uuid4())
        result_path = os.path.join(parent_folder, f"{prefix}{identifier}{extension}")

        logging.info(
            f"create_unique_file_name(): Created unique file name {result_path}"
        )
        return f"{result_path}"

    except Exception as e:
        logging.error(
            f"create_unique_file_name(): Error creating unique file name: {e}"
        )


# def download_video(url, output_file):
#     """
#     Downloads a video from the given URL and saves it to the specified output file.

#     Args:
#         url (str): The URL of the video to download.
#         output_file (str): The path to save the downloaded video.

#     Raises:
#         requests.exceptions.HTTPError: If there is an error in the HTTP request.
#         Exception: If there is an error downloading the video.

#     Returns:
#         None
#     """
#     try:
#         response = requests.get(url, stream=True)
#         response.raise_for_status()  # handle error response
#         with open(output_file, "wb") as file:
#             for chunk in response.iter_content(chunk_size=1024):
#                 file.write(chunk)
#         logging.info(f"download_video(): Video download to {output_file} successfully")

#     except Exception as e:
#         logging.error(f"download_video(): Error downloading video: {e}")


def ffmpeg_process_video(src_file, start_time, end_time, resouce_folder, output_file, user_email):
    """
    Process a video file using FFmpeg.
    Set the operation status to when the edit is done to finished in the database.

    Args:
        src_file (str): The source video file path.
        start_time (str): The start time of the video trim (in HH:MM:SS format).
        end_time (str): The end time of the video trim (in HH:MM:SS format).
        resouce_folder (str): The folder path where the FFmpeg command will be executed.
        output_file (str): The output file path for the processed video.
        user_email (str): The email address of the user.

    Raises:
        Exception: If there is an error processing the video.

    """
    try:
        input_file = f"./input/{src_file}"
        command = f"ffmpeg -hide_banner -loglevel error -i {input_file} -ss {start_time} -to {end_time} -c copy {output_file}"

        logging.info(f"process_video(): Running command {command}")
        subprocess.run(command, shell=True, cwd=resouce_folder)

        subscription_info = database.db_get_subscription_info(user_email)
        if subscription_info.strip('"') == "None":
            subscription_info = None

        if subscription_info is not None:
            api.send_push_notificatio(subscription_info, "Your Video is ready to download")

        database.db_set_operation_finished(user_email, output_file)

        logging.info("process_video(): Video processed successfully")
    except Exception as e:
        logging.error(f"process_video(): Error processing video: {e}")
    finally:
        # Do not store the original video for better privacy concern
        if os.path.exists(src_file):
            os.remove(src_file)
