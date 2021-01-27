from datacube_ows.cfg_parser import main


def test_cfg_parser_simple(runner):
    result = runner.invoke(main, [])
    assert result.exit_code == 0


def test_cfg_parser_parse_only(runner):
    result = runner.invoke(main, ["-p"])
    assert result.exit_code == 0


def test_cfg_parser_version(runner):
    result = runner.invoke(main, ["--version"])
    assert result.exit_code == 0
