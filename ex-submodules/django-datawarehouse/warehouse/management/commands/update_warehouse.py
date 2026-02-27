from __future__ import unicode_literals
from django.core.management.base import BaseCommand
from optparse import make_option
from logistics_project.utils.parsing import string_to_datetime
from warehouse import runner

class Command(BaseCommand):

    help = "Run the data warehouse"

    def add_arguments(self, parser):
        parser.add_argument(
            '--start-date',
            dest='start_date',
            help='Start date for the warehouse run',
            default=None,
        )
        parser.add_argument(
            '--end-date',
            dest='end_date',
            help='End date for the warehouse run',
            default=None,
        )
        parser.add_argument(
            '--cleanup',
            action='store_true',
            dest='cleanup',
            help='Cleanup the tables before starting the warehouse',
            default=False,
        )

    def handle(self, *args, **options):
        start_date = string_to_datetime(options["start_date"]) if options["start_date"] else None
        end_date = string_to_datetime(options["end_date"]) if options["end_date"] else None
        cleanup = options["cleanup"]
        return runner.update_warehouse(start_date, end_date, cleanup)
