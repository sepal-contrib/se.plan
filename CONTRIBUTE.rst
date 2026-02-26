Install dev environment

.. code-block::
    
    conda create -n seplan python=3.10
    export PYTHONNOUSERSITE=1
    conda activate seplan
    pip install -r requirements.txt


To run the container
====================

Inside sepal, the container will be automatically ran by the `all-launcher` module, that module has two main
services: monitor and build the apps. 


Running on local environment
----------------------------
If you want to run this container locally, you're gonna need a valid GEE credentials, they will be mounted
to the container from the path in the host machine: "${EE_CREDENTIALS_PATH:-${HOME}/.config/earthengine/credentials}

.. code-block::
    docker compose up --build


Running with local sepal
------------------------
If you want to run this container locally but using a local sepal instance, follow the instructions below.


To build the docker image, run the following command:

.. code-block::

    docker compose up --build

To run the server (on a test environment), you need to define the environment variables that you can define in the `.env` file, or you can set them in your terminal before running the container.

.. code-block::
    
    export LOCAL_SEPAL_USER=localusername
    export LOCAL_SEPAL_PASSWORD="localusername"
    export SEPAL_HOST="sepalhost.io"
    export SOLARA_TEST=true

The main process of the container is a supervisor that runs the following processes:

    - solara
    - solara-test
    

Inside the container:

.. code-block::

    docker exec -it seplan bash
    cd /usr/local/lib/seplan

    # stop the main solara process (that one changes the root-path to /api/app-launcher/seplan)

    supervisorctl stop solara

    # start the solara-test process (this one removes the root-path and runs it on the localhost)

    supervisorctl start solara-test

    