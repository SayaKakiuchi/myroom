# from save_json import SaveJson
# from decoder1_0702 import EPSDecoder

# epsdecoder = EPSDecoder()
# saver = SaveJson()
# save_path = "test_payload.json"

# # テスト用のペイロードデータ（16進数文字列）
# test_payload_hex = input("Enter payload data (hex string): ")
# test_payload_bytes = bytes.fromhex(test_payload_hex)

# # ヘッダーとペイロードを分解してデコード
# eps_decoded_data = epsdecoder.main_decode_payload(test_payload_bytes)
# print("Decoded Data:", eps_decoded_data)

# # JSONファイルに保存
# command_id = eps_decoded_data.get("command_id", "unknown_command")
# eps_decoded_data = epsdecoder.main_decode_payload(test_payload_bytes)
# saver.save_json(eps_decoded_data, test_payload_hex, command_id)

print("===== SaveJson Debug Start =====")

from save_json import SaveJson
from decoder1_0702 import EPSDecoder

SAVE_DIR = "json/pending"

epsdecoder = EPSDecoder()
saver = SaveJson(SAVE_DIR)

test_payload_hex = input("Enter payload data (hex string): ")
test_payload_bytes = bytes.fromhex(test_payload_hex)

decoded = epsdecoder.main_decode_payload(test_payload_bytes)

print(decoded)

command_id = decoded.get("command_id", "unknown_command")

json_data = saver.save_json(
    decoded,
    test_payload_hex,
    command_id
)

print(json_data)