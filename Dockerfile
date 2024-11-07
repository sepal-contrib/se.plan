# Taken from https://huggingface.co/spaces/giswqs/solara-template/blob/main/Dockerfile
FROM jupyter/base-notebook:latest

RUN mamba install -c conda-forge geopandas localtileserver -y && \
    fix-permissions "${CONDA_DIR}" && \
    fix-permissions "/home/${NB_USER}"

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . /home/${NB_USER}

ENV PROJ_LIB='/opt/conda/share/proj'

USER root
RUN chown -R ${NB_UID} ${HOME}
USER ${NB_USER}

EXPOSE 8765

CMD ["solara", "run", "solara.py", "--host=0.0.0.0", "--production"]