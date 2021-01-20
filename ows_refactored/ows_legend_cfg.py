# Reusable Chunks 3. Legends
legend_idx_0_1_5ticks = {"begin": "0.0", "end": "1.0", "ticks_every": "0.2"}

legend_idx_percentage_by_10 = {
    "begin": "0.0",
    "end": "1.0",
    "ticks_every": 0.1,
    "units": "%",
    "tick_labels": {
        "0.0": {"label": "0"},
        "0.1": {"label": "10"},
        "0.2": {"label": "20"},
        "0.3": {"label": "30"},
        "0.4": {"label": "40"},
        "0.5": {"label": "50"},
        "0.6": {"label": "60"},
        "0.7": {"label": "70"},
        "0.8": {"label": "80"},
        "0.9": {"label": "90"},
        "1.0": {"label": "100"},
    },
}

legend_idx_percentage_by_20 = {
    "begin": "0.0",
    "end": "1.0",
    "decimal_places": 1,
    "ticks_every": "0.2",
    "units": "%",
    "tick_labels": {
        "0.0": {"label": "0"},
        "0.2": {"label": "20"},
        "0.4": {"label": "40"},
        "0.6": {"label": "60"},
        "0.8": {"label": "80"},
        "1.0": {"label": "100"},
    },
}

legend_idx_percentage_by_25 = {
    "units": "%",
    "decimal_places": 2,
    "begin": "0.00",
    "end": "1.00",
    "ticks_every": 0.25,
    "tick_labels": {
        "0.00": {"label": "0"},
        "0.25": {"label": "25"},
        "0.50": {"label": "50"},
        "0.75": {"label": "75"},
        "1.00": {"label": "100"},
    },
}

legend_idx_twentyplus_3ticks = {
    "begin": 0,
    "end": 20,
    "decimal_places": 0,
    "ticks_every": 10,
    "tick_labels": {"20": {"prefix": ">"}},
}

legend_idx_thirtyplus_4ticks = {
    "begin": 0,
    "end": 30,
    "decimal_places": 0,
    "ticks_every": 10,
    "tick_labels": {"30": {"prefix": ">"}},
    "strip_location": [0.05, 0.5, 0.89, 0.15],
}

legend_idx_0_100_as_0_1_5ticks = {
    "begin": 0,
    "end": 100,
    "units": "unitless",
    "ticks_every": 20,
    "tick_labels": {
        "0": {"label": "0.0"},
        "20": {"label": "0.2"},
        "40": {"label": "0.4"},
        "60": {"label": "0.6"},
        "80": {"label": "0.8"},
        "100": {"label": "1.0"},
    },
}

legend_idx_0_100_pixel_fc_25ticks = {
    "begin": 0,
    "end": 100,
    "units": "% / pixel",
    "ticks_every": 25,
    "title": "Percentage of Pixel that is Green Vegetation",
    "rcParams": {"font.size": 9},
}

legend_idx_0_100_pixel_fc_ngv_25ticks = {
    "begin": 0,
    "end": 100,
    "units": "% / pixel",
    "ticks_every": 25,
    "title": "Percentage of Pixel that is Green Vegetation",
    "rcParams": {"font.size": 9},
}

legend_idx_0_100_pixel_fc_bs_25ticks = {
    "begin": 0,
    "end": 100,
    "ticks_every": 25,
    "units": "% / pixel",
    "title": "Percentage of Pixel that is Bare Soil",
    "rcParams": {"font.size": 9},
}

