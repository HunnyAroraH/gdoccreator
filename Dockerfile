# Use a lightweight official Python image
FROM python:3.9-slim

# Set the working directory
WORKDIR /app

# Install Chrome dependencies and supervisor
RUN apt-get update && apt-get install -y \
    wget \
    unzip \
    curl \
    gnupg \
    apt-transport-https \
    ca-certificates \
    libnss3 \
    libxss1 \
    libappindicator1 \
    fonts-liberation \
    libasound2 \
    xdg-utils \
    libgbm-dev \
    supervisor

# Add Google Chrome's official GPG key and stable repo
RUN wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | apt-key add - \
    && echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" > /etc/apt/sources.list.d/google-chrome.list

# Install stable version of Google Chrome
RUN apt-get update && apt-get install -y google-chrome-stable

# Log Chrome version and installation paths
RUN echo "Logging Chrome version and paths" \
    && google-chrome --version \
    && which google-chrome \
    && find / -name chrome 2>/dev/null

# Install ChromeDriver and make it executable
COPY chromedriver /usr/local/bin/chromedriver
RUN chmod +x /usr/local/bin/chromedriver

# Copy requirements and install Python dependencies
COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the supervisord config
COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf

# Copy the rest of the application code
COPY . .

# Expose ports for both apps
EXPOSE 8000 8001

# Start both Flask applications using Supervisor
CMD ["supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]
