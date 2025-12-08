import re
import subprocess
from typing import List

from langchain_core.tools import tool
from network.infrastructure import get_all_stp_info

from .models import ActiveLink, TCOperationResult, TCSettings


@tool
def get_tc_settings(interface: str) -> TCSettings:
    """Get traffic control (TC) settings for a specific network interface.

    This tool queries the Linux traffic control (TC) configuration for a given interface
    to determine if bandwidth limiting, delay, or loss settings are applied. It checks for
    TBF (Token Bucket Filter), netem, and HTB (Hierarchical Token Bucket) qdiscs.

    Use this tool when you need to check if a specific interface has TC settings before
    modifying them, or to verify the current state of an interface.

    Args:
        interface: The network interface name to check (e.g., 'veth-sw1-sw2', 'veth-sw3-sw1').
                  Can be a bridge (br-sw1) or veth pair interface.

    Returns:
        Dictionary containing:
        - interface: The interface name
        - has_tc: Boolean indicating if TC is configured
        - qdiscs: List of qdisc configuration lines
        - bandwidth_limit: Bandwidth limit if TBF is configured (e.g., '1Mbit')
        - burst: Burst size if configured (e.g., '32Kb')
        - has_netem: Boolean indicating if netem (delay/loss) is configured

    Example:
        get_tc_settings('veth-sw1-sw2') might return:
        {
            'interface': 'veth-sw1-sw2',
            'has_tc': True,
            'bandwidth_limit': '1Mbit',
            'burst': '32Kb',
            'qdiscs': ['qdisc tbf 0: root refcnt 2 rate 1Mbit burst 32Kb ...']
        }
    """
    result = subprocess.run(
        ["tc", "qdisc", "show", "dev", interface],
        capture_output=True,
        text=True,
        timeout=5,
    )

    tc_info = {
        "interface": interface,
        "has_tc": False,
        "qdiscs": [],
        "bandwidth_limit": None,
        "burst": None,
    }

    if result.returncode == 0 and result.stdout.strip():
        lines = result.stdout.strip().split("\n")

        for line in lines:
            if re.search(r"\b(noqueue|pfifo_fast|mq|fq_codel)\b", line):
                continue

            if "tbf" in line:
                tc_info["has_tc"] = True
                tc_info["qdiscs"].append(line)
                rate_match = re.search(r"rate\s+(\d+)(\w+)", line)
                if rate_match:
                    tc_info["bandwidth_limit"] = (
                        f"{rate_match.group(1)}{rate_match.group(2)}"
                    )
                burst_match = re.search(r"burst\s+(\d+)(\w*)", line)
                if burst_match:
                    tc_info["burst"] = (
                        f"{burst_match.group(1)}{burst_match.group(2) or 'b'}"
                    )

            elif "netem" in line:
                tc_info["has_tc"] = True
                tc_info["qdiscs"].append(line)
                if "loss" in line or "delay" in line:
                    tc_info["has_netem"] = True

            elif "htb" in line:
                tc_info["has_tc"] = True
                tc_info["qdiscs"].append(line)

    return TCSettings(**tc_info)


@tool
def get_active_links() -> List[ActiveLink]:
    """Get all active network links based on STP (Spanning Tree Protocol) forwarding states.

    This tool identifies which bridge-to-bridge links are actually carrying traffic by
    checking STP port states. Only links where both directions are in FORWARDING state
    are considered active. BLOCKING links are excluded as they don't carry traffic.

    Use this tool when you need to:
    - Determine which links are actually used for traffic
    - Identify interfaces in active paths for TC operations
    - Find interfaces that should be modified

    Returns:
        List of dictionaries, each representing an active bidirectional link:
        [
            {
                'from': 's1',              # Source switch
                'to': 's2',                # Destination switch
                'interface': 'veth-sw1-sw2',  # Forward direction interface
                'reverse_interface': 'veth-sw2-sw1',  # Reverse direction interface
                'state': 'forwarding',     # STP state
                'bridge': 'br-sw1'         # Bridge name
            },
            ...
        ]

    Note:
        - Only returns links where BOTH directions are FORWARDING
        - BLOCKING links are excluded (they don't affect traffic)
        - Each link represents a bidirectional connection between two switches
    """
    stp_info = get_all_stp_info()
    port_states = {}
    for bridge_name, bridge_stp in stp_info.bridges.items():
        for port in bridge_stp.ports:
            interface = port.interface
            state = port.state.lower()
            if interface:
                port_states[interface] = state

    active_links = []
    processed_links = set()

    for bridge_name, bridge_stp in stp_info.bridges.items():
        for port in bridge_stp.ports:
            interface = port.interface
            state = port.state.lower()

            if not interface or state != "forwarding":
                continue

            match = re.match(r"veth-(\w+)-(\w+)", interface)
            if not match:
                continue

            from_node = match.group(1)
            to_node = match.group(2)

            link_key = tuple(sorted([from_node, to_node]))

            if link_key in processed_links:
                continue

            forward_interface = interface
            reverse_interface = f"veth-{to_node}-{from_node}"

            forward_state = port_states.get(forward_interface, "").lower()
            reverse_state = port_states.get(reverse_interface, "").lower()

            if forward_state == "forwarding" and reverse_state == "forwarding":
                active_links.append(
                    ActiveLink(
                        from_node=from_node,
                        to=to_node,
                        interface=forward_interface,
                        reverse_interface=reverse_interface,
                        state="forwarding",
                        bridge=bridge_name,
                    )
                )
                processed_links.add(link_key)

    return active_links


@tool
def remove_tc(interface: str) -> TCOperationResult:
    """Remove all traffic control (TC) settings from a network interface.

    This tool removes any existing TC qdisc configuration from the specified interface,
    effectively restoring full bandwidth and removing any bandwidth limits, delays, or
    packet loss settings. This is useful for troubleshooting or when TC settings are
    causing performance issues.

    Use this tool when:
    - Removing bandwidth limits that are causing problems
    - Restoring full bandwidth to an interface
    - Clearing TC configuration before applying new settings
    - Fixing network performance issues caused by TC

    Args:
        interface: The network interface name to remove TC from (e.g., 'veth-sw1-sw2').
                   Can be a bridge or veth pair interface.

    Returns:
        Dictionary containing:
        - success: Boolean indicating if the operation succeeded
        - details: Human-readable description of the result
        - interface: The interface name that was processed

    Note:
        - Requires sudo privileges (passwordless sudo should be configured)
        - Returns success=True even if TC was not present (no error)
        - This operation is immediate and affects traffic flow
    """
    result = subprocess.run(
        ["sudo", "-n", "tc", "qdisc", "del", "dev", interface, "root"],
        capture_output=True,
        text=True,
        timeout=15,
    )
    success = (
        result.returncode == 0
        or "Cannot find" in result.stderr
        or "Cannot delete qdisc with handle of zero" in result.stderr
    )
    return TCOperationResult(
        success=success,
        details=(
            f"Removed TC from {interface}"
            if success
            else f"Failed to remove TC from {interface}"
        ),
        interface=interface,
    )


@tool
def apply_bandwidth_limit(
    interface: str, rate: str = "1Mbit", burst: str = "32Kb"
) -> TCOperationResult:
    """Apply bandwidth limit to a network interface using traffic control (TC) TBF qdisc.

    This tool configures a Token Bucket Filter (TBF) qdisc on the specified interface
    to limit the bandwidth. It automatically removes any existing TC configuration before
    applying the new limit. This is useful for testing, QoS, or simulating network conditions.

    Use this tool when:
    - Limiting bandwidth on a specific link to test performance
    - Applying QoS policies to control traffic flow
    - Simulating network conditions with reduced bandwidth
    - Troubleshooting by isolating bandwidth issues

    Args:
        interface: The network interface name to apply the limit to (e.g., 'veth-sw1-sw2').
                   Can be a bridge or veth pair interface.
        rate: Bandwidth rate limit in standard format (e.g., '1Mbit', '100Mbit', '500Kbit').
              This is the maximum sustained rate.
        burst: Burst size for the token bucket (e.g., '32Kb', '1Mb', '256Kb').
               Defaults to '32Kb' if not specified. Larger bursts allow temporary traffic spikes.

    Returns:
        Dictionary containing:
        - success: Boolean indicating if the operation succeeded
        - details: Human-readable description of the result
        - interface: The interface name that was configured
        - rate: The bandwidth rate that was applied
        - burst: The burst size that was applied

    Raises:
        Exception: If the TC command fails (e.g., sudo authentication required, invalid parameters)

    Note:
        - Requires sudo privileges (passwordless sudo should be configured)
        - Automatically removes existing TC configuration before applying new limit
        - Uses TBF (Token Bucket Filter) with 50ms latency
        - The limit is applied immediately and affects all traffic on the interface
        - To remove the limit, use remove_tc() tool
    """
    # Remove existing TC first
    subprocess.run(
        ["sudo", "-n", "tc", "qdisc", "del", "dev", interface, "root"],
        capture_output=True,
        text=True,
        timeout=15,
    )

    cmd = ["sudo", "-n", "tc", "qdisc", "add", "dev", interface, "root", "tbf"]
    cmd.extend(["rate", rate])
    cmd.extend(["burst", burst if burst else "32Kb"])
    cmd.extend(["latency", "50ms"])
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

    if result.returncode == 0:
        success = True
    else:
        error_msg = result.stderr.strip() if result.stderr else result.stdout.strip()
        if "password" in error_msg.lower() or "sudo" in error_msg.lower():
            error_msg = "Sudo authentication required. Please configure sudoers to allow passwordless TC commands."
        raise Exception(f"TC command failed: {error_msg}")

    return TCOperationResult(
        success=True,
        details=f"Applied bandwidth limit to {interface}",
        interface=interface,
        rate=rate,
        burst=burst,
    )


TRAFFIC_CONTROLLER_TOOLS = [
    get_tc_settings,
    get_active_links,
    remove_tc,
    apply_bandwidth_limit,
]
