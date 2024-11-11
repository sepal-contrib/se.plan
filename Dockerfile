FROM continuumio/miniconda3

WORKDIR /usr/local/lib/seplan
COPY . /usr/local/lib/seplan

# Initialize Conda and create the environment
RUN conda init bash && \
    bash -c "source ~/.bashrc && \
    conda create -n seplan python==3.10 pip -y && \
    conda activate seplan && \
    pip install -r requirements.txt"


EXPOSE 8765

# CMD ["bash", "-c", "source activate seplan && solara run solara.py --host=0.0.0.0 --production"]

# Long running command
# Keep the container running
CMD ["tail", "-f", "/dev/null"]