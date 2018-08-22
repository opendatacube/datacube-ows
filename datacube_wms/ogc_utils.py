from __future__ import absolute_import, division, print_function

try:
    from datacube_wms.wms_cfg_local import service_cfg, layer_cfg, response_cfg
except ImportError:
    from datacube_wms.wms_cfg import service_cfg, layer_cfg, response_cfg


def resp_headers(d):
    hdrs = {}
    hdrs.update(response_cfg)
    hdrs.update(d)
    return hdrs
