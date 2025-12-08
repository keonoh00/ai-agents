from typing import Dict, List, Optional

from pydantic import BaseModel


class BridgeInfo(BaseModel):
    name: str
    exists: bool
    state: str
    interfaces: List[str] = []


class MemoryInfo(BaseModel):
    value: int
    unit: str


class VMInterface(BaseModel):
    interface: Optional[str] = None
    type: Optional[str] = None
    source: Optional[str] = None
    model: Optional[str] = None
    mac: Optional[str] = None


class VMConfig(BaseModel):
    name: str
    exists: bool
    state: str
    vcpu: Optional[int] = None
    memory: Optional[MemoryInfo] = None
    interfaces: List[VMInterface] = []
    disks: List[dict] = []
    os_type: Optional[str] = None


class STPPort(BaseModel):
    interface: str
    state: str


class STPInfo(BaseModel):
    bridge: str
    ports: List[STPPort] = []


class STPInfoCollection(BaseModel):
    bridges: Dict[str, STPInfo]


class ActiveLink(BaseModel):
    source: str
    target: str
    interface: str
    reverse_interface: str
    state: str
    bridge: str


class VMBridgeConnection(BaseModel):
    bridge: str
    interface: Optional[str] = None
    mac: Optional[str] = None


class VethConnection(BaseModel):
    source: str
    target: str
    interface: str
    type: str


class NetworkTopology(BaseModel):
    bridges: Dict[str, BridgeInfo]
    vms: Dict[str, VMConfig]
    vm_to_bridge: Dict[str, List[VMBridgeConnection]]
    bridge_connections: List[VethConnection] = []
    veth_connections: List[VethConnection] = []
    stp_info: Dict[str, STPInfo]
    active_links: List[ActiveLink]


class BridgeState(BaseModel):
    state: str
    interfaces: List[str] = []


class InterfaceSettings(BaseModel):
    ips: List[str] = []
    mac: Optional[str] = None
    state: str = "DOWN"


class RoutingInfo(BaseModel):
    route_count: int = 0
    routes: List[str] = []


class NetworkSettings(BaseModel):
    bridges: Dict[str, BridgeState]
    interfaces: Dict[str, InterfaceSettings]
    routing: RoutingInfo
    iptables: Dict[str, str] = {}


class AggregatedTopologyInfo(BaseModel):
    topology: NetworkTopology
    network_settings: NetworkSettings
    vm_configs: Dict[str, VMConfig]


class BridgeSummary(BaseModel):
    name: str
    state: str
    interfaces: List[str] = []


class VMInfoSummary(BaseModel):
    name: str
    state: str
    vcpu: Optional[int] = None
    memory: Optional[MemoryInfo] = None
    bridge_connections: List[VMBridgeConnection] = []


class BridgeConnectionSummary(BaseModel):
    from_bridge: str
    to_bridge: str
    interface: str
    from_node: str
    to_node: str


class STPPortSummary(BaseModel):
    interface: str
    state: str
    is_forwarding: bool


class STPSummary(BaseModel):
    ports: List[STPPortSummary] = []


class ExamplePath(BaseModel):
    host: str
    path_switches: List[str] = []
    interfaces_used: List[str] = []


class KeyInterfaceInfo(BaseModel):
    interface: str
    state: str
    ips: List[str] = []
    mac: Optional[str] = None


class NetworkSummary(BaseModel):
    bridges: List[BridgeSummary]
    vms: List[VMInfoSummary]
    bridge_connections: List[BridgeConnectionSummary]
    stp_info: Dict[str, STPSummary]
    active_links: List[ActiveLink]
    example_paths: List[ExamplePath]
    network_notes: List[str]
    key_interfaces: List[KeyInterfaceInfo]
