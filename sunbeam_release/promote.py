# Copyright 2021 Canonical Ltd.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Release helpers for promotion of charms between channels."""

import json
import subprocess
from typing import (
    Union,
)

import click

OPENSTACK_CHARMS = [
    "keystone-k8s",
    "glance-k8s",
    "nova-k8s",
    "placement-k8s",
    "neutron-k8s",
    "heat-k8s",
    "horizon-k8s",
    "cinder-k8s",
    "cinder-ceph-k8s",
    "openstack-hypervisor",
]

OVN_CHARMS = [
    "ovn-relay-k8s",
    "ovn-central-k8s",
]

WORKFLOWS = {
    "edge": "beta",
    "beta": "candidate",
    "candidate": "stable",
}

TRACKS = {
    "antelope": {"openstack": "2023.1", "ovn": "23.03", "rabbitmq": "3.9"}
}


def charm_metadata(app: str) -> dict:
    """Retrieve metadata about a specific charm."""
    cmd = ["charmcraft", "status", app, "--format", "json"]
    process = subprocess.run(cmd, capture_output=True, text=True, check=True)
    return json.loads(process.stdout.strip())


def release_command(
    app: str,
    track: str,
    source_channel: str,
    target_channel: str,
    base_channel: str = "22.04",
    base_arch: str = "amd64",
) -> Union[str, None]:
    """Generate a charmcraft release command to promote between tracks."""
    release_cmd = None
    charm_info = charm_metadata(app)
    print(
        f"Checking {app}: {track}/{source_channel}->{track}/{target_channel}"
    )
    for s in charm_info:
        if s["track"] == track:
            for mapping in s["mappings"]:
                if (
                    mapping["base"]["channel"] == base_channel
                    and mapping["base"]["architecture"] == base_arch
                ):
                    source_release = None
                    target_release = None
                    for release in mapping["releases"]:
                        if release["channel"] == f"{track}/{source_channel}":
                            source_release = release
                        if release["channel"] == f"{track}/{target_channel}":
                            target_release = release

                    if source_release and target_release:
                        if source_release["status"] == "tracking":
                            # Source channel is tracking the channel
                            # above, skip
                            print(
                                "Source track follows target track, skipping"
                            )
                            continue
                        if (
                            source_release["revision"]
                            == target_release["revision"]
                        ):
                            # Source == Target - so skip
                            print("Source and target revision match, skipping")
                            continue
                        release_cmd = [
                            "charmcraft",
                            "release",
                            app,
                            "--channel",
                            f"{track}/{target_channel}",
                            "--revision",
                            str(source_release["revision"]),
                        ]
                        for resource in source_release["resources"]:
                            release_cmd.append("--resource")
                            release_cmd.append(
                                f"{resource['name']}:{resource['revision']}"
                            )
                        break

    return release_cmd


@click.command()
@click.option(
    "--source",
    default="candidate",
    help="Source channel for promotion",
    type=click.Choice(WORKFLOWS.keys()),
    show_default=True,
)
@click.option(
    "--release",
    default="antelope",
    help="Sunbeam release for tracks",
    type=click.Choice(TRACKS.keys()),
    show_default=True,
)
@click.option("--dry-run", "-d", default=False, is_flag=True)
def promote(source: str, release: str, dry_run: bool) -> None:
    """Promote charms between channels."""
    if source not in WORKFLOWS.keys():
        raise click.BadOptionUsage(
            option_name="source",
            message=(
                f"source {source} not supported - must"
                f" be one of {','.join(WORKFLOWS.keys())}"
            ),
        )

    release_cmds = []

    for charm in OPENSTACK_CHARMS:
        cmd = release_command(
            charm,
            track=TRACKS[release]["openstack"],
            source_channel=source,
            target_channel=WORKFLOWS[source],
        )
        if cmd:
            release_cmds.append(cmd)

    for charm in OVN_CHARMS:
        cmd = release_command(
            charm,
            track=TRACKS[release]["ovn"],
            source_channel=source,
            target_channel=WORKFLOWS[source],
        )
        if cmd:
            release_cmds.append(cmd)

    for charm in ["rabbitmq-k8s"]:
        cmd = release_command(
            charm,
            track=TRACKS[release]["rabbitmq"],
            source_channel=source,
            target_channel=WORKFLOWS[source],
        )
        if cmd:
            release_cmds.append(cmd)

    for cmd in release_cmds:
        pcmd = " ".join(cmd)
        print(f"Running cmd: {pcmd}")
        if not dry_run:
            process = subprocess.run(
                cmd, capture_output=True, text=True, check=True
            )
            print(process.stdout)
