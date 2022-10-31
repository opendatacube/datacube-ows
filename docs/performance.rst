=====
Performance deep dive
=====

ows_stats
=========

append ::

    &ows_stats=yes

to getmaps query for a view like this ::

    {
        profile: {
            query: 0.060224294662475586,
            count-datasets: 0.027852535247802734,
            extent-in-query: 0.017885684967041016,
            write: 0.014366865158081055
        },
        info: {
            n_dates: 1,
            zoom_factor: 14.030289733687082,
            n_datasets: 9,
            too_many_datasets: false,
            zoomed_out: true,
            write_action: "Polygon"
        }
    }

Run pyspy
=========

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
