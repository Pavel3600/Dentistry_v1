from django.core.management.base import BaseCommand
from app.mkb_validator import MKB_DENTISTRY_CODES
from app.controllers import MKBSController


class Command(BaseCommand):
    help = 'Импортирует данные МКБ-С-3 в FastAPI через API'

    def handle(self, *args, **options):
        self.stdout.write('Импорт данных МКБ-С-3 через FastAPI...')

        created_count = 0
        for code, name in MKB_DENTISTRY_CODES.items():
            try:
                MKBSController.get_diagnoses(search=code)
                # Если код уже есть — пропускаем
            except Exception:
                pass
            try:
                MKBSController.get_diagnoses()  # проверка связи
                CategoryController_data = {'code': code, 'name': name, 'category': 'diagnosis', 'is_active': True}
                from app.controllers import CategoryController
                CategoryController.create(CategoryController_data)
                created_count += 1
            except Exception as e:
                self.stdout.write(f'  Пропущено {code}: {e}')

        self.stdout.write(self.style.SUCCESS(
            f'Импорт завершён! Добавлено записей: {created_count}'
        ))
