from typing import List, Dict, Literal, TypedDict


class StatsDict(TypedDict):
    total: List[float]
    values: List[float]


class SuitabilityLevel(TypedDict):
    "The suitability level for a given area."
    image: Literal[1, 2, 3, 4, 5, 6]
    sum: float


class SuitabilityDict(TypedDict):
    "The data of the suitability theme for a given area."
    total: float
    values: List[SuitabilityLevel]


class AreaStats(TypedDict):
    "The data structure for the summary statistics of a given area."
    benefit: List[Dict[str, StatsDict]]
    constraint: List[Dict[str, StatsDict]]
    cost: List[Dict[str, StatsDict]]
    suitability: SuitabilityDict
    color: str


SummaryStatsDict = Dict[str, AreaStats]
"The result of running get_summary_statistics" ""


# Parsed layer stats
class ParsedLayer(TypedDict):
    "A dictionary of the statistics for a given layer."
    values: List[float]
    color: str
    total: List[float]


ParsedLayerStats = Dict[str, ParsedLayer]
"The result of parsing a SummaryStatsDict for a given layer."
