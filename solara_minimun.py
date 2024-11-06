import solara.reactive
import solara
import ee
from solara.lab import headers
from eeclient.client import EESession
from eeclient.data import getInfo

ee.Initialize()


sepal_headers = solara.reactive({})


@solara.component
def Page():

    access_token = str(headers.value["access_token"][0])
    access_token_expiry_date = int(headers.value["access_token_expiry_date"][0])
    project_id = str(headers.value["project_id"][0])

    sepal_headers = {
        "id": 1,
        "username": "dguerrero",
        "googleTokens": {
            "accessToken": access_token,
            "accessTokenExpiryDate": access_token_expiry_date,
            "projectId": project_id,
            "refreshToken": "",
            "REFRESH_IF_EXPIRES_IN_MINUTES": 10,
            "legacyProject": "",
        },
        "status": "ACTIVE",
        "roles": ["USER"],
        "systemUser": False,
        "admin": False,
    }
    print(sepal_headers)

    user_session = EESession(sepal_headers, force_refresh=True)

    # I need to perform different operations:

    # Create a map using GEE

    # WE do this with the service account
    asset_id = "USGS/SRTMGL1_003"
    asset = ee.Image(asset_id)

    # Get asset info with users credentials

    asset_info = getInfo(user_session, ee.Number(1))

    print(asset_info)

    # Compute a value using GEE
    # Get user's assets
