"""
Delete tournaments between two leagues
"""

from optparse import make_option
import os

from django.core.management.base import BaseCommand, CommandError

from tourneys.models import *

from TourneysCommand import TourneysCommand

class Command(TourneysCommand):
    args = '[options] <targetleague sourceleague>'
    help = 'Delete tournaments between two leagues'

    def getTournamentName(self, targetteam, sourceleague):
        return '%s_%s__%s_tourney' % (targetteam.attribute.name,
                                      'pos' if targetteam.positive else 'neg',
                                      sourceleague.name)

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
        for targetteam in\
            Team.objects.filter(attribute__in=targetleague.attribute_set.all()):
            name = self.getTournamentName(targetteam, sourceleague)
            try:
                tournament = Tournament.objects.get(name=name)
                self.stdout.write('Deleting `%s`' % tournament.name)
                tournament.delete()
            except Tournament.DoesNotExist:
                self.stderr.write('Tournament `%s` does not exist' % name)
