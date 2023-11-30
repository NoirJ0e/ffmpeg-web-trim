from flask import Flask, request, jsonify, send_from_directory
from flask_jwt_extended import (
    JWTManager,
    create_access_token,
    get_jwt_identity,
    jwt_required,
)
from werkzeug.utils import secure_filename
import logging
import database
import os
from ffmpeg import ffmpeg_process_video, create_unique_file
import pywebpush

logging.basicConfig(level=logging.INFO)

UPLOAD_FOLDER = "./resources/input"
OUTPUT_FOLDER = "./resources/output"
RES_FOLDER = "./resources"

app = Flask(__name__)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["OUTPUT_FOLDER"] = OUTPUT_FOLDER
app.config["RES_FOLDER"] = RES_FOLDER
app.config[
    "JWT_SECRET_KEY"
] = "7xquF94FFn9mct3QKtxK8yNRqXZMxRpPnoaytp2ohhVRgA3G32fta8YdcYyQy4a6GEpNEJFTAuAiTmVnFwyMTj6bXgakWVGCNqHu"

jwt = JWTManager(app)

# Initialize the project
database.db_initialize()


def send_push_notificatio(msg):
    logging.info("send_push_notificatio(): Sending push notification")
    try:
        pywebpush.webpush(
            data=msg,
        )
    except Exception as e:
        logging.error(f"send_push_notificatio(): Error sending push notification: {e}")


@app.route("/register", methods=["POST"])
def register_user():
    """
    Register a new user.

    This function handles the registration of a new user by receiving a POST request with user data.
    It checks if the user already exists in the database and inserts the user if not.
    Returns a JSON response indicating the success or failure of the registration.

    :return: JSON response with success or error message
    """
    logging.info("register_user(): Registering user")
    try:
        data = request.get_json()
        user_email = data.get("email")
        hashed_password = data.get("hashed_password")
        conn = database.db_get_connection()
        c = conn.cursor()
        if not database.db_check_user(user_email, hashed_password):
            c.execute(
                "INSERT INTO users (email, hashed_password) VALUES (?, ?)",
                (user_email, hashed_password),
            )
            conn.commit()
            return jsonify({"success": True}), 200
        else:
            return jsonify({"error": "User already exists"}), 400
    finally:
        conn.close()


@app.route("/user", methods=["POST"])
def authenticate_user():
    """
    Authenticates a user based on the provided email and hashed password.

    Returns:
        If the user is authenticated successfully, returns a JSON response with a success message and an access token.
        If the email or password is incorrect, returns a JSON response with an error message.
        If there is an internal server error, returns a JSON response with an error message.
    """
    try:
        data = request.get_json()
        user_email = data.get("email")
        hashed_password = data.get("hashed_password")
        conn = database.db_get_connection()
        user = database.db_check_user(user_email, hashed_password)
        logging.info("authenticate_user(): Authenticating user")
        if user:
            access_token = create_access_token(identity=user_email)
            logging.info("authenticate_user(): User authenticated successfully")
            return jsonify({"success": True, "access_token": access_token}), 200
        else:
            logging.error("authenticate_user(): Email or Password Incorrect")
            return jsonify({"error": "Email or Password Incorrect"}), 400
    except Exception as e:
        logging.error(f"authenticate_user(): Error: {e}")
        return jsonify({"error": "Internal Server Error"}), 500
    finally:
        conn.close()


@app.route("/user/upload", methods=["POST"])
@jwt_required()
def upload_file():
    """
    Uploads a file to the server.

    Returns:
        A JSON response indicating the success or failure of the file upload.
    """
    logging.info("upload_file(): Uploading file")
    try:
        if "file" not in request.files:
            return jsonify({"success": False}), 400
        file = request.files["file"]
        if file.filename == "":
            logging.error("upload_file(): No selected file")
            return jsonify({"error": "No selected file"}), 400
        else:
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
            file.save(file_path)
            logging.info(f"upload_file(): File {filename} uploaded successfully")
            return jsonify({"message": "File uploaded successfully"}), 200

    except Exception as e:
        logging.error(f"upload_file(): {e}")


@app.route("/user/edit_video", methods=["POST"])
@jwt_required()
def edit_video():
    """
    Endpoint for editing a video.

    This endpoint receives a POST request with the necessary data to edit a video.
    It retrieves the user's email from the JWT token and gets the corresponding user ID from the database.
    If the user is not found, it returns a 404 error.
    The request payload should contain the source file path, start time, and end time for the video editing.
    It creates a unique output file path and adds the video editing operation to the database.
    Then, it calls the `ffmpeg_process_video` function to process the video using the provided parameters.
    After the video processing is complete, it sends a push notification to the user.
    Finally, it updates the database to mark the operation as finished and returns the edited video URL.

    Returns:
        A JSON response with the success status and the edited video URL.
        If an error occurs, it returns a JSON response with the corresponding error message.
    """
    try:
        user_email = get_jwt_identity()
        user_id = database.db_get_user_id(user_email)
        if user_id is None:
            return jsonify({"error": "User not found"}), 404

        data = request.get_json()
        src_file_path = data.get("src_file_path")
        start_time = data.get("start_time")
        end_time = data.get("end_time")

        output_file = create_unique_file(parent_folder="./output")

        database.db_add_operation(
            user_id, src_file_path, start_time, end_time, output_file
        )

        # Process the video (this function needs to be implemented)
        ffmpeg_process_video(
            src_file_path, start_time, end_time, app.config["RES_FOLDER"], output_file
        )

        send_push_notificatio("Your Video is ready to download")
        database.db_set_operation_finished(user_email, output_file)
        return jsonify({"success": True, "edited_video_url": output_file}), 200

    except Exception as e:
        logging.error(f"edit_video(): {e}")
        return jsonify({"error": "Internal Server Error"}), 500


@app.route("/user/download_video", methods=["GET"])
@jwt_required()
def download_video():
    """
    Download a processed video file for a user.

    Returns:
        If the video file is found, it is returned as an attachment for download.
        If the video file is not found, a JSON response with an error message and status code 404 is returned.
        If any other error occurs, a JSON response with an error message and status code 500 is returned.
    """
    try:
        user_email = get_jwt_identity()
        operation_id = request.args.get("operation_id")
        download_file = database.db_get_processed_video(user_email, operation_id)
        if not download_file:
            return jsonify({"error": "Video not found"}), 404

        # Assuming processed_video_url is a relative path from the resources directory
        resources_dir = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "resources"
        )
        logging.info(f"download_video(): {resources_dir}")
        full_path = os.path.join(resources_dir, download_file.strip("./"))
        logging.info(f"download_video(): {full_path}")

        directory = os.path.dirname(full_path)
        filename = os.path.basename(full_path)

        return send_from_directory(directory, filename, as_attachment=True)

    except Exception as e:
        logging.error(f"download_video(): {e}")
        return jsonify({"error": "Internal Server Error"}), 500
