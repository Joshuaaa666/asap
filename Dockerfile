FROM nvidia/cuda:12.1.1-cudnn8-devel-ubuntu22.04

ENV DEBIAN_FRONTEND=noninteractive
ENV CONDA_DIR=/opt/conda
ENV PATH=${CONDA_DIR}/bin:${PATH}

RUN apt-get update && apt-get install -y --no-install-recommends \
    wget \
    curl \
    git \
    ca-certificates \
    build-essential \
    libgl1 \
    libglib2.0-0 \
    libx11-6 \
    libxext6 \
    libxrender1 \
    libxrandr2 \
    libxinerama1 \
    libxcursor1 \
    libxi6 \
    libegl1 \
    mesa-vulkan-drivers \
    vulkan-tools \
    && rm -rf /var/lib/apt/lists/*

RUN wget -q https://mirrors.tuna.tsinghua.edu.cn/anaconda/miniconda/Miniconda3-latest-Linux-x86_64.sh -O /tmp/miniconda.sh \
    && bash /tmp/miniconda.sh -b -p ${CONDA_DIR} \
    && rm -f /tmp/miniconda.sh \
    && conda config --set auto_activate_base false

SHELL ["/bin/bash", "-lc"]


RUN conda tos accept --override-channels --channel https://repo.anaconda.com/pkgs/main && \
    conda tos accept --override-channels --channel https://repo.anaconda.com/pkgs/r

RUN conda create -y -n hvgym python=3.8 \
    && conda clean -afy

RUN conda run -n hvgym python -m pip install --upgrade pip setuptools wheel

WORKDIR /workspace/ASAP-main
COPY . .

# Install Isaac Gym Python API first.
RUN conda run -n hvgym python -m pip install -e isaacgym/python

# Install ASAP project dependencies.
RUN conda run -n hvgym python -m pip install -e . -e isaac_utils

RUN mkdir -p ${CONDA_DIR}/envs/hvgym/etc/conda/activate.d \
    && cat > ${CONDA_DIR}/envs/hvgym/etc/conda/activate.d/asap_isaacgym.sh << 'EOF'
export LD_LIBRARY_PATH="${CONDA_DIR}/envs/hvgym/lib:${LD_LIBRARY_PATH}"
EOF
RUN conda run -n hvgym python -m pip install "git+https://ghfast.top/github.com/ZhengyiLuo/SMPLSim.git@master"


ENV NVIDIA_DRIVER_CAPABILITIES=compute,utility,graphics

CMD ["bash", "-lc", "source /opt/conda/etc/profile.d/conda.sh && conda activate hvgym && bash"]
