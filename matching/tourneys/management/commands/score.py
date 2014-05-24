"""
Compute all missing scores for finished matches and competitions.
"""

from optparse import make_option

from TourneysCommand import TourneysCommand
from tourneys.models import *

class Command(TourneysCommand):
    args = '[options]'
    help = 'Compute all missing scores for finished matches and competitions'

    def handle(self, *args, **options):
        for competition in Competition.objects.filter(finished=False):
            scores = {}
            all_matches_finished = True
            for match in competition.match_set.all():
                if not match.finished:
                    all_matched_finished = False
                    continue
                competitors = match.competitor_set.all()
                num_winners = competitors.filter(winner=True).count()
                if num_winners > 0:
                    winner_score = 1.0/num_winners
                else:
                    winner_score = 1.0/competitors.count()
                for competitor in competitors:
                    if num_winners == 0 or competitor.winner:
                        competitor.score = winner_score
                    else:
                        competitor.score = 0.0
                    competitor.save()
                    if competitor.competitionteam.pk not in scores:
                        scores[competitor.competitionteam.pk] = []
                    scores[competitor.competitionteam.pk]\
                        .append(competitor.score)
            if all_matches_finished:
                for competitionteam_pk, match_scores in scores.items():
                    competitionteam = CompetitionTeam.objects\
                                                     .get(pk=competitionteam_pk)
                    competitionteam.score = sum(match_scores)/len(match_scores)
                    competitionteam.save()
                competition.finished = True
                competition.save()
           
        
