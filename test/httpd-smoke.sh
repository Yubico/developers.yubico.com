#!/bin/sh
set -eu

image="yubico/developers/httpd-smoke"
container="developers-httpd-smoke-$$"
response=$(mktemp)

cleanup() {
  docker rm -f "$container" >/dev/null 2>&1 || true
  rm -f "$response"
}
trap cleanup EXIT INT TERM

docker build --no-cache -t "$image" -f Dockerfile.httpd .
docker run --rm -d \
  --name "$container" \
  -v "$PWD/htdocs/dist:/var/www/localhost/htdocs:ro" \
  -p 127.0.0.1::8080 \
  "$image" >/dev/null

port=$(docker port "$container" 8080/tcp | sed 's/.*://')
attempt=0
while [ "$attempt" -lt 20 ]; do
  if curl --fail --silent --show-error \
    --output "$response" \
    "http://127.0.0.1:${port}/Academy/passkey-app/"; then
    if grep -q '<!DOCTYPE html>' "$response"; then
      exit 0
    fi
  fi
  attempt=$((attempt + 1))
  sleep 0.25
done

docker logs "$container"
exit 1
