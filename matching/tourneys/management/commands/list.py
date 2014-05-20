"""
List all custom commands with help strings.
"""

from django.core.management import find_management_module, find_commands,\
                                   load_command_class
from django.core.management.base import NoArgsCommand
from django.conf import settings

class Command(NoArgsCommand):
    help = 'Show the list of custom management commands in this project.'
    requires_model_validation = False

    def handle_noargs(self, **options):
        app_names = [a for a in settings.INSTALLED_APPS\
                     if not a.startswith('django.')]
        self.stdout.write('Custom management commands in this project:')
        for app_name in app_names:
            command_names = find_commands(find_management_module(app_name))
            for command_name in command_names:
                help_text = load_command_class(app_name, command_name).help
                self.stdout.write(
                    '%s\n\t%s (%s)\n' % (command_name, help_text, app_name)
                )
        if not app_names:
            self.stdout.write('None')

