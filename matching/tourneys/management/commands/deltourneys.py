"""
Delete tournaments between two leagues
"""

from django.core.management.base import CommandError

from TourneysCommand import TourneysCommand
from tourneys.models import *

class Command(TourneysCommand):
    args = '[options] <targetleague sourceleague>'
    help = 'Delete tournaments between two leagues'

    def handle(self, *args, **options):
        # parse commandline
        if len(args) != 2:
            raise CommandError('Must provide targetleague and sourceleague')
        targetleague_name = args[0]
        sourceleague_name = args[1]

        # retrieve targetleague
        try:
            targetleague = League.objects.get(name=targetleague_name)
        except League.DoesNotExist:
            raise CommandError(
                'Target league `%s` does not exist.' % targetleague_name
            )

        # retrieve sourceleague
        try:
            sourceleague = League.objects.get(name=sourceleague_name)
        except League.DoesNotExist:
            raise CommandError(
                'Source league `%s` does not exist.' % sourceleague_name
            )

        # retrieve and delete tournament objects
        for tournament in\
            sourceleague.tournament_set\
                        .filter(targetteam__attribute__league=targetleague):
            self.stdout.write('Deleting `%s`' % tournament.name)
            tournament.delete()
