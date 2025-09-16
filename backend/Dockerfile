FROM python:3.11.5

ARG SLURM_VERSION=24.05.1
ARG USER=1005
ARG GITHUB_PAT
ENV GITHUB_PAT=$GITHUB_PAT
RUN groupadd -g $USER slurm \
    && useradd -m -c "MUNGE Uid 'N' Gid Emporium" -d /var/lib/slurm -u $USER -g slurm -s /sbin/nologin slurm

# Install system dependencies
RUN apt-get update && apt-get install -y \
    wget gcc make \
    munge libmunge-dev libmunge2 libssl-dev libpam0g-dev \
    build-essential gfortran \
    liblapack-dev liblapack3 libopenblas-dev \
    r-base libpcre2-dev libhdf5-dev liblzma-dev libbz2-dev \
    libicu-dev libblas-dev libcurl4-gnutls-dev libxml2-dev \
    nano \
    libharfbuzz-dev libfribidi-dev libfreetype6-dev libpng-dev libglib2.0-dev pkg-config \
    && rm -rf /var/lib/apt/lists/*

# Compile and install SLURM
RUN wget https://download.schedmd.com/slurm/slurm-${SLURM_VERSION}.tar.bz2 \
    && tar -xjf slurm-${SLURM_VERSION}.tar.bz2 \
    && cd slurm-${SLURM_VERSION} \
    && ./configure \
    && make \
    && make install

# Install R packages
RUN R -e "install.packages('BiocManager', repos='http://cran.rstudio.com/')" \
    && R -e "install.packages('remotes', repos='http://cran.rstudio.com/')" \
    && R -e "remotes::install_version('Matrix', version='1.6.4', repos='https://cloud.r-project.org/')" \
    && R -e "BiocManager::install('Seurat')" \
    && R -e "remotes::install_github('mojaveazure/seurat-disk')" \
    && R -e "install.packages('clustree', repos='http://cran.rstudio.com/')" \
    && R -e "install.packages('svglite', repos='http://cran.rstudio.com/')" \
    && R -e "install.packages('anndata', repos='http://cran.rstudio.com/')" \
    && R -e "remotes::install_github('rstudio/reticulate')"
    # && R -e "BiocManager::install('zellkonverter')"

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

RUN chown -R slurm:slurm /usr/local/lib/python3.11/site-packages/

COPY . .
RUN chown -R slurm:slurm /app

COPY slurm.conf /etc/slurm/
COPY slurm.conf /usr/local/etc/slurm.conf

RUN mkdir -p /app/uploads && chown -R slurm:slurm /app/uploads

EXPOSE 8000
USER slurm

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "8"]
