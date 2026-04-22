def main():
    file_path = 'mission_computer_main.log'
    save_path = 'problem_logs.txt'  # 사고 로그 전용 파일명
    # 사고 판단 기준 키워드
    critical_keywords = ['unstable', 'explosion']
    
    try:
        # [실행] 읽기용(file)과 쓰기용(f_out) 파일을 동시에 엽니다.
        with open(file_path, 'r', encoding='utf-8') as file, \
             open(save_path, 'w', encoding='utf-8') as f_out:
            
            logs = file.readlines()
            print(f"총 {len(logs)}줄의 로그를 분석합니다.")
            f_out.write(f"--- 사고 원인 추출 결과 (최신순) ---\n")

            # 로그 내용을 화면에 출력 및 파일 저장 ---
            print("--- [로그 분석 시작] ---")
            
            # --- 박사님의 리스트 슬라이싱 [::-1] 유지 ---
            for line in logs[::-1]:
                clean_line = line.strip()
                
                # 1. 화면 로그 출력
                print(clean_line)
                
                # 2. 사고 키워드가 포함되어 있다면 파일에 기록
                # any()를 사용해 키워드 중 하나라도 걸리면 저장합니다.
                if any(key in clean_line for key in critical_keywords):
                    f_out.write(clean_line + "\n")
            
            print("--- [로그 분석 끝] ---\n")

    # [OSError] 파일/시스템 관련 오류
    except OSError as e:
        print(f"[시스템 오류] {type(e).__name__}: {e}")

    # [Data Errors] 데이터 형식 관련 오류
    except (ValueError, TypeError, IndexError) as e:
        print(f"[데이터 오류] {type(e).__name__}: {e}")

    # [Exception] 그 외 모든 돌발 사고
    except Exception as e:
        print(f"[기타 오류] {type(e).__name__}: {e}")

if __name__ == "__main__":
    main()