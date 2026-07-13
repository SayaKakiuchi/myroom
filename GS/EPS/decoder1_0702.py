# from ..separate_header_payload import SeparateHeaderPayload # パッケージ化したらこっちにする
from separate_header_payload import SeparateHeaderPayload

class EPSDecoder:
    def __init__(self):
        self.SEPARATOR = SeparateHeaderPayload()
        self.COM_HEADER_LEN = self.SEPARATOR.COM_HEADER_LEN
        self.PRIMARY_HEADER_LEN = self.SEPARATOR.PRIMARY_HEADER_LEN
        self.SECONDARY_HEADER_LEN = self.SEPARATOR.SECONDARY_HEADER_LEN
        self.FULL_HEADER_LEN = self.SEPARATOR.FULL_HEADER_LEN
        self.PAYLOAD_START_INDEX = self.SEPARATOR.PAYLOAD_START_INDEX

        # 共通tagキー
        self.QUALITY = "OK"  # デコード品質のデフォルト値
        self.record_type = "single_packet" 
        self.rtc_decode_status = "OK"  # RTCデコードステータスのデフォルト値

        # 格納データのテンプレート
        self.resent_decoded_data = {
            "command_id": None,
            "command_name": None,
            "quality": self.QUALITY,
            "record_type": self.record_type,
            "record_id": None,
            "rtc_time_iso": None,
            "rtc_decode_status": self.rtc_decode_status,
            "raw_hex": None,
            "primary_header_raw": None,
            "primary_header_len": None,
            "secondary_header_raw": None,
            "payload_hex": None,
            "decode_status": None,
            "quality_reason": None,
            "decoded_payload": None
        }

        # シャント抵抗値 [Ω]
        self.RSHUNT_OHM: dict[str, float] = {
            "POWER_5V": 0.01, # SC, COM, SPRE
            "POWER_3V3": 0.01, # LCM, CPM
            "PANEL": 0.01,
            "BATTERY": 0.001,
            "HEATER": 0.001
        }

        # 電圧基準値 [V]
        self.VREF_VOLTAGE: dict[str, float] = {
            "POWER_5V": 0,
            "POWER_3V3": 0,
            "PANEL": 2.5,
            "BATTERY": 2.5,
            "HEATER": 2.5
        }

        # コマンドIDマップ
        self.PRC_CMD_TO_TLM_OP: dict[int, int] = {
            0x01: 0x40,  # power on
            0x02: 0x41,  # power off
            0x03: 0x42,  # power reset
            0x04: 0x43,  # EPS realtime
            0x06: 0x45,  # heater manual control
            0x07: 0x46,  # last command data
            0x08: 0x47,  # battery threshold read
            # 0x09 is PRC_CMD_BATT_THD_UPDATE, but latest policy says
            # single-command telemetry is not implemented. EPS threshold update
            # telemetry is handled as PRC_TLM_OP 0x4C when it appears in the frame.
        }
        self.TLM_OP_NAMES: dict[int, str] = {
            0x40: "EPS_POWER_ON",
            0x41: "EPS_POWER_OFF",
            0x42: "EPS_POWER_RESET",
            0x43: "EPS_REALTIME",
            0x44: "EPS_BEACON",
            0x45: "EPS_HEATER_CONTROL",
            0x46: "EPS_LAST_COMMAND_DATA",
            0x47: "EPS_BATTERY_THRESHOLD_READ",
            0x4C: "EPS_BATTERY_THRESHOLD_UPDATE",  
        }
        self.LEGACY_TLM_OP_ALIASES: dict[int, int] = {
            0x48: 0x4C,
        }


    # ----------------------------------------------
    # デコードメイン
    #  -> ヘッダーとペイロードを分解
    #  -> ヘッダーを解析
    #  -> コマンドID(コマンド名称)に基づいてペイロードをデコード
    # ----------------------------------------------
    def main_decode_payload(self, raw_data_bytes: bytes) -> dict[str, any]:
        # ヘッダーとペイロードを分解
        separator = SeparateHeaderPayload()
        full_header, primary_header, secondary_header = separator.get_header(raw_data_bytes)
        payload = separator.get_payload(raw_data_bytes)

        # ヘッダーを解析
        primary_header_info, secondary_header_info = self._analyze_header(full_header)
        command_id = int(primary_header_info["command_id"], 16)
        command_name = self.TLM_OP_NAMES.get(self.PRC_CMD_TO_TLM_OP.get(command_id), 'Unknown')

        # コマンドIDに基づいてペイロードをデコードする
        raw_payload = payload.hex()
        payload_info = self._classify_payload(command_id, payload)
        
        # デコード結果をまとめて返す
        self.resent_decoded_data.update({
            "command_id": f"{command_id:02X}",
            "command_name": command_name,
            "primary_header_raw": primary_header.hex(),
            "primary_header_len": len(primary_header),
            "secondary_header_raw": secondary_header.hex(),
            "payload_hex": raw_payload,
            "decoded_payload": payload_info
        })


    def show_resent_decoded_data(self, decoded_data: dict[str, any]):
        print("\n===== RESENT DECODED DATA =====")
        for key, value in decoded_data.items():
            print(f"{key}: {value}")
        

    # <<< ここから内部メソッド >>>
    # ----------------------------------------------
    # ヘッダ解析
    #  -> ヘッダを受け取る
    #  -> ヘッダをプライマリとセカンダリに分けて解析
    #  -> dict型で返す

    # プライマリヘッダ構成
    # 　[0]：データの総パケ数（EPSはすべて1パケで来るので，00）
    # 　[1]：コマンドID
    # 　[2]：現在DLしているパケット番号（EPSはすべて1パケで来るので，00）
    # 　[3]：テレメトリバイト数（ヘッダー除く）
    # 　[4]：00

    # セカンダリヘッダ構成
    #   [0]：RTC(S)
    # 　[1]：RTC(M)
    # 　[2]：RTC(H)
    # 　[3]：RTC(d)
    # 　[4]：RTC(m)
    # 　[5]：RTC(y)
    # 　[6]：00
    # ----------------------------------------------
    def _analyze_header(self, fullheader: bytes) -> dict[str, any]:
        # プライマリヘッダ解析
        total_packets = fullheader[self.COM_HEADER_LEN]
        command_id = fullheader[self.COM_HEADER_LEN + 1]
        current_packet_number = fullheader[self.COM_HEADER_LEN + 2]
        telemetry_byte_count = fullheader[self.COM_HEADER_LEN + 3]
        header_fifth_byte = fullheader[self.COM_HEADER_LEN + 4]

        primary_header_info = {
            "total_packets": f"{total_packets:02x}",
            "command_id": f"{command_id:02x}",
            "current_packet_number": f"{current_packet_number:02x}",
            "telemetry_byte_count": f"{telemetry_byte_count:02x}",
            "header_fifth_byte": f"{header_fifth_byte:02x}"
        }

        # セカンダリヘッダ解析
        rtc_s = fullheader[self.COM_HEADER_LEN + self.PRIMARY_HEADER_LEN]
        rtc_m = fullheader[self.COM_HEADER_LEN + self.PRIMARY_HEADER_LEN + 1]
        rtc_h = fullheader[self.COM_HEADER_LEN + self.PRIMARY_HEADER_LEN + 2]
        rtc_d = fullheader[self.COM_HEADER_LEN + self.PRIMARY_HEADER_LEN + 3]
        rtc_m = fullheader[self.COM_HEADER_LEN + self.PRIMARY_HEADER_LEN + 4]
        rtc_y = fullheader[self.COM_HEADER_LEN + self.PRIMARY_HEADER_LEN + 5]
        header_seventh_byte = fullheader[self.COM_HEADER_LEN + self.PRIMARY_HEADER_LEN + 6]

        secondary_header_info = {
            "decoded rtc (y-m-d h:m:s)": f"20{rtc_y:02d}-{rtc_m:02d}-{rtc_d:02d} {rtc_h:02d}:{rtc_m:02d}:{rtc_s:02d}",
            "header_seventh_byte": header_seventh_byte
        }

        return primary_header_info, secondary_header_info


    # ----------------------------------------------
    # 進数変換
    # ----------------------------------------------
    def _hex2bin(self, hex_str: str) -> str:
        # return bin(int(hex_str, 16))[2:].zfill(len(hex_str) * 4) #桁数を揃えるためにzfillを使用(桁数は16進数の文字数×4)
        return bin(int(hex_str, 16))[2:]


    # ----------------------------------------------
    # ペイロード長チェック
    #  -> ペイロードと期待される長さを受け取る
    #  -> ペイロード長が期待値と一致するかを確認
    #  -> 一致しない場合は警告を出して、QUALITYを"WARNING"に設定
    #  -> 一致する場合はTrueを返す
    # ----------------------------------------------
    def _check_payload_length(self, payload: bytes, expected_length: int) -> bool:
        if len(payload) != expected_length:
            self.QUALITY = "WARNING"
            print(f"[WARNING] Payload length is not {expected_length} bytes.")
            return False
        return True
    

    # ----------------------------------------------
    # GPIOステータス
    #  -> Power Line Status / GPIO
    #   bit0: 5V_SC
    #   bit1: 5V_COM
    #   bit2: 5V_SPRE
    #   bit3: 3V3_LCM
    #   bit4: 3V3_CPM
    #  -> Negative logic:
    #   0 = ON
    #   1 = OFF
    # ----------------------------------------------
    def _gpio_status(self, status: int) -> dict[str, bool]:
        """
        Power Line Status / GPIO
        bit0: 5V_SC
        bit1: 5V_COM
        bit2: 5V_SPRE
        bit3: 3V3_LCM
        bit4: 3V3_CPM

        Negative logic:
        0 = ON
        1 = OFF
        """
        # 0ならON，1ならOFFを返す
        return {
            "pwr_5v_sc": "ON" if ((status >> 0) & 1) == 0 else "OFF",
            "pwr_5v_com": "ON" if ((status >> 1) & 1) == 0 else "OFF",
            "pwr_5v_spre": "ON" if ((status >> 2) & 1) == 0 else "OFF",
            "pwr_3v3_lcm": "ON" if ((status >> 3) & 1) == 0 else "OFF",
            "pwr_3v3_cpm": "ON" if ((status >> 4) & 1) == 0 else "OFF",
        }


    # ----------------------------------------------
    # ヒータステータス
    #  -> Negative logic:
    #       0x00 = ON
    #       0x01 = OFF
    # ----------------------------------------------
    def _heater_status(self, status: int) -> dict[str, str]:
        return {
            "heater": "ON" if status == 0x00 else "OFF"
        }
    

    # ----------------------------------------------
    # EPSステータス
    #  -> Negative logic:
    #       0x00 = normal
    #       0x01 = emergency
    # ----------------------------------------------
    def _eps_status(self, status: int) -> dict[str, str]:
        return {
            "eps_status": "NORMAL" if status == 0x00 else "EMERGENCY"
        }
    

    # ----------------------------------------------
    # 電圧変換式
    #  -> Bus Voltage = bit_vol * 2.5 * 2 / 4096
    # ----------------------------------------------
    def _conv_voltage(self, bit_vol: int) -> float:
        return bit_vol * 2.5 * 2 / 4096
    

    # ----------------------------------------------
    # 電流変換式
    #  -> Bus Current = (vol - v_ref) / (R_shunt * 200)
    # ----------------------------------------------
    def _conv_current(self, vol: float, v_ref: float, r_shunt: float) -> float:
        return (vol - v_ref) / (r_shunt * 200.0)
    

    # ----------------------------------------------
    # 温度変換式
    #  -> Temperature = (vol / (6800 * 10^-6)) - 273.15
    # ----------------------------------------------
    def _conv_temperature(self, vol: float) -> float:
        """ Temperature = (vol / (6800 * 10^-6)) - 273.15 """
        return (vol / (6800 * 10**-6)) - 273.15


    # ----------------------------------------------
    # 内部デコーダ 電源系
    #  -> コマンドID：0x40，0x41，0x42
    #  -> バイト数：25(固定)
    #  -> ペイロード構成：
    #   [0]：GPIOステータス
    #   [1][2]：BUS電圧
    #   [3][4]：BUS電流
    #   [5][6]：COM電圧
    #   [7][8]：COM電流
    #   [9][10]：SC電圧
    #   [11][12]：SC電流
    #   [13][14]：SPRE電圧
    #   [15][16]：SPRE電流
    #   [17][18]：LCM電圧
    #   [19][20]：LCM電流
    #   [21][22]：CPM電圧
    #   [23][24]：CPM電流
    # ex) SPRE電源ON：7E 00 94 A6 62 B2 82 AE 60 94 A6 62 B2 A6 A4 67 03 F0 00 01 00 19 00 00 00 00 00 00 00 00 00 0E 79 00 B3 0E 7F 00 43 0E 80 00 36 0E 7B 00 8F 0A A7 00 02 0A 9E 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 7E
    # ----------------------------------------------
    def _power_line(self, payload: bytes) -> dict[str, bool]:
        #データ長が25バイトであることを確認
        self._check_payload_length(payload, 25)

        # ペイロード[0]=GPIOステータス
        gpio_status_byte = payload[0]
        
        # ペイロード[1][2]=BUS電圧
        bus_voltage = self._conv_voltage(int.from_bytes(payload[1:3], byteorder='big'))
        
        # ペイロード[3][4]=BUS電流
        bus_current_vol = self._conv_voltage(int.from_bytes(payload[3:5], byteorder='big'))
        bus_current = self._conv_current(bus_current_vol, self.VREF_VOLTAGE["POWER_5V"], self.RSHUNT_OHM["POWER_5V"])
        
        # ペイロード[5][6]=COM電圧
        com_voltage = self._conv_voltage(int.from_bytes(payload[5:7], byteorder='big'))
        
        # ペイロード[7][8]=COM電流
        com_current_vol = self._conv_voltage(int.from_bytes(payload[7:9], byteorder='big'))
        com_current = self._conv_current(com_current_vol, self.VREF_VOLTAGE["POWER_5V"], self.RSHUNT_OHM["POWER_5V"])
        sc_voltage = self._conv_voltage(int.from_bytes(payload[9:11], byteorder='big'))
        
        # ペイロード[11][12]=SC電流
        sc_current_vol = self._conv_voltage(int.from_bytes(payload[11:13], byteorder='big'))
        sc_current = self._conv_current(sc_current_vol, self.VREF_VOLTAGE["POWER_5V"], self.RSHUNT_OHM["POWER_5V"])
        
        # ペイロード[13][14]=SPRE電圧
        spre_voltage = self._conv_voltage(int.from_bytes(payload[13:15], byteorder='big'))
        
        # ペイロード[15][16]=SPRE電流
        spre_current_vol = self._conv_voltage(int.from_bytes(payload[15:17], byteorder='big'))
        spre_current = self._conv_current(spre_current_vol, self.VREF_VOLTAGE["POWER_5V"], self.RSHUNT_OHM["POWER_5V"])
        
        # ペイロード[17][18]=LCM電圧
        lcm_voltage = self._conv_voltage(int.from_bytes(payload[17:19], byteorder='big'))
        
        # ペイロード[19][20]=LCM電流
        lcm_current_vol = self._conv_voltage(int.from_bytes(payload[19:21], byteorder='big'))
        lcm_current = self._conv_current(lcm_current_vol, self.VREF_VOLTAGE["POWER_3V3"], self.RSHUNT_OHM["POWER_3V3"])
        
        # ペイロード[21][22]=CPM電圧
        cpm_voltage = self._conv_voltage(int.from_bytes(payload[21:23], byteorder='big'))

        # ペイロード[23][24]=CPM電流
        cpm_current_vol = self._conv_voltage(int.from_bytes(payload[23:25], byteorder='big'))
        cpm_current = self._conv_current(cpm_current_vol, self.VREF_VOLTAGE["POWER_3V3"], self.RSHUNT_OHM["POWER_3V3"])

        return {
            "quality": self.QUALITY,
            "gpio_status": self._gpio_status(gpio_status_byte),
            "bus_voltage": bus_voltage,
            "bus_current": bus_current,
            "com_voltage": com_voltage,
            "com_current": com_current,
            "sc_voltage": sc_voltage,
            "sc_current": sc_current,
            "spre_voltage": spre_voltage,
            "spre_current": spre_current,
            "lcm_voltage": lcm_voltage,
            "lcm_current": lcm_current,
            "cpm_voltage": cpm_voltage,
            "cpm_current": cpm_current
        }


    # ----------------------------------------------
    # 内部デコーダ EPSリアルタイム
    #  -> コマンドID：0x43
    #  -> バイト数：44(固定)
    #  -> ペイロード構成：
    #   [0]：GPIOステータス
    #   [1][2]：BUS電圧
    #   [3][4]：BUS電流
    #   [5][6]：COM電圧
    #   [7][8]：COM電流
    #   [9][10]：SC電圧
    #   [11][12]：SC電流
    #   [13][14]：SPRE電圧
    #   [15][16]：SPRE電流
    #   [17][18]：LCM電圧
    #   [19][20]：LCM電流
    #   [21][22]：CPM電圧
    #   [23][24]：CPM電流
    #   [25][26]：+x1パネル電圧
    #   [27][28]：+x2パネル電圧
    #   [29][30]：-xパネル電圧
    #   [31][32]：+yパネル電圧
    #   [33][34]：-y1パネル電圧
    #   [35][36]：-y2パネル電圧
    #   [37][38]：バッテリ電圧
    #   [39][40]：バッテリ電流
    #   [41][42]：バッテリ温度
    # ----------------------------------------------
    def _eps_realtime(self, payload: bytes) -> dict[str, float]:
        #データ長が44バイトであることを確認
        self._check_payload_length(payload, 44)
        
        # ペイロード[0]=GPIOステータス
        gpio_status_byte = payload[0]
        # ペイロード[1][2]=BUS電圧
        bus_voltage = self._conv_voltage(int.from_bytes(payload[1:3], byteorder='big'))

        # ペイロード[3][4]=BUS電流
        bus_current_vol = self._conv_voltage(int.from_bytes(payload[3:5], byteorder='big'))
        bus_current = self._conv_current(bus_current_vol, self.VREF_VOLTAGE["POWER_5V"], self.RSHUNT_OHM["POWER_5V"])

        # ペイロード[5][6]=COM電圧
        com_voltage = self._conv_voltage(int.from_bytes(payload[5:7], byteorder='big'))

        # ペイロード[7][8]=COM電流
        com_current_vol = self._conv_voltage(int.from_bytes(payload[7:9], byteorder='big'))
        com_current = self._conv_current(com_current_vol, self.VREF_VOLTAGE["POWER_5V"], self.RSHUNT_OHM["POWER_5V"])

        # ペイロード[9][10]=SC電圧
        sc_voltage = self._conv_voltage(int.from_bytes(payload[9:11], byteorder='big'))

        # ペイロード[11][12]=SC電流
        sc_current_vol = self._conv_voltage(int.from_bytes(payload[11:13], byteorder='big'))
        sc_current = self._conv_current(sc_current_vol, self.VREF_VOLTAGE["POWER_5V"], self.RSHUNT_OHM["POWER_5V"])

        # ペイロード[13][14]=SPRE電圧
        spre_voltage = self._conv_voltage(int.from_bytes(payload[13:15], byteorder='big'))

        # ペイロード[15][16]=SPRE電流
        spre_current_vol = self._conv_voltage(int.from_bytes(payload[15:17], byteorder='big'))
        spre_current = self._conv_current(spre_current_vol, self.VREF_VOLTAGE["POWER_5V"], self.RSHUNT_OHM["POWER_5V"])

        # ペイロード[17][18]=LCM電圧
        lcm_voltage = self._conv_voltage(int.from_bytes(payload[17:19], byteorder='big'))

        # ペイロード[19][20]=LCM電流
        lcm_current_vol = self._conv_voltage(int.from_bytes(payload[19:21], byteorder='big'))
        lcm_current = self._conv_current(lcm_current_vol, self.VREF_VOLTAGE["POWER_3V3"], self.RSHUNT_OHM["POWER_3V3"])

        # ペイロード[21][22]=CPM電圧
        cpm_voltage = self._conv_voltage(int.from_bytes(payload[21:23], byteorder='big'))

        # ペイロード[23][24]=CPM電流
        cpm_current_vol = self._conv_voltage(int.from_bytes(payload[23:25], byteorder='big'))
        cpm_current = self._conv_current(cpm_current_vol, self.
        VREF_VOLTAGE["POWER_3V3"], self.RSHUNT_OHM["POWER_3V3"])

        # ペイロード[25][26]=+X1パネル電流
        panel_px1_voltage = self._conv_voltage(int.from_bytes(payload[25:27], byteorder='big'))
        panel_px1_current = self._conv_current(panel_px1_voltage, self.VREF_VOLTAGE["PANEL"], self.RSHUNT_OHM["PANEL"])

        # ペイロード[27][28]=+X2パネル電流
        panel_px2_voltage = self._conv_voltage(int.from_bytes(payload[27:29], byteorder='big'))
        panel_px2_current = self._conv_current(panel_px2_voltage, self.VREF_VOLTAGE["PANEL"], self.RSHUNT_OHM["PANEL"])

        # ペイロード[29][30]=-Xパネル電流
        panel_mx1_voltage = self._conv_voltage(int.from_bytes(payload[29:31], byteorder='big'))
        panel_mx1_current = self._conv_current(panel_mx1_voltage, self.VREF_VOLTAGE["PANEL"], self.RSHUNT_OHM["PANEL"])

        # ペイロード[31][32]=+Yパネル電流
        panel_py_voltage = self._conv_voltage(int.from_bytes(payload[31:33], byteorder='big'))
        panel_py_current = self._conv_current(panel_py_voltage, self.VREF_VOLTAGE["PANEL"], self.RSHUNT_OHM["PANEL"])

        # ペイロード[33][34]=-Y1パネル電流
        panel_my1_voltage = self._conv_voltage(int.from_bytes(payload[33:35], byteorder='big'))
        panel_my1_current = self._conv_current(panel_my1_voltage, self.VREF_VOLTAGE["PANEL"], self.RSHUNT_OHM["PANEL"])

        # ペイロード[35][36]=-Y2パネル電流
        panel_my2_voltage = self._conv_voltage(int.from_bytes(payload[35:37], byteorder='big'))
        panel_my2_current = self._conv_current(panel_my2_voltage, self.VREF_VOLTAGE["PANEL"], self.RSHUNT_OHM["PANEL"])

        # ペイロード[37][38]=バッテリ電圧
        battery_voltage = self._conv_voltage(int.from_bytes(payload[37:39], byteorder='big'))

        # ペイロード[39][40]=バッテリ電流
        battery_current_vol = self._conv_voltage(int.from_bytes(payload[39:41], byteorder='big'))
        battery_current = self._conv_current(battery_current_vol, self.VREF_VOLTAGE["BATTERY"], self.RSHUNT_OHM["BATTERY"])

        # ペイロード[41][42]=バッテリ温度
        battery_temperature_vol = self._conv_voltage(int.from_bytes(payload[41:43], byteorder='big'))
        battery_temperature = self._conv_temperature(battery_temperature_vol)

        return {
            "gpio_status": self._gpio_status(gpio_status_byte),
            "bus_voltage [V]": bus_voltage,
            "bus_current [A]": bus_current,
            "com_voltage [V]": com_voltage,
            "com_current [A]": com_current,
            "sc_voltage [V]": sc_voltage,
            "sc_current [A]": sc_current,
            "spre_voltage [V]": spre_voltage,
            "spre_current [A]": spre_current,
            "lcm_voltage [V]": lcm_voltage,
            "lcm_current [A]": lcm_current,
            "cpm_voltage [V]": cpm_voltage,
            "cpm_current [A]": cpm_current,
            "panel_px1_current [A]": panel_px1_current,
            "panel_px2_current [A]": panel_px2_current,
            "panel_mx1_current [A]": panel_mx1_current,
            "panel_py_current [A]": panel_py_current,
            "panel_my1_current [A]": panel_my1_current,
            "panel_my2_current [A]": panel_my2_current,
            "battery_voltage [V]": battery_voltage,
            "battery_current [A]": battery_current,
            "battery_temperature [℃]": battery_temperature
        }


    # ----------------------------------------------
    # 内部デコーダ ヒータ制御
    #  -> コマンドID：0x45
    #  -> バイト数：7(固定)
    #  -> ペイロード構成：
    #   [0]：ヒータステータス
    #   [1][2]：ヒータ電圧
    #   [3][4]：ヒータ電流
    #   [5][6]：ヒータ温度
    # ----------------------------------------------
    def _heater_control(self, payload: bytes) -> dict[str, bool]:
        #データ長が7バイトであることを確認
        self._check_payload_length(payload, 7)

        # ペイロード[0]=ヒータステータス
        heater_status_byte = payload[0]

        # ペイロード[1][2]=ヒータ電圧
        heater_voltage = self._conv_voltage(int.from_bytes(payload[1:3], byteorder='big'))

        # ペイロード[3][4]=ヒータ電流
        heater_current_vol = self._conv_voltage(int.from_bytes(payload[3:5], byteorder='big'))
        heater_current = self._conv_current(heater_current_vol, self.VREF_VOLTAGE["HEATER"], self.RSHUNT_OHM["HEATER"])

        # ペイロード[5][6]=ヒータ温度
        heater_temperature_vol = self._conv_voltage(int.from_bytes(payload[5:7], byteorder='big'))
        heater_temperature = self._conv_temperature(heater_temperature_vol)

        return {
            "heater_status": self.heater_status(heater_status_byte),
            "heater_voltage [V]": heater_voltage,
            "heater_current [A]": heater_current,
            "heater_temperature [℃]": heater_temperature
        }


    # ----------------------------------------------
    # 内部デコーダ ラストコマンド確認
    #  -> コマンドID：0x46
    #  -> バイト数：可変
    #  -> ペイロード構成：
    #   [0-i]：ラストコマンドデータ
    # ----------------------------------------------
    def _last_command_data(self, payload: bytes) -> dict[str, any]:
        # ペイロード=コマンドデータ
        return {
            "last_command_data": payload.hex()
        }


    # ----------------------------------------------
    # 内部デコーダ バッテリ閾値確認
    #  -> コマンドID：0x47
    #  -> バイト数：10(固定)
    #  -> ペイロード構成：
    #   [0][1]：最小SOC電圧閾値
    #   [2][3]：中間SOC電圧閾値
    #   [4][5]：最小バッテリ温度閾値
    #   [6][7]：中間バッテリ温度閾値
    #   [8][9]：最大バッテリ温度閾値
    # ----------------------------------------------
    def _battery_threshold_read(self, payload: bytes) -> dict[str, float]:
        #データ長が10バイトであることを確認
        self._check_payload_length(payload, 10)

        # ペイロード[0][1]=最小SOC電圧閾値
        battery_threshold_minSOC_voltage = self._conv_voltage(int.from_bytes(payload[0:2], byteorder='big'))
        # ペイロード[2][3]=中間SOC電圧閾値
        battery_threshold_midSOC_voltage = self._conv_voltage(int.from_bytes(payload[2:4], byteorder='big'))
        # ペイロード[4][5]=最小バッテリ温度閾値
        battery_threshold_min_temperature = self._conv_temperature(int.from_bytes(payload[4:6], byteorder='big'))
        # ペイロード[6][7]=中間バッテリ温度閾値
        battery_threshold_mid_temperature = self._conv_temperature(int.from_bytes(payload[6:8], byteorder='big'))
        # ペイロード[8][9]=最大バッテリ温度閾値
        battery_threshold_max_temperature = self._conv_temperature(int.from_bytes(payload[8:10], byteorder='big'))

        return {
            "battery_threshold_minSOC_voltage [V]": battery_threshold_minSOC_voltage,
            "battery_threshold_midSOC_voltage [V]": battery_threshold_midSOC_voltage,
            "battery_threshold_min_temperature [℃]": battery_threshold_min_temperature,
            "battery_threshold_mid_temperature [℃]": battery_threshold_mid_temperature,
            "battery_threshold_max_temperature [℃]": battery_threshold_max_temperature
        }


    # ----------------------------------------------
    # 内部デコーダ バッテリ閾値更新
    #  -> コマンドID：0x4C
    #  -> バイト数：4(固定)
    #  -> ペイロード構成：
    #   [0][1]：最小SOC電圧閾値
    #   [2][3]：中間SOC電圧閾値
    # ----------------------------------------------
    def _battery_threshold_update(self, payload: bytes) -> dict[str, float]:
        #データ長が4バイトであることを確認
        self._check_payload_length(payload, 4)

        # ペイロード[0][1]=最小SOC電圧閾値
        battery_threshold_minSOC_voltage = self._conv_voltage(int.from_bytes(payload[0:2], byteorder='big'))
        # ペイロード[2][3]=中間SOC電圧閾値
        battery_threshold_midSOC_voltage = self._conv_voltage(int.from_bytes(payload[2:4], byteorder='big'))

        return {
            "battery_threshold_minSOC_voltage [V]": battery_threshold_minSOC_voltage,
            "battery_threshold_midSOC_voltage [V]": battery_threshold_midSOC_voltage
        }


    # ----------------------------------------------
    # 内部デコーダ ペイロード分類
    #  -> コマンドIDに応じて，対応するデコーダを呼び出す
    # ----------------------------------------------
    def _classify_payload(self, command_id_sc: int, payload: bytes) -> dict[str, any]:
        command_id = self.PRC_CMD_TO_TLM_OP.get(command_id_sc, None)

        if command_id == None:
            raise ValueError(f"[ERROR] Unknown command ID: {command_id_sc:02x}")
        else:
            if command_id == 0x40 or command_id == 0x41 or command_id == 0x42:
                return self._power_line(payload)
            elif command_id == 0x43:
                return self._eps_realtime(payload)
            elif command_id == 0x45:
                return self._heater_control(payload)
            elif command_id == 0x46:
                return self._last_command_data(payload)
            elif command_id == 0x47:
                return self._battery_threshold_read(payload)
            elif command_id == 0x4C:
                return self._battery_threshold_update(payload)
            else:
                raise ValueError(f"[ERROR] Unknown command ID: {command_id:02x}")




if __name__ == "__main__":
    # テスト用のペイロードデータ（16進数文字列）
    test_payload_hex = input("Enter payload data (hex string): ")
    test_payload_bytes = bytes.fromhex(test_payload_hex)

    # インスタンス生成
    decoder = EPSDecoder()
    
    # ヘッダーとペイロードを分解してデコード
    decoded_data = decoder.main_decode_payload(test_payload_bytes)
    print("Decoded Data:", decoded_data)