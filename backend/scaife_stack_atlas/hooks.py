from pathlib import Path  # noqa: F401

from scaife_viewer.atlas.hooks import DefaultHookSet


class ATLASHookSet(DefaultHookSet):
    def get_prepared_tokens(self, version_urn):
        # NOTE: Sample override for The life of Omar ben Saeed below
        if version_urn == "urn:cts:arabicLit:amedsaid1831.dw042.perseus-ara1:":
            from scaife_viewer.atlas.tokenizers import get_tokens_from_csv
            csv_path = Path("data/token-overrides/amedsaid1831.dw042.perseus-ara1.csv")
            return get_tokens_from_csv(version_urn, csv_path)
        return super().get_prepared_tokens(version_urn)
