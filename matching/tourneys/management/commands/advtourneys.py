"""
Advance tournaments, in which all competitions are finished, to the next round.
"""

from django.core.management.base import CommandError

from TourneysCommand import TourneysCommand
from tourneys.models import *

class Command(TourneysCommand):
    args = '[options]'
    help = ('Advance tournaments, in which all competitions are finished, to '
            'the next round')

    def handle(self, *args, **options):
        # advance tournaments
        for tournament in Tournament.objects.filter(finished=False):
            try:
                tournament.advance()
            except ValidationError as e:
                raise CommandError(e.message)
