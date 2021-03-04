from datacube_ows.styles.base import StyleDefBase
from datacube_ows.styles.colormap import ColorMapStyleDef
from datacube_ows.styles.component import ComponentStyleDef
from datacube_ows.styles.hybrid import HybridStyleDef
from datacube_ows.styles.ramp import ColorRampDef


StyleDef = StyleDefBase


class StandaloneGlobalProxy:
    pass

class BandIdxProxy:
    def band(self, band):
        return band

class StandaloneProductProxy:
    name = "standalone"
    global_cfg = None
    band_idx = BandIdxProxy()


def ows_style_standalone(cfg):
    style = StyleDef(StandaloneProductProxy(), cfg, stand_alone=True)
    style.make_ready(None)
    return style

