export type Matrix4 = number[][];

export type PortDefinition = {
  id: string;
  kind: "structural" | "motor_output";
  family: "technic_hole" | "axle_output";
  local_transform: Matrix4;
  compatible_families: Array<"technic_hole" | "axle_output">;
  auto_connector_rule: string;
  joint_behavior: "fixed" | "revolute";
  axis: [number, number, number] | null;
};

export type PartSummary = {
  sku: string;
  label: string;
  category: string;
  geometry_asset: string;
  search_aliases: string[];
};

export type PartDefinition = PartSummary & {
  render_size: [number, number, number];
  ports: PortDefinition[];
};

export type AssemblyNode = {
  instance_id: string;
  sku: string;
  local_transform: Matrix4;
  parent_instance_id: string | null;
  parent_port_id: string | null;
  child_port_id: string | null;
};

export type ConnectionRecord = {
  parent_instance_id: string;
  child_instance_id: string;
  parent_port_id: string;
  child_port_id: string;
  joint_type: "fixed" | "revolute";
  auto_connector_rule: string;
};

export type AssemblyState = {
  nodes: AssemblyNode[];
  connections: ConnectionRecord[];
};

export type PreviewResponse = {
  compatible: boolean;
  joint_type: "fixed" | "revolute";
  auto_connector_rule: string;
  resolved_transform: Matrix4;
  resolved_local_transform: Matrix4;
  source_instance_id: string;
  source_port_id: string;
  target_sku: string;
  target_port_id: string;
  reason: string | null;
};

