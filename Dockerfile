FROM continuumio/miniconda3

WORKDIR /usr/local/lib/seplan

ARG GIT_COMMIT
ENV GIT_COMMIT=${GIT_COMMIT}

COPY requirements.txt /usr/local/lib/seplan/requirements.txt

RUN conda init bash && \
    bash -c "source ~/.bashrc && \
    conda create -n seplan python==3.10 pip -y"

RUN bash -c "source ~/.bashrc && conda activate seplan && pip install -r requirements.txt"

RUN echo "Building commit ${GIT_COMMIT}"

COPY . /usr/local/lib/seplan

EXPOSE 8765

# CMD ["bash", "-c", "source activate seplan && solara run solara.py --host=0.0.0.0 --production"]
CMD ["bash", "-c", "source activate seplan && solara run solara_minimum.py --host=0.0.0.0"]



# Long running command
# Keep the container running
# CMD ["tail", "-f", "/dev/null"]