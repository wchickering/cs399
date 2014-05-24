"""
Advance tournaments in which all competitions are finished to the next round.
"""

from optparse import make_option
import random

from django.core.management.base import CommandError

from TourneysCommand import TourneysCommand
from tourneys.models import *

class Command(TourneysCommand):
    args = '[options]'
    help = ('Advance tournaments in which all competitions are finished to the '
            'next round')
    option_list = TourneysCommand.option_list + (
        make_option('--seed', type='int', dest='seed', default=None,
                    help='Seed for random number generator.'),
    )

    def handle(self, *args, **options):
        # parse command line
        seed = options['seed']

        # seed rng
        if seed is not None:
            random.seed(seed)

        # advance tournaments
        for tournament in Tournament.objects.filter(finished=False):
            all_competitions_finished = True
            winners = []
            for competition in tournament.competition_set\
                                         .filter(round=tournament.round):
                if not competition.finished:
                    all_competitions_finished = False
                    break
                candidates = []
                for competitionteam in competition.competitionteam_set\
                                                  .order_by('-score'):
                    if not candidates or \
                        competitionteam.score == candidates[-1].score:
                        candidates.append(competitionteam)
                    else:
                        break
                winners.append(random.choice(candidates).team)
            if not all_competitions_finished:
                # tournament round not complete
                continue
            if len(winners) == 1:
                # tournament finished
                tournament.finished = True
                tournament.save()
                continue
            random.shuffle(winners)
            # create competition objects
            for i in range(len(winners)/tournament.num_players):
                # create competition object
                competition = Competition(tournament=tournament,
                                          round=tournament.round + 1)
                tournament.competition_set.add(competition)
                # create competitionteam objects
                for j in range(tournament.num_players):
                    team = winners.pop()
                    competitionteam = CompetitionTeam(competition=competition,
                                                      team=team)
                    competition.competitionteam_set.add(competitionteam)
                targetteamplayers =\
                    list(tournament.targetteam.teamplayer_set.all())
                # randomize target teamplayers
                random.shuffle(targetteamplayers)
                teamplayer_lists = {}
                for competitionteam in competition.competitionteam_set.all():
                    teamplayers =\
                        list(competitionteam.team.teamplayer_set.all())
                    # randomize source teamplayers
                    random.shuffle(teamplayers)
                    teamplayer_lists[competitionteam.pk] = teamplayers
                # create matches
                for j in range(tournament.num_matches):
                    # create match object
                    match = Match(competition=competition,
                                  teamplayer=targetteamplayers.pop())
                    competition.match_set.add(match)
                    for competitionteam in competition.competitionteam_set\
                                                      .all():
                        # create competitor object
                        teamplayer =\
                            teamplayer_lists[competitionteam.pk].pop()
                        competitor = Competitor(match=match,
                                                competitionteam=competitionteam,
                                                teamplayer=teamplayer)
                        match.competitor_set.add(competitor)
            tournament.round += 1
            tournament.save()
 
                    
