"""
Creates and save a translation matrix between leagues based on the results of
tournaments.
"""

from optparse import make_option

from django.core.management.base import CommandError

from TourneysCommand import TourneysCommand
from tourneys.models import *

class Command(TourneysCommand):
    args = '[options] <targetleague sourceleague>'
    help = ('Creates and save a translation matrix between leagues based on '
            'the results of tournaments.')
    option_list = TourneysCommand.option_list + (
        make_option('--someoption', dest='someoption', default='blah',
                    help=('This is just an example of what an option looks '
                          'like.')),
    )

    def handle(self, *args, **options):
        # parse command line
        if len(args) != 2:
            raise CommandError('Must provide targetleague and sourceleage')
        targetleague_name = args[0]
        sourceleague_name = args[1]
        someoption = options['someoption']

        # get targetleague
        try:
            targetleague = League.objects.get(name=targetleague_name)
        except League.DoesNotExist:
            raise CommandError('Cannot find targetleague: %s' %\
                               targetleague_name)
        # get sourceleague
        try:
            sourceleague = League.objects.get(name=sourceleague_name)
        except League.DoesNotExist:
            raise CommandError('Cannot find sourceleague: %s' %\
                               sourceleague_name)

        # Get the tournaments
        for targetteam in Team.objects.filter(attribute__league=targetleague):
            try:
                tournament = Tournament.objects\
                                       .filter(targetteam=targetteam).get()
            except Tournament.DoesNotExist:
                raise CommandError(
                    'Tournament not found for %(targetteam)s',
                    params={'targetteam': targetteam}
                )
            self.stdout.write(
                'DBG: Processing tournamet: %s' % tournament.name
            )
            # Get the competitions for this tournament
            for competition in tournament.competition_set.all():
                self.stdout.write(
                    'DBG:     ==== Round %d Competition ====' %\
                    competition.round
                )
                # Get the competitionteams for this competition
                for competitionteam in competition.competitionteam_set.all():
                    self.stdout.write(
                        'DBG:     attribute %s (%s), score=%0.3f' % (
                            competitionteam.team.attribute,
                            ('+' if competitionteam.team.positive else '-'),
                            competitionteam.score
                        )
                    )

