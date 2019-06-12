#pylint: skip-file
# From https://github.com/amitsaha/python-prometheus-demo
from flask import request, Response
from prometheus_client import Histogram
import time
import prometheus_client
from prometheus_client import multiprocess, CollectorRegistry

registry = CollectorRegistry()
multiprocess.MultiProcessCollector(registry)

REQUEST_DURATION = Histogram('http_request_duration_seconds', 'HTTP Request Duration',
                             ['operation', 'service'],
                             registry=registry,
                            )

def start_timer():
    request.start_time = time.time()

def stop_timer(response):
    resp_time = time.time() - request.start_time
    REQUEST_DURATION.labels(operation=request.args.get("request"), service=request.args.get("service")).observe(resp_time)
    return response

def setup_prometheus(app):
    app.before_request(start_timer)
    app.after_request(stop_timer)

    @app.route('/metrics')
    def metrics():
        return Response(prometheus_client.generate_latest(registry))
