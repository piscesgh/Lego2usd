from __future__ import annotations

from collections import defaultdict

from backend.app.domain import AssemblyNode, AssemblyState
from backend.app.math3d import axis_to_usd_token, format_usd_matrix
from backend.app.services.assembly_service import AssemblyService
from backend.app.services.part_registry import PartRegistry


class UsdExporter:
    def __init__(self, registry: PartRegistry, assembly_service: AssemblyService) -> None:
        self.registry = registry
        self.assembly_service = assembly_service

    def export(self, assembly: AssemblyState) -> str:
        children_by_parent: dict[str | None, list[AssemblyNode]] = defaultdict(list)
        for node in assembly.nodes:
            children_by_parent[node.parent_instance_id].append(node)

        lines: list[str] = ["#usda 1.0", "", 'def Xform "World"', "{"]
        path_by_instance: dict[str, str] = {}

        lines.append('    def Xform "Assembly"')
        lines.append("    {")

        def emit_node(node: AssemblyNode, indent: int, parent_path: str) -> None:
            part = self.registry.get_part(node.sku)
            prim_name = self._prim_name(node)
            prim_path = f"{parent_path}/{prim_name}"
            path_by_instance[node.instance_id] = prim_path
            geometry_reference = part.geometry_asset.replace(".dat", ".usd")
            prefix = " " * indent
            lines.append(f'{prefix}def Xform "{prim_name}" (')
            lines.append(f'{prefix}    references = @./parts/{geometry_reference}@')
            lines.append(f"{prefix})")
            lines.append(f"{prefix}{{")
            lines.append(
                f"{prefix}    matrix4d xformOp:transform = "
                f"{format_usd_matrix(node.local_transform)}"
            )
            lines.append(f'{prefix}    uniform token[] xformOpOrder = ["xformOp:transform"]')
            for child in children_by_parent.get(node.instance_id, []):
                emit_node(child, indent + 4, prim_path)
            lines.append(f"{prefix}}}")

        for root in children_by_parent.get(None, []):
            emit_node(root, 8, "/World/Assembly")

        lines.append("    }")
        lines.append("")

        for connection in assembly.connections:
            if connection.joint_type != "revolute":
                continue
            source_node = next(
                node for node in assembly.nodes if node.instance_id == connection.parent_instance_id
            )
            axis = self.registry.get_port(source_node.sku, connection.parent_port_id).axis
            joint_name = f"Joint_{connection.child_instance_id}"
            lines.append(f'    def PhysicsRevoluteJoint "{joint_name}"')
            lines.append("    {")
            lines.append(
                f'        uniform token physics:axis = "{axis_to_usd_token(axis)}"'
            )
            lines.append(
                f"        rel physics:body0 = <{path_by_instance[connection.parent_instance_id]}>"
            )
            lines.append(
                f"        rel physics:body1 = <{path_by_instance[connection.child_instance_id]}>"
            )
            lines.append("        float physics:lowerLimit = -180")
            lines.append("        float physics:upperLimit = 180")
            lines.append("    }")
            lines.append("")

        lines.append("}")
        return "\n".join(lines).strip() + "\n"

    def _prim_name(self, node: AssemblyNode) -> str:
        safe_sku = node.sku.replace("-", "_")
        return f"Part_{safe_sku}_{node.instance_id}"

