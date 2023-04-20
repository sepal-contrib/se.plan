"""
All the process that can be run using nox.
The nox run are build in isolated environment that will be stored in .nox. to force the venv update, remove the .nox/xxx folder.
"""

import nox


@nox.session(reuse_venv=True)
def lint(session):
    """Apply the pre-commits."""
    session.install("pre-commit")
    session.run("pre-commit", "run", "--a", *session.posargs)


from pathlib import Path


@nox.session(reuse_venv=True)
def app(session):
    """Run the application"""
    session.install("numpy")
    session.install("gdal==3.4.3")
    session.install("-r", "requirements.txt")
    session.run("jupyter", "trust", "ui.ipynb")
    session.run("voila", "--show_tracebacks=True", "ui.ipynb")


@nox.session(reuse_venv=True)
def jupyter(session):
    """Run the application"""
    session.install("-r", "requirements.txt")
    session.run("jupyter", "trust", "notebook_ui.ipynb")
    session.run("jupyter", "notebook", "no_ui.ipynb")
