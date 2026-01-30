#!/bin/sh
set -eu

echo "Installing SSH client..."
apk add --no-cache openssh-client

mkdir -p /root/.ssh
chmod 700 /root/.ssh

# Avoid interactive host prompt in containers
printf "Host *\n  StrictHostKeyChecking no\n  UserKnownHostsFile=/dev/null\n" > /root/.ssh/config

# Fix Windows->Linux mount permissions problem:
# copy the key into the container filesystem and lock it down
cp /keys/deploy_key /root/.ssh/deploy_key
chmod 600 /root/.ssh/deploy_key

echo "Fetching dump from server..."
scp -o BatchMode=yes -i /root/.ssh/deploy_key \
  "${DEPLOY_USER}@${DEPLOY_HOST}:${REMOTE_DUMP_PATH}" \
  "/dumps/latest.dump"

echo "Dump saved to /dumps/latest.dump"
