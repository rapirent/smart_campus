from django.core.management.base import BaseCommand, CommandError
from django.contrib.gis.geos import Point

import pandas as pd

from app.models import Beacon, UserGroup


class Command(BaseCommand):
    help = 'Insert beacon datas from xls file'

    def add_arguments(self, parser):
        parser.add_argument('path', nargs=1, type=str)

    def handle(self, *args, **options):
        try:
            data = pd.read_excel(options['path'][0])
            for i in range(0, len(data)):
                Beacon.objects.update_or_create(
                    beacon_id=data['Beacon ID'][i],
                    defaults={
                        'name': data['idname'][i],
                        'description': data['description'][i],
                        'location': Point(y=float(data['Latitude'][i]), x=float(data['Longitude'][i])),
                        'owner_group': UserGroup.objects.filter(name=data['OwnerGroup'][i]).first()
                    }
                )
        except FileNotFoundError as e:
            raise CommandError(e)

        self.stdout.write(self.style.SUCCESS('Successfully updated beacon datas'))
