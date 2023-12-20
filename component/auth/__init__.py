"""Authenticate GEE using the credentials file in the user's home directory."""

import json
from pathlib import Path
import ee

_credential_folder_path = Path.home() / ".config" / "earthengine"
_credential_file_path = _credential_folder_path / "credentials"
_credentials = json.loads(_credential_file_path.read_text())
project = _credentials.get("project_id", _credentials.get("project", None))
gee_folder = f"projects/{project}/assets/"
ee.Initialize(project=project)
if not ee.data.getAssetRoots():
    raise Exception(
        f"Error: You have not initialized the GEE home folder on your project: '{project}'. Please follow the the SEPAL documentation: href=https://docs.sepal.io/en/latest/setup/gee.html#initialize-the-home-folder, and try it again"
    )
