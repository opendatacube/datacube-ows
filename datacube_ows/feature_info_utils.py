"""
Utility functions for custom feature info calls
"""


def get_water_info(data: dict, hostname: str, path: str):
    return {
        'timeseries': f"{hostname}/{path}"\
        f"{int(data['dam_id']) // 100:04}/{int(data['dam_id']):06}.csv"
    }
