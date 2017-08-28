from django.core.management.base import BaseCommand

from app.models import Role

class Command(BaseCommand):
    help = 'Insert predefined roles into database'

    def handle(self, *args, **options):
        Role.insert_roles()
        self.stdout.write(self.style.SUCCESS('Successfully inserted roles'))
