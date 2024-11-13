Install dev environment

.. code-block::
    
    conda create -n seplan python=3.10
    export PYTHONNOUSERSITE=1
    conda activate seplan
    pip install -r requirements.txt


Docker
======

To build the docker image, run the following command:

.. code-block::

    docker compose up --build

