from __future__ import unicode_literals
from django.core.management.base import BaseCommand
from optparse import make_option
from logistics_project.utils.parsing import string_to_datetime
from warehouse import runner

class Command(BaseCommand):

    help = "Run the data warehouse"
    args = "<start_date> <end_date>"
    label = ""

    def add_arguments(self, parser):
        parser.add_argument(
            '--cleanup',
            action='store_true',
            dest='cleanup',
            help='Cleanup the tables before starting the warehouse',
            default=False,
        )

    def handle(self, *args, **options):
        start_date = None if len(args) < 1 else string_to_datetime(args[0])
        end_date = None if len(args) < 2 else string_to_datetime(args[1])
        cleanup = options["cleanup"]
        return runner.update_warehouse(start_date, end_date, cleanup)
