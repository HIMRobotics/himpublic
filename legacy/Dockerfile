# ----------------------------
# Dockerfile
# ----------------------------

# Requirement: Ubuntu 22.04 (Jammy Jellyfish)
FROM ubuntu:22.04

ARG DEBIAN_FRONTEND=noninteractive

# Base system + build tools + Python (pip & venv)
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        ca-certificates \
        curl \
        git \
        build-essential \
        gcc-11 g++-11 \
        make \
        cmake \
        python3 \
        python3-pip \
        python3-dev && \
    rm -rf /var/lib/apt/lists/*

# Make gcc-11 the default compiler
RUN update-alternatives --install /usr/bin/gcc gcc /usr/bin/gcc-11 100 && \
    update-alternatives --install /usr/bin/g++ g++ /usr/bin/g++-11 100

RUN apt-get update && \
    apt-get install -y --no-install-recommends zsh && \
    rm -rf /var/lib/apt/lists/*

RUN sh -c "$(curl -fsSL https://raw.githubusercontent.com/ohmyzsh/ohmyzsh/master/tools/install.sh)" "" --unattended \
    && sed -i 's/ZSH_THEME=".*"/ZSH_THEME="agnoster"/' ~/.zshrc

# Verify compiler and Python tooling
RUN gcc --version && python3 --version && pip --version

# Set working directory
WORKDIR /workspace

# Default command
CMD ["/bin/bash"]