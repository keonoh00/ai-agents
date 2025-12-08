from typing import Dict, List, Optional

from network.models import AggregatedTopologyInfo, NetworkSummary
from pydantic import BaseModel


class TCSettings(BaseModel):
    """Traffic control settings for a network interface."""

    interface: str
    has_tc: bool
    qdiscs: List[str] = []
    bandwidth_limit: Optional[str] = None
    burst: Optional[str] = None
    has_netem: Optional[bool] = None


class InterfaceStats(BaseModel):
    """Network interface statistics."""

    interface: str
    exists: bool
    rx_bytes: int = 0
    tx_bytes: int = 0
    rx_packets: int = 0
    tx_packets: int = 0
    rx_errors: int = 0
    tx_errors: int = 0


class InterfaceState(BaseModel):
    """Interface state information."""

    exists: bool
    state: str


class NetworkStatus(BaseModel):
    """Comprehensive network status."""

    tc_settings: Dict[str, TCSettings]
    interfaces: Dict[str, InterfaceState]


class TCIssue(BaseModel):
    """Traffic control issue detected on an interface."""

    interface: str
    type: str
    bandwidth_limit: Optional[str] = None
    burst: Optional[str] = None
    description: str
