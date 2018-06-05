from datacube_wms.wms_cfg_local import response_cfg


def resp_headers(d):
    hdrs = {}
    hdrs.update(response_cfg)
    hdrs.update(d)
    return hdrs