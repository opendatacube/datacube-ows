# Simple Python script for indexing pre-cached EO3 metadata for non-local data.
#
# TODO: Would ideally use stac-to-dc but it hasn't been migrated to datacube-1.9 yet.
import fileinput
import yaml
from datacube import Datacube
from datacube.model import Dataset
from datacube.index.hl import Doc2Dataset

dc = Datacube()

doc2ds = Doc2Dataset(dc.index, products=["s2_l2a"], skip_lineage=True, verify_lineage=False)

for line in fileinput.input():
    filename, uri = line.split()
    with open(filename, "r") as fp:
        doc = yaml.safe_load(fp)
    if "grid_spatial" in doc:
        del doc["grid_spatial"]
    if "extent" in doc:
        del doc["extent"]
    ds, err = doc2ds(doc, uri)
    if ds:
        dc.index.datasets.add(ds)
    else:
        print("Dataset add failed:", err)
        exit(1)

