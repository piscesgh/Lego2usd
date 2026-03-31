from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

Matrix4 = list[list[float]]
PortKind = Literal["structural", "motor_output"]
PortFamily = Literal["technic_hole", "axle_output"]
JointBehavior = Literal["fixed", "revolute"]


@dataclass(frozen=True)
class PortDefinition:
    id: str
    kind: PortKind
    family: PortFamily
    local_transform: Matrix4
    compatible_families: list[PortFamily]
    auto_connector_rule: str
    joint_behavior: JointBehavior
    axis: tuple[float, float, float] | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "kind": self.kind,
            "family": self.family,
            "local_transform": self.local_transform,
            "compatible_families": self.compatible_families,
            "auto_connector_rule": self.auto_connector_rule,
            "joint_behavior": self.joint_behavior,
            "axis": list(self.axis) if self.axis else None,
        }


@dataclass(frozen=True)
class PartDefinition:
    sku: str
    label: str
    category: str
    geometry_asset: str
    search_aliases: list[str]
    render_size: tuple[float, float, float]
    ports: list[PortDefinition]

    def summary_dict(self) -> dict[str, Any]:
        return {
            "sku": self.sku,
            "label": self.label,
            "category": self.category,
            "geometry_asset": self.geometry_asset,
            "search_aliases": self.search_aliases,
        }

    def to_dict(self) -> dict[str, Any]:
        return {
            "sku": self.sku,
            "label": self.label,
            "category": self.category,
            "geometry_asset": self.geometry_asset,
            "search_aliases": self.search_aliases,
            "render_size": list(self.render_size),
            "ports": [port.to_dict() for port in self.ports],
        }


@dataclass
class AssemblyNode:
    instance_id: str
    sku: str
    local_transform: Matrix4
    parent_instance_id: str | None = None
    parent_port_id: str | None = None
    child_port_id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "instance_id": self.instance_id,
            "sku": self.sku,
            "local_transform": self.local_transform,
            "parent_instance_id": self.parent_instance_id,
            "parent_port_id": self.parent_port_id,
            "child_port_id": self.child_port_id,
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "AssemblyNode":
        return cls(
            instance_id=payload["instance_id"],
            sku=payload["sku"],
            local_transform=payload["local_transform"],
            parent_instance_id=payload.get("parent_instance_id"),
            parent_port_id=payload.get("parent_port_id"),
            child_port_id=payload.get("child_port_id"),
        )


@dataclass
class ConnectionRecord:
    parent_instance_id: str
    child_instance_id: str
    parent_port_id: str
    child_port_id: str
    joint_type: JointBehavior
    auto_connector_rule: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "parent_instance_id": self.parent_instance_id,
            "child_instance_id": self.child_instance_id,
            "parent_port_id": self.parent_port_id,
            "child_port_id": self.child_port_id,
            "joint_type": self.joint_type,
            "auto_connector_rule": self.auto_connector_rule,
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "ConnectionRecord":
        return cls(
            parent_instance_id=payload["parent_instance_id"],
            child_instance_id=payload["child_instance_id"],
            parent_port_id=payload["parent_port_id"],
            child_port_id=payload["child_port_id"],
            joint_type=payload["joint_type"],
            auto_connector_rule=payload["auto_connector_rule"],
        )


@dataclass
class AssemblyState:
    nodes: list[AssemblyNode] = field(default_factory=list)
    connections: list[ConnectionRecord] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "nodes": [node.to_dict() for node in self.nodes],
            "connections": [connection.to_dict() for connection in self.connections],
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any] | None) -> "AssemblyState":
        if not payload:
            return cls()
        return cls(
            nodes=[AssemblyNode.from_dict(item) for item in payload.get("nodes", [])],
            connections=[
                ConnectionRecord.from_dict(item)
                for item in payload.get("connections", [])
            ],
        )


@dataclass(frozen=True)
class PreviewResult:
    compatible: bool
    joint_type: JointBehavior
    auto_connector_rule: str
    resolved_transform: Matrix4
    resolved_local_transform: Matrix4
    source_instance_id: str
    source_port_id: str
    target_sku: str
    target_port_id: str
    reason: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "compatible": self.compatible,
            "joint_type": self.joint_type,
            "auto_connector_rule": self.auto_connector_rule,
            "resolved_transform": self.resolved_transform,
            "resolved_local_transform": self.resolved_local_transform,
            "source_instance_id": self.source_instance_id,
            "source_port_id": self.source_port_id,
            "target_sku": self.target_sku,
            "target_port_id": self.target_port_id,
            "reason": self.reason,
        }

