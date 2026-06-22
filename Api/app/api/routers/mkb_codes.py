from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from typing import List, Optional

router = APIRouter(prefix="/mkb", tags=["МКБ Коды"])

# МКБ-10 коды (примеры основных стоматологических диагнозов)
MKB_CODES_DATABASE = [
    # Кариес
    {"code": "K02.1", "name": "Кариес дентина", "description": "Кариозное поражение с вовлечением дентина"},
    {"code": "K02.3", "name": "Кариес цемента", "description": "Кариозное поражение корня зуба"},
    {"code": "K02.9", "name": "Кариес неуточнённый", "description": "Кариозное поражение неуточненной локализации"},

    # Пульпит
    {"code": "K04.0", "name": "Пульпит острый", "description": "Воспаление пульпы зуба острого течения"},
    {"code": "K04.1", "name": "Пульпит хронический", "description": "Воспаление пульпы зуба хронического течения"},

    # Периодонтит
    {"code": "K04.5", "name": "Периодонтит хронический апикальный", "description": "Хроническое воспаление периодонта"},
    {"code": "K04.6", "name": "Периодонтит периапикальный", "description": "Воспаление тканей вокруг верхушки корня"},

    # Заболевания десен
    {"code": "K05.0", "name": "Гингивит острый", "description": "Острое воспаление десны"},
    {"code": "K05.1", "name": "Хронический гингивит", "description": "Хроническое воспаление десны"},
    {"code": "K05.2", "name": "Острый пародонтит", "description": "Острое воспаление пародонта"},
    {"code": "K05.3", "name": "Хронический пародонтит", "description": "Хроническое воспаление пародонта"},

    # Абсцесс
    {"code": "K06.8", "name": "Абсцесс перидентальный", "description": "Гнойное воспаление тканей вокруг зуба"},

    # Зубной камень
    {"code": "K03.6", "name": "Отложения зубного камня", "description": "Минерализованные отложения на зубах"},

    # Кровоточивость десен
    {"code": "K06.1", "name": "Кровоточивость десен", "description": "Кровотечение из десневых карманов"},

    # Подвижность зубов
    {"code": "K08.1", "name": "Подвижность зубов", "description": "Патологическая подвижность зубов"},

    # Дефекты пломб
    {"code": "K08.8", "name": "Дефекты пломбы", "description": "Нарушение целостности пломбировочного материала"},

    # Бруксизм
    {"code": "K07.6", "name": "Бруксизм", "description": "Непроизвольный скрежет зубами"},

    # Аномалии прикуса
    {"code": "K07.2", "name": "Аномалия прикуса", "description": "Нарушение соотношения зубных рядов"},
    {"code": "K07.3", "name": "Открытый прикус", "description": "Отсутствие контакта между зубами"},

    # Отсутствие зубов
    {"code": "K08.1", "name": "Полная адентия", "description": "Полное отсутствие зубов"},
    {"code": "K08.4", "name": "Частичная адентия", "description": "Частичное отсутствие зубов"},

    # Неправильный рост зубов
    {"code": "K00.6", "name": "Дистопия зубов", "description": "Неправильное положение зуба"},

    # Флюороз
    {"code": "K00.3", "name": "Флюороз эмали", "description": "Поражение эмали избытком фтора"},
]

class MKBCodeSchema(BaseModel):
    code: str
    name: str
    description: Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {
                "code": "K02.1",
                "name": "Кариес дентина",
                "description": "Кариозное поражение с вовлечением дентина"
            }
        }


@router.get("/codes", response_model=List[MKBCodeSchema], summary="Получить все МКБ коды")
async def get_all_mkb_codes():
    """Получить полный список МКБ-10 кодов для стоматологии"""
    return MKB_CODES_DATABASE


@router.get("/search", response_model=List[MKBCodeSchema], summary="Поиск по МКБ кодам")
async def search_mkb_codes(q: str = Query(..., min_length=1, description="Поисковый запрос (код или название)")):
    """Поиск МКБ кодов по коду или названию диагноза"""
    query_lower = q.lower()
    results = [
        code for code in MKB_CODES_DATABASE
        if query_lower in code["code"].lower() or query_lower in code["name"].lower()
    ]
    if not results:
        raise HTTPException(status_code=404, detail="МКБ коды не найдены")
    return results


@router.get("/by-code/{code}", response_model=MKBCodeSchema, summary="Получить МКБ код по коду")
async def get_mkb_code_by_code(code: str):
    """Получить информацию о конкретном МКБ коде"""
    for mkb in MKB_CODES_DATABASE:
        if mkb["code"].upper() == code.upper():
            return mkb
    raise HTTPException(status_code=404, detail=f"МКБ код {code} не найден")


@router.get("/validate/{code}", summary="Проверить валидность МКБ кода")
async def validate_mkb_code(code: str):
    """Проверить, является ли код валидным МКБ кодом"""
    for mkb in MKB_CODES_DATABASE:
        if mkb["code"].upper() == code.upper():
            return {"valid": True, "code": mkb["code"], "name": mkb["name"]}
    return {"valid": False, "code": code, "message": "Код не найден в базе МКБ"}


@router.get("/categories", summary="Получить категории МКБ кодов")
async def get_mkb_categories():
    """Получить список основных категорий МКБ кодов в стоматологии"""
    categories = {
        "K00": "Нарушения развития и прорезывания зубов",
        "K01": "Зубы, не прорезавшиеся и ретенированные",
        "K02": "Кариес зубов",
        "K03": "Болезни твердых тканей зубов",
        "K04": "Болезни пульпы и периапикальные болезни",
        "K05": "Гингивит и болезни пародонта",
        "K06": "Болезни слизистой оболочки, альвеолярного отростка и твердого неба",
        "K07": "Аномалии развития челюстно-лицевой области и прикуса",
        "K08": "Болезни зубов и их осложнения",
        "K09": "Кисты челюстно-лицевой области",
        "K10": "Болезни челюстей",
        "K11": "Болезни слюнных желез",
        "K12": "Стоматит и родственные поражения",
        "K13": "Другие болезни слизистой оболочки полости рта",
    }
    return categories


@router.get("/recent", response_model=List[MKBCodeSchema], summary="Получить последние МКБ коды")
async def get_recent_mkb_codes(limit: int = Query(10, ge=1, le=50)):
    """Получить последние используемые МКБ коды"""
    return MKB_CODES_DATABASE[:limit]


@router.get("/statistics", summary="Статистика по МКБ кодам")
async def get_mkb_statistics():
    """Получить статистику по доступным МКБ кодам"""
    return {
        "total_codes": len(MKB_CODES_DATABASE),
        "categories": {
            "caries": len([c for c in MKB_CODES_DATABASE if c["code"].startswith("K02")]),
            "pulpitis": len([c for c in MKB_CODES_DATABASE if c["code"].startswith("K04")]),
            "periodontitis": len([c for c in MKB_CODES_DATABASE if c["code"].startswith("K05")]),
            "other": len([c for c in MKB_CODES_DATABASE if not any(c["code"].startswith(p) for p in ["K02", "K04", "K05"])])
        },
        "last_updated": "2026-06-22"
    }
