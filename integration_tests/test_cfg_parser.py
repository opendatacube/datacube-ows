from datacube_ows.cfg_parser import main


def test_cfg_parser_simple(runner):
    result = runner.invoke(main, [])
    assert result.exit_code == 0


def test_cfg_parser_parse_only(runner):
    result = runner.invoke(main, ["-p"])
    assert result.exit_code == 0

def test_cfg_parser_parse_only(runner):
    result = runner.invoke(main, ["-p"])
    assert result.exit_code == 0

def test_cfg_parser_folder_hierarchy(runner):
    result = runner.invoke(main, ["-f"])
    assert result.exit_code == 0

def test_cfg_parser_styles(runner):
    result = runner.invoke(main, ["-s"])
    assert result.exit_code == 0

def test_cfg_parser_folder_hierarchy_and_styles(runner):
    result = runner.invoke(main, ["-f", "-s"])
    assert result.exit_code == 0

def test_cfg_parser_folders_parse_only(runner):
    result = runner.invoke(main, ["-f", "-p"])
    assert result.exit_code == 1


def test_cfg_parser_version(runner):
    result = runner.invoke(main, ["--version"])
    assert result.exit_code == 0
