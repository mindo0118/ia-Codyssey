import sys

try:
    from PyQt6.QtCore import Qt
    from PyQt6.QtGui import QFont
    from PyQt6.QtWidgets import (
        QApplication,
        QGridLayout,
        QLabel,
        QPushButton,
        QVBoxLayout,
        QWidget,
    )

    ALIGN_RIGHT = Qt.AlignmentFlag.AlignRight
    ALIGN_VCENTER = Qt.AlignmentFlag.AlignVCenter
except ImportError:
    from PyQt5.QtCore import Qt
    from PyQt5.QtGui import QFont
    from PyQt5.QtWidgets import (
        QApplication,
        QGridLayout,
        QLabel,
        QPushButton,
        QVBoxLayout,
        QWidget,
    )

    ALIGN_RIGHT = Qt.AlignRight
    ALIGN_VCENTER = Qt.AlignVCenter


class CalculatorWindow(QWidget):
    """아이폰 계산기와 유사한 배치의 계산기 창을 구성한다."""

    def __init__(self):
        super().__init__()
        self.current_input = '0'
        self.left_operand = None
        self.pending_operator = None
        self.waiting_for_new_input = False

        self.setWindowTitle('iPhone Style Calculator')
        self.setFixedSize(360, 620)
        self._build_ui()
        self._update_display()

    def _build_ui(self):
        """전체 레이아웃과 버튼을 생성하고 시그널을 연결한다."""
        root_layout = QVBoxLayout()
        root_layout.setContentsMargins(16, 16, 16, 16)
        root_layout.setSpacing(12)
        self.setLayout(root_layout)

        display_layout = QVBoxLayout()
        display_layout.setContentsMargins(0, 0, 0, 0)
        display_layout.setSpacing(6)

        # 현재 선택된 연산자와 이전 피연산자를 작게 보여주는 상태 표시줄이다.
        self.expression_display = QLabel('')
        self.expression_display.setAlignment(ALIGN_RIGHT | ALIGN_VCENTER)
        self.expression_display.setFont(QFont('Arial', 14))
        self.expression_display.setStyleSheet('color: #a5a5a5; padding: 0 6px;')
        display_layout.addWidget(self.expression_display)

        # 계산 결과와 입력 중인 숫자를 크게 보여주는 출력창이다.
        self.display = QLabel('0')
        self.display.setAlignment(ALIGN_RIGHT | ALIGN_VCENTER)
        self.display.setMinimumHeight(120)
        self.display.setFont(QFont('Arial', 30))
        self.display.setStyleSheet(
            'background-color: black;'
            'color: white;'
            'border-radius: 18px;'
            'padding: 20px;'
        )
        display_layout.addWidget(self.display)
        root_layout.addLayout(display_layout)

        button_layout = QGridLayout()
        button_layout.setSpacing(12)
        root_layout.addLayout(button_layout)

        # 아이폰 계산기와 동일한 행/열 순서를 유지하도록 버튼 정의를 배치한다.
        buttons = [
            [('AC', 'function'), ('+/-', 'function'), ('%', 'function'), ('/', 'operator')],
            [('7', 'number'), ('8', 'number'), ('9', 'number'), ('*', 'operator')],
            [('4', 'number'), ('5', 'number'), ('6', 'number'), ('-', 'operator')],
            [('1', 'number'), ('2', 'number'), ('3', 'number'), ('+', 'operator')],
            [('0', 'number-wide'), ('.', 'number'), ('=', 'operator')],
        ]

        for row_index, row in enumerate(buttons):
            column_index = 0
            for label, role in row:
                button = QPushButton(label)
                button.setMinimumHeight(78)
                button.setFont(QFont('Arial', 20))
                button.clicked.connect(self._handle_button_click)
                button.setStyleSheet(self._button_style(role))

                if role == 'number-wide':
                    button.setMinimumWidth(160)
                    button_layout.addWidget(button, row_index, column_index, 1, 2)
                    column_index += 2
                    continue

                button_layout.addWidget(button, row_index, column_index)
                column_index += 1

    def _button_style(self, role):
        """버튼 종류에 따라 아이폰 계산기와 유사한 색상을 반환한다."""
        styles = {
            'function': (
                'background-color: #d4d4d2;'
                'color: black;'
            ),
            'operator': (
                'background-color: #ff9f0a;'
                'color: white;'
            ),
            'number': (
                'background-color: #505050;'
                'color: white;'
            ),
            'number-wide': (
                'background-color: #505050;'
                'color: white;'
                'text-align: left;'
                'padding-left: 28px;'
            ),
        }
        return (
            'border: none;'
            'border-radius: 39px;'
            f'{styles[role]}'
        )

    def _handle_button_click(self):
        """눌린 버튼의 텍스트에 따라 숫자 입력 또는 계산 기능을 실행한다."""
        button = self.sender()
        if button is None:
            return

        value = button.text()

        if value.isdigit():
            self._input_digit(value)
        elif value == '.':
            self._input_decimal()
        elif value in {'+', '-', '*', '/'}:
            self._set_operator(value)
        elif value == '=':
            self._calculate_result()
        elif value == 'AC':
            self._clear_all()
        elif value == '+/-':
            self._toggle_sign()
        elif value == '%':
            self._convert_percent()

        self._update_display()

    def _input_digit(self, digit):
        """숫자 버튼 입력 시 현재 입력 문자열을 갱신한다."""
        if self.waiting_for_new_input:
            self.current_input = digit
            self.waiting_for_new_input = False
            return

        if self.current_input == '0':
            self.current_input = digit
        else:
            self.current_input += digit

    def _input_decimal(self):
        """소수점은 현재 숫자에 한 번만 입력되도록 제한한다."""
        if self.waiting_for_new_input:
            self.current_input = '0.'
            self.waiting_for_new_input = False
            return

        if '.' not in self.current_input:
            self.current_input += '.'

    def _set_operator(self, operator):
        """연산자를 저장하고 필요하면 이전 연산을 먼저 완료한다."""
        if self.pending_operator and not self.waiting_for_new_input:
            self._calculate_result()

        self.left_operand = self._safe_float(self.current_input)
        self.pending_operator = operator
        self.waiting_for_new_input = True

    def _calculate_result(self):
        """저장된 피연산자와 현재 입력값으로 실제 사칙연산을 수행한다."""
        if self.pending_operator is None or self.left_operand is None:
            return

        right_operand = self._safe_float(self.current_input)

        if self.pending_operator == '+':
            result = self.left_operand + right_operand
        elif self.pending_operator == '-':
            result = self.left_operand - right_operand
        elif self.pending_operator == '*':
            result = self.left_operand * right_operand
        else:
            if right_operand == 0:
                self.current_input = 'Error'
                self.left_operand = None
                self.pending_operator = None
                self.waiting_for_new_input = True
                return
            result = self.left_operand / right_operand

        self.current_input = self._format_number(result)
        self.left_operand = None
        self.pending_operator = None
        self.waiting_for_new_input = True

    def _clear_all(self):
        """모든 상태를 초기화하여 계산기를 처음 상태로 되돌린다."""
        self.current_input = '0'
        self.left_operand = None
        self.pending_operator = None
        self.waiting_for_new_input = False

    def _toggle_sign(self):
        """현재 표시 중인 숫자의 부호를 양수와 음수로 전환한다."""
        if self.current_input in {'0', 'Error'}:
            return

        if self.current_input.startswith('-'):
            self.current_input = self.current_input[1:]
        else:
            self.current_input = f'-{self.current_input}'

    def _convert_percent(self):
        """현재 입력값을 100으로 나누어 퍼센트 형태로 변환한다."""
        if self.current_input == 'Error':
            return

        value = self._safe_float(self.current_input) / 100
        self.current_input = self._format_number(value)

    def _update_display(self):
        """출력창과 연산 상태줄을 함께 갱신하여 입력 흐름이 보이도록 한다."""
        if self.pending_operator and self.left_operand is not None:
            left_text = self._format_number(self.left_operand)
            self.expression_display.setText(f'{left_text} {self.pending_operator}')
        else:
            self.expression_display.setText('')

        self.display.setText(self.current_input)

    def _safe_float(self, value):
        """문자열 숫자를 float으로 안전하게 변환하고 실패 시 0.0을 반환한다."""
        try:
            return float(value)
        except ValueError:
            return 0.0

    def _format_number(self, value):
        """불필요한 소수점 0을 제거하여 계산기 표시 형식에 맞춘다."""
        if value.is_integer():
            return str(int(value))
        return f'{value:.12g}'


def main():
    """애플리케이션을 생성하고 계산기 창을 실행한다."""
    app = QApplication(sys.argv)
    window = CalculatorWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    main()