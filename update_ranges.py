from datacube_wms.product_ranges import update_all_ranges, update_range
from datacube import Datacube
import click

@click.command()
@click.option("--product", default=None)
def main(product):
    dc = Datacube(app="wms_update_ranges")
    if (product is not None):
        print("Updating range for: ", product)
        update_range(dc, product)
    else:
        print ("Updating ranges for all layers/products")
        p, u, i, sp, su, si = update_all_ranges(dc)
        print ("Updated ranges for %d existing layers/products and inserted ranges for %d new layers/products (%d existing layers/products unchanged)" % (u, i, p))
        if sp or su or si:
            print ("Updated ranges for %d existing sub-products and inserted ranges for %d new sub-products (%d existing sub-products unchanged)" % (su, si, sp))



if __name__ == '__main__':
    main()
