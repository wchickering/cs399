"""
Setup new tournaments between two leagues.
"""

from optparse import make_option

from django.core.management.base import CommandError

from TourneysCommand import TourneysCommand
from tourneys.models import *

class Command(TourneysCommand):
    args = '[options] <targetleague sourceleague>'
    help = ('Setup new tournaments between two leagues')
    option_list = TourneysCommand.option_list + (
        make_option('--numplayers', type='int', dest='numplayers', default=4,
                    help='Number of players per match.'),
        make_option('--nummatches', type='int', dest='nummatches', default=5,
                    help='Number of matches per competition.'),
    )

    def createTournaments(self, targetleague_name, sourceleague_name,
                          num_players, num_matches):
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
        # for now, all tournaments are single-elimination
        tournamenttype = TournamentType.objects.get(name='single-elimination')
        sourceleague.create_tournaments(targetleague, tournamenttype,
                                        num_players, num_matches)

    def handle(self, *args, **options):
        # parse command line
        if len(args) != 2:
            raise CommandError('Must provide targetleague and sourceleague')
        targetleague_name = args[0]
        sourceleague_name = args[1]
        num_players = options['numplayers']
        num_matches = options['nummatches']

        # create new tournaments
        self.createTournaments(targetleague_name, sourceleague_name,
                               num_players, num_matches)
