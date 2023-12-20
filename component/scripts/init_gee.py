import json
from pathlib import Path

import ee


def authenticate_gee():
    """Authenticate GEE using the credentials file in the user's home directory."""
    credential_folder_path = Path.home() / ".config" / "earthengine"
    credential_file_path = credential_folder_path / "credentials"
    credentials = json.loads(credential_file_path.read_text())
    project = credentials.get("project_id", credentials.get("project", None))
    ee.Initialize(project=project)
