from django.core.management.base import BaseCommand, CommandError

class TourneysCommand(BaseCommand):
    def get_command(self):
        return os.path.splitext(os.path.basename(__file__))[0]

    def print_help(self):
        super(Command, self).print_help(self.get_command(), None)
