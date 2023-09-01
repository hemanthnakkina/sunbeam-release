# Sunbeam Release Tools

## Overview

Repository for useful helpers for managing the promotion of charms and snaps
between channels and tracks on the Charmhub/Snapstore.

## Dependencies

The sunbeam-release tool makes use of charmcraft which can be installed as a
snap:

    sudo snap install --classic charmcraft

charmcraft must also be logged into the charmhub in order for sunbeam-release
operators to work:

    charmcraft login

## Promotion of charms between channels

sunbeam-release can be used to compare and promote charms between channels
within a specific track on the charmhub:

    sunbeam-release promote --source edge --release antelope --dry-run

This command will compare the edge channel of all charms across the Sunbeam
charm set against the charm in the beta channel - any differences will be
detected and the relevant charmcraft commands will be printed to promote
the edge channel to beta channel.  The tracks to use for each charm are
determined by the release argument.

Dropping the '--dry-run' argument will also execute the charmcraft commands.
