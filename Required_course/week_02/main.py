import csv
import pickle


def load_and_convert_inventory(file_path):
    '''조건 1 & 2: CSV 내용을 읽어서 딕셔너리(Dict)의 리스트로 변환'''
    inventory_list = []
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            # csv.reader 대신 csv.DictReader 사용
            reader = csv.DictReader(file)
            for row in reader:
                inventory_list.append(row)
        return inventory_list
    except FileNotFoundError:
        # 가이드 준수: 문자열 내에 '가 포함될 경우 " " 사용
        print("에러: '" + file_path + "' 파일을 찾을 수 없습니다.")
        return []
    except Exception as e:
        print('예상치 못한 오류가 발생했습니다:', e)
        return []


def sort_by_flammability(inventory_data):
    '''조건 3: 딕셔너리 배열을 인화성(Flammability) 기준으로 내림차순 정렬'''
    if not inventory_data:
        return inventory_data
        
    # 딕셔너리는 헤더를 분리할 필요가 없습니다.
    # 인덱스 [4] 대신, 이름표 'Flammability'를 직관적으로 호출합니다.
    sorted_data = sorted(inventory_data, key=lambda x: float(x['Flammability']), reverse=True)
    return sorted_data


def filter_high_flammability(inventory_data, threshold=0.7):
    '''조건 4: 인화성 지수가 특정 수치 이상인 목록 필터링'''
    if not inventory_data:
        return inventory_data
        
    filtered_rows = []
    for row in inventory_data:
        if float(row['Flammability']) >= threshold:
            filtered_rows.append(row)
    return filtered_rows


def save_list_to_csv(data_list, file_path):
    '''조건 5: 추출된 딕셔너리 리스트를 CSV 포맷으로 저장'''
    if not data_list:
        return
        
    try:
        with open(file_path, 'w', encoding='utf-8', newline='') as file:
            # 딕셔너리의 키(Key)들을 추출하여 CSV의 헤더로 사용합니다.
            fieldnames = data_list[0].keys()
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            
            writer.writeheader()  # 첫 줄에 컬럼명(헤더)을 써줍니다.
            writer.writerows(data_list)  # 나머지 딕셔너리 데이터를 기록합니다.
    except Exception as e:
        print('CSV 파일 저장 중 오류가 발생했습니다:', e)


def save_list_to_binary(data_list, file_path):
    '''보너스 1: 딕셔너리 배열을 이진 파일(Binary) 형태로 저장'''
    try:
        # pickle은 딕셔너리 리스트도 완벽하게 압축 포장합니다.
        with open(file_path, 'wb') as file:
            pickle.dump(data_list, file)
    except Exception as e:
        print('이진 파일 저장 중 오류가 발생했습니다:', e)


def load_list_from_binary(file_path):
    '''보너스 2: 저장된 이진 파일을 다시 읽어 들여서 반환'''
    try:
        with open(file_path, 'rb') as file:
            loaded_data = pickle.load(file)
        return loaded_data
    except FileNotFoundError:
        print("에러: '" + file_path + "' 이진 파일을 찾을 수 없습니다.")
        return []
    except Exception as e:
        print('이진 파일 읽기 중 오류가 발생했습니다:', e)
        return []


# --- [메인 컨트롤 타워] ---
if __name__ == '__main__':
    # 파일명 세팅
    input_file = 'Mars_Base_Inventory_List.csv'
    output_csv = 'Mars_Base_Inventory_danger.csv'
    binary_file = 'Mars_Base_Inventory_List.bin'
    
    # 1. 파일 로드 및 정렬
    mars_inventory = load_and_convert_inventory(input_file)
    
    if len(mars_inventory) > 0:
        sorted_inventory = sort_by_flammability(mars_inventory)
        
        # 2. 0.7 이상 필터링 및 CSV, BIN 파일 백그라운드 저장
        hazardous_inventory = filter_high_flammability(sorted_inventory, threshold=0.7)
        save_list_to_csv(hazardous_inventory, output_csv)
        save_list_to_binary(sorted_inventory, binary_file)
        
        # 3. 이진 파일에서 내용 다시 읽어 들이기
        restored_inventory = load_list_from_binary(binary_file)

        # 출력 1: 인화성이 0.7 이상 되는 목록
        print('--- [1. 인화성 0.7 이상 격리 대상 목록 (딕셔너리 구조)] ---')
        for item in hazardous_inventory:
            print(*item.values(), sep=', ')
            
        # 출력 2: 이진 파일에서 복원한 전체 목록
        print('\n--- [2. 이진 파일(Mars_Base_Inventory_List.bin) 복원 내용 (딕셔너리 구조)] ---')
        for item in restored_inventory:
            print(*item.values(), sep=', ')