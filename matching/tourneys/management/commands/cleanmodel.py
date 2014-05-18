"""
Invoke .full_clean() on all models for one or more given apps.
"""

from optparse import make_option

from django.core.management.base import AppCommand
from django.db.models import get_models
from django.core.exceptions import ValidationError

class Command(AppCommand):
    help = 'Validate consistency of tourneys model'
    option_list = AppCommand.option_list + (
        make_option('--exclude',
            dest='exclude',
            default=None,
            help='Exclude model(s) from cleaning.'),
        )

    def writeError(self, model, instance, error):
        self.stderr.write(
            'Validation of %s (pk=%d) failed:\n\t%s' %\
            (model.__name__, instance.pk, '\n\t'.join(error.messages))
        )

    def handle_app(self, app, **options):
        exclude_list = []
        if 'exclude' in options and options['exclude'] is not None:
            exclude_list += options['exclude'].split(',')
        for model in get_models(app):
            if model.__name__ in exclude_list: continue
            self.stdout.write('Cleaning %s. . .' % model.__name__)
            for instance in model.objects.all():
                try:
                    instance.full_clean()
                except ValidationError as e:
                    self.writeError(model, instance, e)
                    return
