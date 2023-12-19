import os
from pathlib import Path

from django.conf import settings

from scaife_viewer.atlas.hooks import DefaultHookSet


OVERRIDES_DATA_PATH = Path(os.path.join(settings.SV_ATLAS_DATA_DIR, "token-overrides"))
OVERRIDES = {
    "urn:cts:greekLit:tlg2022.tlg007.gio-grc1:": OVERRIDES_DATA_PATH
    / "gio_grc_tokens.csv",
    "urn:cts:greekLit:tlg2022.tlg007.gio-eng1:": OVERRIDES_DATA_PATH
    / "gio_eng_tokens.csv",
    "urn:cts:arabicLit:amedsaid1831.dw042.perseus-ara1:": OVERRIDES_DATA_PATH
    / "amedsaid1831.dw042.perseus-ara1.csv",
}


class ATLASHookSet(DefaultHookSet):
    def get_prepared_tokens(self, version_urn):
        override_path = OVERRIDES.get(version_urn)
        if override_path:
            from scaife_viewer.atlas.tokenizers import get_tokens_from_csv

            return get_tokens_from_csv(version_urn, override_path)
        return super().get_prepared_tokens(version_urn)
