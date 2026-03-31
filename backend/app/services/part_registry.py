from __future__ import annotations

from backend.app.domain import PartDefinition, PortDefinition
from backend.app.math3d import translation_matrix


def _port(
    port_id: str,
    *,
    kind: str,
    family: str,
    position: tuple[float, float, float],
    compatible_families: list[str],
    auto_connector_rule: str,
    joint_behavior: str,
    axis: tuple[float, float, float] | None = None,
) -> PortDefinition:
    return PortDefinition(
        id=port_id,
        kind=kind,
        family=family,
        local_transform=translation_matrix(*position),
        compatible_families=compatible_families,
        auto_connector_rule=auto_connector_rule,
        joint_behavior=joint_behavior,
        axis=axis,
    )


class PartRegistry:
    def __init__(self) -> None:
        self._parts = self._build_parts()

    def _build_parts(self) -> dict[str, PartDefinition]:
        return {
            "45601": PartDefinition(
                sku="45601",
                label="Spike Prime Hub",
                category="hub",
                geometry_asset="45601c01.dat",
                search_aliases=["spike hub", "hub"],
                render_size=(72.0, 44.0, 36.0),
                ports=[
                    _port(
                        "left_mount_1",
                        kind="structural",
                        family="technic_hole",
                        position=(-36.0, 0.0, 0.0),
                        compatible_families=["technic_hole", "axle_output"],
                        auto_connector_rule="implicit_pin",
                        joint_behavior="fixed",
                    ),
                    _port(
                        "right_mount_1",
                        kind="structural",
                        family="technic_hole",
                        position=(36.0, 0.0, 0.0),
                        compatible_families=["technic_hole", "axle_output"],
                        auto_connector_rule="implicit_pin",
                        joint_behavior="fixed",
                    ),
                    _port(
                        "top_mount_1",
                        kind="structural",
                        family="technic_hole",
                        position=(0.0, 18.0, 0.0),
                        compatible_families=["technic_hole"],
                        auto_connector_rule="implicit_pin",
                        joint_behavior="fixed",
                    ),
                    _port(
                        "front_mount_1",
                        kind="structural",
                        family="technic_hole",
                        position=(0.0, 0.0, 18.0),
                        compatible_families=["technic_hole"],
                        auto_connector_rule="implicit_pin",
                        joint_behavior="fixed",
                    ),
                ],
            ),
            "45602": PartDefinition(
                sku="45602",
                label="Large Motor",
                category="motor_large",
                geometry_asset="54675.dat",
                search_aliases=["large motor", "large angular motor"],
                render_size=(56.0, 28.0, 28.0),
                ports=[
                    _port(
                        "body_mount_1",
                        kind="structural",
                        family="technic_hole",
                        position=(-28.0, 0.0, 0.0),
                        compatible_families=["technic_hole"],
                        auto_connector_rule="implicit_pin",
                        joint_behavior="fixed",
                    ),
                    _port(
                        "body_mount_2",
                        kind="structural",
                        family="technic_hole",
                        position=(28.0, 0.0, 0.0),
                        compatible_families=["technic_hole"],
                        auto_connector_rule="implicit_pin",
                        joint_behavior="fixed",
                    ),
                    _port(
                        "output_axle",
                        kind="motor_output",
                        family="axle_output",
                        position=(0.0, 0.0, 18.0),
                        compatible_families=["technic_hole"],
                        auto_connector_rule="implicit_axle",
                        joint_behavior="revolute",
                        axis=(0.0, 0.0, 1.0),
                    ),
                ],
            ),
            "45603": PartDefinition(
                sku="45603",
                label="Medium Motor",
                category="motor_medium",
                geometry_asset="54696p01.dat",
                search_aliases=["medium motor", "medium angular motor"],
                render_size=(40.0, 24.0, 24.0),
                ports=[
                    _port(
                        "body_mount_1",
                        kind="structural",
                        family="technic_hole",
                        position=(-20.0, 0.0, 0.0),
                        compatible_families=["technic_hole"],
                        auto_connector_rule="implicit_pin",
                        joint_behavior="fixed",
                    ),
                    _port(
                        "body_mount_2",
                        kind="structural",
                        family="technic_hole",
                        position=(20.0, 0.0, 0.0),
                        compatible_families=["technic_hole"],
                        auto_connector_rule="implicit_pin",
                        joint_behavior="fixed",
                    ),
                    _port(
                        "output_axle",
                        kind="motor_output",
                        family="axle_output",
                        position=(0.0, 0.0, 16.0),
                        compatible_families=["technic_hole"],
                        auto_connector_rule="implicit_axle",
                        joint_behavior="revolute",
                        axis=(0.0, 0.0, 1.0),
                    ),
                ],
            ),
            "6016154": PartDefinition(
                sku="6016154",
                label="5x7 Frame",
                category="frame",
                geometry_asset="64179.dat",
                search_aliases=["5x7 frame", "frame"],
                render_size=(60.0, 12.0, 44.0),
                ports=[
                    _port(
                        "frame_left_top",
                        kind="structural",
                        family="technic_hole",
                        position=(-30.0, 0.0, -22.0),
                        compatible_families=["technic_hole", "axle_output"],
                        auto_connector_rule="implicit_pin",
                        joint_behavior="fixed",
                    ),
                    _port(
                        "frame_right_top",
                        kind="structural",
                        family="technic_hole",
                        position=(30.0, 0.0, -22.0),
                        compatible_families=["technic_hole", "axle_output"],
                        auto_connector_rule="implicit_pin",
                        joint_behavior="fixed",
                    ),
                    _port(
                        "frame_left_bottom",
                        kind="structural",
                        family="technic_hole",
                        position=(-30.0, 0.0, 22.0),
                        compatible_families=["technic_hole", "axle_output"],
                        auto_connector_rule="implicit_pin",
                        joint_behavior="fixed",
                    ),
                    _port(
                        "frame_right_bottom",
                        kind="structural",
                        family="technic_hole",
                        position=(30.0, 0.0, 22.0),
                        compatible_families=["technic_hole", "axle_output"],
                        auto_connector_rule="implicit_pin",
                        joint_behavior="fixed",
                    ),
                    _port(
                        "frame_center_left",
                        kind="structural",
                        family="technic_hole",
                        position=(-30.0, 0.0, 0.0),
                        compatible_families=["technic_hole", "axle_output"],
                        auto_connector_rule="implicit_pin",
                        joint_behavior="fixed",
                    ),
                    _port(
                        "frame_center_right",
                        kind="structural",
                        family="technic_hole",
                        position=(30.0, 0.0, 0.0),
                        compatible_families=["technic_hole", "axle_output"],
                        auto_connector_rule="implicit_pin",
                        joint_behavior="fixed",
                    ),
                ],
            ),
            "6271152": PartDefinition(
                sku="6271152",
                label="Double Angular Beam",
                category="beam",
                geometry_asset="32009.dat",
                search_aliases=["double angular beam", "bent beam"],
                render_size=(68.0, 12.0, 28.0),
                ports=[
                    _port(
                        "beam_end_a",
                        kind="structural",
                        family="technic_hole",
                        position=(-34.0, 0.0, 0.0),
                        compatible_families=["technic_hole", "axle_output"],
                        auto_connector_rule="implicit_pin",
                        joint_behavior="fixed",
                    ),
                    _port(
                        "beam_center",
                        kind="structural",
                        family="technic_hole",
                        position=(0.0, 0.0, 0.0),
                        compatible_families=["technic_hole", "axle_output"],
                        auto_connector_rule="implicit_pin",
                        joint_behavior="fixed",
                    ),
                    _port(
                        "beam_end_b",
                        kind="structural",
                        family="technic_hole",
                        position=(34.0, 0.0, 0.0),
                        compatible_families=["technic_hole", "axle_output"],
                        auto_connector_rule="implicit_pin",
                        joint_behavior="fixed",
                    ),
                    _port(
                        "beam_upper",
                        kind="structural",
                        family="technic_hole",
                        position=(18.0, 18.0, 0.0),
                        compatible_families=["technic_hole"],
                        auto_connector_rule="implicit_pin",
                        joint_behavior="fixed",
                    ),
                ],
            ),
        }

    def search(self, query: str = "") -> list[PartDefinition]:
        normalized = query.strip().lower()
        parts = list(self._parts.values())
        if not normalized:
            return sorted(parts, key=lambda part: part.sku)

        exact = [
            part
            for part in parts
            if part.sku.lower() == normalized
            or any(alias.lower() == normalized for alias in part.search_aliases)
        ]
        prefix = [
            part
            for part in parts
            if part not in exact
            and (
                part.sku.lower().startswith(normalized)
                or any(alias.lower().startswith(normalized) for alias in part.search_aliases)
            )
        ]
        contains = [
            part
            for part in parts
            if part not in exact
            and part not in prefix
            and any(normalized in alias.lower() for alias in part.search_aliases)
        ]
        return exact + sorted(prefix, key=lambda part: part.sku) + sorted(
            contains, key=lambda part: part.sku
        )

    def get_part(self, sku: str) -> PartDefinition:
        try:
            return self._parts[sku]
        except KeyError as error:
            raise KeyError(f"Unsupported SKU: {sku}") from error

    def get_port(self, sku: str, port_id: str) -> PortDefinition:
        part = self.get_part(sku)
        for port in part.ports:
            if port.id == port_id:
                return port
        raise KeyError(f"Unsupported port '{port_id}' for SKU '{sku}'")

