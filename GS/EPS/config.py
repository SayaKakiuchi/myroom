from pathlib import Path
from dotenv import load_dotenv
import os

load_dotenv()

DB_INFO = {
    "url": os.getenv("INFLUX_URL"),
    "token": os.getenv("INFLUX_TOKEN"),
    "org": os.getenv("INFLUX_ORG"),
    "bucket": os.getenv("INFLUX_BUCKET"),
}

DIR_INFO = {
    "pending": Path(os.getenv("JSON_PENDING_DIR")),
    "done": Path(os.getenv("JSON_DONE_DIR")),
    "failed": Path(os.getenv("JSON_FAILED_DIR")),
}