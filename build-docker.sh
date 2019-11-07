#!/bin/sh
DOCKER_HUB_REPO=jenswbe/imap-alerter

echo "=== Enable Docker's experimental mode ==="
export DOCKER_CLI_EXPERIMENTAL=enabled

echo "=== Setup Buildx ==="
docker run --rm --privileged docker/binfmt:66f9012c56a8316f9244ffd7622d7c21c1f6f28d
docker buildx create --name multiarch
docker buildx use multiarch
docker buildx inspect --bootstrap

echo "=== Start build ==="
docker buildx build --platform linux/amd64,linux/arm64,linux/arm/v7 --push -t ${DOCKER_HUB_REPO} .
