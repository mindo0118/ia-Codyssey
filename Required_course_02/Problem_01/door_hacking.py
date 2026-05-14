# door_hacking.py - 메타데이터 기반 빠른 해독 (1초 알고리즘)

import zipfile
import time
import string
import datetime
import multiprocessing
import os

CHARSET = string.ascii_lowercase + string.digits
PASSWORD_LENGTH = 6
CHUNK_SIZE = 50_000


def idx_to_password(idx, charset, length):
    """인덱스를 비밀번호 문자열로 변환 (O(length), itertools.product와 동일한 순서)"""
    base = len(charset)
    chars = []
    for _ in range(length):
        chars.append(charset[idx % base])
        idx //= base
    return "".join(reversed(chars))


def extract_metadata_indices(zip_filepath):
    """
    ZIP 메타데이터에서 인덱스 후보 생성 (1초 알고리즘)
    메타데이터: CRC-32, 파일 크기, 생성 시간, 압축 크기
    """
    try:
        with zipfile.ZipFile(zip_filepath) as zf:
            if not zf.namelist():
                return []
            
            info = zf.infolist()[0]
            crc = info.CRC
            file_size = info.file_size
            compress_size = info.compress_size
            year, month, day, hour, minute, second = info.date_time
            
            base = len(CHARSET) ** PASSWORD_LENGTH
            indices = []
            
            # A. 직접 메타데이터 사용
            indices.extend([
                file_size,
                compress_size,
                second,
                hour * 60 + minute,
                day,
                month,
                year % 100,
                day * 100 + month,
                (year % 100) * 10000 + month * 100 + day,
            ])
            
            # B. CRC 분해 (바이트 단위)
            b0 = crc & 0xFF
            b1 = (crc >> 8) & 0xFF
            b2 = (crc >> 16) & 0xFF
            b3 = (crc >> 24) & 0xFF
            
            indices.extend([
                crc % base,
                (crc >> 8) % base,
                (crc >> 16) % base,
                (crc >> 24) % base,
                b0,
                b1,
                b2,
                b3,
            ])
            
            # C. 메타데이터 조합 (XOR, 덧셈, 곱셈)
            indices.extend([
                (crc ^ file_size) % base,
                (crc + file_size) % base,
                (crc * file_size) % base if (crc * file_size) < base else (crc * file_size) % base,
                abs(crc - file_size) % base,
                (day * 100000 + month * 1000 + hour) % base,
                (minute * 60 + second) % base,
                (crc >> 16 ^ file_size) % base,
            ])
            
            # D. 중복 제거 및 범위 확인
            indices = [idx % base for idx in set(indices) if idx < base * 2]
            
            return sorted(indices)
    except Exception:
        return []


def verify_password_fast(zip_filepath, pwd):
    """빠른 비밀번호 검증 (1바이트만 읽음)"""
    try:
        with zipfile.ZipFile(zip_filepath) as zf:
            test_file = zf.namelist()[0]
            with zf.open(test_file, pwd=pwd.encode()) as f:
                f.read(1)
            return True
    except Exception:
        return False


def worker_metadata(args):
    """메타데이터 기반 인덱스를 검증하는 워커"""
    zip_filepath, charset, indices, password_length = args
    for idx in indices:
        pwd = idx_to_password(idx, charset, password_length)
        if verify_password_fast(zip_filepath, pwd):
            return pwd
    return None



def worker(args):
    """워커 프로세스: 지정된 인덱스 범위의 비밀번호를 시도"""
    zip_filepath, charset, start_idx, end_idx, password_length = args
    try:
        zf = zipfile.ZipFile(zip_filepath)
        test_file = zf.namelist()[0]
    except Exception:
        return None

    for i in range(start_idx, end_idx):
        guess = idx_to_password(i, charset, password_length)
        try:
            # extractall 대신 첫 파일 1바이트만 읽어 빠르게 검증
            with zf.open(test_file, pwd=guess.encode()) as f:
                f.read(1)
            zf.close()
            return guess
        except Exception:
            pass

    zf.close()
    return None


def unlock_zip(zip_filepath=None):
    if zip_filepath is None:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        zip_filepath = os.path.join(script_dir, "emergency_storage_key.zip")

    zip_filepath = os.path.abspath(zip_filepath)
    charset = CHARSET
    password_length = PASSWORD_LENGTH
    total = len(charset) ** password_length
    num_workers = multiprocessing.cpu_count()

    start_time = time.time()
    print("=" * 60)
    print(f"[*] ZIP 암호 해독 (메타데이터 기반 1초 알고리즘)")
    print(f"[*] 대상 파일: {zip_filepath}")
    print(f"[*] 시작 시간: {datetime.datetime.now():%Y-%m-%d %H:%M:%S}")
    print(f"[*] 총 조합: {total:,} | 프로세스: {num_workers} | 청크: {CHUNK_SIZE:,}")
    print("=" * 60)

    try:
        with zipfile.ZipFile(zip_filepath):
            pass
    except FileNotFoundError:
        print(f"[!] 파일 없음: {zip_filepath}")
        return None
    except zipfile.BadZipFile:
        print(f"[!] 유효하지 않은 ZIP 파일")
        return None

    # 1단계: 메타데이터 기반 빠른 검증 (1초 이내)
    print("\n[*] Phase 1: 메타데이터 기반 후보 검증 중...")
    metadata_start = time.time()
    metadata_indices = extract_metadata_indices(zip_filepath)
    
    if metadata_indices:
        print(f"[*] 메타데이터 인덱스 후보: {len(metadata_indices)}개")
        
        # 병렬로 메타데이터 인덱스 검증
        with multiprocessing.Pool(num_workers) as pool:
            chunk_size = max(1, len(metadata_indices) // (num_workers * 4))
            chunks = [
                (zip_filepath, charset, metadata_indices[i:i+chunk_size], password_length)
                for i in range(0, len(metadata_indices), chunk_size)
            ]
            
            for result in pool.imap_unordered(worker_metadata, chunks):
                if result is not None:
                    metadata_elapsed = time.time() - metadata_start
                    total_elapsed = time.time() - start_time
                    print(f"\n{'=' * 60}")
                    print(f"[+] 메타데이터 방식으로 암호 해독 성공!")
                    print(f"[+] 암호: {result}")
                    print(f"[+] 메타데이터 단계 소요: {metadata_elapsed:.4f}초")
                    print(f"[+] 전체 소요 시간: {total_elapsed:.4f}초")
                    print(f"{'=' * 60}")
                    
                    with zipfile.ZipFile(zip_filepath) as zf:
                        zf.extractall(path=os.path.dirname(zip_filepath), pwd=result.encode())
                    print(f"[+] 압축 해제 완료: {os.path.dirname(zip_filepath)}")
                    
                    pwd_path = os.path.join(os.path.dirname(zip_filepath), "password.txt")
                    with open(pwd_path, "w", encoding="utf-8") as f:
                        f.write(result)
                    print(f"[+] 비밀번호 저장: {pwd_path}")
                    return result
    
    metadata_elapsed = time.time() - metadata_start
    print(f"[-] 메타데이터 방식 실패 ({metadata_elapsed:.4f}초) → Phase 2: 전체 브루트포스로 전환")
    
    # 2단계: 전통적인 멀티프로세싱 브루트포스 (폴백)
    print("\n[*] Phase 2: 전체 브루트포스 시작...")
    brute_start = time.time()
    
    chunks = [
        (zip_filepath, charset, i, min(i + CHUNK_SIZE, total), password_length)
        for i in range(0, total, CHUNK_SIZE)
    ]

    chunks_done = 0
    last_print_time = brute_start

    with multiprocessing.Pool(num_workers) as pool:
        for result in pool.imap_unordered(worker, chunks, chunksize=1):
            chunks_done += 1

            if result is not None:
                pool.terminate()
                brute_elapsed = time.time() - brute_start
                total_elapsed = time.time() - start_time
                print(f"\n{'=' * 60}")
                print(f"[+] 브루트포스로 암호 해독 성공!")
                print(f"[+] 암호: {result}")
                print(f"[+] 브루트포스 단계 소요: {brute_elapsed:.2f}초")
                print(f"[+] 전체 소요 시간: {total_elapsed:.2f}초")
                print(f"{'=' * 60}")

                with zipfile.ZipFile(zip_filepath) as zf:
                    zf.extractall(path=os.path.dirname(zip_filepath), pwd=result.encode())
                print(f"[+] 압축 해제 완료: {os.path.dirname(zip_filepath)}")

                pwd_path = os.path.join(os.path.dirname(zip_filepath), "password.txt")
                with open(pwd_path, "w", encoding="utf-8") as f:
                    f.write(result)
                print(f"[+] 비밀번호 저장: {pwd_path}")
                return result

            now = time.time()
            if now - last_print_time >= 10:
                last_print_time = now
                elapsed = now - brute_start
                done = chunks_done * CHUNK_SIZE
                pct = min(done / total * 100, 100)
                speed = done / elapsed
                eta = (total - done) / speed
                print(f"[-] {pct:.1f}% ({done:,}/{total:,}) | {speed:,.0f}/초 | 예상 남은: {eta:.0f}초")

    total_elapsed = time.time() - start_time
    print(f"\n[-] 암호를 찾지 못했습니다. (소요: {total_elapsed:.2f}초)")
    return None


if __name__ == "__main__":
    unlock_zip()
