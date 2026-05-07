# door_hacking.py

import zipfile
import itertools
import time
import string
import datetime
import os

def unlock_zip(zip_filepath="emergency_storage_key.zip"):
    # 사용할 문자셋: 소문자 알파벳 + 숫자
    charset = string.ascii_lowercase + string.digits
    password_length = 6
    
    # 시작 시간 기록
    start_time = time.time()
    start_datetime = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    print("=" * 50)
    print(f"[*] ZIP 암호 해독(브루트포스)을 시작합니다.")
    print(f"[*] 대상 파일: {zip_filepath}")
    print(f"[*] 작업 시작 시간: {start_datetime}")
    print("=" * 50)

    # ZIP 파일 객체 생성 (예외 처리 포함)
    try:
        zFile = zipfile.ZipFile(zip_filepath)
    except FileNotFoundError:
        print(f"[!] 에러: '{zip_filepath}' 파일을 찾을 수 없습니다. 파일 경로를 확인해주세요.")
        return
    except zipfile.BadZipFile:
        print(f"[!] 에러: '{zip_filepath}' 파일이 손상되었거나 유효한 ZIP 파일이 아닙니다.")
        return
    except Exception as e:
        print(f"[!] ZIP 파일을 여는 중 알 수 없는 에러가 발생했습니다: {e}")
        return

    attempts = 0
    total_combinations = len(charset) ** password_length
    print(f"[*] 시도할 최대 조합 수: {total_combinations:,} 개")
    print("[*] 해독 진행 중... (10만 번 시도마다 진행 상황을 출력합니다)\n")

    # itertools.product를 사용하여 6자리 중복 순열(모든 경우의 수) 생성
    for guess_tuple in itertools.product(charset, repeat=password_length):
        attempts += 1
        guess = "".join(guess_tuple)

        # 진행 상황 출력 (너무 많은 출력을 방지하기 위해 100,000번 마다 출력)
        if attempts % 100000 == 0:
            elapsed = time.time() - start_time
            print(f"[-] 진행 중... 반복 횟수: {attempts:,}회 | 경과 시간: {elapsed:.2f}초 | 현재 테스트 암호: {guess}")

        try:
            # 암호를 바이트(bytes) 형태로 변환하여 압축 해제 시도
            zFile.extractall(pwd=guess.encode('utf-8'))
            
            # 성공했을 경우 처리
            elapsed_time = time.time() - start_time
            print("\n" + "=" * 50)
            print(f"[+] 암호 해독 성공!")
            print(f"[+] 찾아낸 암호: {guess}")
            print(f"[+] 총 반복(시도) 횟수: {attempts:,}회")
            print(f"[+] 총 소요 시간: {elapsed_time:.2f}초")
            print("=" * 50)

            # 암호를 password.txt에 저장 (예외 처리 포함)
            try:
                with open("password.txt", "w", encoding="utf-8") as f:
                    f.write(guess)
                print(f"[+] 성공적으로 암호를 'password.txt' 파일에 저장했습니다.")
            except IOError as e:
                print(f"[!] 암호를 파일로 저장하는 중 오류가 발생했습니다: {e}")
            except Exception as e:
                print(f"[!] 파일 저장 중 알 수 없는 에러 발생: {e}")

            zFile.close()
            return guess

        except RuntimeError as e:
            # 비밀번호가 틀렸을 때 발생하는 기본 에러 무시
            pass
        except Exception as e:
            # 지원하지 않는 암호화 방식 등 기타 에러 무시 (경고창 방지)
            pass

    # 모든 경우의 수를 시도했으나 실패한 경우
    elapsed_time = time.time() - start_time
    print("\n" + "=" * 50)
    print(f"[-] 암호를 찾지 못했습니다.")
    print(f"[-] 총 시도 횟수: {attempts:,}회 | 총 소요 시간: {elapsed_time:.2f}초")
    print("=" * 50)
    
    zFile.close()
    return None

if __name__ == '__main__':
    # 함수 실행
    unlock_zip()