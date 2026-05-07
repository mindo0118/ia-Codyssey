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


class Calculator:

    def add(self, a, b):
        return a + b

    def subtract(self, a, b):
        return a - b

    def multiply(self, a, b):
        return a * b

    def divide(self, a, b):
        if b == 0:
            raise ZeroDivisionError('0으로 나눌 수 없습니다.')
        return a / b

    def reset(self):
        return 0.0

    def negative_positive(self, value):
        return -value

    def percent(self, value):
        return value / 100.0

    def equal(self, expression):
        tokens = self._tokenize(expression)
        if not tokens:
            return 0.0
        return self._evaluate(tokens)

    def _tokenize(self, expression):
        tokens = []
        i = 0
        n = len(expression)

        while i < n:
            ch = expression[i]

            is_unary_minus = (
                ch == '-'
                and (not tokens or isinstance(tokens[-1], str))
            )
            if is_unary_minus:
                i += 1
                j = i
                while j < n and (expression[j].isdigit() or expression[j] == '.'):
                    j += 1
                if j > i:
                    try:
                        num_val = float('-' + expression[i:j])
                    except ValueError:
                        num_val = 0.0
                    if j < n and expression[j] == '%':
                        num_val = self.percent(num_val)
                        j += 1
                    tokens.append(num_val)
                    i = j
                else:
                    tokens.append('-')
            elif ch.isdigit() or ch == '.':
                j = i
                while j < n and (expression[j].isdigit() or expression[j] == '.'):
                    j += 1
                try:
                    num_val = float(expression[i:j])
                except ValueError:
                    num_val = 0.0
                if j < n and expression[j] == '%':
                    num_val = self.percent(num_val)
                    j += 1
                tokens.append(num_val)
                i = j
            elif ch in '+-*/':
                tokens.append(ch)
                i += 1
            else:
                i += 1

        return tokens

    def _evaluate(self, tokens):
        if not tokens:
            return 0.0

        if len(tokens) == 1:
            return float(tokens[0]) if isinstance(tokens[0], (int, float)) else 0.0

        reduced = list(tokens)
        i = 1
        while i < len(reduced):
            if isinstance(reduced[i], str) and reduced[i] in '*/':
                op = reduced[i]
                left = float(reduced[i - 1])
                right = float(reduced[i + 1])
                val = self.multiply(left, right) if op == '*' else self.divide(left, right)
                reduced = reduced[:i - 1] + [val] + reduced[i + 2:]
            else:
                i += 1

        result = float(reduced[0])
        i = 1
        while i < len(reduced) - 1:
            op = reduced[i]
            right = float(reduced[i + 1])
            if op == '+':
                result = self.add(result, right)
            elif op == '-':
                result = self.subtract(result, right)
            i += 2

        return result


class CalculatorWindow(QWidget):

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
        super().__init__()
        self._calculator = Calculator()
        self.raw_text = '0'
        self.wrap_leading_negative = False
        self.ac_button = None
        self._show_ac = False
        self._after_equal = False
        self._is_error = False

        self.setWindowTitle(self.WINDOW_TITLE)
        self.setFixedSize(*self.WINDOW_SIZE)
        self._load_stylesheet()
        self._build_ui()

    def _load_stylesheet(self):
        style_path = Path(__file__).with_name('calculator.qss')
        self.setStyleSheet(style_path.read_text(encoding='utf-8'))

    def _build_ui(self):
        root_layout = QVBoxLayout()
        root_layout.setContentsMargins(*self.ROOT_MARGINS)
        root_layout.setSpacing(self.ROOT_SPACING)
        self.setLayout(root_layout)

        root_layout.addStretch(self.TOP_STRETCH)

        display_layout = QVBoxLayout()
        display_layout.setContentsMargins(0, 0, 0, 0)
        display_layout.setSpacing(self.DISPLAY_SPACING)

        self.expression_display = QLabel('')
        self.expression_display.setObjectName('expressionDisplay')
        self.expression_display.setAlignment(ALIGN_RIGHT | ALIGN_VCENTER)
        display_layout.addWidget(self.expression_display)

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
        if current_text[-1].isdigit():
            return current_text + '%'
        return current_text

    def _toggle_plus_minus(self, text):
        if text in {'', '0'} or text[-1] in self.BASIC_OPERATORS:
            return text, False

        index = len(text) - 1
        while index >= 0 and text[index] not in self.BASIC_OPERATORS:
            index -= 1

        token_start = index + 1
        prefix = text[:token_start]
        token = text[token_start:]

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
            if prev_operator == '+':
                return prefix + abs_token, False
            if prev_operator == '-':
                return prefix[:-1] + '+' + abs_token, False
            return prefix + abs_token, False
        else:
            if prev_operator == '-':
                return prefix[:-1] + '+' + token, False
            if prev_operator == '+':
                return prefix + '-' + token, False
            wrap_leading = token_start == 0
            return prefix + '-' + token, wrap_leading

    def _group_digits(self, digits):
        if not digits or not digits.isdigit():
            return digits
        chunks = []
        while digits:
            chunks.append(digits[-3:])
            digits = digits[:-3]
        return ','.join(reversed(chunks))

    def _format_number_token(self, token, wrap_negative):
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
        result = []
        token = ''
        token_start_index = 0

        for index, char in enumerate(text):
            if char in self.TOKEN_SPLIT_OPERATORS:
                is_unary_minus = char == '-' and (
                    index == 0 or text[index - 1] in self.TOKEN_SPLIT_OPERATORS
                )
                if is_unary_minus:
                    if not token:
                        token_start_index = index
                    token += char
                    continue

                if token:
                    should_wrap_negative = token_start_index > 0 or (
                        token_start_index == 0 and self.wrap_leading_negative
                    )
                    result.append(
                        self._format_number_token(token, wrap_negative=should_wrap_negative)
                    )
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
            result.append(
                self._format_number_token(token, wrap_negative=should_wrap_negative)
            )

        return ''.join(result) if result else '0'

    def _set_display_from_raw(self, raw_text, leading_negative_wrapped=None):
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
        if self.ac_button is not None:
            show_c = self.raw_text != '0' and not self._show_ac
            self.ac_button.setText('C' if show_c else 'AC')

    def _adjust_display_font_size(self, text):
        display_text = text if text else '0'
        available_width = max(
            self.DISPLAY_MIN_AVAILABLE_WIDTH,
            self.display.width() - self.DISPLAY_SIDE_PADDING
        )
        font_size = self.DISPLAY_MAX_FONT_SIZE

        while font_size > self.DISPLAY_MIN_FONT_SIZE:
            test_font = QFont(self.FONT_FAMILY, font_size)
            if QFontMetrics(test_font).horizontalAdvance(display_text) <= available_width:
                break
            font_size -= 1

        self.display.setFont(QFont(self.FONT_FAMILY, font_size))

    def _format_result(self, value):
        rounded = round(value, 6)
        if rounded == int(rounded):
            return str(int(rounded))
        return f'{rounded:.6f}'.rstrip('0')

    def _handle_digit_input(self, value, current_text):
        self._show_ac = False
        if current_text == '0' or self._after_equal:
            if self._after_equal:
                self.expression_display.setText('')
            self._after_equal = False
            self._set_display_from_raw(value, leading_negative_wrapped=False)
        else:
            self._set_display_from_raw(current_text + value)

    def _handle_operator_input(self, value, current_text):
        self._show_ac = False
        self._after_equal = False
        next_text = self._append_operator(current_text, value)
        is_manual_leading_minus = current_text == '0' and value == '-'
        self._set_display_from_raw(
            next_text,
            leading_negative_wrapped=False if is_manual_leading_minus else None
        )

    def _handle_decimal_input(self, current_text):
        self._show_ac = False
        if self._after_equal:
            self._after_equal = False
            self.expression_display.setText('')
            self._set_display_from_raw('0.')
            return
        last_op_idx = -1
        for i in range(len(current_text) - 1, -1, -1):
            if current_text[i] in self.TOKEN_SPLIT_OPERATORS:
                last_op_idx = i
                break
        current_token = current_text[last_op_idx + 1:]
        if '.' not in current_token:
            prefix = '0' if not current_token or current_token == '-' else ''
            self._set_display_from_raw(current_text + prefix + '.')

    def _handle_c_input(self, current_text):
        if self._is_error:
            self._is_error = False
            self._show_ac = False
            self.expression_display.setText('')
            self._set_display_from_raw('0', leading_negative_wrapped=False)
            return

        if current_text[-1] in self.TOKEN_SPLIT_OPERATORS:
            self._show_ac = True
            self._update_ac_button()
            return

        idx = len(current_text) - 1
        while idx >= 0 and current_text[idx] not in self.TOKEN_SPLIT_OPERATORS:
            idx -= 1

        if idx < 0:
            self._show_ac = False
            self._set_display_from_raw('0', leading_negative_wrapped=False)
            return

        self._show_ac = True
        self._set_display_from_raw(current_text[:idx + 1])

    def _handle_ac_input(self, _current_text):
        self._is_error = False
        self._after_equal = False
        self._show_ac = False
        self.expression_display.setText('')
        self._set_display_from_raw('0', leading_negative_wrapped=False)

    def _handle_percent_input(self, current_text):
        self._set_display_from_raw(self._append_percent(current_text))

    def _handle_plus_minus_input(self, current_text):
        toggled_text, wrap_leading = self._toggle_plus_minus(current_text)
        self._set_display_from_raw(toggled_text, leading_negative_wrapped=wrap_leading)

    def _handle_backspace_input(self, current_text):
        if len(current_text) <= 1:
            self._set_display_from_raw('0')
        else:
            self._set_display_from_raw(current_text[:-1])

    def _handle_equal_input(self, current_text):
        try:
            result = self._calculator.equal(current_text)
            result_str = self._format_result(result)
            self.expression_display.setText(
                self._format_expression(current_text) + ' ='
            )
            self._after_equal = True
            self._is_error = False
            self._set_display_from_raw(result_str, leading_negative_wrapped=False)
        except ZeroDivisionError:
            self.expression_display.setText(
                self._format_expression(current_text) + ' ='
            )
            self._is_error = True
            self._after_equal = False
            self._show_ac = False
            self.display.setText('오류')
            if self.ac_button:
                self.ac_button.setText('AC')
        except (ValueError, OverflowError, ArithmeticError):
            self._is_error = True
            self._after_equal = False
            self._show_ac = False
            self.display.setText('오류')
            if self.ac_button:
                self.ac_button.setText('AC')

    def _handle_button_click(self):
        button = self.sender()
        if button is None:
            return

        value = button.text()
        current_text = self.raw_text

        if self._is_error:
            if value in ('AC', 'C', '⌫'):
                self._is_error = False
                self._after_equal = False
                self._show_ac = False
                self.expression_display.setText('')
                self._set_display_from_raw('0', leading_negative_wrapped=False)
            return

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
            '=': self._handle_equal_input,
        }

        if value in self.BASIC_OPERATORS:
            self._handle_operator_input(value, current_text)
            return

        handler = handlers.get(value)
        if handler is not None:
            handler(current_text)


def main():
    app = QApplication(sys.argv)
    window = CalculatorWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
