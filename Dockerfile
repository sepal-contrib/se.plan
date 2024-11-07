FROM continuumio/miniconda3

RUN mkdir /home/seplan
COPY . /home/seplan

WORKDIR /home/seplan

# Initialize Conda and create the environment
RUN conda init bash && \
    bash -c "source ~/.bashrc && \
    conda create -n seplan python==3.10 pip -y && \
    conda activate seplan && \
    pip install -r requirements.txt"

EXPOSE 8765

# Adding debugging information to check environment variables, paths, and Conda activation status
CMD ["bash", "-c", "echo 'Starting in environment seplan...' && \
    source activate seplan && \
    echo 'Environment activated' && \
    which solara && \
    echo 'Python version:' && python --version && \
    echo 'Listing installed packages:' && pip list && \
    solara run solara.py --host=0.0.0.0 --production"]