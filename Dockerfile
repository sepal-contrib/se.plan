# Taken from https://huggingface.co/spaces/giswqs/solara-template/blob/main/Dockerfile
FROM continuumio/miniconda3

RUN conda create -n seplan python==3.10 pip -y
RUN conda activate seplan

RUN pip install -r requirements.txt

# Create a directory for the app
RUN mkdir /home/seplan
COPY . /home/seplan

EXPOSE 8765

CMD ["solara", "run", "solara.py", "--host=0.0.0.0", "--production"]