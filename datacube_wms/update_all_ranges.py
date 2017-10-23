from datacube_wms.product_ranges import update_all_ranges
from datacube import Datacube

if __name__ == "___main__":
    dc = Datacube(app="wms_update")
    updated, inserted = update_all_ranges(dc)
    print ("%d existing products updated")
    print ("%d new products inserted")