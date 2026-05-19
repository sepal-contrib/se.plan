FROM mambaorg/micromamba:latest@sha256:dc6e3fc34e7d8179ee2f1af3218b59bc17b2625d0ef5d31190de28ced840007f

LABEL org.opencontainers.image.source="https://github.com/sepal-contrib/se.plan"

WORKDIR /usr/local/lib/seplan

USER root
RUN apt-get update && apt-get install -y \
    nano curl neovim supervisor netcat-openbsd net-tools git \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* \
    && rm -rf /tmp/* \
    && rm -rf /var/tmp/*

COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf

USER $MAMBA_USER

COPY requirements.lock /home/$MAMBA_USER/requirements.lock
RUN micromamba create -n seplan python=3.12 pip -c conda-forge -y && \
    micromamba run -n seplan pip install --require-hashes -r /home/$MAMBA_USER/requirements.lock --no-cache-dir && \
    micromamba clean --all --yes && \
    rm -f /home/$MAMBA_USER/requirements.lock && \
    rm -rf ~/.cache/pip

COPY . /usr/local/lib/seplan

EXPOSE 8765

USER root
CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]