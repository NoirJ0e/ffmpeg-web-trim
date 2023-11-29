from flask import Flask, request, jsonify, send_from_directory
from flask_jwt_extended import (
    JWTManager,
    create_access_token,
    get_jwt,
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
        # Assuming the JWT identity is the user's email
        user_email = get_jwt_identity()

        data = request.get_json()
        src_file_path = data.get("src_file_path")
        start_time = data.get("start_time")
        end_time = data.get("end_time")

        # Process the video (this function needs to be implemented)
        edited_video_url = ffmpeg_process_video(
            src_file_path, start_time, end_time, app.config["OUTPUT_FOLDER"]
        )

        # Store operation record in the database
        # conn = database.get_db_connection()
        # c = conn.cursor()
        # c.execute(
        #     "INSERT INTO operations (user_email, video_url, start_time, end_time, edited_video_url) VALUES (?, ?, ?, ?, ?)",
        #     (user_email, video_url, start_time, end_time, edited_video_url),
        # )
        # conn.commit()

        return jsonify({"success": True, "edited_video_url": edited_video_url}), 200

    except Exception as e:
        logging.error(f"edit_video(): {e}")
        return jsonify({"error": "Internal Server Error"}), 500
    # finally:
    # conn.close()
