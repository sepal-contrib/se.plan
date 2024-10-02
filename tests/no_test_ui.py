"""Named as no_test_ui.py to avoid running the test in the nox session.
It will tested in the CI/CD pipeline."""

from pathlib import Path
import nbformat
from nbconvert.preprocessors import ExecutePreprocessor
from jupyter_client.kernelspec import KernelSpecManager


def get_kernel_names():
    ksm = KernelSpecManager()
    return list(ksm.get_all_specs())


print(get_kernel_names())


# get the current path
root_folder = Path(__file__).parent.parent

test_notebooks = [
    # *(root_folder / "ui_tests").glob("test*.ipynb"),
    root_folder
    / "ui.ipynb",
]


for notebook in test_notebooks:
    with open(notebook) as ff:
        nb_in = nbformat.read(ff, nbformat.NO_CONVERT)

    print("Running notebook", notebook)

    try:
        ep = ExecutePreprocessor(timeout=600, kernel_name="test-se.plan")

        nb_out = ep.preprocess(nb_in)
    except Exception as e:
        print("########### Error running notebook", notebook)
        raise e
