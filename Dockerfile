# Use the official Ubuntu 22.04 image
FROM ubuntu:22.04

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV DEBIAN_FRONTEND=noninteractive
ENV TZ=Etc/UTC

# Set the timezone (required for Ubuntu 22.04)
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# Install system dependencies and Python 3.10
RUN apt-get update && \
    apt-get install -y \
        software-properties-common \
        build-essential \
        portaudio19-dev \
        ffmpeg \
        alsa-utils \
        pulseaudio \
        libasound2-dev \
        libportaudio2 \
        libportaudiocpp0 \
        curl \
        libsqlite3-dev \
        sqlite3 \
        python3.10 \
        python3.10-distutils \
        python3.10-dev \
    && rm -rf /var/lib/apt/lists/*

# Install pip for Python 3.10
RUN curl -sS https://bootstrap.pypa.io/get-pip.py | python3.10

# Set the default Python version to Python 3.10
RUN update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.10 1

# Install required Python packages
RUN python3 -m pip install --upgrade pip

# Set the working directory
WORKDIR /app

# Copy requirements.txt and install dependencies
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY . /app/

# Set the default command to run when starting the container
# Totally Optional --> Use this once the app has been built. --> combined_script.py is a place holder.
#CMD ["python3", "combined_script.py"]
