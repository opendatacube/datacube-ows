#!/bin/sh

if [ "$WMS_CONFIG_URL" ]
then
    A=$$; ( wget -q "$WMS_CONFIG_URL" -O $A.d && mv $A.d /code/datacube_wms/wms_cfg.py ) || (rm $A.d; echo "Failed to download WMS config file")
fi
