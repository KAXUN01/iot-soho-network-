FROM python:3.10-slim

# System deps for cryptography, building wheels, and runtime tools
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       build-essential \
       libssl-dev \
       libffi-dev \
       iproute2 \
       curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy framework into /app/framework (avoid spaces in path)
COPY framework /app/framework

# Install Python deps
# Work around Ryu build hook incompatibility with modern setuptools
ENV SETUPTOOLS_USE_DISTUTILS=stdlib
RUN pip install --no-cache-dir --upgrade pip wheel \
    && pip install --no-cache-dir "setuptools<58" \
    && pip install --no-cache-dir \
         flask==2.3.3 \
         cryptography==41.0.4 \
         docker==6.1.3 \
         scapy==2.5.0 \
    && pip install --no-cache-dir ryu==4.34 \
    && pip install --no-cache-dir "setuptools==65.5.1"

# Create runtime dirs (mounted as volumes by compose)
RUN mkdir -p /app/framework/data /app/framework/logs /app/framework/honeypot_logs /app/framework/certificates

ENV PYTHONUNBUFFERED=1 \
    PYTHONIOENCODING=UTF-8 \
    PYTHONPATH=/app/framework

WORKDIR /app/framework

# Expose Flask and OpenFlow ports
EXPOSE 5000/tcp 6653/tcp

# Entrypoint launches Ryu controller and framework
COPY docker-entrypoint.sh /usr/local/bin/docker-entrypoint.sh
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

ENTRYPOINT ["/usr/local/bin/docker-entrypoint.sh"]

