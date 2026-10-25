#!/usr/bin/with-contenv bashio
# shellcheck shell=bash
set -e

# Model files (~660 MB for int8) are cached in /data, so they download once.
export HF_HOME=/data

ARGS=(
  --uri "tcp://0.0.0.0:10300"
  --quantization "$(bashio::config 'quantization')"
  --pad-seconds "$(bashio::config 'pad_seconds')"
)
if bashio::config.true 'debug_logging'; then
  ARGS+=(--debug)
fi

/opt/venv/bin/python3 -m wyoming_pianissimo "${ARGS[@]}" &
SERVER_PID=$!

# Announce the service to Home Assistant once the port is open,
# so it appears under Settings > Devices & services.
until bash -c "echo > /dev/tcp/127.0.0.1/10300" 2>/dev/null; do
  if ! kill -0 "${SERVER_PID}" 2>/dev/null; then
    bashio::exit.nok "Pianissimo server exited during startup"
  fi
  sleep 2
done

bashio::discovery "wyoming" \
  "$(bashio::var.json uri "tcp://$(hostname):10300")" >/dev/null \
  && bashio::log.info "Announced to Home Assistant" \
  || bashio::log.warning "Discovery failed; add the Wyoming integration manually (host: $(hostname), port: 10300)"

wait "${SERVER_PID}"
