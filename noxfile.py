"""All the process that can be run using nox.

The nox run are build in isolated environment that will be stored in .nox. to force the venv update, remove the .nox/xxx folder.
"""

from pathlib import Path
import nbformat
from nbconvert.preprocessors import ExecutePreprocessor
from jupyter_client.kernelspec import KernelSpecManager
import nox


@nox.session(reuse_venv=True)
def lint(session):
    """Apply the pre-commits."""
    session.install("pre-commit")
    session.run("pre-commit", "run", "--a", *session.posargs)


@nox.session(reuse_venv=True)
def app(session):
    """Run the application."""

    entry_point = str(Path("ui.ipynb"))

    # Duplicate the entry point file
    session.run("cp", entry_point, "nox_ui.ipynb")

    # change the kernel name in the entry point
    session.run("entry_point", "--test", "nox_ui.ipynb")

    session.run("jupyter", "trust", entry_point)
    session.run(
        "voila", "--show_tracebacks=True", "--template=sepal-ui-base", "nox_ui.ipynb"
    )


@nox.session()
def test_ui(session):
    """Run the application."""

    ksm = KernelSpecManager()
    kernel_names = list(ksm.get_all_specs())
    print(kernel_names)

    # get the current path
    root_folder = Path(__file__).parent
    repo_name = root_folder.name

    # Copy the ui.ipynb to test_ui.ipynb
    session.run("cp", root_folder / "ui.ipynb", root_folder / "nox_ui.ipynb")

    session.run("entry_point", "--test", root_folder / "nox_ui.ipynb")

    test_notebooks = [root_folder / "nox_ui.ipynb"]

    for notebook in test_notebooks:
        with open(notebook) as ff:
            nb_in = nbformat.read(ff, nbformat.NO_CONVERT)

        print("Running notebook", notebook)

        try:
            ep = ExecutePreprocessor(timeout=600, kernel_name=f"test-{repo_name}")

            nb_out = ep.preprocess(nb_in)
        except Exception as e:
            print("########### Error running notebook", notebook)
            raise e


@nox.session(reuse_venv=True)
def jupyter(session):
    """Run the application."""
    session.install("-r", "requirements.txt")
    session.run("jupyter", "trust", "no_ui.ipynb")
    session.run("jupyter", "notebook", "no_ui.ipynb")
