# Use the official Nginx base image
FROM nginx:1.25.3

ENV PORT_IP_MAP ""
ENV PYTHONUNBUFFERED=1

# Install Python and pip
RUN apt-get update && apt-get install -y python3 python3-pip python3-venv 

# Install Docker
RUN apt-get update && apt-get install -y \
  apt-transport-https \
  ca-certificates \
  curl \
  gnupg \
  lsb-release && \
  curl -fsSL https://download.docker.com/linux/debian/gpg | apt-key add - && \
  echo "deb [arch=amd64] https://download.docker.com/linux/debian $(lsb_release -cs) stable" > /etc/apt/sources.list.d/docker.list && \
  apt-get update && \
  apt-get install -y docker-ce docker-ce-cli containerd.io

# Create a virtual environment and activate it
RUN python3 -m venv /app/venv
ENV PATH="/app/venv/bin:$PATH"

# Copy the Python app files to the container
COPY app/* /app/

# Set the working directory
WORKDIR /app

# Install the Python dependencies
RUN pip install --upgrade pip 
RUN pip install -r requirements.txt

# Expose port 80 for Nginx
EXPOSE 80

# Start Nginx and run the Python app
CMD docker compose up -d --remove-orphans && service nginx start && exec python app.py