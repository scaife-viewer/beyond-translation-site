import multiprocessing
import os

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.core.management import call_command
from django.core.management.base import BaseCommand

from contexttimer import Timer
from scaife_viewer.atlas import tokenizers
from scaife_viewer.atlas.importers import (
    # alignments,
    audio_annotations,
    token_annotations,
    image_annotations,
    metrical_annotations,
    named_entities,
    text_annotations,
    versions,
)

from ...temp import process_alignments


class Command(BaseCommand):
    """
    Prepares the database
    """

    help = "Prepares the database"

    def add_arguments(self, parser):
        parser.add_argument(
            "--force",
            action="store_true",
            help="Forces the ATLAS management command to run",
        )

    def emit_log(self, func_name, elapsed):
        self.stdout.write(f"Step completed: [func={func_name} elapsed={elapsed:.2f}]")

    def do_step(self, label, callback):
        with Timer() as t:
            self.stdout.write(f"--[{label}]--")
            callback()
        self.emit_log(callback.__name__, t.elapsed)

    def do_stage(self, stage):
        # NOTE: Revisit running stage callbacks in parallel in the future
        for label, callback in stage["callbacks"]:
            self.do_step(label, callback)

    def handle(self, *args, **options):
        # TODO: Factor out in favor of scaife_viewer_atlas `prepare_atlas_db` command
        database_path = settings.SV_ATLAS_DB_PATH

        if database_path is None:
            msg = "The SV_ATLAS_DB_PATH setting is missing and is required for this management command to work."
            raise ImproperlyConfigured(msg)

        db_path_exists = os.path.exists(database_path)

        reset_data = options.get("force") or not db_path_exists
        if not reset_data:
            self.stdout.write(f"Found existing ATLAS data at {database_path}")
            return

        if db_path_exists:
            os.remove(database_path)
            self.stdout.write("--[Removed existing ATLAS database]--")
        else:
            db_dir = os.path.dirname(database_path)
            os.makedirs(db_dir, exist_ok=True)

        with Timer() as t:
            db_label = settings.SV_ATLAS_DB_LABEL
            self.stdout.write(f'--[Running database migrations on "{db_label}"]--')
            call_command("migrate", database=db_label)

        self.emit_log("migrate", t.elapsed)

        self.do_step("Loading versions", versions.import_versions)

        stage_1 = {
            "name": "stage 1",
            "callbacks": [
                ("Loading text annotations", text_annotations.import_text_annotations,),
                (
                    "Loading metrical annotations",
                    metrical_annotations.import_metrical_annotations,
                ),
                (
                    "Loading image annotations",
                    image_annotations.import_image_annotations,
                ),
                (
                    "Loading audio annotations",
                    audio_annotations.import_audio_annotations,
                ),
            ],
        }
        self.do_stage(stage_1)

        # NOTE: Tokenizing should never be ran in parallel, because
        # it is already parallel

        concurrency_value = (
            settings.SV_ATLAS_INGESTION_CONCURRENCY or multiprocessing.cpu_count()
        )
        self.stdout.write(f"SV_ATLAS_INGESTION_CONCURRENCY: {concurrency_value}")
        self.do_step(
            "Tokenizing versions/exemplars", tokenizers.tokenize_all_text_parts
        )

        stage_2 = {
            "name": "stage 2",
            "callbacks": [
                (
                    "Loading token annotations",
                    token_annotations.apply_token_annotations,
                ),
                (
                    "Loading named entity annotations",
                    named_entities.apply_named_entities,
                ),
                ("Loading alignments", process_alignments),
            ],
        }
        self.do_stage(stage_2)
