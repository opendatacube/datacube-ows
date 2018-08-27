import pytest
import datacube


def pytest_addoption(parser):
    parser.addoption("--db_hostname", action="store")
    parser.addoption("--db_port", action="store")
    parser.addoption("--cfg_location", action="store")


@pytest.fixture
def db_hostname(request):
    return request.config.getoption("--db_hostname")


@pytest.fixture
def db_port(request):
    return request.config.getoption("--db_port")


@pytest.fixture
def cube(db_hostname, db_port):
    def get():
        config = {}
        config['db_hostname'] = db_hostname
        config['db_port'] = db_port
        config['db_database'] = 'postgres'
        config['db_username'] = 'postgres'
        config['db_password'] = 'dbtestpassword'
        dc = datacube.Datacube(config=config)
        return dc
    return get


@pytest.fixture
def release_cube_dummy():
    def release(arg):
        pass
    return release
