from typing import List, Optional

from pydantic import BaseModel


class TCSettings(BaseModel):
    """Traffic control settings for a network interface."""

    interface: str
    has_tc: bool
    qdiscs: List[str] = []
    bandwidth_limit: Optional[str] = None
    burst: Optional[str] = None
    has_netem: Optional[bool] = None


class ActiveLink(BaseModel):
    """Active network link based on STP forwarding state."""

    from_node: str
    to: str
    interface: str
    reverse_interface: str
    state: str
    bridge: str


class TCOperationResult(BaseModel):
    """Result of a TC operation (remove or apply bandwidth limit)."""

    success: bool
    details: str
    interface: str
    rate: Optional[str] = None
    burst: Optional[str] = None
