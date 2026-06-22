"""
Эмулятор DLL для работы с МКБ-С-3
В реальном проекте здесь будет вызов внешней DLL
"""
import json
import os
from typing import Dict, Optional, List, Tuple

# Встроенная база кодов МКБ-С-3 (для эмуляции)
# В реальном проекте данные загружаются из DLL или внешнего источника
_MKBS_DATA = {
    # Диагнозы (категория: diagnosis)
    "K00.0": {"name": "Адентия", "category": "diagnosis"},
    "K00.1": {"name": "Сверхкомплектные зубы", "category": "diagnosis"},
    "K00.2": {"name": "Аномалии размеров и формы зубов", "category": "diagnosis"},
    "K00.3": {"name": "Крапчатые зубы (флюороз)", "category": "diagnosis"},
    "K00.4": {"name": "Нарушения формирования зубов", "category": "diagnosis"},
    "K00.5": {"name": "Наследственные нарушения структуры зубов", "category": "diagnosis"},
    "K00.6": {"name": "Нарушения прорезывания зубов", "category": "diagnosis"},
    "K00.7": {"name": "Синдром прорезывания зубов", "category": "diagnosis"},
    "K00.8": {"name": "Другие нарушения развития зубов", "category": "diagnosis"},
    "K01.0": {"name": "Ретенированные зубы", "category": "diagnosis"},
    "K01.1": {"name": "Импактные зубы", "category": "diagnosis"},
    "K02.0": {"name": "Кариес эмали", "category": "diagnosis"},
    "K02.1": {"name": "Кариес дентина", "category": "diagnosis"},
    "K02.2": {"name": "Кариес цемента", "category": "diagnosis"},
    "K02.3": {"name": "Приостановившийся кариес", "category": "diagnosis"},
    "K02.4": {"name": "Одонтоклазия", "category": "diagnosis"},
    "K02.5": {"name": "Кариес с обнажением пульпы", "category": "diagnosis"},
    "K02.8": {"name": "Другой кариес зубов", "category": "diagnosis"},
    "K02.9": {"name": "Кариес зубов неуточненный", "category": "diagnosis"},
    "K03.0": {"name": "Повышенное стирание зубов", "category": "diagnosis"},
    "K03.1": {"name": "Пришлифовывание зубов", "category": "diagnosis"},
    "K03.2": {"name": "Эрозия зубов", "category": "diagnosis"},
    "K03.3": {"name": "Патологическая резорбция зубов", "category": "diagnosis"},
    "K03.4": {"name": "Гиперцементоз", "category": "diagnosis"},
    "K03.5": {"name": "Анкилоз зубов", "category": "diagnosis"},
    "K03.6": {"name": "Отложения на зубах", "category": "diagnosis"},
    "K03.7": {"name": "Изменения цвета твердых тканей зубов", "category": "diagnosis"},
    "K04.0": {"name": "Пульпит", "category": "diagnosis"},
    "K04.1": {"name": "Некроз пульпы", "category": "diagnosis"},
    "K04.2": {"name": "Дегенерация пульпы", "category": "diagnosis"},
    "K04.3": {"name": "Неправильное формирование твердых тканей в пульпе", "category": "diagnosis"},
    "K04.4": {"name": "Острый апикальный периодонтит", "category": "diagnosis"},
    "K04.5": {"name": "Хронический апикальный периодонтит", "category": "diagnosis"},
    "K04.6": {"name": "Периапикальный абсцесс со свищом", "category": "diagnosis"},
    "K04.7": {"name": "Периапикальный абсцесс без свища", "category": "diagnosis"},
    "K04.8": {"name": "Киста корня зуба", "category": "diagnosis"},
    "K05.0": {"name": "Острый гингивит", "category": "diagnosis"},
    "K05.1": {"name": "Хронический гингивит", "category": "diagnosis"},
    "K05.2": {"name": "Острый периодонтит", "category": "diagnosis"},
    "K05.3": {"name": "Хронический периодонтит", "category": "diagnosis"},
    "K05.4": {"name": "Пародонтоз", "category": "diagnosis"},
    "K05.5": {"name": "Другие болезни пародонта", "category": "diagnosis"},
    "K05.6": {"name": "Болезнь пародонта неуточненная", "category": "diagnosis"},
    "K06.0": {"name": "Рецессия десны", "category": "diagnosis"},
    "K06.1": {"name": "Гипертрофия десны", "category": "diagnosis"},
    "K06.2": {"name": "Поражения десны", "category": "diagnosis"},
    "K07.0": {"name": "Аномалии размеров челюстей", "category": "diagnosis"},
    "K07.1": {"name": "Аномалии положения челюстей", "category": "diagnosis"},
    "K07.2": {"name": "Аномалии прикуса", "category": "diagnosis"},
    "K07.3": {"name": "Аномалии положения зубов", "category": "diagnosis"},
    "K07.4": {"name": "Аномалии зубного ряда", "category": "diagnosis"},
    "K07.5": {"name": "Височно-нижнечелюстные аномалии", "category": "diagnosis"},
    "K07.6": {"name": "Другие аномалии челюстно-лицевой области", "category": "diagnosis"},
    "K08.0": {"name": "Эксфолиация зубов вследствие системных нарушений", "category": "diagnosis"},
    "K08.1": {"name": "Потеря зубов вследствие травмы", "category": "diagnosis"},
    "K08.2": {"name": "Атрофия альвеолярного отростка", "category": "diagnosis"},
    "K08.3": {"name": "Корень зуба", "category": "diagnosis"},
    "K08.8": {"name": "Боль в челюсти", "category": "diagnosis"},
    "K09.0": {"name": "Одонтогенные кисты", "category": "diagnosis"},
    "K09.1": {"name": "Неодонтогенные кисты", "category": "diagnosis"},
    "K09.2": {"name": "Другие кисты челюстей", "category": "diagnosis"},
    "K09.8": {"name": "Другие кисты ротовой области", "category": "diagnosis"},
    "K10.0": {"name": "Воспалительные болезни челюстей", "category": "diagnosis"},
    "K10.1": {"name": "Гиперплазия челюстей", "category": "diagnosis"},
    "K10.2": {"name": "Воспалительные состояния челюстей", "category": "diagnosis"},
    "K10.3": {"name": "Альвеолит", "category": "diagnosis"},
    "K11.0": {"name": "Атрофия слюнной железы", "category": "diagnosis"},
    "K11.1": {"name": "Гипертрофия слюнной железы", "category": "diagnosis"},
    "K11.2": {"name": "Сиаладенит", "category": "diagnosis"},
    "K11.3": {"name": "Абсцесс слюнной железы", "category": "diagnosis"},
    "K11.4": {"name": "Фисгула слюнной железы", "category": "diagnosis"},
    "K11.5": {"name": "Сиалолитиаз", "category": "diagnosis"},
    "K11.6": {"name": "Мукоцеле слюнной железы", "category": "diagnosis"},
    "K11.7": {"name": "Нарушения секреции слюнных желез", "category": "diagnosis"},
    "K11.8": {"name": "Другие болезни слюнных желез", "category": "diagnosis"},
    "K12.0": {"name": "Рецидивирующие афты полости рта", "category": "diagnosis"},
    "K12.1": {"name": "Стоматит", "category": "diagnosis"},
    "K12.2": {"name": "Абсцесс полости рта", "category": "diagnosis"},
    "K12.3": {"name": "Флегмона полости рта", "category": "diagnosis"},
    "K13.0": {"name": "Болезни губ", "category": "diagnosis"},
    "K13.1": {"name": "Болезни слизистой щек и губ", "category": "diagnosis"},
    "K13.2": {"name": "Лейкоплакия полости рта", "category": "diagnosis"},
    "K13.3": {"name": "Эритроплакия полости рта", "category": "diagnosis"},
    "K13.4": {"name": "Гранулема полости рта", "category": "diagnosis"},
    "K13.5": {"name": "Фиброз слизистой полости рта", "category": "diagnosis"},
    "K13.6": {"name": "Разрастание слизистой полости рта", "category": "diagnosis"},
    "K13.7": {"name": "Другие поражения слизистой полости рта", "category": "diagnosis"},
    "K14.0": {"name": "Глоссит", "category": "diagnosis"},
    "K14.1": {"name": "Складчатый язык", "category": "diagnosis"},
    "K14.2": {"name": "Срединный ромбовидный глоссит", "category": "diagnosis"},
    "K14.3": {"name": "Гипертрофия сосочков языка", "category": "diagnosis"},
    "K14.4": {"name": "Атрофия сосочков языка", "category": "diagnosis"},
    "K14.5": {"name": "Складчатый язык", "category": "diagnosis"},
    "K14.6": {"name": "Глоссодиния", "category": "diagnosis"},
    "K14.8": {"name": "Другие болезни языка", "category": "diagnosis"},

    # Стоматологические услуги (категория: service) - условные коды
    "11101": {"name": "Пломбирование зуба (1 поверхность)", "category": "service"},
    "11102": {"name": "Пломбирование зуба (2 поверхности)", "category": "service"},
    "11103": {"name": "Пломбирование зуба (3 поверхности)", "category": "service"},
    "11104": {"name": "Пломбирование зуба (4 и более поверхностей)", "category": "service"},
    "11201": {"name": "Реставрация зуба композитным материалом", "category": "service"},
    "11202": {"name": "Реставрация зуба керамической вкладкой", "category": "service"},
    "11203": {"name": "Реставрация зуба культевой вкладкой", "category": "service"},
    "21101": {"name": "Удаление зуба (простое)", "category": "service"},
    "21102": {"name": "Удаление зуба (сложное)", "category": "service"},
    "21103": {"name": "Удаление зуба (хирургическое)", "category": "service"},
    "21104": {"name": "Удаление ретинированного зуба", "category": "service"},
    "31101": {"name": "Лечение корневого канала (1 канал)", "category": "service"},
    "31102": {"name": "Лечение корневого канала (2 канала)", "category": "service"},
    "31103": {"name": "Лечение корневого канала (3 канала)", "category": "service"},
    "31104": {"name": "Лечение корневого канала (4 и более каналов)", "category": "service"},
    "31105": {"name": "Ретроградное пломбирование корневого канала", "category": "service"},
    "41101": {"name": "Профессиональная гигиена полости рта", "category": "service"},
    "41102": {"name": "Ультразвуковая чистка зубов", "category": "service"},
    "41103": {"name": "Air-Flow (снятие зубных отложений)", "category": "service"},
    "41104": {"name": "Фторирование зубов", "category": "service"},
    "41105": {"name": "Реминерализирующая терапия", "category": "service"},
    "51101": {"name": "Рентгенологическое исследование (прицельный снимок)", "category": "service"},
    "51102": {"name": "Ортопантомограмма (панорамный снимок)", "category": "service"},
    "51103": {"name": "Компьютерная томография челюсти", "category": "service"},
    "61101": {"name": "Анестезия аппликационная", "category": "service"},
    "61102": {"name": "Анестезия инфильтрационная", "category": "service"},
    "61103": {"name": "Анестезия проводниковая", "category": "service"},
    "61104": {"name": "Седация", "category": "service"},
    "71101": {"name": "Наложение временной пломбы", "category": "service"},
    "71102": {"name": "Наложение лечебной прокладки", "category": "service"},
    "71103": {"name": "Изолирование зуба коффердамом", "category": "service"},
    "71104": {"name": "Временное шинирование зубов", "category": "service"},
    "81101": {"name": "Консультация стоматолога", "category": "service"},
    "81102": {"name": "Консультация стоматолога-хирурга", "category": "service"},
    "81103": {"name": "Консультация стоматолога-ортодонта", "category": "service"},
}

# Кэш для ускорения поиска
_SEARCH_CACHE = {}


class MKBSEmulator:
    """Эмулятор DLL для работы с МКБ-С-3"""

    def __init__(self):
        self._data = _MKBS_DATA.copy()
        self._load_from_database = False

    def load_from_dll(self, dll_path: str) -> bool:
        """
        Загрузить данные из внешней DLL
        В реальном проекте здесь будет вызов DLL
        """
        if os.path.exists(dll_path):
            # Эмуляция загрузки из DLL
            print(f"Эмуляция: загрузка данных из DLL {dll_path}")
            # Здесь будет реальный вызов DLL
            # Например: self.dll = ctypes.CDLL(dll_path)
            return True
        return False

    def get_code_info(self, code: str) -> Optional[Dict]:
        """Получить информацию о коде"""
        return self._data.get(code.upper())

    def get_diagnosis_name(self, code: str) -> str:
        """Получить название диагноза по коду"""
        info = self.get_code_info(code)
        if info and info.get("category") == "diagnosis":
            return info.get("name", "")
        return ""

    def get_service_name(self, code: str) -> str:
        """Получить название услуги по коду"""
        info = self.get_code_info(code)
        if info and info.get("category") == "service":
            return info.get("name", "")
        return ""

    def search_codes(self, query: str, category: Optional[str] = None) -> List[Tuple[str, str, str]]:
        """Поиск кодов по названию"""
        query_lower = query.lower()
        results = []

        for code, info in self._data.items():
            if category and info.get("category") != category:
                continue
            if query_lower in code.lower() or query_lower in info.get("name", "").lower():
                results.append((code, info.get("name", ""), info.get("category", "")))

        return results[:50]  # Ограничиваем результат

    def get_diagnosis_codes(self) -> List[Tuple[str, str]]:
        """Получить все коды диагнозов"""
        return [(code, info["name"]) for code, info in self._data.items()
                if info.get("category") == "diagnosis"]

    def get_service_codes(self) -> List[Tuple[str, str]]:
        """Получить все коды услуг"""
        return [(code, info["name"]) for code, info in self._data.items()
                if info.get("category") == "service"]

    def validate_code(self, code: str, category: Optional[str] = None) -> bool:
        """Проверить существование кода"""
        info = self.get_code_info(code)
        if not info:
            return False
        if category and info.get("category") != category:
            return False
        return True


# Создаем глобальный экземпляр
mkbs_emulator = MKBSEmulator()