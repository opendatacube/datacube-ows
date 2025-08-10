# This file is part of datacube-ows, part of the Open Data Cube project.
# See https://opendatacube.org for more information.
#
# Copyright (c) 2017-2024 OWS Contributors
# SPDX-License-Identifier: Apache-2.0

import numpy as np
import pytest

from datacube_ows.config_utils import CFG_DICT, ConfigException
from datacube_ows.styles.base import StyleDefBase


def test_multidate_handler() -> None:
    # TODO: Consolidate these into a fixture
    class FakeData:
        def __init__(self) -> None:
            self.nodata = np.nan

        def item(self) -> float:
            return np.nan

    class FakeDataset:
        def __getitem__(self, key):
            return FakeData()

    class FakeMdhStyle:
        include_in_feature_info = True

        def __init__(self) -> None:
            self.product = "test"
            self.needed_bands = ["test"]
            self.index_function = lambda x: FakeData()
            self.stand_alone = True
            self.transform_single_date_data = lambda x: x

    fake_cfg: CFG_DICT = {
        "allowed_count_range": [0, 10],
        "aggregator_function": "datacube_ows.band_utils.multi_date_delta",
    }

    fake_cfg_anim: CFG_DICT = {
        "allowed_count_range": [2, 10],
        "aggregator_function": "datacube_ows.band_utils.multi_date_pass",
        "animate": True,
    }

    fake_cfg_equal: CFG_DICT = {
        "allowed_count_range": [1, 1],
        "aggregator_function": "datacube_ows.band_utils.multi_date_delta",
    }

    mdh = StyleDefBase.MultiDateHandler(FakeMdhStyle(), fake_cfg)
    with pytest.raises(NotImplementedError):
        mdh.legend_cfg.render(None)
    assert isinstance(mdh.range_str(), str)
    assert mdh.applies_to(2)
    assert not mdh.applies_to(11)
    assert not mdh.animate

    mdh_anim = StyleDefBase.MultiDateHandler(FakeMdhStyle(), fake_cfg_anim)
    assert mdh_anim.animate

    mdh_equal = StyleDefBase.MultiDateHandler(FakeMdhStyle(), fake_cfg_equal)
    assert isinstance(mdh_equal.range_str(), str)

    with pytest.raises(ConfigException) as excinfo:
        _ = StyleDefBase.MultiDateHandler(FakeMdhStyle(), {})

    assert "must have an allowed_count_range" in str(excinfo.value)

    with pytest.raises(ConfigException) as excinfo:
        _ = StyleDefBase.MultiDateHandler(
            FakeMdhStyle(), {"allowed_count_range": [0, 5, 10]}
        )

    assert "allowed_count_range must have 2" in str(excinfo.value)

    with pytest.raises(ConfigException) as excinfo:
        _ = StyleDefBase.MultiDateHandler(
            FakeMdhStyle(), {"allowed_count_range": [10, 5]}
        )

    assert "minimum must be less than equal to maximum" in str(excinfo.value)

    with pytest.raises(ConfigException) as excinfo:
        _ = StyleDefBase.MultiDateHandler(
            FakeMdhStyle(), {"allowed_count_range": [0, 10]}
        )

    assert "Aggregator function is required" in str(excinfo.value)

    assert mdh.transform_data(None) is None
