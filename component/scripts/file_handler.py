from pathlib import Path
from typing import Optional
import json


def read_file(file_path: str, sepal_session) -> Optional[Path]:
    if sepal_session:
        # Read the file from the sepal session
        data = sepal_session.get_file(file_path, parse_json=True)
    else:
        # Read the file from the local system
        with Path(file_path).open() as f:
            data = json.loads(f.read())

    return data


def save_file(file_path: str, json_data, sepal_session=None) -> Optional[Path]:
    """Save JSON data to a local file or to the sepal session, if provided."""
    # Convert the data to a nicely formatted JSON string
    json_data = json.dumps(json_data, indent=4)

    if sepal_session:
        # Save the file to the sepal session
        return sepal_session.set_file(file_path, json_data)
    else:
        # Save the file to the local system
        with Path(file_path).open("w") as f:
            f.write(json_data)

        return Path(file_path)
