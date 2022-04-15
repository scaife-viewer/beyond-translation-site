# TODO: Update extractors to use this wrapper

import importlib

from django.core.management.base import BaseCommand


class Command(BaseCommand):
    """
    Runs an extractor script from a Django context.

    This enables us to import from scaife_viewer.* modules
    that use appconf.
    """

    help = "Runs an extractor script from a Django context"

    def add_arguments(self, parser):
        parser.add_argument(
            "script_name", help="Name of the extractor script to run",
        )

    def handle(self, *args, **options):
        script = options["script_name"]
        extractor = importlib.import_module(f"scaife_stack_atlas.extractors.{script}")
        self.stdout.write(f"Running {script}")
        extractor.main()
