FROM python:3.11-slim

# ========== INSTALL SYSTEM DEPENDENCIES ==========
RUN apt-get update && apt-get install -y \
    # Audio/Video processing
    ffmpeg \
    libsndfile1 \
    # Process manager
    supervisor \
    # Node.js для N8N
    curl \
    gnupg \
    && curl -fsSL https://deb.nodesource.com/setup_18.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/*

# ========== INSTALL N8N ==========
RUN npm install -g n8n

# ========== WORKDIR ==========
WORKDIR /app

# ========== PYTHON DEPENDENCIES ==========
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ========== COPY APPLICATION ==========
COPY agent.py .
COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf

# ========== CREATE N8N DIRECTORIES ==========
RUN mkdir -p /app/n8n_data /app/n8n_workflows

# ========== ENVIRONMENT VARIABLES ==========
ENV PYTHONUNBUFFERED=1
ENV N8N_USER_FOLDER=/app/n8n_data
ENV N8N_PORT=5678
ENV N8N_HOST=0.0.0.0
ENV N8N_BASIC_AUTH_ACTIVE=false
ENV N8N_PROTOCOL=http
ENV WEBHOOK_URL=http://localhost:5678/
ENV N8N_WEBHOOK_URL=http://localhost:5678/webhook/get-news

# ========== EXPOSE PORTS ==========
EXPOSE 7860

# ========== START SUPERVISOR ==========
CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]
