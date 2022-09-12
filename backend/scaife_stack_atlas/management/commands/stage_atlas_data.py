import json
import os
import shutil
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand

import yaml


LIBRARY_DIR = os.path.join(settings.SV_ATLAS_DATA_DIR, "library")
ANNOTATIONS_DIR = os.path.join(settings.SV_ATLAS_DATA_DIR, "annotations")


class Command(BaseCommand):
    """
    Stages the ATLAS library data directory

    Demonstrates using external data sets (e.g., data sets that are not
    committed into source control within the repo.)

    jtauber/plato-texts is an example of data packaged in the format used
    by Greek Learner Texts <https://greek-learner-texts.org>

    scaife-viewer/explorhomer-atlas is an example of data packed for ATLAS
    """

    help = "Stages the ATLAS library data directory"

    def add_arguments(self, parser):
        parser.add_argument(
            "--rebuild",
            action="store_true",
            help="Rebuilds the ATLAS library data directory",
        )

    def get_repo_directories(self):
        tmp_path = os.path.join(settings.PROJECT_ROOT, "data-tmp")
        p = Path(tmp_path)
        try:
            return [x for x in p.iterdir() if x.is_dir()]
        except FileNotFoundError:
            self.stderr.write(
                f"{tmp_path} was not found; run fetch-explorehomer-data to create it"
            )
            return []

    def load_atlas_conf(self, repo_dir):
        atlas_conf_path = next(repo_dir.glob("atlas.yaml"), None)
        if not atlas_conf_path:
            self.stdout.write(
                "{repo_dir.name} does not contain an ATLAS configuration file"
            )
            return

        try:
            return yaml.load(open(atlas_conf_path), Loader=yaml.FullLoader)
        except yaml.scanner.ScannerError:
            raise ValueError(f"Unable to load {atlas_conf_path.name}")

    def write_textgroup_metadata(self, dirpaths, data):
        text_group_metadata_path = Path(
            os.path.join(dirpaths["text_group"], "metadata.json")
        )
        if text_group_metadata_path.exists():
            raise ValueError(f"metadata already exists for {data['urn']}")

        json.dump(
            data,
            open(text_group_metadata_path, "w"),
            ensure_ascii=False,
            indent=2,
        )

    def write_work_metadata(self, dirpaths, data):
        work_metadata_path = Path(os.path.join(dirpaths["work"], "metadata.json"))
        if work_metadata_path.exists():
            raise ValueError(f"metadata already exists for {data['urn']}")
        json.dump(data, open(work_metadata_path, "w"), ensure_ascii=False, indent=2)

    def traverse_text_groups(self, repo_dir, conf):
        for text_group in conf["text_groups"]:
            group_part = text_group["urn"][:-1].rsplit(":", maxsplit=1)[1]
            dirpaths = {
                "repo": repo_dir,
                "text_group": os.path.join(LIBRARY_DIR, group_part),
            }
            os.makedirs(dirpaths["text_group"], exist_ok=True)

            works = text_group.pop("works")

            self.write_textgroup_metadata(dirpaths, text_group)

            self.traverse_works(dirpaths, works)

    def traverse_works(self, dirpaths, works):
        for work in works:
            work_part = work["urn"][:-1].rsplit(".", maxsplit=1)[1]
            dirpaths["work"] = os.path.join(dirpaths["text_group"], work_part)
            os.makedirs(dirpaths["work"], exist_ok=True)

            self.write_work_metadata(dirpaths, work)

            self.traverse_versions(dirpaths, work["versions"])

    def get_atlas_version_path(self, version):
        version_part = version["urn"].rsplit(":", maxsplit=2)[1]
        parts = [
            "data",
            "library",
        ]
        parts.extend(version_part.split(".")[:-1])
        extension = version.get("format", "txt")
        parts.append(f"{version_part}.{extension}")
        return "/".join(parts)

    def get_version_path(self, dirpaths, version):
        try:
            version_path = version["path"]
        except KeyError:
            # FIXME: Just refactor LibraryDataResolver a bit to support the
            # "native" structure
            version_path = self.get_atlas_version_path(version)
        return os.path.join(dirpaths["repo"], version_path)

    def traverse_versions(self, dirpaths, versions):
        for version in versions:
            src_path = self.get_version_path(dirpaths, version)
            version_part = version["urn"].rsplit(":")[-2]
            ext = Path(src_path).suffix
            dest_path = Path(os.path.join(dirpaths["work"], f"{version_part}{ext}"))
            if dest_path.exists():
                raise ValueError(f"{dest_path.name} already exists!")
            shutil.copy2(src_path, dest_path)

    def copy_annotations(self, repo_dir, conf):
        if conf.get("annotations"):
            # TODO: Implement copying of annotations
            raise NotImplementedError("Cannot copy annotations")
        else:
            annotations_path = os.path.join(repo_dir, "data", "annotations")
            if os.path.exists(annotations_path):
                for subdir in os.listdir(annotations_path):
                    src = os.path.join(annotations_path, subdir)
                    dest = os.path.join(ANNOTATIONS_DIR, subdir)
                    shutil.copytree(src, dest)

    def rebuild_directory(self, path):
        self.stdout.write(f"Removing and recreating {path}")
        shutil.rmtree(path)
        os.makedirs(path)

    def handle(self, *args, **options):
        if options.get("rebuild"):
            directories = [LIBRARY_DIR, ANNOTATIONS_DIR]
            for dir in directories:
                if os.path.exists(dir):
                    self.rebuild_directory(dir)

        for repo_dir in self.get_repo_directories():
            conf = self.load_atlas_conf(repo_dir)
            if not conf:
                continue
            self.traverse_text_groups(repo_dir, conf)
            self.copy_annotations(repo_dir, conf)
