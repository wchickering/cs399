"""
Form teams for one or more given leagues.
"""

from optparse import make_option

from django.core.management.base import CommandError

from TourneysCommand import TourneysCommand
from tourneys.models import *

class Command(TourneysCommand):
    args = '[options] <league1> [league2 league3 ...]'
    help = 'Form teams for one or more given leagues'
    option_list = TourneysCommand.option_list + (
        make_option('--teamsize', type='int', dest='teamsize', default=10,
                    help='Number of players per team.'),
    )

    def handle(self, *args, **options):
        # parse command line
        if len(args) < 1:
            raise CommandError(self.args)
        teamsize = options['teamsize']

        # get leagues
        if len(args) == 1 and args[0] == '__all__':
            leagues = League.objects.all()
        else:
            leagues = League.objects.filter(name__in=args)

        # form teams
        for league in leagues:
            self.stdout.write('Forming teams for %s. . .' % league.name)
            for attribute in league.attribute_set.all():
                for positive in [True, False]:
                    team_name = '%s_%s_team' %\
                        (attribute.name, 'pos' if positive else 'neg')
                    # delete any preexisting team
                    try:
                        team = Team.objects.get(name=team_name)
                        team.delete() # cascading delete
                    except Team.DoesNotExist:
                        pass
                    # create new team object
                    team = Team(name=team_name, attribute=attribute,
                                positive=positive)
                    team.save()
                    # get top players for attribute
                    top_playerattributes = PlayerAttribute.objects\
                        .filter(attribute=attribute)\
                        .order_by('-value' if positive else 'value')[:teamsize]
                    for top_pa in top_playerattributes:
                        # create teamplayer object
                        teamplayer = TeamPlayer(team=team, player=top_pa.player)
                        teamplayer.save()

