#!/bin/bash

# Create and hook for schroot destroy.
SCHROOT_SESSION=$(schroot -b -c stable-amd64-trusty)
trap "schroot -c $SCHROOT_SESSION -e" EXIT

# Execute a script in schroot
schroot -u "spotify-buildagent" -r -c $SCHROOT_SESSION -- sh ci/linux.sh