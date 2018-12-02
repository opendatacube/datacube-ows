#!/usr/bin/env bash

# Pass in dir to watch, allows us to update wms config without changing
# how wms loads config
# Pass in file name to watch

if [[ ! -f gunicorn.pid ]]
then
    exit 1
fi

watchmedo shell-command \
    --patterns="*$2" \
    --ignore-directories \
    --command='cp "${watch_src_path}" /code/datacube_wms/wms_cfg.py && kill -HUP `cat gunicorn.pid`' \
    --wait \
    $1
