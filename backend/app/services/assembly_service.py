from __future__ import annotations

from collections import defaultdict

from backend.app.domain import (
    AssemblyNode,
    AssemblyState,
    ConnectionRecord,
    PreviewResult,
)
from backend.app.math3d import identity_matrix, multiply_matrix


class AssemblyService:
    def create_root(self, assembly: AssemblyState, sku: str) -> AssemblyState:
        if assembly.nodes:
            raise ValueError("Root placement is only allowed on an empty assembly")
        assembly.nodes.append(
            AssemblyNode(
                instance_id=self.next_instance_id(assembly),
                sku=sku,
                local_transform=identity_matrix(),
            )
        )
        return assembly

    def attach_part(self, assembly: AssemblyState, preview: PreviewResult) -> AssemblyState:
        instance_id = self.next_instance_id(assembly)
        assembly.nodes.append(
            AssemblyNode(
                instance_id=instance_id,
                sku=preview.target_sku,
                local_transform=preview.resolved_local_transform,
                parent_instance_id=preview.source_instance_id,
                parent_port_id=preview.source_port_id,
                child_port_id=preview.target_port_id,
            )
        )
        assembly.connections.append(
            ConnectionRecord(
                parent_instance_id=preview.source_instance_id,
                child_instance_id=instance_id,
                parent_port_id=preview.source_port_id,
                child_port_id=preview.target_port_id,
                joint_type=preview.joint_type,
                auto_connector_rule=preview.auto_connector_rule,
            )
        )
        return assembly

    def next_instance_id(self, assembly: AssemblyState) -> str:
        used = {
            int(node.instance_id.split("_")[1])
            for node in assembly.nodes
            if node.instance_id.startswith("node_")
            and node.instance_id.split("_")[1].isdigit()
        }
        candidate = 1
        while candidate in used:
            candidate += 1
        return f"node_{candidate}"

    def build_world_transforms(
        self, assembly: AssemblyState
    ) -> dict[str, list[list[float]]]:
        by_parent: dict[str | None, list[AssemblyNode]] = defaultdict(list)
        for node in assembly.nodes:
            by_parent[node.parent_instance_id].append(node)

        world: dict[str, list[list[float]]] = {}

        def visit(node: AssemblyNode, parent_world: list[list[float]]) -> None:
            current_world = multiply_matrix(parent_world, node.local_transform)
            world[node.instance_id] = current_world
            for child in by_parent.get(node.instance_id, []):
                visit(child, current_world)

        for root in by_parent.get(None, []):
            visit(root, identity_matrix())

        return world

