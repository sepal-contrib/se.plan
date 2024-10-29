from component.model.aoi_model import SeplanAoi
from component.model.benefit_model import BenefitModel
from component.model.constraint_model import ConstraintModel
from component.model.cost_model import CostModel
from component.scripts.seplan import Seplan
import pytest
from pathlib import Path
from component.model.recipe import Recipe


@pytest.fixture()
def recipe():

    return Recipe()


def test_load_recipe(recipe: Recipe):

    # Get the path of the current file
    path = Path(__file__).parent / "data/recipes/test_recipe.json"

    # Load the recipe
    recipe.load(path)

    # Check the recipe values
    assert isinstance(recipe.seplan, Seplan)

    # Check the aoi model
    assert isinstance(recipe.seplan_aoi, SeplanAoi)

    assert recipe.seplan_aoi.aoi_model.admin == "959"
    assert not recipe.seplan_aoi.aoi_model.asset_name
    assert recipe.seplan_aoi.aoi_model.method == "ADMIN1"
    assert recipe.seplan_aoi.aoi_model.name == "COL_Risaralda"
    assert not recipe.seplan_aoi.aoi_model.asset_json
    assert not recipe.seplan_aoi.aoi_model.vector_json
    assert not recipe.seplan_aoi.aoi_model.point_json
    assert recipe.seplan_aoi.aoi_model.geo_json == {
        "type": "FeatureCollection",
        "features": [],
    }
    assert recipe.seplan_aoi.custom_layers == {
        "type": "FeatureCollection",
        "features": [
            {
                "id": "0",
                "type": "Feature",
                "properties": {
                    "ADM0_CODE": 57,
                    "ADM0_NAME": "Colombia",
                    "ADM1_CODE": 959,
                    "ADM1_NAME": "Risaralda",
                    "ADM2_CODE": 14191,
                    "ADM2_NAME": "Belen De Umbria",
                    "DISP_AREA": "NO",
                    "EXP2_YEAR": 3000,
                    "STATUS": "Member State",
                    "STR2_YEAR": 1000,
                    "Shape_Area": 0.0142980478307,
                    "Shape_Leng": 0.483782087526,
                    "ISO": "COL",
                    "id": 1,
                    "name": "Custom_COL_Risaralda_Belen_De_Umbria",
                    "style": {
                        "stroke": True,
                        "color": "#ff7f0e",
                        "weight": 1,
                        "opacity": 1,
                        "fill": True,
                        "fillColor": "#ff7f0e",
                        "fillOpacity": 0.05,
                    },
                    "hover_style": {
                        "stroke": True,
                        "color": "#ff7f0e",
                        "weight": 2,
                        "opacity": 1,
                        "fill": True,
                        "fillColor": "#ff7f0e",
                        "fillOpacity": 0.4,
                    },
                },
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [
                        [
                            [-75.88099525703937, 5.134400708103579],
                            [-75.8786988696803, 5.141900923470893],
                            [-75.87699995508858, 5.151198138367563],
                            [-75.86949973911334, 5.160401676549815],
                            [-75.8510970233442, 5.187499693496826],
                            [-75.84880059392, 5.19610128308356],
                            [-75.851698984368, 5.212898679221378],
                            [-75.85399545549073, 5.222699850866091],
                            [-75.85690278206363, 5.241798163851318],
                            [-75.86440295688308, 5.261997840498351],
                            [-75.86549994580224, 5.2664079043848275],
                            [-75.8719031773528, 5.265498300931676],
                            [-75.87760189455763, 5.265498281307336],
                            [-75.88970395852098, 5.264401329859792],
                            [-75.89550077530826, 5.262697946647666],
                            [-75.89779715493181, 5.26449942805161],
                            [-75.90699630066081, 5.260499611438583],
                            [-75.90930170894552, 5.258198756446402],
                            [-75.91400155853864, 5.2546983038247586],
                            [-75.92489516544357, 5.250100962908251],
                            [-75.93120027020416, 5.24899956229022],
                            [-75.93869604590597, 5.246698670378934],
                            [-75.97390064081574, 5.232398358690908],
                            [-75.9859982001465, 5.229000513521437],
                            [-75.98999801175997, 5.220398933852722],
                            [-75.99170140182231, 5.210597848482396],
                            [-75.99230337999602, 5.195601827745555],
                            [-75.9824978166806, 5.185100696807917],
                            [-75.96459896931827, 5.17000214528316],
                            [-75.95420038909751, 5.15550113111059],
                            [-75.94389981914627, 5.144500536230641],
                            [-75.93579767252535, 5.135198905347807],
                            [-75.93628816660984, 5.123556146698505],
                            [-75.93169972934437, 5.124800245375167],
                            [-75.92189859292775, 5.124800237669669],
                            [-75.91850081095015, 5.124800246402791],
                            [-75.91269501683483, 5.120697912819483],
                            [-75.9029028339459, 5.107998379082327],
                            [-75.88970395852098, 5.109099784728734],
                            [-75.88559704883002, 5.112502061400686],
                            [-75.8839026489505, 5.115997980571393],
                            [-75.88159726811026, 5.125799057850983],
                            [-75.88099525703937, 5.134400708103579],
                        ]
                    ],
                },
                "bbox": [
                    -75.99230337999602,
                    5.107998379082327,
                    -75.84880059392,
                    5.2664079043848275,
                ],
            },
            {
                "type": "Feature",
                "properties": {
                    "id": 2,
                    "name": "Custom AOI 2",
                    "style": {
                        "stroke": True,
                        "color": "#2ca02c",
                        "weight": 1,
                        "opacity": 1,
                        "fill": True,
                        "fillColor": "#2ca02c",
                        "fillOpacity": 0.05,
                    },
                    "hover_style": {
                        "stroke": True,
                        "color": "#2ca02c",
                        "weight": 2,
                        "opacity": 1,
                        "fill": True,
                        "fillColor": "#2ca02c",
                        "fillOpacity": 0.4,
                    },
                },
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [
                        [
                            [-76.236753, 5.111321],
                            [-76.236753, 5.254959],
                            [-76.103585, 5.254959],
                            [-76.103585, 5.111321],
                            [-76.236753, 5.111321],
                        ]
                    ],
                },
            },
        ],
    }

    # Check the benefit model

    assert isinstance(recipe.benefit_model, BenefitModel)

    assert recipe.benefit_model.ids == [
        "biodiversity_intactness",
        "endangered_species",
        "ground_carbon",
        "forest_job",
        "woodfuel_harvest",
        "plantation_growth_rates",
    ]

    assert recipe.benefit_model.themes == [
        "bii",
        "bii",
        "carbon_seq",
        "local",
        "local",
        "wood",
    ]

    assert recipe.benefit_model.weights == [0, 0, 2, 1, 1, 0]

    # Check the constraint model

    assert isinstance(recipe.constraint_model, ConstraintModel)

    assert recipe.constraint_model.ids == [
        "treecover_with_potential",
        "land_cover",
        "city_access",
    ]

    assert recipe.constraint_model.values == [[0], [20, 60, 70, 40], [249, 594]]

    # Check the cost model

    assert isinstance(recipe.cost_model, CostModel)
    assert recipe.cost_model.ids == ["opportunity_cost", "implementation_cost"]


def test_save_recipe(recipe, tmp_path: pytest.TempPathFactory):

    # Get the path of the current file
    path = Path(__file__).parent / "data/recipes/test_recipe.json"

    # Load the recipe
    recipe.load(path)

    # let's change some values in the models
    recipe.seplan_aoi.aoi_model.admin = "935"

    # we have to do this manually
    recipe.seplan_aoi.aoi_model.set_object()

    recipe.seplan.benefit_model.weights = [1, 1, 1, 1, 1, 1]

    # Save the recipe
    recipe.save(tmp_path / "test_recipe_modified.json")

    # Load the recipe
    recipe.load(tmp_path / "test_recipe_modified.json")

    # Check the recipe values
    assert isinstance(recipe.seplan, Seplan)

    # Check the changed values
    assert recipe.seplan.benefit_model.weights == [1, 1, 1, 1, 1, 1]

    # remove the file

    (tmp_path / "test_recipe_modified.json").unlink()


def test_reset_recipe(recipe):

    # Get the path of the current file
    path = Path(__file__).parent / "data/recipes/test_recipe.json"

    # Load the recipe
    recipe.load(path)

    # reset the recipe

    recipe.reset()

    # Check the recipe default values
    recipe.seplan_aoi.export_data() == {
        "primary": {
            "admin": None,
            "asset_name": None,
            "method": None,
            "name": None,
            "updated": 0,
            "asset_json": None,
            "vector_json": None,
        },
        "custom": {"type": "FeatureCollection", "features": []},
    }

    recipe.seplan_aoi.feature_collection == None
    recipe.seplan_aoi.aoi_model == None

    # Check the benefit model
    # I won't check everything to prove that the values were reset, but at least tehm
    recipe.benefit_model.weights == [4, 4, 4, 4, 4, 4]
    recipe.benefit_model.themes == [
        "bii",
        "bii",
        "carbon_seq",
        "local",
        "local",
        "wood",
    ]

    recipe.benefit_model.ids = [
        "biodiversity_intactness",
        "endangered_species",
        "ground_carbon",
        "forest_job",
        "woodfuel_harvest",
        "plantation_growth_rates",
    ]

    recipe.benefit_model.names == [
        "Biodiversity Intactness Index",
        "Endangered species",
        "Unrealized biomass potential",
        "Forest employment",
        "Woodfuel harvest",
        "Plantation growth rate",
    ]

    # check the constraint model
    recipe.constraint_model.ids == ["treecover_with_potential"]
    recipe.constraint_model.values == [[0, 1]]

    # check the cost model
    recipe.cost_model.ids == ["opportunity_cost", "implementation_cost"]
    recipe.cost_model.assets == [
        "projects/se-plan/assets/inputLayers/opportunity_cost_20221110",
        "projects/se-plan/assets/inputLayers/AfCost_ha",
    ]


def test_get_path(recipe):

    output_path = str(
        Path().home() / "module_results/se.plan/recipes/output_recipe.json"
    )
    recipe.get_recipe_path("output_recipe.json") == output_path
