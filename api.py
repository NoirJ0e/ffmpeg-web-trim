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
from ffmpeg import ffmpeg_process_video

logging.basicConfig(level=logging.INFO)

app = Flask(__name__)
UPLOAD_FOLDER = "./resources/upload"
OUTPUT_FOLDER = "./resources/output"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["OUTPUT_FOLDER"] = OUTPUT_FOLDER
app.config[
    "JWT_SECRET_KEY"
] = "7xquF94FFn9mct3QKtxK8yNRqXZMxRpPnoaytp2ohhVRgA3G32fta8YdcYyQy4a6GEpNEJFTAuAiTmVnFwyMTj6bXgakWVGCNqHu"
jwt = JWTManager(app)

database.db_initialize()


@app.route("/register", methods=["POST"])
def register_user():
    try:
        data = request.get_json()
        user_email = data.get("email")
        hashed_password = data.get("hashed_password")
        conn = database.db_get_connection()
        c = conn.cursor()
        if database.db_check_user(user_email, hashed_password):
            return jsonify({"error": "User already exists"}), 400
        else:
            c.execute(
                "INSERT INTO users (email, hashed_password) VALUES (?, ?)",
                (user_email, hashed_password),
            )
            conn.commit()
            return jsonify({"success": True}), 200
    finally:
        conn.close()


@app.route("/user", methods=["POST"])
def authenticate_user():
    try:
        data = request.get_json()
        user_email = data.get("email")
        hashed_password = data.get("hashed_password")
        conn = database.db_get_connection()
        user = database.db_check_user(user_email, hashed_password)
        if user:
            access_token = create_access_token(identity=user_email)
            return jsonify({"success": True, "access_token": access_token}), 200
        else:
            return jsonify({"error": "Email or Password Incorrect"}), 400
    except Exception as e:
        logging.error(f"authenticate_user(): {e}")
        return jsonify({"error": "Internal Server Error"}), 500
    finally:
        conn.close()


@app.route("/user/upload", methods=["POST"])
@jwt_required()
def upload_file():
    try:
        if "file" not in request.files:
            return jsonify({"success": False}), 400
        file = request.files["file"]
        if file.filename == "":
            return jsonify({"error": "No selected file"}), 400
        else:
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
            file.save(file_path)
            return jsonify({"message": "File uploaded successfully"}), 200

    except Exception as e:
        logging.error(f"upload_file(): {e}")


@app.route("/user/edit_video", methods=["POST"])
@jwt_required()
def edit_video():
    try:
        user_email = get_jwt_identity()
        user_id = database.db_get_user_id(user_email)
        if user_id is None:
            return jsonify({"error": "User not found"}), 404

        data = request.get_json()
        src_file_path = data.get("src_file_path")
        start_time = data.get("start_time")
        end_time = data.get("end_time")

        # Process the video (this function needs to be implemented)
        edited_video_url = ffmpeg_process_video(
            src_file_path, start_time, end_time, app.config["OUTPUT_FOLDER"]
        )
        database.db_add_operation(
            user_id, src_file_path, start_time, end_time, edited_video_url
        )
        return jsonify({"success": True, "edited_video_url": edited_video_url}), 200

    except Exception as e:
        logging.error(f"edit_video(): {e}")
        return jsonify({"error": "Internal Server Error"}), 500


@app.route("/user/download_video", methods=["GET"])
@jwt_required()
# TODO: Allow user to fetch a specific video instead of the latest one
def download_video():
    try:
        # fetch the processed video url from the database
        user_email = get_jwt_identity()
        operation_id = database.db_get_operation_id(user_email)
        if not operation_id:
            return jsonify({"error": "Video not found"}), 404
        processed_video_url = database.db_get_processed_video_url(
            user_email, operation_id
        )
        directory = os.path.dirname(processed_video_url)
        filename = os.path.basename(processed_video_url)

        return send_from_directory(directory, filename, as_attachment=True), 200

    except Exception as e:
        logging.error(f"download_video(): {e}")
        return jsonify({"error": "Internal Server Error"}), 500
