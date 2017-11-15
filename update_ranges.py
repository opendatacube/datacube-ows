from datacube_wms.product_ranges import update_all_ranges
from datacube import Datacube

if __name__ == '__main__':
    dc = Datacube(app="wms_update_ranges")
    print ("Updating ranges for all layers/products")
    p, u, i = update_all_ranges(dc)
    print ("Updated ranges for %d existing layers/products and inserted ranges for %d new layers/products (%d existing layers/products unchanged)" % (u, i, p))
