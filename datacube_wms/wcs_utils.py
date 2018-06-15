import datetime

from datacube.utils import geometry

from datacube_wms.ogc_exceptions import WCS1Exception
from datacube_wms.wms_layers import get_layers, get_service_cfg

class WCS1GetCoverageRequest(object):
    def __init__(self, args):
        self.args = args
        layers = get_layers()
        svc_cfg = get_service_cfg()

        # Argument: Coverage (required)
        if "coverage" not in args:
            raise WCS1Exception("No coverage specified",
                                WCS1Exception.MISSING_PARAMETER_VALUE,
                                locator="COVERAGE parameter")
        self.product_name = args["coverage"]
        self.product = layers.product_index.get(self.product_name)
        if not self.product:
            raise WCS1Exception("Invalid coverage: %s" % self.product_name,
                                WCS1Exception.COVERAGE_NOT_DEFINED,
                                locator="COVERAGE parameter")

        # Argument: (request) CRS (required)
        if "crs" not in args:
            raise WCS1Exception("No request CRS specified",
                                WCS1Exception.MISSING_PARAMETER_VALUE,
                                locator="CRS parameter")
        self.request_crsid = args["crs"]
        if self.request_crsid not in svc_cfg.published_CRSs:
            raise WCS1Exception("%s is not a supported CRS" % self.request_crsid,
                                WCS1Exception.INVALID_PARAMETER_VALUE,
                                locator="CRS parameter")
        self.request_crs = geometry.CRS(self.request_crsid)

        # Argument: response_crs (optional)
        if "response_crs" in args:
            self.response_crsid = args["response_crs"]
            if self.response_crsid not in svc_cfg.published_CRSs:
                raise WCS1Exception("%s is not a supported CRS" % self.request_crsid,
                                    WCS1Exception.INVALID_PARAMETER_VALUE,
                                    locator="RESPONSE_CRS parameter")
            self.response_crs = geometry.CRS(self.response_crsid)
        else:
            self.response_crsid = self.request_crsid
            self.response_crs = self.request_crs

        # Arguments: One of BBOX or TIME is required
        if "bbox" not in args and "time" not in args:
            raise WCS1Exception("At least one of BBOX or TIME parameters must be supplied",
                                WCS1Exception.MISSING_PARAMETER_VALUE,
                                locator="BBOX or TIME parameter"
                                )

        # Argument: BBOX
        if "bbox" in args:
            try:
                if svc_cfg.published_CRSs[self.request_crsid]["vertical_coord_first"]:
                    self.miny, self.minx, self.maxy, self.maxx = map(float, args['bbox'].split(','))
                else:
                    self.minx, self.miny, self.maxx, self.maxy = map(float, args['bbox'].split(','))
            except:
                raise WCS1Exception("Invalid BBOX parameter",
                                    WCS1Exception.INVALID_PARAMETER_VALUE,
                                    locator="BBOX parameter")
        else:
            self.miny, self.minx, self.maxy, self.maxx = (None, None, None, None)

        # Argument: TIME
        if "time" in args:
            # TODO: the min/max/res format option?
            # It's a bit underspeced. I'm not sure what the "res" would look like.
            times = args["times"].split(",")
            self.times = []
            for t in times:
                try:
                    time = datetime.strptime(t, "%Y-%m-%d").date()
                    if time not in self.product.ranges["time_set"]:
                        raise WCS1Exception(
                            "Time value '%s' not a valid date for coverage %s" % (t,self.product_name),
                            WCS1Exception.INVALID_PARAMETER_VALUE,
                            locator="TIME parameter"
                        )
                    self.times.append[t]
                except ValueError:
                    raise WCS1Exception(
                        "Time value '%s' not a valid ISO-8601 date" % t,
                        WCS1Exception.INVALID_PARAMETER_VALUE,
                        locator="TIME parameter"
                    )
            self.times.sort()
        else:
            self.times = None


