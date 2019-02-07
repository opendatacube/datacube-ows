# Style index functions

def norm_diff(data, band1, band2, product_cfg=None):
    # Calculate a normalised difference index.

    if product_cfg:
        b1=product_cfg.band_idx.band(band1)
        b2=product_cfg.band_idx.band(band2)
    else:
        b1 = band1
        b2 = band2
    return (data[b1] - data[b2]) / (data[b1] + data[b2])


def constant(data, band, const, product_cfg=None):
    # Covert an xarray for a flat constant.
    # Useful for displaying mask extents as a flat colour and debugging.
    # params is assumed to be a tuple containing a constant value and a band name/alias.

    if product_cfg:
        b = product_cfg.band_idx.band(band)
    else:
        b = band
    return data[b] * 0.0 + const


def single_band(data, band, product_cfg=None):
    # Use the raw value of a band directly as the index function.

    if product_cfg:
        b = product_cfg.band_idx.band(band)
    else:
        b = band
    return data[b]

