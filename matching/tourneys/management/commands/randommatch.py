"""
Randomly choose winners for all unfinished matches.
"""

from optparse import make_option
import os
import random

from django.core.management.base import BaseCommand, CommandError

from tourneys.models import *

from TourneysCommand import TourneysCommand

class Command(TourneysCommand):
    args = '[options]'
    help = 'Randomly choose winners for all unfinished matches'
    option_list = BaseCommand.option_list + (
        make_option('--seed', type='int', dest='seed', default=None,
                    help='Seed for random number generator.'),
    )

    def handle(self, *args, **options):
        # parse command line
        seed = options['seed']

        # seed rng
        if seed is not None:
            random.seed(seed)

        for match in Match.objects.filter(finished=False):
            competitors = match.competitor_set.all()
            winner = random.choice(competitors)
            winner.winner = True
            winner.save()
            for competitor in competitors:
                if competitor.winner != True:
                    competitor.winner = False
                    competitor.save()
            match.finished = True
            match.save()
