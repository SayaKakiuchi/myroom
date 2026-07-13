from config import DB_INFO, DIR_INFO
from influx_sink import WriteAndHandle

writer = WriteAndHandle(DB_INFO, DIR_INFO)
db_info = {
    "url": "http://localhost:8086",
    "token": "my-super-secret-auth-token",
    "org": "my-org",
    "bucket": "my-bucket",
}

dir_info = {
    "pending": "json/pending",
    "done": "json/done",
    "failed": "json/failed",
}

writer = WriteAndHandle(db_info, dir_info)

if writer.connect_db():
    writer.watch_directory()