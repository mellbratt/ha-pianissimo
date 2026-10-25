ARG BUILD_FROM
FROM ${BUILD_FROM}

# Debian base: onnxruntime ships manylinux wheels for aarch64 and amd64,
# which do not install on the Alpine (musl) base images.
RUN apt-get update \
    && apt-get install -y --no-install-recommends python3 python3-venv \
    && rm -rf /var/lib/apt/lists/*

RUN python3 -m venv /opt/venv \
    && /opt/venv/bin/pip install --no-cache-dir \
        "onnx-asr[cpu,hub]==0.12.0" \
        "wyoming==1.10.2" \
        numpy

COPY wyoming_pianissimo /app/wyoming_pianissimo
COPY run.sh /run.sh
RUN chmod a+x /run.sh

WORKDIR /app
CMD ["/run.sh"]
