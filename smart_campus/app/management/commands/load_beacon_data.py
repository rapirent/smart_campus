from django.core.management.base import BaseCommand, CommandError
from django.contrib.gis.geos import Point

import pandas as pd

from app.models import Beacon, UserGroup


class Command(BaseCommand):
    help = 'Insert beacon data from xls file'

    def add_arguments(self, parser):
        parser.add_argument('path', nargs=1, type=str)

    def handle(self, *args, **options):
        try:
            data = pd.read_excel(options['path'][0])
            for index, datum in data.iterrows():
                Beacon.objects.update_or_create(
                    beacon_id=datum['Beacon ID'],
                    defaults={
                        'name': datum['idname'],
                        'description': datum['description'],
                        'location': Point(y=float(datum['Latitude']), x=float(datum['Longitude'])),
                        'owner_group': UserGroup.objects.filter(name=datum['OwnerGroup']).first()
                    }
                )
        except FileNotFoundError as e:
            raise CommandError(e)

        self.stdout.write(self.style.SUCCESS('Update beacon data succeeded.'))
