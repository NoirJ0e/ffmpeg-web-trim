import sqlite3
import logging

logging.basicConfig(level=logging.INFO)


def db_initialize():
    try:
        conn = sqlite3.connect("app.db")
        c = conn.cursor()
        # Create user table
        c.execute(
            """CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    email TEXT UNIQUE NOT NULL,
                    hashed_password TEXT NOT NULL
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
    try:
        conn = sqlite3.connect("app.db")
        conn.row_factory = sqlite3.Row
        return conn
    except Exception as e:
        logging.error(f"db_get_connection(): Error connecting to database: {e}")


def db_check_user(email, hashed_password):
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
    try:
        conn = db_get_connection()
        c = conn.cursor()
        c.execute(
            "INSERT INTO users (email, hashed_password) VALUES (?, ?)",
            (email, hashed_password),
        )
        conn.commit()
        return True
    except Exception as e:
        logging.error(f"db_add_user(): Error adding user: {e}")
        return False
    finally:
        conn.close()


def db_add_operation(
    user_id, video_url, start_time, end_time, processed_video_url, finished=0
):
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


def db_get_operation_id(email):
    try:
        user_id = db_get_user_id(email)
        conn = db_get_connection()
        c = conn.cursor()
        operation_id = c.execute(
            "SELECT operation_id FROM operations WHERE user_id=?", (user_id,)
        )
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
    try:
        user_id = db_get_user_id(email)
        conn = db_get_connection()
        c = conn.cursor()
        processed_video = c.execute(
            "SELECT processed_video_url FROM operations WHERE user_id=? AND operation_id=?",
            (user_id, operation_id),
        )
        if processed_video:
            return processed_video[0]
        else:
            raise Exception("processed_video not found")
    except Exception as e:
        logging.error(f"db_get_processed_video(): Error getting processed_video: {e}")
        return None
