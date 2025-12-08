import re
import subprocess
from collections import deque
from typing import Dict, List

from network.models import (
    ActiveLink,
    AggregatedTopologyInfo,
    BridgeConnectionSummary,
    BridgeInfo,
    BridgeState,
    BridgeSummary,
    ExamplePath,
    InterfaceSettings,
    KeyInterfaceInfo,
    MemoryInfo,
    NetworkSettings,
    NetworkSummary,
    NetworkTopology,
    RoutingInfo,
    STPInfo,
    STPInfoCollection,
    STPPort,
    STPPortSummary,
    STPSummary,
    VethConnection,
    VMBridgeConnection,
    VMConfig,
    VMInfoSummary,
    VMInterface,
)

# Constants
BRIDGES = ["br-sw1", "br-sw2", "br-sw3", "br-sw4", "br-wan", "br-lan"]
VMS = ["host1", "host2", "host3", "host4", "router1", "router2", "ss"]
VETH_PAIRS = [
    "veth-sw1-sw2",
    "veth-sw2-sw1",
    "veth-sw1-sw3",
    "veth-sw3-sw1",
    "veth-sw2-sw4",
    "veth-sw4-sw2",
    "veth-sw3-sw4",
    "veth-sw4-sw3",
]


def get_bridge_info(bridge_name: str) -> BridgeInfo:
    """Collect bridge information including state and connected interfaces."""
    try:
        result = subprocess.run(
            ["ip", "link", "show", bridge_name],
            capture_output=True,
            text=True,
            timeout=5,
        )

        exists = result.returncode == 0
        state = "UP" if "UP" in result.stdout else "DOWN"
        interfaces: List[str] = []

        if exists:
            result2 = subprocess.run(
                ["ip", "link", "show", "master", bridge_name],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result2.returncode == 0:
                interfaces = re.findall(r"\d+:\s+(\w+):", result2.stdout)

        return BridgeInfo(
            name=bridge_name,
            exists=exists,
            state=state,
            interfaces=interfaces,
        )
    except Exception:
        return BridgeInfo(name=bridge_name, exists=False, state="DOWN", interfaces=[])


def get_vm_config(vm_name: str) -> VMConfig:
    """Collect VM configuration information using virsh commands."""
    try:
        exists = False
        state = "unknown"
        vcpu = None
        memory = None
        interfaces: List[VMInterface] = []
        disks: List[dict] = []
        os_type = None

        result = subprocess.run(
            ["virsh", "dominfo", vm_name],
            capture_output=True,
            text=True,
            timeout=5,
        )

        if result.returncode == 0:
            exists = True

            state_match = re.search(r"State:\s+(\w+)", result.stdout)
            if state_match:
                state = state_match.group(1)

            vcpu_match = re.search(r"CPU\(s\):\s+(\d+)", result.stdout)
            if vcpu_match:
                vcpu = int(vcpu_match.group(1))

            mem_match = re.search(r"Max memory:\s+(\d+)\s+(\w+)", result.stdout)
            if mem_match:
                memory = MemoryInfo(
                    value=int(mem_match.group(1)),
                    unit=mem_match.group(2),
                )

            iflist_result = subprocess.run(
                ["virsh", "domiflist", vm_name],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if iflist_result.returncode == 0:
                lines = iflist_result.stdout.strip().split("\n")[2:]
                for line in lines:
                    parts = line.split()
                    if len(parts) >= 3:
                        interfaces.append(
                            VMInterface(
                                interface=parts[0],
                                type=parts[1],
                                source=parts[2],
                                model=parts[3] if len(parts) > 3 else None,
                                mac=parts[4] if len(parts) > 4 else None,
                            )
                        )

        return VMConfig(
            name=vm_name,
            exists=exists,
            state=state,
            vcpu=vcpu,
            memory=memory,
            interfaces=interfaces,
            disks=disks,
            os_type=os_type,
        )
    except Exception:
        return VMConfig(
            name=vm_name,
            exists=False,
            state="unknown",
            interfaces=[],
            disks=[],
        )


def get_stp_info(bridge_name: str) -> STPInfo:
    """Collect Spanning Tree Protocol (STP) information for a bridge."""
    ports: List[STPPort] = []

    try:
        result = subprocess.run(
            ["brctl", "showstp", bridge_name],
            capture_output=True,
            text=True,
            timeout=5,
        )

        if result.returncode == 0:
            lines = result.stdout.split("\n")
            current_port = None
            port_section_started = False

            for i, line in enumerate(lines):
                port_match = re.match(r"^(\w+-\w+-\w+)\s+\(", line)
                if port_match:
                    current_port = port_match.group(1)
                    port_section_started = True
                    ports.append(STPPort(interface=current_port, state="unknown"))
                    continue

                if port_section_started and current_port:
                    if "port id" in line.lower() and "state" in line.lower():
                        state_match = re.search(r"state\s+(\w+)", line)
                        if state_match:
                            for port in ports:
                                if port.interface == current_port:
                                    port.state = state_match.group(1)
                                    port_section_started = False
                                    break
                        continue

                    if line.strip() == "" and i > 0 and lines[i - 1].strip() != "":
                        port_section_started = False
    except Exception:
        pass

    return STPInfo(bridge=bridge_name, ports=ports)


def get_all_stp_info() -> STPInfoCollection:
    """Collect STP information for all bridges in the network."""
    stp_info: Dict[str, STPInfo] = {}
    for bridge in BRIDGES:
        stp_info[bridge] = get_stp_info(bridge)
    return STPInfoCollection(bridges=stp_info)


def collect_active_links() -> List[ActiveLink]:
    """Get all active network links based on STP forwarding states.

    Only links where both directions are in FORWARDING state are considered active.
    BLOCKING links are excluded as they don't carry traffic.

    Returns:
        List of dictionaries, each representing an active bidirectional link:
        - from: Source switch node (e.g., 'sw1', 'sw2')
        - to: Destination switch node
        - interface: Forward direction interface (e.g., 'veth-sw1-sw2')
        - reverse_interface: Reverse direction interface (e.g., 'veth-sw2-sw1')
        - state: Always 'forwarding' for active links
        - bridge: Bridge name where the link is connected
    """
    stp_info = get_all_stp_info().bridges
    port_states = {}
    for bridge_name, bridge_stp in stp_info.items():
        for port in bridge_stp.ports:
            interface = port.interface
            state = port.state.lower()
            if interface:
                port_states[interface] = state

    active_links = []
    processed_links = set()

    for bridge_name, bridge_stp in stp_info.items():
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
                        source=from_node,
                        target=to_node,
                        interface=forward_interface,
                        reverse_interface=reverse_interface,
                        state="forwarding",
                        bridge=bridge_name,
                    )
                )
                processed_links.add(link_key)

    return active_links


def get_network_topology() -> NetworkTopology:
    """Collect complete network topology including bridges, VMs, and connections."""
    bridges: Dict[str, BridgeInfo] = {}
    vms: Dict[str, VMConfig] = {}
    vm_to_bridge: Dict[str, List[VMBridgeConnection]] = {}
    veth_connections: List[VethConnection] = []

    for bridge in BRIDGES:
        bridges[bridge] = get_bridge_info(bridge)

    for vm in VMS:
        vm_config = get_vm_config(vm)
        vms[vm] = vm_config

        for iface in vm_config.interfaces:
            if iface.type == "bridge":
                bridge_name = iface.source
                if bridge_name:
                    vm_to_bridge.setdefault(vm, []).append(
                        VMBridgeConnection(
                            bridge=bridge_name,
                            interface=iface.interface,
                            mac=iface.mac,
                        )
                    )

    for veth in VETH_PAIRS:
        match = re.match(r"veth-sw(\d+)-sw(\d+)", veth)
        if match:
            from_node = "s" + match.group(1)
            to_node = "s" + match.group(2)

            result = subprocess.run(
                ["ip", "link", "show", veth],
                capture_output=True,
                text=True,
                timeout=2,
            )
            if result.returncode == 0:
                veth_connections.append(
                    VethConnection(
                        source=from_node, target=to_node, interface=veth, type="veth"
                    )
                )

    stp_info = get_all_stp_info().bridges
    active_links = collect_active_links()

    return NetworkTopology(
        bridges=bridges,
        vms=vms,
        vm_to_bridge=vm_to_bridge,
        bridge_connections=[],
        veth_connections=veth_connections,
        stp_info=stp_info,
        active_links=active_links,
    )


def get_network_settings() -> NetworkSettings:
    """Collect network configuration information including IPs, MACs, and routing."""
    bridges: Dict[str, BridgeState] = {}
    interfaces: Dict[str, InterfaceSettings] = {}

    for bridge in BRIDGES:
        bridge_info = get_bridge_info(bridge)
        bridges[bridge] = BridgeState(
            state=bridge_info.state,
            interfaces=bridge_info.interfaces,
        )

    all_interfaces = set()
    for bridge_info in bridges.values():
        all_interfaces.update(bridge_info.interfaces)

    for iface in all_interfaces:
        try:
            result = subprocess.run(
                ["ip", "addr", "show", iface],
                capture_output=True,
                text=True,
                timeout=3,
            )
            if result.returncode == 0:
                ip_matches = re.findall(r"inet\s+([\d.]+/\d+)", result.stdout)
                mac_match = re.search(r"link/ether\s+([\da-f:]+)", result.stdout)

                interfaces[iface] = InterfaceSettings(
                    ips=ip_matches,
                    mac=mac_match.group(1) if mac_match else None,
                    state="UP" if "UP" in result.stdout else "DOWN",
                )
        except Exception:
            pass

    routing = RoutingInfo()
    try:
        result = subprocess.run(
            ["ip", "route", "show"],
            capture_output=True,
            text=True,
            timeout=3,
        )
        if result.returncode == 0:
            routes = result.stdout.strip().split("\n")
            routing = RoutingInfo(route_count=len(routes), routes=routes[:10])
    except Exception:
        pass

    return NetworkSettings(
        bridges=bridges,
        interfaces=interfaces,
        routing=routing,
        iptables={},
    )


def calculate_path_to_host(host_vm: str) -> List[str]:
    """Calculate the shortest active path from root switch (s1) to a host VM.

    Uses BFS (Breadth-First Search) to find the path through active STP links.
    Only considers links in FORWARDING state.

    Args:
        host_vm: The host VM name (e.g., 'host1', 'host2', 'host3', 'host4')

    Returns:
        List of switch nodes in the path from root (s1) to the host's switch.
        Example: ['s1', 's3'] means path goes s1 -> s3 -> host
        Returns empty list if host is not found or path cannot be determined.
    """
    topology = get_network_topology()
    vm_to_bridge = topology.vm_to_bridge

    host_connections = vm_to_bridge.get(host_vm)
    if not host_connections:
        return []

    host_bridge = host_connections[0].bridge
    if not host_bridge:
        return []

    match = re.match(r"br-sw(\d+)", host_bridge)
    if not match:
        return []

    host_switch = f"s{match.group(1)}"
    active_links = collect_active_links()

    if host_switch == "s1":
        return ["s1"]

    adjacency = {}
    for link in active_links:
        from_node = link.source
        to_node = link.target
        if from_node not in adjacency:
            adjacency[from_node] = []
        if to_node not in adjacency:
            adjacency[to_node] = []
        adjacency[from_node].append(to_node)
        adjacency[to_node].append(from_node)

    queue = deque([("s1", ["s1"])])
    visited = {"s1"}

    while queue:
        current, path = queue.popleft()

        if current == host_switch:
            return path

        for neighbor in adjacency.get(current, []):
            if neighbor not in visited:
                visited.add(neighbor)
                queue.append((neighbor, path + [neighbor]))

    return []


def collect_all_topology_info() -> AggregatedTopologyInfo:
    """Collect all topology and configuration information in one comprehensive structure."""
    return AggregatedTopologyInfo(
        topology=get_network_topology(),
        network_settings=get_network_settings(),
        vm_configs={vm: get_vm_config(vm) for vm in VMS},
    )


def build_topology_summary() -> NetworkSummary:
    """Convert topology information to structured pydantic models optimized for LLMs."""
    info = collect_all_topology_info()
    topology = info.topology
    vm_to_bridge = topology.vm_to_bridge
    veth_connections = topology.veth_connections
    stp_info = topology.stp_info
    active_links = topology.active_links

    bridges: List[BridgeSummary] = []
    for bridge_name, bridge_info in topology.bridges.items():
        if bridge_info.exists:
            bridges.append(
                BridgeSummary(
                    name=bridge_name,
                    state=bridge_info.state,
                    interfaces=bridge_info.interfaces,
                )
            )

    vms: List[VMInfoSummary] = []
    for vm_name, vm_config in topology.vms.items():
        if vm_config.exists:
            vms.append(
                VMInfoSummary(
                    name=vm_name,
                    state=vm_config.state,
                    vcpu=vm_config.vcpu,
                    memory=vm_config.memory,
                    bridge_connections=vm_to_bridge.get(vm_name, []),
                )
            )

    bridge_connections: List[BridgeConnectionSummary] = []
    processed_links = set()
    for conn in veth_connections:
        from_node = conn.source
        to_node = conn.target
        interface = conn.interface
        link_key = tuple(sorted([from_node, to_node]))
        if link_key not in processed_links:
            bridge_from = f"br-{from_node}" if from_node.startswith("s") else from_node
            bridge_to = f"br-{to_node}" if to_node.startswith("s") else to_node
            bridge_connections.append(
                BridgeConnectionSummary(
                    from_bridge=bridge_from,
                    to_bridge=bridge_to,
                    interface=interface,
                    from_node=from_node,
                    to_node=to_node,
                )
            )
            processed_links.add(link_key)

    stp_summary: Dict[str, STPSummary] = {}
    for bridge_name, bridge_stp in stp_info.items():
        if bridge_stp.ports:
            stp_summary[bridge_name] = STPSummary(
                ports=[
                    STPPortSummary(
                        interface=port.interface,
                        state=port.state,
                        is_forwarding=port.state.lower() == "forwarding",
                    )
                    for port in bridge_stp.ports
                ]
            )

    example_paths: List[ExamplePath] = []
    for vm_name in ["host1", "host2", "host3", "host4"]:
        if vm_name in vm_to_bridge:
            path = calculate_path_to_host(vm_name)
            if path:
                used_veths: List[str] = []
                for i in range(len(path) - 1):
                    current = path[i]
                    next_node = path[i + 1]
                    for link in active_links:
                        if (link.source == current and link.target == next_node) or (
                            link.source == next_node and link.target == current
                        ):
                            used_veths.append(link.interface)
                            break

                example_paths.append(
                    ExamplePath(
                        host=vm_name,
                        path_switches=path,
                        interfaces_used=used_veths,
                    )
                )

    network_notes = [
        "VM-to-Bridge: VMs connect to bridges via vnet interfaces (e.g., host1 connects to br-sw3 via vnet3)",
        "Bridge-to-Bridge: Bridges connect to each other via veth pairs (e.g., br-sw1 ↔ br-sw2 via veth-sw1-sw2)",
        "STP Impact: Only FORWARDING links carry traffic. BLOCKING links do NOT affect traffic flow.",
        "Traffic Flow: Traffic flows from VM → vnet → bridge → veth (only if FORWARDING) → bridge → vnet → VM",
        "TC Settings: Traffic Control (TC) can be applied to vnet or veth interfaces to limit bandwidth or add delay/loss",
        "When analyzing traffic: Only consider TC settings on FORWARDING links in the active path.",
        "IMPORTANT: When user asks 'which link is set TC?', check the veth interfaces (veth-sw1-sw2, veth-sw1-sw3, etc.)",
    ]

    key_interfaces: List[KeyInterfaceInfo] = []
    for iface_name, iface_info in list(info.network_settings.interfaces.items())[:10]:
        key_interfaces.append(
            KeyInterfaceInfo(
                interface=iface_name,
                state=iface_info.state,
                ips=iface_info.ips,
                mac=iface_info.mac,
            )
        )

    return NetworkSummary(
        bridges=bridges,
        vms=vms,
        bridge_connections=bridge_connections,
        stp_info=stp_summary,
        active_links=active_links,
        example_paths=example_paths,
        network_notes=network_notes,
        key_interfaces=key_interfaces,
    )
