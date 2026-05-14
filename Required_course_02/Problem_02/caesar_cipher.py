DICTIONARY = [
    "the", "be", "to", "of", "and", "a", "in", "that", "have", "it",
    "for", "not", "on", "with", "he", "as", "you", "do", "at", "this",
    "but", "his", "by", "from", "they", "we", "say", "her", "she", "or",
    "an", "will", "my", "one", "all", "would", "there", "their", "what",
    "so", "up", "out", "if", "about", "who", "get", "which", "go", "me",
    "when", "make", "can", "like", "time", "no", "just", "him", "know",
    "take", "people", "into", "year", "your", "good", "some", "could",
    "them", "see", "other", "than", "then", "now", "look", "only", "come",
    "its", "over", "think", "also", "back", "after", "use", "two", "how",
    "our", "work", "first", "well", "way", "even", "new", "want", "because",
    "any", "these", "give", "day", "most", "us", "love", "mars", "planet",
    "space", "earth", "moon", "star", "sky", "life", "world", "hello",
    "here", "home", "long", "big", "down", "did", "get", "has", "had",
    "let", "put", "too", "old", "see", "him", "his", "how", "man", "much",
    "own", "same", "tell", "very", "came", "does", "each", "find", "hand",
    "high", "keep", "last", "left", "live", "move", "name", "need", "next",
    "open", "part", "play", "read", "real", "room", "side", "small", "such",
    "sure", "talk", "turn", "used", "walk", "want", "were", "what", "when",
    "whom", "why", "wish", "with", "word", "year", "away",
]


def load_dictionary(filepath):
    words = set()
    try:
        with open(filepath, "r") as f:
            for line in f:
                word = line.strip().lower()
                if word:
                    words.add(word)
        print(f"사전 파일 '{filepath}' 로드 완료 ({len(words)}개 단어)")
    except FileNotFoundError:
        print(f"사전 파일 '{filepath}'을 찾을 수 없어 내장 사전을 사용합니다.")
    except IOError as e:
        print(f"사전 파일 읽기 오류: {e} — 내장 사전을 사용합니다.")
    return words


def matches_dictionary(text, dictionary):
    words = text.lower().split()
    for word in words:
        cleaned = "".join(c for c in word if c.isalpha())
        if len(cleaned) >= 3 and cleaned in dictionary:
            return cleaned
    return None


def caesar_cipher_decode(target_text, dictionary):
    results = {}
    auto_shift = None

    for shift in range(1, 27):
        decoded = ""
        for char in target_text:
            if char.isalpha():
                base = ord('A') if char.isupper() else ord('a')
                decoded += chr((ord(char) - base - shift) % 26 + base)
            else:
                decoded += char

        results[shift] = decoded
        matched_word = matches_dictionary(decoded, dictionary)

        if matched_word:
            print(f"Shift {shift:2d}: {decoded}  <-- 사전 단어 발견: '{matched_word}' → 반복 중단")
            auto_shift = shift
            break
        else:
            print(f"Shift {shift:2d}: {decoded}")

    return results, auto_shift


def save_result(text):
    try:
        with open("result.txt", "w") as f:
            f.write(text)
        print("result.txt에 저장되었습니다.")
    except IOError as e:
        print(f"오류: 파일을 저장하는 중 오류가 발생했습니다. {e}")


def main():
    try:
        with open("password.txt", "r") as f:
            content = f.read().strip()
        print(f"암호문: {content}")
        print("-" * 40)
    except FileNotFoundError:
        print("오류: password.txt 파일을 찾을 수 없습니다.")
        return
    except IOError as e:
        print(f"오류: 파일을 읽는 중 오류가 발생했습니다. {e}")
        return

    # 외부 사전 파일 시도 후 내장 사전으로 폴백
    dictionary = load_dictionary("dictionary.txt")
    if not dictionary:
        dictionary = set(DICTIONARY)
        print(f"내장 사전 사용 ({len(dictionary)}개 단어)")
    print("-" * 40)

    results, auto_shift = caesar_cipher_decode(content, dictionary)
    print("-" * 40)

    if auto_shift is not None:
        print(f"자동 감지된 shift: {auto_shift}")
        use_auto = input("자동 감지된 결과를 사용하시겠습니까? (y/n): ").strip().lower()
        if use_auto == "y":
            decoded_result = results[auto_shift]
            print(f"해독된 암호: {decoded_result}")
            save_result(decoded_result)
            return

    try:
        shift_num = int(input("올바른 자리수(shift)를 입력하세요 (1-26): "))
        if shift_num < 1 or shift_num > 26:
            print("오류: 1에서 26 사이의 숫자를 입력해주세요.")
            return
    except ValueError:
        print("오류: 올바른 숫자를 입력해주세요.")
        return

    # 아직 시도하지 않은 shift라면 직접 계산
    if shift_num not in results:
        decoded = ""
        for char in content:
            if char.isalpha():
                base = ord('A') if char.isupper() else ord('a')
                decoded += chr((ord(char) - base - shift_num) % 26 + base)
            else:
                decoded += char
        results[shift_num] = decoded

    decoded_result = results[shift_num]
    print(f"해독된 암호: {decoded_result}")
    save_result(decoded_result)


if __name__ == "__main__":
    main()
