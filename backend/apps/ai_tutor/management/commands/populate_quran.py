from django.core.management.base import BaseCommand
from apps.ai_tutor.services import populate_database


class Command(BaseCommand):
    help = 'Populate ChromaDB with Quran and Hadith data'

    def handle(self, *args, **options):
        self.stdout.write('Starting Quran database population...')
        try:
            populate_database()
            self.stdout.write(
                self.style.SUCCESS('Successfully populated Quran database!')
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error: {e}')
            )