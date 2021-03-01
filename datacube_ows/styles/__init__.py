from datacube_ows.styles.base import StyleDefBase
from datacube_ows.styles.colormap import ColorMapStyleDef
from datacube_ows.styles.component import ComponentStyleDef
from datacube_ows.styles.hybrid import HybridStyleDef
from datacube_ows.styles.ramp import ColorRampDef


StyleDef = StyleDefBase


class StandaloneGlobalProxy:
    pass

class StandaloneProductProxy:
    name = "standalone"
    global_cfg = None


def ows_style_standalone(cfg):
    return StyleDef(StandaloneProductProxy(), cfg, stand_alone=True)

