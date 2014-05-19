"""
Delete a tournament along with all child objects.
"""

from optparse import make_option
import os

from django.core.management.base import BaseCommand, CommandError

from tourneys.models import *

class Command(BaseCommand):
    args = '[options] <tournament>'
    help = 'Delete a tournament along with all child objects'

    def get_command(self):
        return os.path.splitext(os.path.basename(__file__))[0]

    def print_help(self):
        super(Command, self).print_help(self.get_command(), None)

    def handle(self, *args, **options):
        # parse commandline
        if len(args) != 1:
            self.print_help()
            return
        tournament_name = args[0]

        # retrieve and delete tournament object
        try:
            tournament = Tournament.objects.get(name=tournament_name)
            self.stdout.write('Deleting `%s`' % tournament.name)
            tournament.delete()
        except Tournament.DoesNotExist:
            raise CommandError('Tournament `%s` does not exist' %\
                               tournament_name)
