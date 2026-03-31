# LEGO-to-USD Builder: Curated V1 Implementation Plan

A browser-based assembly builder for a curated set of LEGO Spike Prime parts. Users search supported parts by ID, place them in a 3D scene, click visible ports on two parts to connect them, preview the snap, and export the resulting assembly as Isaac Sim-compatible USD.

This v1 plan is intentionally narrow:

- Search is ID-first with exact and prefix matching.
- The supported catalog is limited to five initial user-facing SKUs.
- Connector pieces are skipped entirely and resolved implicitly by port compatibility rules.
- Counts are not enforced in v1. Users may place unlimited instances of the supported parts.
- The backend remains Python-based for geometry processing and USD export.

---

## Product Summary

### User Goal

Build a robot topology interactively in the web app by searching a supported part ID, placing the part, and connecting it to another part by clicking curated ports on both parts.

### V1 Scope

- Web UI for search, placement, connection preview, assembly editing, and export
- Python backend for curated part registry, connection validation, and USD export
- Curated part support for five user-facing SKUs only
- Fixed joints for structural mounts
- Revolute joints only when a connection uses a motor output port
- Save/load as assembly JSON

### Out Of Scope For V1

- Whole-library LEGO or Spike Prime part coverage
- Runtime geometry heuristics for discovering connection points
- Explicit connector part placement
- Inventory or BOM enforcement
- Database-backed persistence is not required in v1

---

## Architecture Overview

```text
┌──────────────────────────────────────────────┐
│ Frontend (React + Three.js / R3F)           │
│ Search UI · 3D viewer · Port picking        │
│ Snap preview · Assembly state               │
├──────────────────────────────────────────────┤
│ Backend (Python + FastAPI)                  │
│ Part registry · Connection validation       │
│ Assembly JSON serialization · USD export    │
├──────────────────────────────────────────────┤
│ Data / Assets                               │
│ Curated LDraw geometry · Port registry      │
│ SKU-to-geometry mapping                     │
└──────────────────────────────────────────────┘
```

---

## Tech Stack

| Layer | Choice | Rationale |
| --- | --- | --- |
| Frontend | React + Vite | Fast iteration and a clean component model |
| 3D Viewer | Three.js + React Three Fiber | Good fit for interactive part placement and port picking |
| Backend | Python + FastAPI | Works well with USD tooling and lightweight APIs |
| Geometry Source | LDraw | Canonical source for curated LEGO geometry in v1 |
| USD Generation | OpenUSD `pxr` | Direct control over Isaac Sim-compatible output |
| Persistence | JSON | Sufficient for v1 save/load without database complexity |
| State Management | Zustand or equivalent | Simple assembly/editor state handling |

---

## Initial Supported Parts

LDraw is the canonical geometry source for v1. User-facing IDs stay stable even when the underlying mesh asset uses a different design ID.

| User-Facing SKU | Part Label | Internal Geometry Asset | Notes |
| --- | --- | --- | --- |
| `45601` | Spike Prime Hub | `45601c01.dat` | Use the hub assembly asset as the default render source |
| `45602` | Large Motor | `54675.dat` | Use the motor body asset without cable-included variant |
| `45603` | Medium Motor | `54696p01.dat` | Use the motor body asset without cable-included variant |
| `6016154` | 5x7 Frame | `64179.dat` | `6016154` is an element/color ID mapped to design ID `64179` |
| `6271152` | Double Angular Beam | `32009.dat` | `6271152` is an element/color ID mapped to design ID `32009` |

### Search Behavior

- Search is optimized for numeric part IDs.
- Exact matches rank first.
- Prefix matches rank second.
- Optional curated aliases may be shown in the UI, but ID search is the primary interaction.

---

## Core Data Model

### Part Registry

Each supported part is defined by a curated registry entry. This registry is the only source of truth for searchable parts in v1.

```python
@dataclass
class PartDefinition:
    sku: str
    label: str
    category: str                    # hub, motor_large, motor_medium, frame, beam
    geometry_asset: str              # LDraw filename
    search_aliases: list[str]
    ports: list["PortDefinition"]
```

### Port Registry

Ports are authored by hand for each supported part. V1 does not attempt to detect ports from geometry at runtime.

```python
@dataclass
class PortDefinition:
    id: str
    kind: str                        # structural | motor_output
    family: str                      # technic_hole | axle_output
    local_transform: Matrix4x4       # Authored in canonical part space
    compatible_families: list[str]
    auto_connector_rule: str         # implicit_pin | implicit_axle
    joint_behavior: str              # fixed | revolute
```

### Assembly State

Assembly state should remain lightweight and serializable as JSON in v1.

```python
@dataclass
class AssemblyNode:
    instance_id: str
    sku: str
    local_transform: Matrix4x4
    parent_instance_id: str | None
    parent_port_id: str | None
    child_port_id: str | None

@dataclass
class ConnectionRecord:
    parent_instance_id: str
    child_instance_id: str
    parent_port_id: str
    child_port_id: str
    joint_type: str                  # fixed | revolute
    auto_connector_rule: str
```

---

## Core Modules

### Module 1: Curated Part Registry

**File**: `/backend/services/part_registry.py`

Responsibilities:

- Expose the five initial supported SKUs
- Map user-facing SKUs to internal LDraw geometry assets
- Return curated port definitions for each part
- Support ID-first exact and prefix search

Non-goals:

- No indexing of the entire LDraw library
- No fallback search over unrelated LEGO parts

### Module 2: Port Compatibility And Connection Preview

**File**: `/backend/services/connection_service.py`

Responsibilities:

- Validate whether two selected ports are compatible
- Resolve the child transform required to align the target port to the source port
- Return preview metadata for the frontend
- Decide whether the resulting connection is `fixed` or `revolute`

Rules:

- Connector pieces are implicit and skipped
- Structural ports produce fixed joints
- Motor body mount ports produce fixed joints
- Only motor output ports produce revolute joints

### Module 3: Assembly Service

**File**: `/backend/services/assembly_service.py`

Responsibilities:

- Maintain the assembly graph
- Add placed parts and committed connections
- Serialize and deserialize assembly JSON
- Support repeated instances of the same SKU

V1 storage choice:

- Keep assembly state in memory during editing
- Save and load plain JSON documents
- Do not require SQLite for v1

### Module 4: USD Exporter

**File**: `/backend/services/usd_exporter.py`

Responsibilities:

- Walk the assembly graph
- Reference curated part geometry assets
- Emit fixed transforms for structural connections
- Emit revolute joints only for motor output connections
- Export an Isaac Sim-compatible `.usda` file

USD semantics:

- No connector prims
- No hidden connector geometry
- No cable geometry requirement in v1

### Module 5: Builder UI And Viewer

**File**: `/frontend/components/LegoBuilder.tsx`

Responsibilities:

- Search supported parts by ID
- Place parts into the scene
- Render clickable ports for the selected or hovered part
- Show a snap preview before confirming a connection
- Display the current assembly and allow export

---

## Interaction Flow

The connection flow for v1 is fixed and should be implemented exactly as follows:

1. User searches a supported part by ID.
2. User places the part in the scene.
3. User clicks a visible port on an existing part.
4. User clicks a compatible visible port on the new part.
5. The app shows a snap preview.
6. User confirms the connection.
7. The assembly updates.
8. User exports USD.

### UX Notes

- The first placed part starts at the world origin.
- The UI should clearly distinguish structural ports from motor output ports.
- Invalid port combinations should be rejected before the assembly mutates.
- If a port pair supports multiple discrete orientations, the backend may return ordered variants and the UI should default to the first valid variant.

---

## Connection Semantics

### Port Families

V1 needs only the families required for the initial supported catalog:

- `technic_hole`
- `axle_output`

### Compatibility Rules

- `technic_hole` connects to `technic_hole` through an implicit structural connector rule
- `axle_output` connects to a compatible structural receiving port defined in the curated registry
- Compatibility is authored per port definition, not inferred from generic geometry analysis

### Connector Handling

Connector pieces are skipped automatically:

- They are not searchable parts
- They are not placeable scene items
- They are not stored as assembly nodes
- They are not exported as USD prims

Instead, each valid port pairing carries an `auto_connector_rule` such as `implicit_pin` or `implicit_axle`.

---

## API Surface

| Endpoint | Method | Description |
| --- | --- | --- |
| `/api/parts?query=456` | GET | Return supported parts using exact and prefix ID matching |
| `/api/parts/{sku}` | GET | Return metadata, geometry asset, and curated port definitions for a supported part |
| `/api/assemblies/preview-connection` | POST | Validate a selected port pair and return resolved transform and joint metadata |
| `/api/assemblies/connect` | POST | Commit a validated connection and return the updated assembly JSON |
| `/api/assemblies/export/usd` | POST | Export the current assembly to USD |

### Preview Request Shape

```json
{
  "source_instance_id": "node_1",
  "source_port_id": "left_mount_1",
  "target_sku": "45602",
  "target_port_id": "body_mount_2"
}
```

### Preview Response Shape

```json
{
  "compatible": true,
  "joint_type": "fixed",
  "resolved_transform": [[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]],
  "auto_connector_rule": "implicit_pin"
}
```

---

## Data Flow

```text
User searches "45602"
    |
    v
[Frontend] GET /api/parts?query=45602
    |
    v
[Backend] returns curated part metadata + geometry mapping
    |
    v
User places part in scene
    |
    v
User clicks a source port on an existing part
    |
    v
User clicks a target port on the new part
    |
    v
[Frontend] POST /api/assemblies/preview-connection
    |
    v
[Backend] validates curated port pair, resolves transform, returns joint type
    |
    v
[Frontend] shows snap preview
    |
    v
User confirms
    |
    v
[Frontend] POST /api/assemblies/connect
    |
    v
[Assembly Service] updates JSON assembly state
    |
    v
User clicks Export
    |
    v
[Frontend] POST /api/assemblies/export/usd
    |
    v
[USD Exporter] writes .usda with fixed and revolute joints
```

---

## USD Export Behavior

### Fixed Connections

- Structural-to-structural mounts export as fixed transforms or fixed joints
- Motor body mounts also export as fixed transforms or fixed joints

### Revolute Connections

- Only connections that use a `motor_output` port export as revolute joints
- The exported joint axis comes from the curated motor output port definition

### Export Constraints

- No connector prims are written
- No extra helper parts are written
- The exported hierarchy should contain only the placed parts and their joint relationships

---

## Development Roadmap

### Phase 1: Curated Geometry Registry And Viewer

Goal:

- Load the five supported parts from the curated registry
- Render their geometry in the 3D viewer
- Support ID-first exact and prefix search

Milestone:

- User can search for `45601`, `45602`, `45603`, `6016154`, or `6271152` and view the selected part with its curated ports

### Phase 2: Click-To-Connect Builder And Preview

Goal:

- Allow users to place parts in the scene
- Let users click source and target ports
- Show a snap preview for valid connections

Milestone:

- User can build a multi-part topology interactively using visible ports

### Phase 3: Assembly State And JSON Save/Load

Goal:

- Persist the assembly as JSON
- Restore saved assemblies accurately
- Support repeated instances of the same SKU

Milestone:

- User can save and reload an assembly without losing topology or joint semantics

### Phase 4: USD Export

Goal:

- Export fixed and revolute joint relationships correctly
- Produce Isaac Sim-compatible USD

Milestone:

- Exported assemblies open in Isaac Sim with structural mounts fixed and motor output connections articulated

---

## Technical Challenges

### Stable SKU-To-Geometry Mapping

User-facing SKUs and geometry design IDs are not always the same. The registry must keep the public SKU stable while resolving to the correct internal asset.

### Correct Local Port Transforms

The most important authored data in v1 is the local transform for each curated port. These transforms must be measured once and kept stable because connection preview, assembly transforms, and USD export all depend on them.

### Coordinate System Alignment

LDraw coordinates, LEGO dimensions, and USD coordinates differ. Establish a canonical conversion early and apply it consistently to:

- Geometry import
- Port transforms
- Preview transform resolution
- USD export

### Motor Output Articulation Without Connectors

Because connectors are implicit, the articulation model must come from port semantics alone. The exporter cannot rely on explicit intermediate connector parts to define revolute behavior.

---

## Testing Strategy

- Unit tests for ID-first search ranking and SKU-to-geometry mapping
- Unit tests for port compatibility validation and transform resolution
- Unit tests for joint-type resolution, especially `motor_output` behavior
- Integration tests for the full flow: search -> place -> preview -> connect -> export
- Snapshot tests for saved assembly JSON
- Isaac Sim validation tests for exported USD

### Required V1 Scenarios

- Search returns only the five supported SKUs
- Exact ID matches rank ahead of prefix matches
- Counts are not enforced when placing repeated instances
- Invalid port pair selections are rejected without mutating assembly state
- Structural connections export as fixed
- Motor body mount connections export as fixed
- Only motor output connections export as revolute
- Exported USD contains no connector prims

---

## Acceptance Criteria

- The document describes a curated v1 builder rather than a broad general-purpose part platform
- The five supported SKUs are named explicitly anywhere the initial catalog is referenced
- Search is described as ID-first with exact and prefix matching
- Connector pieces are explicitly skipped and implicit
- Counts are explicitly not enforced in v1
- Only motor output connections are described as revolute in USD
