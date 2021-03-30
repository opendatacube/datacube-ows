#!/bin/bash
# Run a bunch of test URL for performance
while true
do
    curl 'http://localhost:8000/wms?service=WMS&version=1.3.0&request=GetMap&layers=ls8_usgs_level1_scene_layer&styles=rgb_ndvi&width=150&height=150&crs=EPSG%3A4326&bbox=-43.82093348558336%2C145.040403833046%2C-42.53486321090564%2C147.787537852719&format=image%2Fpng&transparent=TRUE&bgcolor=0xFFFFFF&exceptions=XML&time=2019-07-09' -o map.png
done
