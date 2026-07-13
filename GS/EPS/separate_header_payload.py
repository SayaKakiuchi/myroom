class SeparateHeaderPayload:
    def __init__(self):
        """
        ヘッダ構成
        """
        self.FLAG_FRAME_LEN = 2 # Ax25フラッグ=7E，フレーム=00
        self.COM_HEADER_LEN = 16 # 94 A6 62 B2 82 AE 60 94 A6 62 B2 A6 A4 67 03 F0
        self.PRIMARY_HEADER_LEN = 5
        self.SECONDARY_HEADER_LEN = 7
        
        self.FULL_HEADER_LEN = self.FLAG_FRAME_LEN + self.COM_HEADER_LEN + self.PRIMARY_HEADER_LEN + self.SECONDARY_HEADER_LEN
        self.PAYLOAD_START_INDEX = self.FULL_HEADER_LEN
    
    def get_header(self, data: bytes) -> bytes:
        """
        AX.25フラグと00フレームを取り除く
        """
        if data[0] == 0x7E:
            if data[1] == 0x00:
                full_header = data[self.FLAG_FRAME_LEN:self.FULL_HEADER_LEN]
                primary_header = full_header[self.COM_HEADER_LEN:self.COM_HEADER_LEN + self.PRIMARY_HEADER_LEN]
                secondary_header = full_header[self.COM_HEADER_LEN + self.PRIMARY_HEADER_LEN:self.FULL_HEADER_LEN]
            else:
                raise ValueError(f"Unexpected frame value, expected 0x00. Got: {data[1]:#04x}")            
        else:
            raise ValueError(f"AX.25 flag not found at the beginning of the frame. Got: {data[0]:#04x}")
        
        return full_header, primary_header, secondary_header
    
    def get_payload(self, data: bytes) -> bytes:
        """
        データからペイロードを抽出する
        """
        payload = data[self.PAYLOAD_START_INDEX:-1]  # 最後の7Eフラグを除外

        return payload


if __name__ == "__main__":
    raw_data_hex = input("Enter raw data (hex string): ")
    raw_data_bytes = bytes.fromhex(raw_data_hex)
    separator = SeparateHeaderPayload()
    full_header, primary_header, secondary_header = separator.get_header(raw_data_bytes)
    payload = separator.get_payload(raw_data_bytes)
    print(f"Full Header: {full_header.hex()}, length: {len(full_header)}")
    print(f"Primary Header: {primary_header.hex()}, length: {len(primary_header)}")
    print(f"Secondary Header: {secondary_header.hex()}, length: {len(secondary_header)}")
    print(f"Payload: {payload.hex()}, length: {len(payload)}")