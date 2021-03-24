import io

import requests
from PIL import Image


def get_image_from_url(url):
    r = requests.get(url, timeout=1)
    if r.status_code == 200 and r.headers["content-type"] == "image/png":
        bytesio = io.BytesIO()
        bytesio.write(r.content)
        bytesio.seek(0)
        return Image.open(bytesio)
    return None
