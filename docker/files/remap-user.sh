#!/bin/bash -e

# Script that gives the container user uid $LOCAL_UID and gid $LOCAL_GID.
# If $LOCAL_UID or $LOCAL_GID are not set, they default to 1001 (default
# for the first user created in Ubuntu).

USER_ID=${LOCAL_UID:-1001}
GROUP_ID=${LOCAL_GID:-1001}
OWS_ID=$(id -u ows)

[[ "$USER_ID" == "$OWS_ID" ]] || usermod -u $USER_ID -o -m -d /home/ows ows
[[ "$GROUP_ID" == "$OWS_ID" ]] || groupmod -g $GROUP_ID ows
[[ $(id -u) != "0" ]] || GOSU="/usr/sbin/gosu ows"
exec /usr/bin/tini -- $GOSU "$@"
