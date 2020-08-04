=====
Run pyspy
=====


Docker-Compose
--------------
To make the chained docker-compose with pre-indexed database: ::

     COMPOSE_CHAIN='docker-compose -f docker-compose.yaml -f docker-compose.db.yaml -f docker-compose.pyspy.yaml'

To make the chained docker-compose with local database: ::

     COMPOSE_CHAIN='docker-compose -f docker-compose.yaml -f docker-compose.pyspy.yaml'

To start ows with pre-indexed db and pyspy on the side: ::

    $COMPOSE_CHAIN up -d

Get Datacube-ows docker process id: ::

    OWS_PID=$(docker inspect --format '{{.State.Pid}}' $(docker inspect -f '{{.Name}}' \
    $($COMPOSE_CHAIN ps -q ows) | cut -c2-))

Run py-spy: ::

    $COMPOSE_CHAIN run pyspy record -f speedscope -o profile.json \
    --pid $OWS_PID --subprocesses