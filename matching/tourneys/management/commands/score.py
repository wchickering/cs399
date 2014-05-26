"""
Compute all missing scores for finished matches and competitions.
"""

from django.core.management.base import CommandError

from TourneysCommand import TourneysCommand
from tourneys.models import *

class Command(TourneysCommand):
    args = '[options]'
    help = 'Compute all missing scores for finished matches and competitions'

    def handle(self, *args, **options):
        for competition in Competition.objects.filter(finished=False):
            try:
                competition.score()
            except ValidationError as e:
                raise CommandError(e.message)
