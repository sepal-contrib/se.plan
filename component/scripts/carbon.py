import numpy as np
from typing import Any, Tuple


def chapman_richards(age: float, b0: float, b1: float, b2: float):
    return (b0 * (1 - np.exp(-b1 * age))) ** b2


def growth_function_by_hectares(
    growth_func, x: float, parameters: Tuple[float], hectares: float
):
    return growth_func(x, *parameters) * hectares


def get_growth_params(params, key):
    return params[key]


def get_growth_hectares(values, hectares, age):
    res = growth_function_by_hectares(
        chapman_richards, age, values["parameters"], hectares
    )
    return res

