from datacube import Datacube
from yaml import dump

dc = Datacube()

i = 1
for ds in dc.index.datasets.search(product="s2_l2a"):
    filename = "s2_l2a_ds_%02d.yaml" % i
    with open(filename, "w") as fp:
        fp.write(dump(ds.metadata_doc, default_flow_style=False))
    print(filename, ds.uri)

    i = i + 1
