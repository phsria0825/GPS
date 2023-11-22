"""
`GPS_GUI.py` 파일은 PyQt5 라이브러리를 사용하여 GUI 애플리케이션을 만들었다.
이 코드는 GPS 데이터를 처리하고 표시하기 위한 프로그램의 일부로 보이며, 이를 위해 PyQt5의 위젯과 레이아웃 클래스, QThread, 그리고 `GPS_Tx` 모듈을 사용
코드의 시작 부분에는 시리얼 연결을 위한 포트 설정과 통신 속도 설정

`GPS_GUI.py` 파일의 전체적인 구조와 내용을 분석한 결과, 이 파일은 PyQt5를 사용하여 GUI 기반의 GPS 데이터 수집 및 처리 애플리케이션을 구현

### 1. 코드의 구조와 주석

- **라이브러리 임포트**: PyQt5 (GUI 구성), sys (시스템 관련 함수), time (시간 관련 처리), boto3 (AWS 서비스 사용), `GPS_Tx` (GPS 데이터 처리 관련 모듈).

- **GPS 설정 변수**:
  - `GPS_BAUDRATE = 9600`: GPS 모듈과 통신하기 위한 보드레이트 설정.
  - `GPS_PORTNUM = 'COM0'`: GPS 모듈이 연결된 시리얼 포트 번호 설정.

- **main 함수**:
  - GPS 데이터를 파싱하고 AWS S3 버킷에 업로드
  - `NMEAParser` 인스턴스 생성: NMEA 포맷의 GPS 데이터를 파싱.
  - `nmea_data_dict`: 시뮬레이션을 위해 하드코딩된 GPS 데이터.
  - AWS S3 클라이언트 생성 및 데이터 업로드 로직 포함.

- **Worker 클래스 (QThread 상속)**:
  - 별도의 스레드에서 `main` 함수를 실행하여 GUI와 데이터 처리를 분리.

- **App 클래스 (QWidget 상속)**:
  - GUI 구성 및 이벤트 핸들링을 담당.
  - `init_ui` 메소드: 버튼과 레이아웃 구성.
  - `start_collecting` 및 `stop_collecting` 메소드: 데이터 수집 시작 및 종료 기능.

- **애플리케이션 실행 코드**:
  - PyQt 애플리케이션 인스턴스 생성 및 실행.

### 2. 클래스 및 메소드별 목적

- **Worker 클래스**:
  - 목적: 메인 애플리케이션의 GUI와 데이터 처리를 별도의 스레드에서 실행하여 GUI 응답성을 유지.
  - `run` 메소드: `main` 함수를 별도의 스레드에서 실행.

- **App 클래스**:
  - 목적: 사용자 인터페이스를 구성하고 사용자의 입력에 반응하여 데이터 수집을 제어.
  - `init_ui` 메소드: 윈도우, 버튼, 레이아웃을 설정.
  - `start_collecting` 메소드: 데이터 수집을 시작하는 기능.
  - `stop_collecting` 메소드: 데이터 수집을 중단하는 기능.
"""
# 필요한 모듈들을 임포트
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton  # PyQt5를 이용한 GUI 구성 요소
from PyQt5.QtCore import QThread  # PyQt5의 스레드 관련 기능 사용
import sys  # 시스템 관련 기능 사용 (여기서는 애플리케이션 종료에 필요)
import time  # 시간 지연 기능 사용 (데이터 처리 시 딜레이를 주기 위해 사용)
import boto3  # AWS 서비스를 사용하기 위한 모듈 (여기서는 S3 클라이언트 사용)
from GPS_Tx import *  # 사용자 정의 모듈, GPS 데이터 처리 관련 기능 포함

# GPS 장치와의 통신 설정을 위한 상수
GPS_BAUDRATE = 9600  # GPS 모듈과의 통신 속도 설정
GPS_PORTNUM = 'COM0'  # GPS 모듈이 연결된 포트 번호

def main():
    """
    NMEA 파싱을 위한 인스턴스 생성. NMEA 프로토콜을 이용하여 GPS 데이터를 해석할 수 있는 클래스의 인스턴스
    """
    parser = NMEAParser()

    # NMEA 데이터를 dictionary 형태로 저장
    nmea_data_dict = {
        "data0": "$GPRMC,123456.00,A,3734.0160,N,12643.3440,E,0.0,0.0,180923,,*30\n"
                 "$GPGGA,123456.00,3712.4058,N,12644.0063,E,1,08,1.0,100.0,M,50.0,M,,*68\n"
                 "$GPVTG,0.0,T,0.0,M,0.0,N,0.0,K*4E\n"
                 "$GPGLL,3734.0160,N,12643.3440,E,123456.00,A*06",

        "data1": "$GPGGA,123457.00,3712.4071,N,12644.0164,E,1,08,1.0,100.0,M,50.0,M,,*64\n"
                 "$GPRMC,123457.00,A,3734.0157,N,12643.3442,E,0.0,0.0,180923,,*37\n"
                 "$GPVTG,0.0,T,0.0,M,0.0,N,0.0,K*4E\n"
                 "$GPGLL,3734.0157,N,12643.3442,E,123457.00,A*01",

        "data2": "$GPGGA,123458.00,3712.4138,N,12644.0069,E,1,08,1.0,100.0,M,50.0,M,,*6B\n"
                 "$GPRMC,123458.00,A,3734.0152,N,12643.3438,E,0.0,0.0,180923,,*30\n"
                 "$GPVTG,0.0,T,0.0,M,0.0,N,0.0,K*4E\n"
                 "$GPGLL,3734.0152,N,12643.3438,E,123458.00,A*06",

        "data3": "$GPGGA,123459.00,3712.4131,N,12644.0238,E,1,08,1.0,100.0,M,50.0,M,,*65\n"
                 "$GPRMC,123459.00,A,3734.0159,N,12643.3437,E,0.0,0.0,180923,,*35\n"
                 "$GPVTG,0.0,T,0.0,M,0.0,N,0.0,K*4E\n"
                 "$GPGLL,3734.0159,N,12643.3437,E,123459.00,A*03"
    }

    # AWS S3 서비스를 이용하기 위한 클라이언트 객체 생성
    s3 = boto3.client('s3')

    # 사전에 저장된 NMEA 데이터를 순회하면서 처리
    for key in nmea_data_dict.keys():
        # NMEA 문자열을 파싱하여 GPS 데이터 추출
        parser.parse(nmea_data_dict.get(key))

        # 추출된 위도와 경도 데이터 출력
        latitude, longitude = parser.get_coordinates()
        print(f"Latitude: {latitude}, Longitude: {longitude}")

        # 데이터 처리 간 일시정지를 위해 sleep 함수 사용, 너무 빠른 처리로 인한 문제 방지
        time.sleep(2)

    # AWS S3에 데이터 전송 완료 메시지 출력
    print('AWS로 위치정보 전송')

    # 위치 데이터를 파일로 저장 후, S3에 업로드
    with open('gps_data.txt', 'rb') as f:
        s3.upload_fileobj(f, 'gpsdatasave', 'gps_data.txt')


class Worker(QThread):
    """
    멀티스레딩을 위한 Worker 클래스, QThread를 상속
    """
    def run(self):
        # 멀티스레딩 환경에서 main 함수 실행
        main()


class App(QWidget):
    """
    애플리케이션의 GUI를 정의하는 클래스, QWidget을 상속
    """
    def __init__(self):
        # 부모 클래스의 생성자 실행
        super().__init__()

        # GUI 초기화 함수 호출
        self.init_ui()

        # 멀티스레딩을 위한 Worker 클래스 인스턴스 생성
        self.worker = Worker()

    def init_ui(self):
        # 윈도우 제목과 크기 설정
        self.setWindowTitle('GPS GUI')

        # 애플리케이션 윈도우의 위치와 크기 설정: (x, y, width, height)
        self.setGeometry(300, 300, 300, 150)

        # 수직 박스 레이아웃 설정
        layout = QVBoxLayout()

        # 데이터 수집 시작 버튼 생성 및 이벤트 핸들러 연결
        self.start_btn = QPushButton('데이터 수집', self)

        # 버튼 클릭 시 start_collecting 메소드 호출
        self.start_btn.clicked.connect(self.start_collecting)

        # 데이터 수집 종료 버튼 생성 및 이벤트 핸들러 연결
        self.stop_btn = QPushButton('수집 종료', self)

        # 버튼 클릭 시 stop_collecting 메소드 호출
        self.stop_btn.clicked.connect(self.stop_collecting)

        # 버튼을 수직 레이아웃에 추가
        layout.addWidget(self.start_btn)  # '데이터 수집' 버튼
        layout.addWidget(self.stop_btn)  # '수집 종료' 버튼

        # 설정된 레이아웃을 현재 위젯에 적용
        self.setLayout(layout)

    def start_collecting(self):
        # 데이터 수집 시작 버튼 클릭 시 호출될 함수
        global END_FLAG
        END_FLAG = False
        self.worker.start()

    def stop_collecting(self):
        # 데이터 수집 종료 버튼 클릭 시 호출될 함수
        global END_FLAG
        END_FLAG = True


# 프로그램의 시작점
if __name__ == '__main__':
    app = QApplication(sys.argv)  # PyQt 애플리케이션 인스턴스 생성
    ex = App()  # 메인 윈도우 클래스의 인스턴스 생성
    ex.show()  # 생성된 윈도우 표시

    # 애플리케이션 이벤트 루프 시작:
    sys.exit(app.exec_())  # 이 코드가 실행되면 애플리케이션이 시작되어 사용자의 입력을 기다림
