FROM continuumio/miniconda3

WORKDIR /usr/local/lib/seplan

RUN conda init bash && \
    bash -c "source ~/.bashrc && \
    conda create -n seplan python==3.10 pip -y"

COPY requirements.txt /usr/local/lib/seplan/requirements.txt

RUN bash -c "source ~/.bashrc && conda activate seplan && pip install -r requirements.txt"

COPY . /usr/local/lib/seplan

EXPOSE 8765

# CMD ["bash", "-c", "source activate seplan && solara run solara.py --host=0.0.0.0 --production"]
CMD ["bash", "-c", "source activate seplan && solara run solara.py --host=0.0.0.0 --root-path=/api/app-launcher/seplan" ]