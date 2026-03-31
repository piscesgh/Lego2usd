from __future__ import annotations

from backend.app.domain import AssemblyState, PreviewResult
from backend.app.math3d import multiply_matrix, rigid_inverse
from backend.app.services.part_registry import PartRegistry


class ConnectionService:
    def __init__(self, registry: PartRegistry) -> None:
        self.registry = registry

    def preview_connection(
        self,
        assembly: AssemblyState,
        *,
        world_transforms: dict[str, list[list[float]]],
        source_instance_id: str,
        source_port_id: str,
        target_sku: str,
        target_port_id: str,
    ) -> PreviewResult:
        source_node = next(
            (node for node in assembly.nodes if node.instance_id == source_instance_id), None
        )
        if source_node is None:
            raise ValueError(f"Unknown source instance '{source_instance_id}'")

        source_port = self.registry.get_port(source_node.sku, source_port_id)
        target_port = self.registry.get_port(target_sku, target_port_id)

        is_compatible = (
            target_port.family in source_port.compatible_families
            or source_port.family in target_port.compatible_families
        )
        if not is_compatible:
            raise ValueError(
                f"Incompatible port families: {source_port.family} -> {target_port.family}"
            )

        source_world = world_transforms[source_instance_id]
        local_transform = multiply_matrix(
            source_port.local_transform, rigid_inverse(target_port.local_transform)
        )
        world_transform = multiply_matrix(source_world, local_transform)

        if source_port.kind == "motor_output" or target_port.kind == "motor_output":
            joint_type = "revolute"
        else:
            joint_type = "fixed"

        auto_connector_rule = (
            "implicit_axle"
            if source_port.family == "axle_output" or target_port.family == "axle_output"
            else "implicit_pin"
        )

        return PreviewResult(
            compatible=True,
            joint_type=joint_type,
            auto_connector_rule=auto_connector_rule,
            resolved_transform=world_transform,
            resolved_local_transform=local_transform,
            source_instance_id=source_instance_id,
            source_port_id=source_port_id,
            target_sku=target_sku,
            target_port_id=target_port_id,
        )

