"""
Utility functions for custom feature info calls
"""


def get_water_info(data: dict, hostname: str, path: str):
    """
    Use in ows_cfg.py as below:

    "feature_info": {
     "include_custom": {
        "function" : "datacube_ows.feature_info_utils.get_water_info",
        "kwargs" : {
            "hostname" : "https://data.dea.ga.gov.au",
            "path" : "projects/WaterBodies/feature_info/"
            }
        }
    }

    Returns:
        [dict] -- Timeseries feature info
    """
    return {
        'timeseries': f"{hostname}/{path}"
        f"{int(data['dam_id']) // 100:04}/{int(data['dam_id']):06}.csv"
    }
