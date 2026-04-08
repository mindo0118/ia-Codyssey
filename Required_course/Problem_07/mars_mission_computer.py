import sys
import time
import threading

# 상위 폴더를 경로에 추가하여 Problem_06의 모듈을 가져올 수 있게 함
sys.path.append('D:\\codyssey_university\\Required_course')
from Problem_06.mars_mission_computer import DummySensor


class MissionDisplay:
    '''사용자 인터페이스(UI) 출력을 전담하는 클래스'''

    @staticmethod
    def show_realtime(data):
        '''실시간 센서 데이터를 화면에 출력'''
        print('\n[Real-time Data]')
        for key, value in data.items():
            print(f'  - {key}: {value}')

    @staticmethod
    def show_average(avg_data):
        '''5분 평균 계산 결과를 화면에 출력'''
        print('\n====================================')
        print('[Average Data - 5 Minutes]')
        for key, value in avg_data.items():
            print(f'  - {key}: {value}')
        print('====================================\n')

    @staticmethod
    def show_system_message(message):
        '''시스템 상태 및 안내 메시지 출력'''
        print(f'\n>>> {message}')


class MissionComputer:
    '''데이터 수집, 연산 로직 및 하드웨어 제어를 전담하는 클래스'''

    def __init__(self, sensor, display, update_interval=5, avg_interval=300):
        # 의존성 주입 (센서와 출력 도구를 외부에서 받아옴)
        self.sensor = sensor
        self.display = display
        
        # 동작 주기 설정 (초 단위)
        self.update_interval = update_interval
        self.avg_interval = avg_interval
        
        # 데이터 누적을 위한 저장소 초기화
        self.history_data = {key: [] for key in self.sensor.env_values.keys()}
        self.running = True

    def update_sensor_data(self):
        '''센서로부터 새 데이터를 읽고 기록함'''
        self.sensor.set_env() 
        current_data = self.sensor.env_values
        
        # 평균 계산을 위해 리스트에 값 추가
        for key, value in current_data.items():
            self.history_data[key].append(value)
            
        # UI 클래스를 통해 데이터 출력
        self.display.show_realtime(current_data)

    def calculate_average(self):
        '''누적된 데이터의 평균을 구하고 저장소를 비움'''
        avg_values = {}
        for key, values_list in self.history_data.items():
            # 데이터가 있을 때만 산술 평균 계산
            avg_values[key] = round(sum(values_list) / len(values_list), 2) if values_list else 0.0
            
        # 다음 주기를 위해 누적 데이터 초기화
        self.history_data = {key: [] for key in self.sensor.env_values.keys()}
        self.display.show_average(avg_values)

    def monitor_loop(self):
        '''백그라운드에서 시간을 체크하며 주기적으로 업무를 수행'''
        start_time = time.time()
        last_print_time = time.time()
        
        while self.running:
            current_time = time.time()
            
            # 설정된 갱신 주기마다 데이터 업데이트 실행
            if current_time - last_print_time >= self.update_interval:
                self.update_sensor_data()
                last_print_time = current_time
                
            # 설정된 평균 주기마다 결과 출력 실행
            if current_time - start_time >= self.avg_interval:
                self.calculate_average()
                start_time = current_time
            
            # CPU 점유율을 낮추기 위한 최소한의 대기
            time.sleep(0.1)

    def check_exit(self):
        '''사용자의 종료 입력('q' + Enter)을 감시'''
        while self.running:
            try:
                if input().strip().lower() == 'q':
                    self.running = False
                    self.display.show_system_message('System stopped....')
                    break
            except KeyboardInterrupt:
                self.running = False
                self.display.show_system_message('System stopped....')
                break

    def run(self):
        '''미션 컴퓨터 기동 및 멀티스레딩 시작'''
        self.display.show_system_message('Mission Computer Started. (Press \'q\' + Enter to stop)')
        
        # 출력/로직 루프를 별도 스레드로 분리하여 입력 대기와 동시에 실행
        monitor_thread = threading.Thread(target=self.monitor_loop, daemon=True)
        monitor_thread.start()
        
        # 메인 스레드는 사용자 종료 입력 대기에 집중
        self.check_exit()


if __name__ == '__main__':
    # 1. 사용할 부품(객체) 생성
    mars_sensor = DummySensor()
    mars_display = MissionDisplay()
    
    # 2. 시스템 조립 및 실행 (기본값: 5초 갱신 / 300초 평균)
    RunComputer = MissionComputer(
        sensor=mars_sensor, 
        display=mars_display, 
        update_interval=5, 
        avg_interval=300
    )
    
    RunComputer.run()