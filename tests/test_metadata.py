import copy

import pytest
import yaml

from common.metadata import lab_directory, load_lab


@pytest.mark.parametrize("mutation", ["no_nc1", "duplicate_claim"])
def test_invalid_scientific_metadata(tmp_path, mutation):
    meta = load_lab(lab_directory("02"))
    if mutation == "no_nc1":
        meta["negative_controls"] = []
    else:
        meta["claims"].append(copy.deepcopy(meta["claims"][0]))
    directory = tmp_path / "02-trace-reuse"
    directory.mkdir()
    (directory / "lab.yaml").write_text(yaml.safe_dump(meta))
    with pytest.raises(ValueError):
        load_lab(directory)
