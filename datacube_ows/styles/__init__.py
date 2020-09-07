from datacube_ows.ogc_utils import ConfigException
from datacube_ows.styles.colormap import ColorMapStyleDef
from datacube_ows.styles.component import ComponentStyleDef
from datacube_ows.styles.hybrid import HybridStyleDef
from datacube_ows.styles.ramp import ColorRampDef


def StyleDef(product, cfg):
    try:
        if "component_ratio" in cfg:
            return HybridStyleDef(product, cfg)
        elif cfg.get("components", False):
            return ComponentStyleDef(product, cfg)
        elif cfg.get("value_map", False):
            return ColorMapStyleDef(product, cfg)
        elif cfg.get("color_ramp", False) or cfg.get("range", False):
            return ColorRampDef(product, cfg)
    except KeyError:
        raise ConfigException("Required field missing in style %s of layer %s" % (
            cfg.get("name", ""),
            product.name
        ))