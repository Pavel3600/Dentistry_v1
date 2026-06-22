"""Tests for utils.py, validators.py and mkb_validator.py."""
import pytest
import requests as req

from app.utils import is_fastapi_available
from app.validators import validate_phone_number
from app.mkb_validator import (
    validate_mkb_code,
    get_mkb_name,
    search_mkb_by_name,
    get_mkb_code_by_name,
    get_all_mkb_codes,
    get_mkb_by_category,
    format_mkb_for_print,
    get_mkb_statistics,
)
from django.core.exceptions import ValidationError


# ──────────────────────────────────────────────────────────────────────────────
# is_fastapi_available
# ──────────────────────────────────────────────────────────────────────────────

class TestIsFastapiAvailable:
    def test_returns_true_on_200(self, mocker):
        """Функция возвращает True, если FastAPI отвечает статусом 200."""
        # Arrange
        mock_resp = mocker.MagicMock()
        mock_resp.status_code = 200
        mocker.patch('app.utils.requests.get', return_value=mock_resp)

        # Act / Assert
        assert is_fastapi_available() is True

    def test_returns_false_on_500(self, mocker):
        """Функция возвращает False, если FastAPI отвечает статусом 500."""
        # Arrange
        mock_resp = mocker.MagicMock()
        mock_resp.status_code = 500
        mocker.patch('app.utils.requests.get', return_value=mock_resp)

        # Act / Assert
        assert is_fastapi_available() is False

    def test_returns_false_on_connection_error(self, mocker):
        """Функция возвращает False при ConnectionError от requests."""
        # Arrange
        mocker.patch('app.utils.requests.get', side_effect=req.exceptions.ConnectionError())

        # Act / Assert
        assert is_fastapi_available() is False

    def test_returns_false_on_timeout(self, mocker):
        """Функция возвращает False при Timeout от requests."""
        # Arrange
        mocker.patch('app.utils.requests.get', side_effect=req.exceptions.Timeout())

        # Act / Assert
        assert is_fastapi_available() is False

    def test_returns_false_on_generic_exception(self, mocker):
        """Функция возвращает False при любом непредвиденном исключении."""
        # Arrange
        mocker.patch('app.utils.requests.get', side_effect=Exception('unexpected'))

        # Act / Assert
        assert is_fastapi_available() is False

    def test_uses_fastapi_url_from_settings(self, mocker, settings):
        """Функция использует FASTAPI_URL из настроек Django при построении URL запроса."""
        # Arrange
        settings.FASTAPI_URL = 'http://custom-host:9999'
        captured = {}

        def fake_get(url, timeout):
            captured['url'] = url
            raise req.exceptions.ConnectionError()

        mocker.patch('app.utils.requests.get', side_effect=fake_get)

        # Act
        is_fastapi_available()

        # Assert
        assert captured['url'] == 'http://custom-host:9999/'


# ──────────────────────────────────────────────────────────────────────────────
# validate_phone_number
# ──────────────────────────────────────────────────────────────────────────────

class TestValidatePhoneNumber:
    def test_valid_plus7(self):
        """Телефон в формате +7XXXXXXXXXX нормализуется и возвращает 11-значный номер."""
        # Act
        result = validate_phone_number('+79991234567')

        # Assert
        assert result == '79991234567'

    def test_valid_8_prefix_converted(self):
        """Телефон с префиксом 8 преобразуется в номер, начинающийся на 7."""
        # Act
        result = validate_phone_number('89991234567')

        # Assert
        assert result.startswith('7')

    def test_valid_10_digits_prefixed(self):
        """10-значный номер без кода страны получает префикс 7."""
        # Act
        result = validate_phone_number('9001112233')

        # Assert
        assert result == '79001112233'

    def test_valid_formatted(self):
        """Телефон в форматированном виде +7(999)123-45-67 нормализуется корректно."""
        # Act
        result = validate_phone_number('+7(999)123-45-67')

        # Assert
        assert result == '79991234567'

    def test_invalid_too_short(self):
        """Слишком короткий номер вызывает ValidationError."""
        # Act / Assert
        with pytest.raises(ValidationError):
            validate_phone_number('12345')

    def test_invalid_letters(self):
        """Строка с буквами вместо цифр вызывает ValidationError."""
        # Act / Assert
        with pytest.raises(ValidationError):
            validate_phone_number('abc-def-ghij')

    def test_invalid_empty_string(self):
        """Пустая строка вызывает ValidationError."""
        # Act / Assert
        with pytest.raises(ValidationError):
            validate_phone_number('')


# ──────────────────────────────────────────────────────────────────────────────
# validate_mkb_code
# ──────────────────────────────────────────────────────────────────────────────

class TestValidateMkbCode:
    def test_valid_code_returns_true_and_name(self):
        """Известный код МКБ возвращает (True, название болезни)."""
        # Act
        exists, name = validate_mkb_code('K02.0')

        # Assert
        assert exists is True
        assert name == 'Кариес эмали'

    def test_invalid_code_returns_false(self):
        """Неизвестный код МКБ возвращает (False, None)."""
        # Act
        exists, name = validate_mkb_code('Z99.9')

        # Assert
        assert exists is False
        assert name is None

    def test_empty_string_returns_false(self):
        """Пустая строка возвращает False как первый элемент кортежа."""
        # Act
        exists, name = validate_mkb_code('')

        # Assert
        assert exists is False

    def test_case_insensitive(self):
        """Поиск кода МКБ нечувствителен к регистру."""
        # Act
        exists, _ = validate_mkb_code('k02.0')

        # Assert
        assert exists is True

    def test_strips_whitespace(self):
        """Код МКБ с пробелами по краям обрабатывается корректно."""
        # Act
        exists, _ = validate_mkb_code('  K02.0  ')

        # Assert
        assert exists is True

    def test_k04_pulsit(self):
        """Код K04.0 распознаётся как «Пульпит»."""
        # Act
        exists, name = validate_mkb_code('K04.0')

        # Assert
        assert exists is True
        assert 'Пульпит' in name


# ──────────────────────────────────────────────────────────────────────────────
# get_mkb_name
# ──────────────────────────────────────────────────────────────────────────────

class TestGetMkbName:
    def test_returns_name_for_valid_code(self):
        """По известному коду возвращается русское название болезни."""
        # Act / Assert
        assert get_mkb_name('K02.1') == 'Кариес дентина'

    def test_returns_error_message_for_unknown(self):
        """По неизвестному коду возвращается строка, содержащая «не найден»."""
        # Act
        result = get_mkb_name('Z00.0')

        # Assert
        assert 'не найден' in result


# ──────────────────────────────────────────────────────────────────────────────
# search_mkb_by_name
# ──────────────────────────────────────────────────────────────────────────────

class TestSearchMkbByName:
    def test_finds_caries_codes(self):
        """Поиск по слову «Кариес» возвращает непустой список только с кариесными кодами."""
        # Act
        results = search_mkb_by_name('Кариес')

        # Assert
        assert len(results) > 0
        assert all('кариес' in name.lower() for _, name in results)

    def test_empty_query_returns_empty(self):
        """Пустой поисковый запрос возвращает пустой список."""
        # Act / Assert
        assert search_mkb_by_name('') == []

    def test_results_limited_to_20(self):
        """Количество результатов поиска не превышает 20."""
        # Act
        results = search_mkb_by_name('K')

        # Assert
        assert len(results) <= 20

    def test_case_insensitive(self):
        """Поиск нечувствителен к регистру: строчные буквы дают результат."""
        # Act
        results = search_mkb_by_name('кариес')

        # Assert
        assert len(results) > 0

    def test_no_match_returns_empty(self):
        """Несуществующая подстрока возвращает пустой список."""
        # Act
        results = search_mkb_by_name('xyznonexistent')

        # Assert
        assert results == []


# ──────────────────────────────────────────────────────────────────────────────
# get_mkb_code_by_name
# ──────────────────────────────────────────────────────────────────────────────

class TestGetMkbCodeByName:
    def test_finds_code_by_exact_name(self):
        """По точному русскому названию возвращается соответствующий код МКБ."""
        # Act
        code = get_mkb_code_by_name('Кариес эмали')

        # Assert
        assert code == 'K02.0'

    def test_returns_none_for_unknown_name(self):
        """По несуществующему названию возвращается None."""
        # Act / Assert
        assert get_mkb_code_by_name('Несуществующий диагноз') is None

    def test_returns_none_for_empty(self):
        """По пустой строке возвращается None."""
        # Act / Assert
        assert get_mkb_code_by_name('') is None

    def test_finds_by_code_string(self):
        """Если передать сам код в виде строки — он же и возвращается."""
        # Act
        code = get_mkb_code_by_name('K02.0')

        # Assert
        assert code == 'K02.0'


# ──────────────────────────────────────────────────────────────────────────────
# get_all_mkb_codes
# ──────────────────────────────────────────────────────────────────────────────

class TestGetAllMkbCodes:
    def test_returns_nonempty_list(self):
        """Список всех кодов МКБ содержит более 50 элементов."""
        # Act
        all_codes = get_all_mkb_codes()

        # Assert
        assert len(all_codes) > 50

    def test_returns_tuples_of_code_and_name(self):
        """Каждый элемент списка — кортеж из двух строк: код и название."""
        # Act
        all_codes = get_all_mkb_codes()
        code, name = all_codes[0]

        # Assert
        assert isinstance(code, str)
        assert isinstance(name, str)

    def test_sorted_by_code(self):
        """Список кодов МКБ возвращается отсортированным по коду."""
        # Act
        all_codes = get_all_mkb_codes()
        codes = [c for c, _ in all_codes]

        # Assert
        assert codes == sorted(codes)


# ──────────────────────────────────────────────────────────────────────────────
# get_mkb_by_category
# ──────────────────────────────────────────────────────────────────────────────

class TestGetMkbByCategory:
    def test_k02_returns_caries_codes(self):
        """Категория K02 возвращает только коды, начинающиеся с K02."""
        # Act
        results = get_mkb_by_category('K02')

        # Assert
        assert len(results) > 0
        assert all(code.startswith('K02') for code, _ in results)

    def test_empty_returns_empty(self):
        """Пустая строка категории возвращает пустой список."""
        # Act / Assert
        assert get_mkb_by_category('') == []

    def test_unknown_category_returns_empty(self):
        """Несуществующая категория возвращает пустой список."""
        # Act / Assert
        assert get_mkb_by_category('Z99') == []

    def test_case_insensitive(self):
        """Поиск по категории нечувствителен к регистру."""
        # Act
        results = get_mkb_by_category('k02')

        # Assert
        assert len(results) > 0


# ──────────────────────────────────────────────────────────────────────────────
# format_mkb_for_print
# ──────────────────────────────────────────────────────────────────────────────

class TestFormatMkbForPrint:
    def test_formats_valid_code(self):
        """Известный код форматируется в строку «КОД – Название»."""
        # Act
        result = format_mkb_for_print('K02.0')

        # Assert
        assert 'K02.0' in result
        assert 'Кариес эмали' in result
        assert '–' in result

    def test_formats_unknown_code_with_placeholder(self):
        """Неизвестный код форматируется с заглушкой «???»."""
        # Act
        result = format_mkb_for_print('Z00.0')

        # Assert
        assert '???' in result


# ──────────────────────────────────────────────────────────────────────────────
# get_mkb_statistics
# ──────────────────────────────────────────────────────────────────────────────

class TestGetMkbStatistics:
    def test_returns_dict(self):
        """Функция возвращает словарь."""
        # Act
        stats = get_mkb_statistics()

        # Assert
        assert isinstance(stats, dict)

    def test_k02_in_stats(self):
        """Категория K02 присутствует в статистике с положительным счётчиком."""
        # Act
        stats = get_mkb_statistics()

        # Assert
        assert 'K02' in stats
        assert stats['K02'] > 0

    def test_all_values_positive(self):
        """Все значения счётчиков статистики положительны."""
        # Act
        stats = get_mkb_statistics()

        # Assert
        assert all(v > 0 for v in stats.values())

    def test_sorted_keys(self):
        """Ключи словаря статистики отсортированы по алфавиту."""
        # Act
        stats = get_mkb_statistics()
        keys = list(stats.keys())

        # Assert
        assert keys == sorted(keys)
