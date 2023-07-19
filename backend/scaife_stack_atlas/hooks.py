from pathlib import Path  # noqa: F401

from scaife_viewer.atlas.hooks import DefaultHookSet


class ATLASHookSet(DefaultHookSet):
    def get_prepared_tokens(self, version_urn):
        # NOTE: Sample override for Iliad tokens shown below:
        # if version_urn == "urn:cts:greekLit:tlg0012.tlg001.perseus-grc2:":
        #     from scaife_viewer.atlas.tokenizers import get_tokens_from_csv
        #     csv_path = Path("killroy.csv")
        #     return get_tokens_from_csv(version_urn, csv_path)
        return super().get_prepared_tokens(version_urn)
