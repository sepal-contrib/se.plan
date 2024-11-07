FROM continuumio/miniconda3

RUN mkdir /home/seplan
COPY . /home/seplan

# Create and copy credentials file
RUN mkdir /home/seplan/.config/earthengine
COPY /var/lib/sepal/app-launcher/service-account-credentials.json /home/.config/earthengine/credentials.json

WORKDIR /home/seplan

# Initialize Conda and create the environment
RUN conda init bash && \
    bash -c "source ~/.bashrc && \
    conda create -n seplan python==3.10 pip -y && \
    conda activate seplan && \
    pip install -r requirements.txt"

EXPOSE 8765

CMD ["bash", "-c", "source activate seplan && solara run solara.py --host=0.0.0.0 --production"]

# CMD ["tail", "-f", "/dev/null"]