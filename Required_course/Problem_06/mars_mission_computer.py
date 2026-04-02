import random
import os
import unicodedata
from datetime import datetime

# =====================================================================
# [핵심 도메인 클래스] : 환경 데이터 시뮬레이터
# =====================================================================
class DummySensor:
    """
    [화성 기지 메인 환경 관제 센서 시스템]
    실제 하드웨어 센서가 작동되기 전, 시스템 통합 테스트를 위해 환경 데이터를 시뮬레이션하는 더미(Dummy) 클래스입니다.
    - 주요 기능: 7개 화성환경값 난수 생성, 인위적 걸측치 주입(Fault Injection), 개별 상태 판정
    """
    
    # ---------------------------------------------------------
    # [1] 시스템 설정 상수 (Configuration)
    # ---------------------------------------------------------
    # [1] 범위 설정 상수
    _CONFIG = {
        'internal_temp': (18, 30),      # 내온 (°C)
        'external_temp': (0, 21),       # 외온 (°C)
        'internal_humidity': (50, 60),  # 습도 (%)
        'external_lux': (500, 715),     # 광량 (W/m2)
        'internal_co2': (0.02, 0.1),    # CO2 (%)
        'internal_o2': (4, 7),          # O2 (%)
        'internal_pressure': (950, 1050)# 기압 (hPa)
    }

    # [2] 키 매핑 상수
    _KEY_MAP = {
        'internal_temp': 'mars_base_internal_temperature',
        'external_temp': 'mars_base_external_temperature',
        'internal_humidity': 'mars_base_internal_humidity',
        'external_lux': 'mars_base_external_illuminance',
        'internal_co2': 'mars_base_internal_co2',
        'internal_o2': 'mars_base_internal_oxygen',
        'internal_pressure': 'mars_base_internal_pressure'
    }

    def __init__(self):
        # 센서 데이터가 외부에서 직접 조작되지 않도록 은닉(Encapsulation)합니다.
        self.env_values = {
            'mars_base_internal_temperature': 0.0,
            'mars_base_external_temperature': 0.0,
            'mars_base_internal_humidity': 0.0,
            'mars_base_external_illuminance': 0.0,
            'mars_base_internal_co2': 0.0,
            'mars_base_internal_oxygen': 0.0,
            'mars_base_internal_pressure': 0.0
        }

    # ---------------------------------------------------------
    # [2] 데이터 시뮬레이터 (자연스러운 측정 및 우발적 에러)
    # ---------------------------------------------------------
    def set_env(self):
        """
        _CONFIG의 범위를 기반으로 7개의 환경 데이터를 측정(생성)합니다.
        약 15%의 확률로 우발적인 이상 수치가 발생하도록 시뮬레이션합니다.
        """

        for cfg_key, (min_val, max_val) in self._CONFIG.items():
            sensor_key = self._KEY_MAP[cfg_key]
            
            # 자연스러운 에러 발생 시뮬레이션 (각 센서마다 15% 확률로 에러 발생)
            if random.random() <= 0.15: 
                if random.choice([True, False]):
                    val = max_val + random.uniform(2, 15)  # 상한 초과
                else:
                    val = max(0, min_val - random.uniform(2, 15))  # 하한 미달
            # 85% 확률로 정상 수치 측정
            else:
                val = random.uniform(min_val, max_val)
            
            precision = 4 if 'co2' in sensor_key else 2
            self.env_values[sensor_key] = round(val, precision)
            

    # ---------------------------------------------------------
    # [3] 사전 객체 개별 판독기 (Evaluation)
    # ---------------------------------------------------------
    def get_env(self):
        """
        생성된 딕셔너리의 '각 항목(사전 객체)별'로
        정상/비정상 여부를 독립적으로 판독하여 상태값을 1:1로 매핑합니다.
        """
        now = datetime.now()
        current_time = now.strftime('%Y-%m-%d %H:%M:%S')
        
        result = self.env_values.copy()
        result['timestamp'] = current_time
        
        # [핵심] 사전 객체를 순회하며 1:1로 범위를 대조하여 🚨/✅ 마킹
        for cfg_key, (min_v, max_v) in self._CONFIG.items():
            s_key = self._KEY_MAP[cfg_key]
            val = result[s_key]
            result[f"{s_key}_status"] = "🚨" if val < min_v or val > max_v else "✅"
        
        return result

# =====================================================================
# [공통 유틸리티] : 텍스트 정렬 및 스토리지 로깅
# =====================================================================

# ---------------------------------------------------------
# [A] 텍스트 UI 정렬 및 스타일 유틸리티
# ---------------------------------------------------------
def get_display_width(text):
    """이모티콘(2px)과 일반 영문/숫자(1px)의 시각적 폭 차이를 계산"""
    width = 0
    for char in str(text):
        if unicodedata.east_asian_width(char) in ('W', 'F'):
            width += 2
        else:
            width += 1
    return width

def format_psv_cell(text, target_width):
    """
    텍스트를 고정 폭으로 맞추고, 우리 시스템 표준 구분자(\t|)를 붙여 반환합니다.
    - text: 셀에 들어갈 텍스트 (숫자, 이모티콘, 문자열 모두 가능)
    """
    text_str = str(text)
    current_width = get_display_width(text_str)
    padding = target_width - current_width
    
    # 공백 패딩 + 탭 스냅 + 파이프 구분자까지 한 번에 결합
    return text_str + (" " * max(0, padding)) + "\t| "

# ---------------------------------------------------------
# [B] 스토리지 로깅 (Log Rotation & PSV Write)
# ---------------------------------------------------------
def save_csv_log(data, date_str):
    """
    데이터를 텍스트 파일에 기록합니다.
    """
    file_name = f"mars_env_log_{date_str}.csv"
    file_exists = os.path.exists(file_name)
    
    log_format = {
        'timestamp': ('📅 시각', 22),
        'mars_base_internal_temperature': ('🌡️ 내온', 12),
        'mars_base_external_temperature': ('❄️ 외온', 12),
        'mars_base_internal_humidity': ('💧 습도', 10),
        'mars_base_external_illuminance': ('☀️ 광량', 12),
        'mars_base_internal_co2': ('😷 CO2', 10),
        'mars_base_internal_oxygen': ('🧬 O2', 10),
        'mars_base_internal_pressure': ('🌬️ 기압', 12) 
    }
    
    ordered_keys = list(log_format.keys())
    
    with open(file_name, 'a', encoding='utf-8') as f:
        # 헤더 작성
        if not file_exists or os.path.getsize(file_name) == 0:
            # 이제 각 셀이 스스로 구분자를 달고 나오므로 단순 join만 수행합니다.
            header = "".join(format_psv_cell(log_format[k][0], log_format[k][1]) for k in ordered_keys)
            f.write(header + "\n")
        
        # 데이터 행 작성
        row = "".join(format_psv_cell(data[k], log_format[k][1]) for k in ordered_keys)
        f.write(row + "\n")

# =====================================================================
# [메인] : 시스템 엔트리 포인트 (Dashboard UI)
# =====================================================================
if __name__ == '__main__':
    ds = DummySensor()
    today_date = datetime.now().strftime('%Y-%m-%d')
    
    print("\n" + "="*165)
    print("   🚀 MARS MISSION COMPUTER - CONTINUOUS MONITORING ACTIVE")
    print("="*165)
    
    # 인위적인 모드 설정 없이, 5회 연속 관제 수행
    for _ in range(5):
        ds.set_env()  # 센서 스스로 측정 (우발적 에러 포함)
        d = ds.get_env()  # 사전 객체별로 판독된 결과 반환
        
        save_csv_log(d, today_date)
        
        report = (
            f"[{d['timestamp']}] "
            f"내온: {d['mars_base_internal_temperature']:>5}°C {d['mars_base_internal_temperature_status']} | "
            f"외온: {d['mars_base_external_temperature']:>5}°C {d['mars_base_external_temperature_status']} | "
            f"습도: {d['mars_base_internal_humidity']:>5}% {d['mars_base_internal_humidity_status']} | "
            f"광량: {d['mars_base_external_illuminance']:>6}W {d['mars_base_external_illuminance_status']} | "
            f"CO2: {d['mars_base_internal_co2']:>7}% {d['mars_base_internal_co2_status']} | "
            f"O2: {d['mars_base_internal_oxygen']:>5}% {d['mars_base_internal_oxygen_status']} | "
            f"기압: {d['mars_base_internal_pressure']:>7.2f}hPa {d['mars_base_internal_pressure_status']}"
        )
        print(report)