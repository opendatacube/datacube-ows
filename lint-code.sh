set -eu
set -x

pylint -j 2 --reports no datacube_ows --disable=C,R,E1136

set +x
