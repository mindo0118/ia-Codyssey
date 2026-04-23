import sys
from pathlib import Path

try:
    from PyQt6.QtCore import Qt
    from PyQt6.QtGui import QFont, QFontMetrics
    from PyQt6.QtWidgets import (
        QApplication,
        QGridLayout,
        QLabel,
        QPushButton,
        QVBoxLayout,
        QWidget
    )
    ALIGN_RIGHT = Qt.AlignmentFlag.AlignRight
    ALIGN_VCENTER = Qt.AlignmentFlag.AlignVCenter
except ImportError:
    from PyQt5.QtCore import Qt
    from PyQt5.QtGui import QFont, QFontMetrics
    from PyQt5.QtWidgets import (
        QApplication, QGridLayout, QLabel, QPushButton, QVBoxLayout, QWidget
    )
    ALIGN_RIGHT = Qt.AlignRight
    ALIGN_VCENTER = Qt.AlignVCenter


class CalculatorWindow(QWidget):
    """숫자와 사칙연산 기호가 화면에 누적되어 표시되는 UI 클래스입니다."""

    WINDOW_TITLE = 'iPhone Style Calculator'
    WINDOW_SIZE = (360, 640)
    ROOT_MARGINS = (14, 20, 14, 20)
    ROOT_SPACING = 10
    TOP_STRETCH = 1
    DISPLAY_SPACING = 4
    BUTTON_SPACING = 10
    DISPLAY_MAX_FONT_SIZE = 40
    DISPLAY_MIN_FONT_SIZE = 20
    DISPLAY_SIDE_PADDING = 16
    DISPLAY_MIN_AVAILABLE_WIDTH = 40
    FONT_FAMILY = 'Helvetica Neue'
    BASIC_OPERATORS = frozenset({'+', '-', '*', '/'})
    TOKEN_SPLIT_OPERATORS = frozenset({'+', '-', '*', '/', '%'})
    NON_MINUS_OPERATORS = frozenset({'+', '*', '/'})

    def __init__(self):
        # 상태 초기화 및 창 설정, 스타일 로드, UI 구성 순으로 진행합니다.
        super().__init__()
        self.raw_text = '0'
        self.wrap_leading_negative = False
        self.ac_button = None
        self._show_ac = False
        
        self.setWindowTitle(self.WINDOW_TITLE)
        self.setFixedSize(*self.WINDOW_SIZE)
        self._load_stylesheet()
        self._build_ui()

    def _load_stylesheet(self):
        # calculator.qss 파일을 읽어 위젯 전체에 스타일을 적용합니다.
        style_path = Path(__file__).with_name('calculator.qss')
        self.setStyleSheet(style_path.read_text(encoding='utf-8'))

    def _build_ui(self):
        # 레이아웃, 디스플레이 라벨, 버튼 그리드를 생성하고 이벤트를 연결합니다.
        root_layout = QVBoxLayout()
        root_layout.setContentsMargins(*self.ROOT_MARGINS)
        root_layout.setSpacing(self.ROOT_SPACING)
        self.setLayout(root_layout)

        # 상단 여백을 크게 두어 iOS 계산기 비율과 유사하게 맞춥니다.
        root_layout.addStretch(self.TOP_STRETCH)

        display_layout = QVBoxLayout()
        display_layout.setContentsMargins(0, 0, 0, 0)
        display_layout.setSpacing(self.DISPLAY_SPACING)

        self.expression_display = QLabel('')
        self.expression_display.setObjectName('expressionDisplay')
        self.expression_display.setAlignment(ALIGN_RIGHT | ALIGN_VCENTER)
        display_layout.addWidget(self.expression_display)

        # 메인 출력창
        self.display = QLabel('0')
        self.display.setObjectName('mainDisplay')
        self.display.setAlignment(ALIGN_RIGHT | ALIGN_VCENTER)
        display_layout.addWidget(self.display)
        root_layout.addLayout(display_layout)

        button_layout = QGridLayout()
        button_layout.setHorizontalSpacing(self.BUTTON_SPACING)
        button_layout.setVerticalSpacing(self.BUTTON_SPACING)
        root_layout.addLayout(button_layout)

        buttons = [
            [('⌫', 'function'), ('AC', 'function'), ('%', 'function'), ('/', 'operator')],
            [('7', 'number'), ('8', 'number'), ('9', 'number'), ('*', 'operator')],
            [('4', 'number'), ('5', 'number'), ('6', 'number'), ('-', 'operator')],
            [('1', 'number'), ('2', 'number'), ('3', 'number'), ('+', 'operator')],
            [('+/-', 'function'), ('0', 'number'), ('.', 'number'), ('=', 'operator')],
        ]

        for row_index, row in enumerate(buttons):
            column_index = 0
            for label, role in row:
                button = QPushButton(label)
                button.setProperty('role', role)
                button.clicked.connect(self._handle_button_click)

                if label == 'AC':
                    self.ac_button = button

                button_layout.addWidget(button, row_index, column_index)
                column_index += 1

    def _append_operator(self, current_text, operator):
        # 연산자 입력 규칙을 처리합니다. /- 와 *- 조합은 허용하고, 그 외 연속 연산자는 마지막 하나로 교체합니다.
        if current_text == '0':
            return '0' if operator != '-' else '-'

        if current_text.endswith(('/-', '*-')) and operator in self.NON_MINUS_OPERATORS:
            return current_text[:-2] + operator

        last_char = current_text[-1]
        if last_char in {'*', '/'} and operator == '-':
            return current_text + operator

        if last_char in self.BASIC_OPERATORS:
            return current_text[:-1] + operator

        return current_text + operator

    def _append_percent(self, current_text):
        # 마지막 문자가 숫자일 때만 % 기호를 뒤에 붙입니다.
        if current_text[-1].isdigit():
            return current_text + '%'
        return current_text

    def _toggle_plus_minus(self, text):
        # 마지막 숫자 토큰의 부호를 앞 연산자와 조합해 전환합니다. 예: 66-22 → 66+22 → 66+(-22) → 66+22 (3단계 사이클)
        if text in {'', '0'} or text[-1] in self.BASIC_OPERATORS:
            return text, False

        index = len(text) - 1
        while index >= 0 and text[index] not in self.BASIC_OPERATORS:
            index -= 1

        token_start = index + 1
        prefix = text[:token_start]
        token = text[token_start:]

        # 마지막 숫자가 단항 음수인 경우(예: 66+-22), 음수 부호를 토큰에 포함합니다.
        if token_start > 0 and text[token_start - 1] == '-':
            minus_index = token_start - 1
            if minus_index == 0 or text[minus_index - 1] in self.BASIC_OPERATORS:
                prefix = text[:minus_index]
                token = text[minus_index:]
                token_start = minus_index

        prev_operator = prefix[-1] if prefix and prefix[-1] in self.BASIC_OPERATORS else ''
        is_negative = token.startswith('-')
        abs_token = token[1:] if is_negative else token

        if is_negative:
            # 음수 토큰: 부호 제거
            if prev_operator == '+':
                # 66+(-22) → 66+22
                return prefix + abs_token, False
            if prev_operator == '-':
                # 66-(-22) → 66+22
                return prefix[:-1] + '+' + abs_token, False
            # * / 뒤 또는 시작: 음수 제거
            return prefix + abs_token, False
        else:
            # 양수 토큰
            if prev_operator == '-':
                # (연산자만 반전)
                return prefix[:-1] + '+' + token, False
            if prev_operator == '+':
                # (연산자 유지, 음수화)
                return prefix + '-' + token, False
            # * / 뒤 또는 시작: 음수화
            wrap_leading = token_start == 0
            return prefix + '-' + token, wrap_leading

    def _group_digits(self, digits):
        # 정수 문자열을 세 자리마다 콤마로 구분합니다. 예: '1234567' → '1,234,567'
        if not digits or not digits.isdigit():
            return digits
        chunks = []
        while digits:
            chunks.append(digits[-3:])
            digits = digits[:-3]
        return ','.join(reversed(chunks))

    def _format_number_token(self, token, wrap_negative):
        # 숫자 토큰 하나를 포맷합니다. 음수는 wrap_negative 여부에 따라 -123 또는 (-123) 형태로 표시합니다.
        suffix = ''
        if token.endswith('%'):
            suffix = '%'
            token = token[:-1]

        if token in {'', '-', '.', '-.'}:
            return token + suffix

        is_negative = False
        if token.startswith('-'):
            is_negative = True
            token = token[1:]

        formatted_core = ''
        if '.' in token:
            integer_part, fractional_part = token.split('.', 1)
            grouped_integer = self._group_digits(integer_part) if integer_part else ''
            formatted_core = f'{grouped_integer}.{fractional_part}'
        else:
            formatted_core = self._group_digits(token)

        if is_negative and wrap_negative:
            formatted_core = f'(-{formatted_core})'
        elif is_negative:
            formatted_core = f'-{formatted_core}'

        return f'{formatted_core}{suffix}'

    def _format_expression(self, text):
        # raw_text 전체를 순회해 연산자와 숫자 토큰을 나눈 뒤, 숫자에만 콤마 포맷을 적용합니다.
        result = []
        token = ''
        token_start_index = 0

        for index, char in enumerate(text):
            if char in self.TOKEN_SPLIT_OPERATORS:
                is_unary_minus = char == '-' and (index == 0 or text[index - 1] in self.TOKEN_SPLIT_OPERATORS)
                if is_unary_minus:
                    if not token:
                        token_start_index = index
                    token += char
                    continue

                if token:
                    should_wrap_negative = token_start_index > 0 or (
                        token_start_index == 0 and self.wrap_leading_negative
                    )
                    result.append(self._format_number_token(token, wrap_negative=should_wrap_negative))
                    token = ''
                result.append(char)
                continue

            if not token:
                token_start_index = index
            token += char

        if token:
            should_wrap_negative = token_start_index > 0 or (
                token_start_index == 0 and self.wrap_leading_negative
            )
            result.append(self._format_number_token(token, wrap_negative=should_wrap_negative))

        return ''.join(result) if result else '0'

    def _set_display_from_raw(self, raw_text, leading_negative_wrapped=None):
        # 화면 갱신의 단일 진입점입니다. raw_text 저장 → 음수 괄호 상태 조정 → 포맷 → 폰트 크기 조정 → 화면 반영 순으로 처리합니다.
        self.raw_text = raw_text if raw_text else '0'
        if leading_negative_wrapped is not None:
            self.wrap_leading_negative = leading_negative_wrapped

        if (
            not self.raw_text.startswith('-')
            or any(op in self.raw_text[1:] for op in '+*/')
            or '-' in self.raw_text[1:]
        ):
            self.wrap_leading_negative = False

        formatted_text = self._format_expression(raw_text)
        self._adjust_display_font_size(formatted_text)
        self.display.setText(formatted_text)
        self._update_ac_button()

    def _update_ac_button(self):
        # 현재 상태에 따라 버튼 문구를 'C' 또는 'AC'로 전환합니다.
        if self.ac_button is not None:
            show_c = self.raw_text != '0' and not self._show_ac
            self.ac_button.setText('C' if show_c else 'AC')

    def _adjust_display_font_size(self, text):
        # 표시 문자열 길이에 따라 폰트 크기를 줄여 화면이 넘치지 않게 합니다.
        display_text = text if text else '0'
        available_width = max(self.DISPLAY_MIN_AVAILABLE_WIDTH, self.display.width() - self.DISPLAY_SIDE_PADDING)
        font_size = self.DISPLAY_MAX_FONT_SIZE

        while font_size > self.DISPLAY_MIN_FONT_SIZE:
            test_font = QFont(self.FONT_FAMILY, font_size)
            if QFontMetrics(test_font).horizontalAdvance(display_text) <= available_width:
                break
            font_size -= 1

        self.display.setFont(QFont(self.FONT_FAMILY, font_size))

    def _handle_digit_input(self, value, current_text):
        # 숫자 버튼 처리: 현재 값이 '0'이면 교체, 아니면 이어 붙입니다.
        self._show_ac = False
        if current_text == '0':
            self._set_display_from_raw(value, leading_negative_wrapped=False)
        else:
            self._set_display_from_raw(current_text + value)

    def _handle_operator_input(self, value, current_text):
        # 연산자 버튼 처리: _append_operator 규칙에 따라 raw_text를 갱신합니다.
        self._show_ac = False
        next_text = self._append_operator(current_text, value)
        is_manual_leading_minus = current_text == '0' and value == '-'
        self._set_display_from_raw(next_text, leading_negative_wrapped=False if is_manual_leading_minus else None)

    def _handle_decimal_input(self, current_text):
        # 소수점 버튼 처리: 마지막 문자가 이미 소수점이면 무시합니다.
        self._show_ac = False
        if not current_text.endswith('.'):
            self._set_display_from_raw(current_text + '.')

    def _handle_c_input(self, current_text):
        # C 버튼 처리: 마지막 숫자 토큰을 지웁니다. 연산자로 끝나는 상태면 화면은 그대로 두고 버튼만 AC로 전환합니다.
        if current_text[-1] in self.TOKEN_SPLIT_OPERATORS:
            # 연산자로 끝나는 상태: 화면 변화 없이 버튼만 AC로 전환
            self._show_ac = True
            self._update_ac_button()
            return

        # 마지막 숫자 토큰만 제거
        idx = len(current_text) - 1
        while idx >= 0 and current_text[idx] not in self.TOKEN_SPLIT_OPERATORS:
            idx -= 1

        if idx < 0:
            # 연산자 없음 → 숫자만 있던 상태, 0으로 초기화
            self._show_ac = False
            self._set_display_from_raw('0', leading_negative_wrapped=False)
            return

        # 연산자 뒤 숫자만 지우고 연산자까지 남김
        # 결과가 연산자로 끝나므로 버튼은 AC로 전환
        self._show_ac = True
        self._set_display_from_raw(current_text[:idx + 1])

    def _handle_ac_input(self, _current_text):
        # AC 버튼 처리: expression_display와 raw_text를 모두 초기 상태로 되돌립니다.
        self._show_ac = False
        self.expression_display.setText('')
        self._set_display_from_raw('0', leading_negative_wrapped=False)

    def _handle_percent_input(self, current_text):
        # % 버튼 처리: 숫자 뒤에 % 기호를 붙입니다.
        self._set_display_from_raw(self._append_percent(current_text))

    def _handle_plus_minus_input(self, current_text):
        # +/- 버튼 처리: 마지막 숫자 토큰의 부호를 전환합니다.
        toggled_text, wrap_leading = self._toggle_plus_minus(current_text)
        self._set_display_from_raw(toggled_text, leading_negative_wrapped=wrap_leading)

    def _handle_backspace_input(self, current_text):
        # ⌫ 버튼 처리: raw_text의 마지막 문자를 하나 제거합니다.
        if len(current_text) <= 1:
            self._set_display_from_raw('0')
        else:
            self._set_display_from_raw(current_text[:-1])

    def _handle_button_click(self):
        # 모든 버튼 클릭의 진입점입니다. 버튼 텍스트를 보고 전용 핸들러로 분배합니다.
        button = self.sender()
        if button is None:
            return

        value = button.text()
        current_text = self.raw_text

        if value.isdigit():
            self._handle_digit_input(value, current_text)
            return

        handlers = {
            '.': self._handle_decimal_input,
            'C': self._handle_c_input,
            'AC': self._handle_ac_input,
            '%': self._handle_percent_input,
            '+/-': self._handle_plus_minus_input,
            '⌫': self._handle_backspace_input,
        }

        if value in self.BASIC_OPERATORS:
            self._handle_operator_input(value, current_text)
            return

        handler = handlers.get(value)
        if handler is not None:
            handler(current_text)
            return

        print(f"[{value}] 버튼이 눌렸습니다.")


def main():
    # QApplication을 생성하고 계산기 창을 띄우는 프로그램 진입점입니다.
    app = QApplication(sys.argv)
    window = CalculatorWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    main()