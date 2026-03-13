# 기본 과제
def main():
    # 파일명 설정
    file_path = 'mission_computer_main.log'
    
    try:
        # 파일을 읽기 모드('r')와 UTF-8 인코딩으로 열기
        with open(file_path, 'r', encoding='utf-8') as file:
            # 전체 내용을 읽어 화면에 출력
            log_content = file.read()
            
            if not log_content:
                print('로그 파일은 존재하나 내용이 비어 있습니다.')
            else:
                print(log_content)
                
    except FileNotFoundError:
        # 파일이 없을 경우 발생하는 예외 처리
        print(f"오류: '{file_path}' 파일을 찾을 수 없습니다.")
        print('파일이 현재 폴더에 있는지 확인해 주세요.')
        
    except UnicodeDecodeError:
        # 파일 인코딩이 맞지 않을 경우 발생하는 예외 처리
        print('오류: 파일을 읽는 중 인코딩 에러가 발생했습니다.')
        
    except Exception as e:
        # 그 외 예상치 못한 모든 예외 처리
        print(f'알 수 없는 시스템 오류가 발생했습니다: {e}')

if __name__ == '__main__':
    main()
    
# # 보너스 과제

# def main():
#     file_path = 'mission_computer_main.log'
#     error_file_path = 'critical_issues.log'
    
#     try:
#         with open(file_path, 'r', encoding='utf-8') as file:
#             # 파일의 각 줄을 리스트로 읽어오기
#             lines = file.readlines()
            
#             if not lines:
#                 print('로그 파일이 비어 있습니다.')
#                 return

#             # 첫 번째 줄(헤더)과 나머지 데이터 분리
#             header = lines[0].strip()
#             data_lines = lines[1:]

#             # 1. 시간의 역순으로 정렬 (리스트 뒤집기)
#             reversed_lines = data_lines[::-1]

#             print(f'--- [로그 출력: 시간 역순] ---')
#             print(header)
#             for line in reversed_lines:
#                 print(line.strip())

#             # 2. 문제가 되는 부분(unstable, explosion)만 추출하여 파일 저장
#             # 'INFO' 등급이지만 메시지 내용에 문제 키워드가 있는 것을 필터링
#             problem_keywords = ['unstable', 'explosion']
#             critical_logs = []

#             for line in data_lines:
#                 # 소문자로 변환하여 검색 (대소문자 구분 방지)
#                 if any(key in line.lower() for key in problem_keywords):
#                     critical_logs.append(line)

#             # 필터링된 내용을 별도 파일로 저장
#             if critical_logs:
#                 with open(error_file_path, 'w', encoding='utf-8') as error_file:
#                     error_file.write(header + '\n')
#                     error_file.writelines(critical_logs)
#                 print(f'\n--- [알림: 문제 로그 저장 완료] ---')
#                 print(f"'{error_file_path}' 파일에 {len(critical_logs)}개의 이벤트를 기록했습니다.")

#     except FileNotFoundError:
#         print(f"오류: '{file_path}' 파일을 찾을 수 없습니다.")
#     except Exception as e:
#         print(f'알 수 없는 오류 발생: {e}')

# if __name__ == '__main__':
#     main()