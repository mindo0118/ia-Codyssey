import csv
import pickle


def load_and_convert_inventory(file_path):
    '''조건 1 & 2: CSV 내용을 읽어서 리스트(List) 객체로 변환 (출력 없음)'''
    inventory_list = []
    try:
        # PEP 8 준수: 대입문 = 앞뒤 공백
        with open(file_path, 'r', encoding='utf-8') as file:
            reader = csv.reader(file)
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
    '''조건 3: 배열 내용을 인화성이 높은 순(내림차순)으로 정렬'''
    if len(inventory_data) <= 1:
        return inventory_data
    header = inventory_data[0]
    data_rows = inventory_data[1:]
    sorted_data = sorted(data_rows, key=lambda x: float(x[4]), reverse=True)
    return [header] + sorted_data


def filter_high_flammability(inventory_data, threshold=0.7):
    '''조건 4: 인화성 지수가 특정 수치 이상인 목록 필터링'''
    if len(inventory_data) <= 1:
        return inventory_data
    header = inventory_data[0]
    filtered_rows = []
    for row in inventory_data[1:]:
        if float(row[4]) >= threshold:
            filtered_rows.append(row)
    return [header] + filtered_rows


def save_list_to_csv(data_list, file_path):
    '''조건 5: 추출된 리스트를 CSV 포맷으로 저장 (출력 없음)'''
    try:
        with open(file_path, 'w', encoding='utf-8', newline='') as file:
            writer = csv.writer(file)
            writer.writerows(data_list)
    except Exception as e:
        print('CSV 파일 저장 중 오류가 발생했습니다:', e)


def save_list_to_binary(data_list, file_path):
    '''보너스 1: 정렬된 배열을 이진 파일(Binary) 형태로 저장 (출력 없음)'''
    try:
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
        
        # --- [최종 출력 요구사항 딱 2가지 실행] ---
        
        # 출력 1: 인화성이 0.7 이상 되는 목록
        print('--- [1. 인화성 0.7 이상 격리 대상 목록] ---')
        for item in hazardous_inventory:
            print(item)
            
        # 출력 2: 이진 파일에서 복원한 전체 목록
        print('\n--- [2. 이진 파일(Mars_Base_Inventory_List.bin) 복원 내용] ---')
        for item in restored_inventory:
            print(item)