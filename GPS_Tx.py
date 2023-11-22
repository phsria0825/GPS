"""
사용되는 모듈과 그 역할:
1. `pynmea2`: NMEA 데이터를 파싱하기 위한 라이브러리
    GPS 장치로부터 받은 데이터가 NMEA 형식으로 되어 있어, 모듈을 사용하여 그 형식을 해석하고 가독 가능한 데이터로 변환한다.
2. `serial`: 시리얼 포트를 통한 데이터 통신을 가능하게 하는 라이브러리 이 경우에는 GPS 장치와의 통신을 위해 사용된다.

클래스 및 함수 역할:
1. `SerialComm` 클래스:
   - `__init__`: 생성자에서는 시리얼 포트와 통신 속도 설정하고, `serial.Serial` 객체를 초기화한다.
   - `read_nmea`: 메서드는 시리얼 포트로부터 NMEA 데이터를 읽고, 문자열로 디코딩하여 반환한다.

2. `NMEAParser` 클래스:
   - `__init__`: 생성자에서는 위도와 경도를 None으로 초기화하고, GPS 데이터가 저장될 파일 경로를 설정한다.
   - `parse`: NMEA 데이터를 받아서 각 라인을 파싱한다. 특히 `$GPGGA` 형식의 문장을 찾아 위도와 경도 데이터를 추출하고 저장한다. 
              NMEA 문장을 파싱할 수 없는 경우 오류 메시지를 출력한다.
   - `get_coordinates`: 위도와 경도를 파일에 저장하고, 이 값을 반환한다.

코드의 작동 흐름:
1. `SerialComm` 객체를 생성하여 시리얼 통신을 설정한다.
2. `read_nmea` 메서드를 통해 NMEA 데이터를 지속적으로 읽는다.
3. 수신된 데이터는 `NMEAParser` 객체에 전달되어 `parse` 메서드에 의해 처리된다.
4. `parse` 메서드는 NMEA 데이터 중에서 `$GPGGA` 형식의 문장을 파싱하여 위도와 경도를 추출한다.
5. 추출된 위도와 경도 정보는 `get_coordinates` 메서드를 통해 파일에 저장된다.
"""

import pynmea2  # NMEA데이터 해석 모듈
import serial  # GPS USART 통신 모듈


"""시리얼 통신 클래스"""
class SerialComm:
    def __init__(self, port, baudrate):
        """
        생성자 초기화
        :param port: GPS 포트
        :param baudrate: GPS와의 통신속도
        """
        self.port = port
        self.baudrate = baudrate
        self.ser = serial.Serial(self.port, self.baudrate)

    def read_nmea(self):
        """
        :return : GPS NMEA데이터를 읽어오는 메소드
        """
        nmea = self.ser.readline().decode(encoding='utf-8', errors='replace')
        return nmea


"""NMEA 파싱 클래스"""
class NMEAParser:
    def __init__(self, file_path='gps_data.txt'):

        # 위도, 경도 초기화
        self.latitude = None
        self.longitude = None

        # txt 파일 저장 경로 설정
        self.file_path = file_path

    def parse(self, data):
        """
        :param data: 블루투스에서 읽어온 NMEA data
        :return: 위도, 경도
        """
        sentences = data.splitlines()  # 데이터를 줄 별로 분할

        # NMEA 데이터가 잘 받아지는지 확인하는 테스트 코드
        # print("\n")
        # print(f"Raw Data: {sentences}")  # raw 데이터 출력

        """
        분활된 NMEA데이터 문단을 for문을 통해서, 1개의 문장씩 파싱한다.
        :try : for문에서 추출된 문장을 1개씩 처리한다.
               단일 문장을 객체로 만들어 문장포맷을 해석하고, 각 속성들에 접근하게 만든다.
               속성들: https://sordid-wren-ca8.notion.site/GPS-NMEA-0183-f6f8665c7bba42c581581696a5c88160?pvs=4
              
               만약 msg의 포맷이 $GPGGA의 형식을 따르고 있는지 체크
               $GPGGA 형식이 맞으면, 위도,경도를 인스턴스 변수에 저장
        
        :except : 만약에 단일문장을 해석하는 과정에서 오류 발생시 오류 메세지 출력
        """
        for sentence in sentences:  # 문단의 각 줄을 반복 (문단을 각 포맷으로 분할)
            try:
                msg = pynmea2.parse(sentence)
                if isinstance(msg, pynmea2.types.talker.GGA):
                    print(f"Parsed Data: {msg}")  # $GPGGA 포맷만 출력
                    self.latitude = msg.latitude
                    self.longitude = msg.longitude

            except pynmea2.nmea.ParseError as e:  # 오류 발생원인 출력
                print(f"Could not parse NMEA sentence: {e}")

    def get_coordinates(self):
        """
        :return: 클래스 self변수에 저장된 위도, 경도 반환
        """
        # 위도, 경도를 txt 파일에 저장하는 함수
        with open(self.file_path, 'a') as f:
            f.write(f'{self.latitude}, {self.longitude}\n')

        return self.latitude, self.longitude
