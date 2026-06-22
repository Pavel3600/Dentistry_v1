from django.core.exceptions import ValidationError
import re


def validate_phone_number(value):
    """Валидация российского номера телефона"""
    pattern = r'^(\+7|7|8)?[\s\-]?\(?[0-9]{3}\)?[\s\-]?[0-9]{3}[\s\-]?[0-9]{2}[\s\-]?[0-9]{2}$'
    if not re.match(pattern, value):
        raise ValidationError('Введите корректный номер телефона (например: +7(999)123-45-67)')

    # Приводим к единому формату +7XXXXXXXXXX
    digits = re.sub(r'\D', '', value)
    if len(digits) == 10:
        digits = '7' + digits
    elif len(digits) == 11 and digits[0] == '8':
        digits = '7' + digits[1:]

    return digits