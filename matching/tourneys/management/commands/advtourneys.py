"""
Advance tournaments, in which all competitions are finished, to the next round.
"""

from TourneysCommand import TourneysCommand
from tourneys.models import *

class Command(TourneysCommand):
    args = '[options]'
    help = ('Advance tournaments, in which all competitions are finished, to '
            'the next round')

    def handle(self, *args, **options):
        # advance tournaments
        for tournament in Tournament.objects.filter(finished=False):
            tournament.advance()
