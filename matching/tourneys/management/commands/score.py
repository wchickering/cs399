"""
Compute all missing scores for finished matches and competitions.
"""

from TourneysCommand import TourneysCommand
from tourneys.models import *

class Command(TourneysCommand):
    args = '[options]'
    help = 'Compute all missing scores for finished matches and competitions'

    def handle(self, *args, **options):
        for competition in Competition.objects.filter(finished=False):
            competition.score()
