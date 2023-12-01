import sqlite3
import logging
import os

logging.basicConfig(level=logging.INFO)


def db_initialize():
    """
    Initializes the database by creating necessary tables if they don't exist.
    Also creates the resources, resources/input, resources/output folders if they don't exist.

    Raises:
        Exception: If there is an error initializing the database.

    Returns:
        None
    """
    try:
        # create resources, resources/input, resources/output folders
        if not os.path.exists("./resources"):
            os.mkdir("./resources")
        if not os.path.exists("./resources/input"):
            os.mkdir("./resources/input")
        if not os.path.exists("./resources/output"):
            os.mkdir("./resources/output")

        conn = sqlite3.connect("app.db")
        c = conn.cursor()
        c.execute(
            """CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    email TEXT UNIQUE NOT NULL,
                    hashed_password TEXT NOT NULL,
                    subscription_info TEXT  DEFAULT NULL
                    )"""
        )
        c.execute(
            """CREATE TABLE IF NOT EXISTS operations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    video_url TEXT NOT NULL,
                    start_time TEXT NOT NULL,
                    end_time TEXT NOT NULL,
                    processed_video_url TEXT NOT NULL,
                    finished INTEGER NOT NULL DEFAULT 0,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
              """
        )
        conn.commit()
    except Exception as e:
        logging.error(f"db_initialize(): Error initializing database: {e}")
    finally:
        conn.close()


def db_get_connection():
    """
    Establishes a connection to the SQLite database.

    Returns:
        conn (sqlite3.Connection): The connection object to the database.

    Raises:
        Exception: If there is an error connecting to the database.
    """
    try:
        conn = sqlite3.connect("app.db")
        conn.row_factory = sqlite3.Row
        return conn
    except Exception as e:
        logging.error(f"db_get_connection(): Error connecting to database: {e}")


def db_check_user(email, hashed_password):
    """
    Check if a user exists in the database with the given email and hashed password.

    Args:
        email (str): The email of the user.
        hashed_password (str): The hashed password of the user.

    Returns:
        int or None: The user ID if the user exists, None otherwise.
    """
    try:
        conn = db_get_connection()
        c = conn.cursor()
        c.execute(
            "SELECT * FROM users WHERE email=? AND hashed_password=?",
            (email, hashed_password),
        )
        user = c.fetchone()
        if user:
            return user[0]
        else:
            raise Exception("User not found")
    except Exception as e:
        logging.error(f"db_check_user(): Error checking user: {e}")
        return None
    finally:
        conn.close()


def db_get_user_id(email):
    """
    Retrieve the user ID associated with the given email from the database.

    Args:
        email (str): The email of the user.

    Returns:
        int or None: The user ID if found, None otherwise.
    """
    try:
        conn = db_get_connection()
        c = conn.cursor()
        c.execute("SELECT id FROM users WHERE email=?", (email,))
        user_id = c.fetchone()
        if user_id:
            return user_id[0]
        else:
            raise Exception("User not found")
    except Exception as e:
        logging.error(f"db_get_user_id(): Error getting user id: {e}")
        return None


def db_add_user(email, hashed_password):
    """
    Add a new user to the database.

    Args:
        email (str): The email address of the user.
        hashed_password (str): The hashed password of the user.

    Returns:
        bool: True if the user was successfully added, False otherwise.
    """
    try:
        conn = db_get_connection()
        c = conn.cursor()
        c.execute(
            "INSERT INTO users (email, hashed_password) VALUES (?, ?)",
            (email, hashed_password),
        )
        operation_id = c.lastrowid
        conn.commit()
        return operation_id
    except Exception as e:
        logging.error(f"db_add_user(): Error adding user: {e}")
        return False
    finally:
        conn.close()


def db_add_operation(
    user_id, video_url, start_time, end_time, processed_video_url, finished=0
):
    """
    Add an operation to the database.

    Args:
        user_id (int): The ID of the user.
        video_url (str): The URL of the original video.
        start_time (str): The start time of the operation.
        end_time (str): The end time of the operation.
        processed_video_url (str): The URL of the processed video.
        finished (int, optional): The status of the operation. Defaults to 0(Unfinished).

    Returns:
        operation_id for the operation if the operation was successfully added, False otherwise.
    """
    logging.info(f"db_add_operation(): processing video {processed_video_url}")
    try:
        conn = db_get_connection()
        c = conn.cursor()
        c.execute(
            "INSERT INTO operations (user_id, video_url, start_time, end_time, processed_video_url, finished) VALUES (?, ?, ?, ?, ?, ?)",
            (user_id, video_url, start_time, end_time, processed_video_url, finished),
        )
        conn.commit()
        return True
    except Exception as e:
        logging.error(f"db_add_operation(): Error adding operation: {e}")
        return False
    finally:
        conn.close()


def db_get_operation_id(email, processed_video_url):
    """
    Retrieves the operation ID associated with the given email and processed video URL.

    Args:
        email (str): The email of the user.
        processed_video_url (str): The URL of the processed video.

    Returns:
        int: The operation ID if found, None otherwise.

    Raises:
        Exception: If the operation is not found.

    """
    try:
        user_id = db_get_user_id(email)
        conn = db_get_connection()
        c = conn.cursor()
        c.execute(
            "SELECT id FROM operations WHERE user_id=? AND processed_video_url=?",
            (user_id, processed_video_url),
        )
        operation_id = c.fetchone()
        if operation_id:
            return operation_id[0]
        else:
            raise Exception("operation not found")
    except Exception as e:
        logging.error(f"db_get_operation_id(): Error getting operation id: {e}")
        return None
    finally:
        conn.close()


def db_get_processed_video(email, operation_id):
    """
    Retrieves the processed video URL from the database for the given email and operation ID.

    Args:
        email (str): The email of the user.
        operation_id (int): The ID of the operation.

    Returns:
        str: The URL of the processed video if found, None otherwise.
    """
    try:
        user_id = db_get_user_id(email)
        conn = db_get_connection()
        c = conn.cursor()
        c.execute(
            "SELECT processed_video_url FROM operations WHERE operations.user_id=? AND operations.id=?",
            (user_id, operation_id),
        )
        processed_video = c.fetchone()
        if processed_video:
            logging.info(f"db_get_processed_video(): {processed_video[0]}")
            return processed_video[0]
        else:
            raise Exception("processed_video not found")
    except Exception as e:
        logging.error(f"db_get_processed_video(): Error getting processed_video: {e}")
        return None


def db_set_operation_finished(email, output_file):
    """
    Sets the 'finished' flag to 1 for the specified operation in the database.

    Args:
        email (str): The email of the user.
        output_file (str): The URL of the processed video file.

    Returns:
        bool: True if the operation was successfully updated, False otherwise.
    """
    try:
        user_id = db_get_user_id(email)
        conn = db_get_connection()
        c = conn.cursor()
        c.execute(
            "UPDATE operations SET finished=1 WHERE operations.user_id=? AND operations.processed_video_url=?",
            (user_id, output_file),
        )
        conn.commit()
        logging.info(f"db_set_operation_finished(): operation {output_file} finished")
        return True
    except Exception as e:
        logging.error(
            f"db_set_operation_finished(): Error setting operation finished: {e}"
        )
        return False
    finally:
        conn.close()


def db_get_subscription_info(email):
    """
    Retrieves the subscription info from the database for the given email.

    Args:
        email (str): The email of the user.

    Returns:
        str: The subscription info if found, None otherwise.
    """
    try:
        conn = db_get_connection()
        c = conn.cursor()
        c.execute(
            "SELECT subscription_info FROM users WHERE users.email=?",
            (email,),
        )
        subscription_info = c.fetchone()
        if subscription_info:
            logging.info("deb_get_subscription_info(): Retrieved subscription_info")
            return subscription_info[0]
        else:
            raise Exception("subscription_info not found")
    except Exception as e:
        logging.error(
            f"deb_get_subscription_info(): Error getting subscription_info: {e}"
        )
        return None
    finally:
        conn.close()

def db_operation_is_complete(operation_id):
    """
    Checks if the operation with the given ID is complete.

    Args:
        operation_id (int): The ID of the operation.

    Returns:
        bool: True if the operation is complete, False otherwise.
    """
    try:
        conn = db_get_connection()
        c = conn.cursor()
        c.execute(
            "SELECT finished FROM operations WHERE operations.id=?",
            (operation_id,),
        )
        finished = c.fetchone()
        if finished == 1:
            logging.info("deb_operation_is_complete(): Retrieved finished")
            return True
        else:
            return False
    except Exception as e:
        logging.error(
            f"deb_operation_is_complete(): Error getting finished: {e}"
        )
        return None
    finally:
        conn.close()