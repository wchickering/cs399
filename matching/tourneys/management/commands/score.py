"""
Compute all missing scores for finished matches and competitions.
"""

from optparse import make_option
import os
import numpy as np

from django.core.management.base import BaseCommand, CommandError

from tourneys.models import *

class Command(BaseCommand):
    args = '[options]'
    help = 'Compute all missing scores for finished matches and competitions'

    def get_command(self):
        return os.path.splitext(os.path.basename(__file__))[0]

    def print_help(self):
        super(Command, self).print_help(self.get_command(), None)

    def handle(self, *args, **options):
        for competition in Competition.objects.raw(
            ('SELECT * FROM tourneys_competition AS C '
             'WHERE finished = 0 '
             'AND EXISTS (SELECT * FROM tourneys_match AS M, '
                         'tourneys_competitor AS CR '
                         'WHERE CR.match_id = M.id '
                         'AND M.competition_id = C.id '
                         'AND CR.score IS NULL)')
        ):
            scores = {}
            for match in competition.match_set.filter(finished=True):
                competitors = match.competitor_set.all()
                num_winners = competitors.filter(winner=True).count()
                winner_score = 1.0/num_winners
                for competitor in competitors:
                    if competitor.winner:
                        competitor.score = winner_score
                    else:
                        competitor.score = 0.0
                    competitor.save()
                    if competitor.competitionteam.pk not in scores:
                        scores[competitor.competitionteam.pk] = []
                    scores[competitor.competitionteam.pk]\
                        .append(competitor.score)
            for competitionteam_pk, match_scores in scores.items():
                competitionteam = CompetitionTeam.objects\
                                                 .get(pk=competitionteam_pk)
                competitionteam.score = sum(match_scores)/len(match_scores)
                competitionteam.save()
            competition.finished = True
            competition.save()
           
        
