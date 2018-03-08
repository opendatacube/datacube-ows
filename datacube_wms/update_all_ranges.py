from datacube_wms.product_ranges import update_all_ranges
from datacube_wms.cube_pool import get_cube, release_cube

if __name__ == "__main__":
    app = "wms_update"
    dc = get_cube(app=app)
    passed, updated, inserted, sub_passed, sub_updated, sub_inserted = update_all_ranges(dc)
    release_cube(dc, app=app)
    print("%d existing products unchanged" % passed)
    print("%d existing products updated" % updated)
    print("%d new products inserted" % inserted)

    if sub_updated or sub_inserted or sub_passed:
        print("%d existing sub-products unchanged" % sub_passed)
        print("%d existing sub-products updated" % sub_updated)
        print("%d new sub-products inserted" % sub_inserted)
