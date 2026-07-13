import json
import time
from datetime import datetime
from copy import deepcopy
from pathlib import Path
import os


class SaveJson:
    # タグとして保存する項目とフォーマット(クラス変数)
    TAG_KEYS = {
        "command_id": lambda x: f"{x:02X}",
        "command_name": str,
        "quality": str,
    }

    def __init__(self, directory_path):
        self.JSON_FILE_NAME = None
        self.DIRECTORY_PATH = directory_path    # jsonファイルを保存するディレクトリパス
        if not os.path.exists(self.DIRECTORY_PATH):
            os.makedirs(self.DIRECTORY_PATH)


    # ---------------------------------------
    # jsonファイルを作成する
    #   -> decoded_data, raw_data, command_idを受け取る
    #   -> _make_filename()を呼び出してファイル名を作成する
    #   -> _make_tags()と _make_fields()を呼び出してtagsとfieldsを作成する
    #   -> timestampを追加する(現在時刻)
    #   -> jsonファイルを作成する
    #   -> 作成したjsonデータ(output)を返す
    # ---------------------------------------
    def save_json(self, decoded_data, raw_data, command_id):
        # jsonファイル名作成メソッド呼び出し
        self._make_filename(command_id, hash(raw_data))

        if self.JSON_FILE_NAME is None:
            raise ValueError(
                "Filename is not set. Please call _make_filename() first."
            )
        
        # jsonデータ作成(measurement, tags, fields, timestamp)
        tags, measurement = self._make_tags(decoded_data)
        fields = self._make_fields(decoded_data)
        output = {
            "measurement": measurement,
            "tags": tags,
            "fields": fields,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3], #タイムスタンプはどのタイミングのを採用する???
        }

        # jsonファイル作成(一時ファイルを経由)
        dir_path = Path(self.DIRECTORY_PATH) / Path(self.JSON_FILE_NAME)
        tmp_path = dir_path.with_suffix(".tmp")

        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(output, f, indent=4, ensure_ascii=False)

        os.replace(tmp_path, dir_path)  # 一時ファイルをリネームして最終的なjsonファイルにする
        
        return output
    

    # <<< ここから内部メソッド >>>
    # ---------------------------------------
    # 保存するjsonファイル名(日付_時刻_コマンドID_ハッシュ値)を作成する
    # ---------------------------------------
    def _make_filename(self, command_id, hash_value):
        self.JSON_FILE_NAME = (
            f"{time.strftime('%Y%m%d_%H%M%S')}_{command_id}_{hash_value}.json"
        )
        return self.JSON_FILE_NAME


    # ---------------------------------------
    # dataからタグを生成する
    #   -> dataを受け取る
    #   -> TAG_KEYSに登録された項目だけを取り出す
    # ---------------------------------------
    def _make_tags(self, data):
        tags = {}

        for key, formatter in self.TAG_KEYS.items():
            if key not in data:
                print(f"Warning: Key '{key}' not found in data. Skipping this tag.")
                continue
            tags[key] = formatter(data[key])
            # command_nameからmeasurementを取り出す
            if key == "command_name":
                measurement = data[key].split("_")[0]

        return tags, measurement


    # ---------------------------------------
    # dataからfieldsを生成する
    #   -> TAG_KEYSに入ってる項目は除外
    #   -> dataを受け取る
    #   -> header_infoとdecoded_payloadを展開する
    # ---------------------------------------
    def _make_fields(self, data):
        fields = deepcopy(data)

        # タグ項目を削除
        for key in self.TAG_KEYS:
            fields.pop(key, None)

        # header_infoを展開
        header_info = fields.pop("header_info", {})
        for section in header_info.values():
            if isinstance(section, dict):
                fields.update(section)

        # decoded_payloadも展開
        decoded_payload = fields.pop("decoded_payload", {})
        if isinstance(decoded_payload, dict):
            fields.update(decoded_payload)

        return fields


