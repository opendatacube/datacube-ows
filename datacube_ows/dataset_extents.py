from datacube_ows.utils import get_sqlconn
from datacube_ows.product_ranges import get_ranges as old_get_ranges


# UNUSED AND DEPRECATED
#
# Keeping temporarily as an exemplar of what not to do.
def get_ranges(dc, product, path=None, is_dc_product=False):
    if (
            (is_dc_product and product.multi_product)
            or path is not None
        ):
        return old_get_ranges(dc, product, path, is_dc_product)

    with get_sqlconn(dc) as conn:
        if is_dc_product:
            prod_id = product.id
        else:
            prod_id = product.product.id
        # Space
        crsids = list(product.global_cfg.published_CRSs.keys())
        transforms = [
            "Box2D(ST_Transform(ST_SetSRID(ST_Union(spatial_extent), 4326), %s))" % crs_label[5:]
            for crs_label in crsids
            if crs_label != "EPSG:4326"
        ]
        sql = """
        SELECT Box2D(ST_Union(spatial_extent)), 
        """ + ",".join(transforms) + """
        FROM public.space_view sv,
             agdc.dataset ds
        WHERE sv.id = ds.id
        AND   ds.dataset_type_ref = %s
        """
        results = conn.execute(sql,  prod_id)

        for result in results:
            coords = box_coords_from_pgis_str(result[0])
            bboxes = {
            }
            if "EPSG:4326" in crsids:
                bboxes["EPSG:4326"] = {
                    "top": coords[3],
                    "bottom": coords[1],
                    "left": coords[0],
                    "right": coords[2]
                }
            for crsid, bbox in zip(filter(lambda x: x != "EPSG:4326", crsids), result[1:]):
                crs_coords = box_coords_from_pgis_str(bbox)
                bboxes[crsid] = {
                    "top": crs_coords[3],
                    "bottom": crs_coords[1],
                    "left": crs_coords[0],
                    "right": crs_coords[2]
                }

        return {
            "lat": {
                "min": coords[1],
                "max": coords[3]
            },
            "lon": {
                "min": coords[0],
                "max": coords[2]
            },
            "times": [],
            "start_time": None,
            "end_time": None,
            "time_set": set(),
            "bboxes": bboxes
        }


def box_coords_from_pgis_str(pgstr):
    if pgstr[0:4] != "BOX(":
        raise Exception("Not a bounding box string: %s" % pgstr)

    meat = pgstr[4:-1]
    corners = meat.split(",")
    str_coords = [ c.split(" ") for c in corners ]
    return [ float(s) for c in str_coords for s in c ]