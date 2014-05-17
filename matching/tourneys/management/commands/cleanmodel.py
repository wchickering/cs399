from django.core.management.base import BaseCommand, CommandError
from django.db.models import get_app, get_models
from django.core.exceptions import ValidationError

class Command(BaseCommand):
    help = 'Validate consistency of tourneys model'

    def writeError(self, model, instance, error):
        self.stderr.write(
            'Validation of %s (pk=%d) failed:\n\t%s' %\
            (model.__name__, instance.pk, '\n\t'.join(error.messages))
        )

    def handle(self, *args, **options):
        app = get_app(args[0])
        for model in get_models(app):
            self.stdout.write('Cleaning %s. . .' % model.__name__)
            for instance in model.objects.all():
                try:
                    instance.full_clean()
                except ValidationError as e:
                    self.writeError(model, instance, e)
                    break
