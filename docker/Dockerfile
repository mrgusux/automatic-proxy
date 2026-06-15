# Lightweight Alpine-based image for the proxy collector.
FROM python:3.11-alpine

# Build deps for aiohttp/aiodns C extensions.
RUN apk add --no-cache --virtual .build gcc musl-dev libffi-dev \
    && apk add --no-cache libstdc++

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt \
    && apk del .build

COPY src ./src
COPY config ./config

# Runtime data dirs.
RUN mkdir -p data/raw data/cache data/geoip outputs

ENTRYPOINT ["python", "-m", "src.main"]
CMD ["run", "--log-level", "INFO"]
