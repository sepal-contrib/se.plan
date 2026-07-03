FROM mambaorg/micromamba:latest@sha256:dc6e3fc34e7d8179ee2f1af3218b59bc17b2625d0ef5d31190de28ced840007f

LABEL org.opencontainers.image.source="https://github.com/sepal-contrib/se.plan"

WORKDIR /usr/local/lib/seplan

USER root
# libjemalloc2: allocator for the runtime (see ENV block near the end).
RUN apt-get update && apt-get install -y \
    nano curl neovim supervisor netcat-openbsd net-tools git libjemalloc2 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* \
    && rm -rf /tmp/* \
    && rm -rf /var/tmp/*

COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf

# Copy the project and hand ownership to the mamba user so the editable install
# can write its build metadata into the project dir.
COPY . /usr/local/lib/seplan
RUN chown -R $MAMBA_USER:$MAMBA_USER /usr/local/lib/seplan

USER $MAMBA_USER

# pyproject.toml is the single source of truth for dependencies; the same
# `pip install -e .` is used by sepal_environment.yml for the SEPAL deploy.
RUN micromamba create -n seplan python=3.12 pip -c conda-forge -y && \
    micromamba run -n seplan pip install -e . --no-cache-dir && \
    micromamba clean --all --yes && \
    rm -rf ~/.cache/pip

# Run under jemalloc so freed per-session memory returns to the OS. glibc/pymalloc
# never release the arenas dented by per-session widget churn, so RSS ratchets to
# the peak working set and stays there (the production OOM); jemalloc purges free
# pages on a decay timer, so memory follows users back down.
# NOTE: if the .so is missing, LD_PRELOAD is silently ignored and PYTHONMALLOC=malloc
# is worse than stock — after any image change verify jemalloc is actually loaded:
#   grep -c jemalloc /proc/<solara-python-pid>/maps   # >= 1
# Placed after the build layers so image builds don't run under the preload.
ENV LD_PRELOAD=/usr/lib/x86_64-linux-gnu/libjemalloc.so.2 \
    PYTHONMALLOC=malloc \
    MALLOC_CONF=background_thread:true,dirty_decay_ms:1000,muzzy_decay_ms:1000

EXPOSE 8765

USER root
CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]
