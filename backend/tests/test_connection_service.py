import unittest

from backend.app.domain import AssemblyState
from backend.app.services.assembly_service import AssemblyService
from backend.app.services.connection_service import ConnectionService
from backend.app.services.part_registry import PartRegistry


class ConnectionServiceTest(unittest.TestCase):
    def setUp(self) -> None:
        self.registry = PartRegistry()
        self.assembly_service = AssemblyService()
        self.connection_service = ConnectionService(self.registry)

    def test_structural_connection_is_fixed(self) -> None:
        assembly = AssemblyState()
        self.assembly_service.create_root(assembly, "45601")
        preview = self.connection_service.preview_connection(
            assembly,
            world_transforms=self.assembly_service.build_world_transforms(assembly),
            source_instance_id="node_1",
            source_port_id="left_mount_1",
            target_sku="45602",
            target_port_id="body_mount_1",
        )
        self.assertEqual(preview.joint_type, "fixed")
        self.assertEqual(preview.auto_connector_rule, "implicit_pin")

    def test_motor_output_connection_is_revolute(self) -> None:
        assembly = AssemblyState()
        self.assembly_service.create_root(assembly, "45602")
        preview = self.connection_service.preview_connection(
            assembly,
            world_transforms=self.assembly_service.build_world_transforms(assembly),
            source_instance_id="node_1",
            source_port_id="output_axle",
            target_sku="6016154",
            target_port_id="frame_center_left",
        )
        self.assertEqual(preview.joint_type, "revolute")
        self.assertEqual(preview.auto_connector_rule, "implicit_axle")


if __name__ == "__main__":
    unittest.main()

