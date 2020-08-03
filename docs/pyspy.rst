=====
Run pyspy
=====


Docker-Compose
--------------

To start ows with pre-indexed db and pyspy on the side: ::

    docker-compose -f docker-compose.yaml -f docker-compose.db.yaml -f docker-compose.pyspy.yaml up -d

Get Datacube-ows docker process id: ::

    OWS_PID=$(docker inspect --format '{{.State.Pid}}' $(docker inspect -f '{{.Name}}' \
    $(docker-compose -f docker-compose.yaml -f docker-compose.db.yaml -f docker-compose.pyspy.yaml ps -q ows) \
    | cut -c2-))

Run py-spy: ::

    docker-compose -f docker-compose.yaml -f docker-compose.db.yaml -f docker-compose.pyspy.yaml \
    run pyspy record -f speedscope -o profile.json --pid $OWS_PID --subprocesses