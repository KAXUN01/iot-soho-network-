#!/bin/bash
set -e

CTRL_IP=${1:-127.0.0.1}
CTRL_PORT=${2:-6653}

echo "Starting Mininet against controller $CTRL_IP:$CTRL_PORT"
docker run --rm -it --privileged --network host \
  opennetworking/mininet:stable \
  bash -lc "mn --topo single,3 --mac --controller=remote,ip=$CTRL_IP,port=$CTRL_PORT --switch ovsk,protocols=OpenFlow13"

