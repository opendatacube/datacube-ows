# Simple Python script for indexing pre-cached EO3 metadata for non-local data.
#
# TODO: Would ideally use stac-to-dc but it hasn't been migrated to datacube-1.9 yet.
import fileinput
import yaml
from datacube import Datacube
from datacube.index.hl import Doc2Dataset

dc = Datacube()
dc_pgis = Datacube(env="owspostgis")

doc2ds = Doc2Dataset(dc.index, products=["s2_l2a", "geodata_coast_100k"], skip_lineage=True, verify_lineage=False)
doc2ds_pgis = Doc2Dataset(dc_pgis.index, products=["s2_l2a", "geodata_coast_100k"], skip_lineage=True, verify_lineage=False)

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
        dc.index.datasets.add(ds, with_lineage=False)
    else:
        print("Dataset add (postgres) failed:", err)
        exit(1)

    ds, err = doc2ds_pgis(doc, uri)
    if ds:
        dc_pgis.index.datasets.add(ds, with_lineage=False)
    else:
        print("Dataset add (postgis) failed:", err)
        exit(1)
