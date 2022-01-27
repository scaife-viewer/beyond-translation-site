#!/usr/bin/env python

import os
import sys


if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "scaife_stack_atlas.settings")
    # FIXME: Local dev hack
    os.environ.setdefault("SV_ATLAS_RESOLVE_DICTIONARY_ENTRIES_VIA_LEMMAS", "1")

    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)
