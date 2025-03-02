#!/bin/bash

# Update system packages
sudo apt update && sudo apt upgrade -y

# Install required dependencies
sudo apt install -y build-essential zlib1g-dev libssl-dev libreadline-dev libsqlite3-dev libbz2-dev libffi-dev

# Download and extract Python 3.8.20
wget https://www.python.org/ftp/python/3.8.20/Python-3.8.20.tgz
tar -xvf Python-3.8.20.tgz
cd Python-3.8.20

# Configure and compile Python
./configure --enable-optimizations
make -j$(nproc)
sudo make altinstall

# Verify Python installation
python3.8 --version

# Return to the original directory
cd ..
echo "Python 3.8.20 installation completed!"
