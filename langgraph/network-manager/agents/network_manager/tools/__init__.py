import re
import subprocess
from typing import Dict, List

from langchain_core.tools import tool
from network.infrastructure import (
    BRIDGES,
    VETH_PAIRS,
    build_topology_summary,
    collect_all_topology_info,
)

from .models import (
    AggregatedTopologyInfo,
    InterfaceState,
    InterfaceStats,
    NetworkStatus,
    NetworkSummary,
    TCIssue,
    TCSettings,
)


@tool
def get_tc_settings(interface: str) -> TCSettings:
    """
    Get traffic control (TC) settings for a specific network interface.

    This tool queries the Linux traffic control (TC) configuration for a given interface
    to determine if bandwidth limiting, delay, or loss settings are applied. It checks for
    TBF (Token Bucket Filter), netem, and HTB (Hierarchical Token Bucket) qdiscs.

    Use this tool when you need to check if a specific interface has TC settings that might
    be affecting network performance or bandwidth.

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
def get_all_tc_settings() -> Dict[str, TCSettings]:
    """Get traffic control (TC) settings for all network interfaces.

    This tool scans all bridges and veth pair interfaces in the network to check for
    any traffic control configurations.

    Use this tool when you need a comprehensive view of all TC settings across the network,
    such as when diagnosing network performance issues or identifying which links have
    bandwidth limits applied.

    Returns:
        Dictionary mapping interface names to their TC settings. Each interface entry
        contains the same structure as get_tc_settings() output:
        {
            'veth-sw1-sw2': {
                'interface': 'veth-sw1-sw2',
                'has_tc': True/False,
                'bandwidth_limit': '1Mbit' or None,
                ...
            },
            'br-sw1': { ... },
            ...
        }

    Note:
        This tool checks all bridges (br-sw1 through br-sw4, br-wan, br-lan) and all
        veth pair interfaces. It's more efficient than calling get_tc_settings() multiple times.
    """
    all_interfaces = BRIDGES + VETH_PAIRS
    tc_status = {}

    for iface in all_interfaces:
        result = subprocess.run(
            ["tc", "qdisc", "show", "dev", iface],
            capture_output=True,
            text=True,
            timeout=5,
        )

        tc_info = {
            "interface": iface,
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

        tc_status[iface] = TCSettings(**tc_info)

    return tc_status


@tool
def get_interface_stats(interface: str) -> InterfaceStats:
    """Get real-time traffic statistics for a specific network interface.

    This tool retrieves current network interface statistics including bytes and packets
    transmitted/received, and any errors. This is useful for monitoring network activity
    and diagnosing performance issues.

    Use this tool when you need to check:
    - Current traffic volume on an interface
    - Whether an interface is actively transmitting/receiving data
    - Error rates that might indicate network problems

    Args:
        interface: The network interface name to query (e.g., 'veth-sw1-sw2', 'br-sw1')

    Returns:
        Dictionary containing:
        - interface: The interface name
        - exists: Boolean indicating if the interface exists
        - rx_bytes: Total bytes received
        - tx_bytes: Total bytes transmitted
        - rx_packets: Total packets received
        - tx_packets: Total packets transmitted
        - rx_errors: Receive errors (if available)
        - tx_errors: Transmit errors (if available)

    Note:
        If the interface doesn't exist, returns {'interface': name, 'exists': False}
    """
    result = subprocess.run(
        ["ip", "-s", "link", "show", interface],
        capture_output=True,
        text=True,
        timeout=5,
    )

    if result.returncode == 0:
        stats = {
            "interface": interface,
            "exists": True,
            "rx_bytes": 0,
            "tx_bytes": 0,
            "rx_packets": 0,
            "tx_packets": 0,
            "rx_errors": 0,
            "tx_errors": 0,
        }

        lines = result.stdout.split("\n")
        for i, line in enumerate(lines):
            if "RX:" in line and i + 1 < len(lines):
                next_line = lines[i + 1]
                rx_match = re.search(r"(\d+)\s+bytes", next_line)
                if rx_match:
                    stats["rx_bytes"] = int(rx_match.group(1))
                rx_pkt = re.search(r"(\d+)\s+packets", next_line)
                if rx_pkt:
                    stats["rx_packets"] = int(rx_pkt.group(1))

            if "TX:" in line and i + 1 < len(lines):
                next_line = lines[i + 1]
                tx_match = re.search(r"(\d+)\s+bytes", next_line)
                if tx_match:
                    stats["tx_bytes"] = int(tx_match.group(1))
                tx_pkt = re.search(r"(\d+)\s+packets", next_line)
                if tx_pkt:
                    stats["tx_packets"] = int(tx_pkt.group(1))

        return InterfaceStats(**stats)
    else:
        return InterfaceStats(interface=interface, exists=False)


@tool
def get_network_status() -> NetworkStatus:
    """Get comprehensive network status including TC settings and interface states.

    This tool provides a complete overview of the network by checking:
    1. Traffic control settings on all interfaces (bridges and veth pairs)
    2. Interface state (UP/DOWN) for key network interfaces

    Use this tool when you need a high-level view of the entire network status,
    such as during initial diagnostics or when monitoring overall network health.

    Returns:
        Dictionary containing:
        - tc_settings: Dictionary of all TC settings (same format as get_all_tc_settings())
        - interfaces: Dictionary mapping interface names to their state:
          {
              'veth-sw1-sw2': {'exists': True, 'state': 'UP'},
              'br-sw1': {'exists': True, 'state': 'UP'},
              ...
          }

    Note:
        This tool checks the first 4 veth pairs and all bridges for interface state.
        For complete TC information, it checks all interfaces sequentially.
    """
    all_interfaces = BRIDGES + VETH_PAIRS
    tc_status = {}

    for iface in all_interfaces:
        result = subprocess.run(
            ["tc", "qdisc", "show", "dev", iface],
            capture_output=True,
            text=True,
            timeout=5,
        )

        tc_info = {
            "interface": iface,
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
                if "tbf" in line or "netem" in line or "htb" in line:
                    tc_info["has_tc"] = True
                    tc_info["qdiscs"].append(line)
                    if "tbf" in line:
                        rate_match = re.search(r"rate\s+(\d+)(\w+)", line)
                        if rate_match:
                            tc_info["bandwidth_limit"] = (
                                f"{rate_match.group(1)}{rate_match.group(2)}"
                            )

        tc_status[iface] = TCSettings(**tc_info)

    interfaces = {}
    for iface in BRIDGES + VETH_PAIRS[:4]:
        result = subprocess.run(
            ["ip", "link", "show", iface], capture_output=True, text=True, timeout=2
        )
        if result.returncode == 0:
            interfaces[iface] = InterfaceState(
                exists=True,
                state="UP" if "UP" in result.stdout else "DOWN",
            )

    return NetworkStatus(tc_settings=tc_status, interfaces=interfaces)


@tool
def detect_tc_issues() -> List[TCIssue]:
    """
    Detect and list all interfaces with active traffic control (TC) configurations.

    This tool scans all network interfaces and identifies which ones have TC settings
    that could be affecting network performance, such as bandwidth limits, delays, or
    packet loss configurations.

    Use this tool when:
    - Diagnosing network performance problems
    - Identifying which links have bandwidth restrictions
    - Finding interfaces that might be causing traffic bottlenecks

    Returns:
        List of dictionaries, each containing:
        - interface: The interface name with TC configured
        - type: Type of TC issue ('bandwidth_limit' or 'tc_configured')
        - bandwidth_limit: The bandwidth limit if TBF is configured (e.g., '1Mbit')
        - burst: Burst size if configured
        - description: Human-readable description of the issue

    Example:
        [
            {
                'interface': 'veth-sw1-sw2',
                'type': 'bandwidth_limit',
                'bandwidth_limit': '1Mbit',
                'burst': '32Kb',
                'description': 'Interface veth-sw1-sw2 has TC bandwidth limiting configured'
            },
            ...
        ]

    Note:
        Only returns interfaces that actually have TC configured (has_tc=True).
        Interfaces without TC are not included in the results.
    """
    issues = []
    all_interfaces = BRIDGES + VETH_PAIRS
    tc_status = {}

    for iface in all_interfaces:
        result = subprocess.run(
            ["tc", "qdisc", "show", "dev", iface],
            capture_output=True,
            text=True,
            timeout=5,
        )

        tc_info = {
            "interface": iface,
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
                if "tbf" in line or "netem" in line or "htb" in line:
                    tc_info["has_tc"] = True
                    tc_info["qdiscs"].append(line)
                    if "tbf" in line:
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

        tc_status[iface] = tc_info

    for iface, tc_info in tc_status.items():
        if tc_info.get("has_tc") and tc_info.get("qdiscs"):
            has_restriction = any(
                "tbf" in qdisc or "netem" in qdisc or "htb" in qdisc
                for qdisc in tc_info.get("qdiscs", [])
            )

            if has_restriction:
                issues.append(
                    TCIssue(
                        interface=iface,
                        type=(
                            "bandwidth_limit"
                            if tc_info.get("bandwidth_limit")
                            else "tc_configured"
                        ),
                        bandwidth_limit=tc_info.get("bandwidth_limit"),
                        burst=tc_info.get("burst"),
                        description=f"Interface {iface} has TC bandwidth limiting configured",
                    )
                )

    return issues


@tool
def get_topology_info() -> AggregatedTopologyInfo:
    """Get complete network topology and configuration information.

    This tool collects comprehensive information about the network infrastructure including:
    - Bridge configurations and states
    - VM configurations and their bridge connections
    - VM-to-bridge mappings
    - Bridge-to-bridge connections via veth pairs
    - STP (Spanning Tree Protocol) information
    - Active links based on STP forwarding states
    - Network settings and interface details

    Use this tool when you need detailed topology information for:
    - Understanding network structure
    - Analyzing traffic paths
    - Diagnosing connectivity issues
    - Planning network changes

    Returns:
        Dictionary containing:
        - topology: Complete network topology including bridges, VMs, connections
        - network_settings: Network interface settings and configurations
        - vm_configs: VM configuration details for all VMs

    Note:
        This is a comprehensive data collection that may take a few seconds to complete.
        For a human-readable summary, use get_topology_summary() instead.
    """
    return collect_all_topology_info()


@tool
def get_topology_summary() -> NetworkSummary:
    """Get a structured summary of the network topology.

    This tool generates a comprehensive, structured dictionary of the network topology
    that is easy for LLMs to parse and understand. It includes:
    - Bridge states and interfaces
    - VM configurations and bridge connections
    - Bridge-to-bridge connections via veth pairs
    - STP port states (forwarding/blocking)
    - Active links that actually carry traffic
    - Example paths to various hosts
    - Network path understanding and traffic flow

    Use this tool when you need a clear, structured overview of the network structure
    for analysis or when explaining the network to users.

    Returns:
        Dictionary containing:
        - bridges: List of bridge information with name, state, and interfaces
        - vms: List of VM information with name, state, vcpu, memory, and bridge connections
        - bridge_connections: List of bridge-to-bridge connections via veth pairs
        - stp_info: Dictionary of STP port states per bridge
        - active_links: List of active links (FORWARDING state only)
        - example_paths: List of example paths to various hosts with interfaces used
        - network_notes: List of important notes about network behavior
        - key_interfaces: List of key interface settings

    Note:
        This summary is optimized for LLM consumption with structured data format
        and includes important notes about STP behavior and traffic flow patterns.
    """
    return build_topology_summary()


NETWORK_MANAGER_TOOLS = [
    get_tc_settings,
    get_all_tc_settings,
    get_interface_stats,
    get_network_status,
    detect_tc_issues,
    get_topology_info,
    get_topology_summary,
]
