# ruff: noqa: E402
import os
import sys
import ee

parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(parent_dir)
from component.scripts.seplan import get_weighted_average


ee.Initialize()


def test_get_weighted_benefits():
    images = [
        ee.Image(value)
        for value in [
            0.10720205307006836,
            0.03448275849223137,
            0.9781022071838379,
            0.9337244629859924,
            0.964881181716919,
            0.9337817430496216,
        ]
    ]

    themes = ["bii", "bii", "carbon_seq", "local", "local", "wood"]

    weights = [4, 4, 4, 4, 4, 4]

    weighted_val = get_weighted_average(themes, images, weights).getInfo()["bands"][0][
        "data_type"
    ]["min"]

    assert weighted_val == 0.7330072945915163
