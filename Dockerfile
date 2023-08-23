# Set base image (host OS)
FROM python:3.10

# By default, listen on port 5000
EXPOSE 5000/tcp

# Set the working directory in the container
WORKDIR /app

# Copy the dependencies file to the working directory
COPY requirements.txt .

# Install required packages
RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    && rm -rf /var/lib/apt/lists/*
# RUN apt-get update && apt-get install ffmpeg libsm6 libxext6  -y

# Install Python dependencies 
RUN pip install -r requirements.txt

# Install gevent-websocket
RUN pip install gevent-websocket

# Copy all contents from the local directory to the working directory in the Docker image
COPY . .

# Specify the command to run on container start
# CMD ["gunicorn", "-k", "eventlet", "-w", "1", "-b", "0.0.0.0:5000", "my_app:app"]
# CMD ["gunicorn", "-k", "gevent", "-w", "1", "-b", "0.0.0.0:5000", "my_app:app"]
CMD ["gunicorn", "-k", "geventwebsocket.gunicorn.workers.GeventWebSocketWorker", "-w", "1", "-b", "0.0.0.0:5000", "my_app:app"]

