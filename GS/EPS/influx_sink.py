import time
from datetime import datetime
import json
from pathlib import Path
import shutil

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS


class WriteAndHandle:
    def __init__(self, db_info: dict, dir_info: dict):
        # Influx接続用データ値
        self.URL    = db_info.get("url")
        self.TOKEN  = db_info.get("token")
        self.ORG    = db_info.get("org")
        self.BUCKET = db_info.get("bucket")

        # ClientとAPI
        self.client = None
        self.write_api = None

        # JSONファイルの保存先ディレクトリ
        self.JSON_PENDING_DIR = Path(dir_info.get("pending"))
        self.JSON_DONE_DIR    = Path(dir_info.get("done"))
        self.JSON_FAILED_DIR  = Path(dir_info.get("failed"))
        # もしなかったら作っておく
        for directory in [self.JSON_PENDING_DIR, self.JSON_DONE_DIR, self.JSON_FAILED_DIR]:
            if not directory.exists():
                directory.mkdir(parents=True, exist_ok=True)
    

    def connect_db(self):
        try:
            self.client = InfluxDBClient(url=self.URL, token=self.TOKEN, org=self.ORG) # クライアント生成
            self.write_api = self.client.write_api(write_options=SYNCHRONOUS) # 書き込みAPI生成
            if not self.client.ping():
                raise ConnectionError("[Connection Error] InfluxDB ping failed. Check your connection settings.")
            print("Connected to InfluxDB successfully.")
            return True
        
        except Exception as e:
            print(f"Failed to connect to InfluxDB: {e}")
            return False
    

    def close_db(self):
        if self.client:
            self.client.close()
            print("InfluxDB client closed.")
            self.client = None
            self.write_api = None
        

    def watch_directory(self):
        event_handler = EventHandler(self)
        watch_target = Path(self.JSON_PENDING_DIR)

        observer = Observer() # 監視役を用意
        observer.schedule( 
            event_handler,  # イベント発生時の通知(連動)先
            watch_target,   # 監視対象
            recursive=False # サブディレクトリも監視するかどうか(今回はしない)
        )

        observer.start() # 監視スタート
        print(f"Watching {watch_target} for new JSON files... (Press Ctrl+C to stop)")

        try:
            while True: # 無限ループ(Ctrl+Cされるまで)
                time.sleep(1)

        except KeyboardInterrupt: 
            observer.stop() # 監視終了

        observer.join()


    # <<< ここから内部メソッド >>>
    # ----------------------------------------------
    # Point作成
    #  -> dict型のjson_dataを受け取る
    #  -> json_dataを展開する
    #  -> (timestamp, tags, fields)をPointに変換する
    #  -> Pointを返す
    # ----------------------------------------------
    def _make_point(self, json_data):
        measurement = json_data.get("measurement")
        if not measurement:
            raise ValueError(
                "Measurement is not set in json_data. Please ensure 'measurement' key exists."
            )
        point = Point(measurement) #measurement指定

        # タイムスタンプを指定するなら
        timestamp = json_data.get("timestamp")
        if timestamp:
            dt = datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S.%f")
            point.time(dt, WritePrecision.NS)
        
        # タグを追加
        tags = json_data.get("tags", {})
        for tkey, tvalue in tags.items():
            point.tag(tkey, tvalue)
        
        # フィールドを追加
        fields = json_data.get("fields", {})
        for fkey, fvalue in fields.items():
            # フィールドの値がNoneの場合はスキップ
            if fvalue is None:
                continue

            # フィールドの値が辞書型の場合、サブキーを展開してフィールドとして追加(InfluxDBは辞書型を直接保存できない)
            if isinstance(fvalue, dict):
                for subkey, subvalue in fvalue.items():
                    if subvalue is None:
                        continue
                    point.field(f"{fkey}_{subkey}", subvalue)

            else:
                point.field(fkey, fvalue)
        
        return point
    

    # ----------------------------------------------
    # DB書き込み
    #   -> dict型のjson_dataを受け取る
    #   -> InfluxDBに書き込む
    # ----------------------------------------------
    def _write_to_db(self, json_data):
        if self.write_api is None:
            raise RuntimeError("InfluxDB is not connected.")
        point = self._make_point(json_data)
        
        try:
            # DB書き込み
            self.write_api.write(
                bucket=self.BUCKET,
                org=self.ORG,
                record=point
            )
            print(f"Data written to InfluxDB: {point}")
            return True

        except Exception as e:
            print(f"Failed to write data to InfluxDB: {e}")
            return False
    

    # ----------------------------------------------
    # ファイル移動
    #   -> 移動対象のファイルパスを受け取る
    #   -> 移動先ディレクトリを受け取る
    #   -> ファイルを移動する
    # ----------------------------------------------
    def _move_file(self, file_path, destination):
        try:
            file_path = Path(file_path)
            shutil.move(str(file_path), destination / file_path.name)

            print(f"Moved file {file_path} to {destination / file_path.name}")
        
        except Exception as e:
            print(f"Failed to move file {file_path}: {e}")
            

    # ----------------------------------------------
    # JSONファイル処理
    #   -> JSONファイルを読み込む
    #   -> measurement名を取得
    #   -> DB書き込みメソッドを呼び出す
    # ----------------------------------------------
    def _process_json_file(self, file_path):
        file_path = Path(file_path)
        try:
            with file_path.open('r', encoding='utf-8') as f:
                json_data = json.load(f)
            
            # DB書き込みメソッド呼び出し
            if self._write_to_db(json_data):
                print(f"Successfully processed JSON file: {file_path}")
                # 書き込みが完了したら，doneディレクトリに移動する
                self._move_file(file_path, self.JSON_DONE_DIR)
                return True
            else:
                print(f"Failed to write data from JSON file {file_path} to InfluxDB.")
                # 書き込みが失敗した場合，failedディレクトリに移動する
                self._move_file(file_path, self.JSON_FAILED_DIR)
                return False
        
        except Exception as e:
            print(f"Failed to process JSON file {file_path}: {e}")
            # JSONファイルの読み込みや処理が失敗した場合，failedディレクトリに移動する
            self._move_file(file_path, self.JSON_FAILED_DIR)
            return False



# ----------------------------------------------
# watchdog用のイベントハンドラ
# あまり変更予定がないので，独立させてます
# ----------------------------------------------
class EventHandler(FileSystemEventHandler):
    def __init__(self, writer):
        self.writer = writer
    
    # # ! ! ! メソッド名は変更しない ! ! !
    def _handle(self, path):
        if path.endswith(".json"):
            self.writer._process_json_file(path)

    def on_created(self, event):
        if not event.is_directory:
            self._handle(event.src_path)

    def on_moved(self, event):
        if not event.is_directory:
            self._handle(event.dest_path)

    # デバッグ用
    # def on_any_event(self, event):
    #     print(event.event_type, event.src_path)