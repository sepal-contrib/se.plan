FROM continuumio/miniconda3

WORKDIR /usr/local/lib/seplan

# Install nano and curl
RUN apt-get update && apt-get install -y nano curl neovim supervisor netcat-openbsd net-tools

COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf


RUN conda init bash && \
    bash -c "source ~/.bashrc && \
    conda create -n seplan python==3.10 pip -y --no-cache"

COPY requirements.txt /usr/local/lib/seplan/requirements.txt

RUN bash -c "source ~/.bashrc && conda activate seplan && pip install -r requirements.txt --no-cache-dir"

COPY . /usr/local/lib/seplan

EXPOSE 8765

CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]