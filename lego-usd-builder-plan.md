# LEGO-to-USD Builder: Implementation Plan

A desktop/web tool for searching LEGO Spike Prime parts by ID, interactively connecting them, and exporting Isaac Sim-compatible USD files with articulated joints.

---

## Architecture Overview

```
┌──────────────────────────────────────────────┐
│  Frontend  (React + Three.js)                │
│  Search bar · 3D viewer · Connection UI      │
├──────────────────────────────────────────────┤
│  Backend   (Python FastAPI)                  │
│  Part search · Connection detection · Export │
├──────────────────────────────────────────────┤
│  Data Layer                                  │
│  LDraw library · Connection catalog · SQLite │
│  OpenUSD (pxr) · Geometry cache              │
└──────────────────────────────────────────────┘
```

---

## Tech Stack

| Layer            | Choice                  | Rationale                                                  |
| ---------------- | ----------------------- | ---------------------------------------------------------- |
| Backend          | Python + FastAPI        | Native OpenUSD bindings (`pxr`), great for geometry math   |
| Database         | SQLite                  | Simple, no infra needed, stores part catalog + assemblies  |
| 3D Frontend      | React + Three.js        | Lightweight WebGL, large community, LDraw loaders exist    |
| USD Generation   | OpenUSD `pxr`           | Official NVIDIA-supported, articulation support             |
| LDraw Parsing    | `ldraw3` or custom      | Recursive part refs flattened to meshes                     |
| Geometry Format  | Pre-cached `.usd`/part  | Avoids runtime conversion overhead                          |
| Build Tool       | Vite                    | Fast HMR, optimized for 3D apps                            |
| State Management | Zustand or Redux Toolkit| Assembly tree state, viewport state                         |

---

## Core Modules

### Module 1: Part Discovery Service

**File**: `/backend/services/part_service.py`

Indexes the LDraw parts library on startup, caches part metadata, and provides full-text search by part ID, name, or category. Geometry is lazy-loaded on demand.

**Data Model**:

```python
@dataclass
class PartMetadata:
    id: str                          # LDraw part ID (e.g., "3001.dat")
    name: str                        # "Brick 2 x 4"
    category: str                    # "Brick", "Beam", "Motor", etc.
    color: str                       # Color code
    bbox: BoundingBox                # Min/max coordinates
    connections: list[Connection]    # All connection points
    geometry_path: str               # Path to cached USD or OBJ
    is_motor: bool                   # Whether this part is a motor
    motor_type: str | None           # "LargeMotor", "SmallMotor", etc.
```

### Module 2: Connection Detector

**File**: `/backend/services/connection_detector.py`

Detects all valid connection points on each part by parsing LDraw geometry for known sub-primitives (`stud.dat`, `axlehole.dat`, etc.). For any two selected parts, it returns all compatible connection pairs ranked by common building patterns.

**Connection Point Model**:

```python
@dataclass
class Connection:
    type: ConnectionType             # STUD, AXLE_HOLE, PIN_HOLE, MOTOR_SOCKET, BEAM_END
    position: tuple[float, float, float]  # Local coordinates
    orientation: tuple[float, float, float]  # Normal vector / rotation axis
    compatible_with: list[ConnectionType]    # What can connect here
```

**Detection Algorithm**:

1. Load Part A geometry, extract connection points
2. Load Part B geometry, extract connection points
3. For each `(point_a, point_b)` pair:
   - Check type compatibility (stud-to-hole, pin-to-pin-hole, etc.)
   - Compute alignment transform
   - Check for geometric collision/overlap
   - If valid, add to candidates list
4. Rank candidates by gravity direction, symmetry, and typical patterns

### Module 3: Assembly Tree Manager

**File**: `/backend/services/assembly_service.py`

Maintains the hierarchical assembly structure with parent-child relationships, transforms, and joint metadata.

**Assembly Node Model**:

```python
@dataclass
class AssemblyNode:
    part_id: str
    instance_id: str                # Unique within assembly
    local_transform: Matrix4x4      # Relative to parent
    global_transform: Matrix4x4     # Cached world-space
    children: list[AssemblyNode]
    parent: AssemblyNode | None
    connection_info: ConnectionInfo | None

@dataclass
class ConnectionInfo:
    parent_connection: Connection
    child_connection: Connection
    joint_type: JointType           # FIXED, REVOLUTE, CONTINUOUS
    motor_power: int | None
    torque_limit: float | None
    speed_limit: float | None
```

### Module 4: USD Exporter

**File**: `/backend/services/usd_exporter.py`

Walks the assembly tree depth-first and generates a `.usda` file using Python `pxr` bindings. Fixed connections become rigid Xform hierarchies; motors become `PhysicsRevoluteJoint` articulations.

**Process**:

1. Traverse assembly tree depth-first
2. For each node:
   - Reference cached part `.usd` asset
   - Apply local transform via `xformOp:transform`
   - If motor: create `PhysicsRevoluteJoint` with axis + limits
3. Build prim hierarchy respecting parent-child relationships
4. Apply physics properties (mass, friction, restitution)
5. Export with proper layer structure for Isaac Sim

**Example USD Output**:

```usda
#usda 1.0

def Xform "World"
{
    def Xform "SPIKE_Robot"
    {
        def Xform "Hub" (
            references = @./parts/37000_hub.usd@
        )
        {
            matrix4d xformOp:transform = ((...))
            uniform token[] xformOpOrder = ["xformOp:transform"]

            def Xform "Motor_A" (
                references = @./parts/45028_large_motor.usd@
            )
            {
                matrix4d xformOp:transform = ((...))
                uniform token[] xformOpOrder = ["xformOp:transform"]
            }
        }
    }

    def PhysicsRevoluteJoint "Motor_A_Joint"
    {
        uniform token physics:axis = "Z"
        rel physics:body0 = </World/SPIKE_Robot/Hub>
        rel physics:body1 = </World/SPIKE_Robot/Hub/Motor_A>
        float physics:lowerLimit = -180
        float physics:upperLimit = 180
    }
}
```

### Module 5: 3D Viewer (Frontend)

**File**: `/frontend/components/LegoViewer.tsx`

React + Three.js (React Three Fiber) component that renders parts with connection points as interactive markers, handles selection, shows snap previews, and visualizes the full assembly.

**Interaction Flow**:

1. User searches for Part A → renders in viewer with connection points highlighted
2. User clicks a connection point on Part A
3. User searches for Part B → compatible points for A's selected point are shown
4. User clicks a compatible point on Part B → live preview of the snap
5. User confirms → assembly tree updates, view refreshes
6. Repeat until build is complete
7. Click "Export USD" → download `.usda` file

---

## Spike Prime Motor Mapping

| Motor                     | Part ID | RPM  | Torque    | USD Joint Type               |
| ------------------------- | ------- | ---- | --------- | ---------------------------- |
| Large Motor               | 45028   | ~160 | ~0.35 Nm  | `RevoluteJoint`, continuous  |
| Medium / Small Motor      | 45009   | ~240 | ~0.18 Nm  | `RevoluteJoint`, ±180°       |
| Medium Angular Servo      | 45055   | ~135 | ~0.20 Nm  | `RevoluteJoint`, position    |

---

## Spike Prime Part Categories

| Part Type | Connection Types               | Example                     |
| --------- | ------------------------------ | --------------------------- |
| Beam      | Axle holes, pin holes          | 32525 (Beam 1x9)            |
| Brick     | Studs                          | 3001 (Brick 2x4)            |
| Plate     | Studs (thinner)                | 3022 (Plate 2x2)            |
| Gear      | Axle holes                     | 94925 (Gear 16-tooth)        |
| Motor     | Beam connector + motor socket  | 45028 (Large Motor)          |
| Hub       | Pin connectors                 | 37000 (Spike Prime Hub)      |

---

## Connection Point Catalog (Example)

```json
{
  "3001": {
    "name": "Brick 2 x 4",
    "studs": [
      { "position": [0, 8, 0], "orientation": [0, 1, 0] },
      { "position": [8, 8, 0], "orientation": [0, 1, 0] }
    ]
  },
  "32525": {
    "name": "Beam 1 x 9",
    "axle_holes": [
      { "position": [0, 0, 0], "axis": [1, 0, 0] },
      { "position": [72, 0, 0], "axis": [1, 0, 0] }
    ],
    "pin_holes": [
      { "position": [8, 0, 0], "axis": [1, 0, 0] },
      { "position": [16, 0, 0], "axis": [1, 0, 0] }
    ]
  },
  "45028": {
    "name": "Large Motor",
    "motor_socket": [
      { "position": [0, 0, 0], "axis": [0, 0, 1] }
    ],
    "beam_connector": [
      { "position": [0, -8, 0], "axis": [0, 1, 0] }
    ]
  }
}
```

---

## Database Schema

```sql
CREATE TABLE parts (
    id TEXT PRIMARY KEY,
    name TEXT,
    category TEXT,
    color_code INT,
    bbox_min_x REAL, bbox_min_y REAL, bbox_min_z REAL,
    bbox_max_x REAL, bbox_max_y REAL, bbox_max_z REAL,
    geometry_hash TEXT,
    is_motor BOOLEAN DEFAULT FALSE,
    motor_type TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE connection_points (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    part_id TEXT NOT NULL,
    type TEXT NOT NULL,
    position_x REAL, position_y REAL, position_z REAL,
    orientation_x REAL, orientation_y REAL, orientation_z REAL,
    axis_x REAL, axis_y REAL, axis_z REAL,
    compatible_types TEXT,
    FOREIGN KEY (part_id) REFERENCES parts(id)
);

CREATE TABLE assemblies (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    created_at TIMESTAMP,
    updated_at TIMESTAMP,
    data JSON
);

CREATE TABLE assembly_nodes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    assembly_id INTEGER NOT NULL,
    part_id TEXT NOT NULL,
    instance_id TEXT,
    parent_node_id INTEGER,
    transform_matrix BLOB,
    connection_type TEXT,
    is_motor_joint BOOLEAN,
    motor_power INT,
    FOREIGN KEY (assembly_id) REFERENCES assemblies(id),
    FOREIGN KEY (part_id) REFERENCES parts(id),
    FOREIGN KEY (parent_node_id) REFERENCES assembly_nodes(id)
);
```

---

## API Specification

| Endpoint                                 | Method | Description                          |
| ---------------------------------------- | ------ | ------------------------------------ |
| `/api/parts/search?query=3001&limit=20`  | GET    | Search parts by ID or name           |
| `/api/parts/{partId}/geometry`           | GET    | Get part 3D geometry (USD/OBJ)       |
| `/api/parts/{partId}/connections`        | GET    | List all connection points on a part |
| `/api/connections/validate`              | POST   | Validate a connection between two parts |
| `/api/assemblies`                        | POST   | Create a new assembly                |
| `/api/assemblies/{id}/nodes`             | POST   | Add a part to an assembly            |
| `/api/assemblies/{id}/export?format=usda`| POST   | Export assembly as USD               |

---

## Data Flow

```
User searches "3001"
    │
    ▼
[Frontend] GET /api/parts/search ──▶ [Part Service] query DB + LDraw index
    │
    ▼
[Frontend] renders part in 3D viewer, highlights connection points
    │
    ▼
User clicks connection point on Part A
    │
    ▼
User searches & loads Part B
    │
    ▼
[Frontend] POST /api/connections/validate
    │
    ▼
[Connection Detector] analyzes all point pairs, returns ranked candidates
    │
    ▼
[Frontend] shows snap preview (Part B transformed to align with Part A)
    │
    ▼
User confirms connection
    │
    ▼
[Assembly Service] creates node, updates tree
    │
    ▼
User clicks "Export USD"
    │
    ▼
[USD Exporter] traverses tree ──▶ generates .usda ──▶ download
```

---

## Phased Development Roadmap

### Phase 1: Foundation (Weeks 1-3)

**Goal**: Core infrastructure + single part visualization

- Project scaffolding (FastAPI backend + React frontend)
- Download and index LDraw parts library
- Parse `.ldr` / `.dat` files into geometry assets
- Build SQLite part catalog
- React frontend with Three.js 3D viewer
- Basic REST API: search and geometry endpoints
- **Milestone**: User can search by part ID and see a 3D-rendered part

### Phase 2: Connection Detection (Weeks 4-6)

**Goal**: Detect connection points, validate compatibility

- Connection detector service (LDraw primitive recognition)
- Hardcoded catalog for ~40 Spike Prime parts (JSON)
- Heuristic fallback for other parts (stud/hole geometry analysis)
- Connection validation API
- Frontend: highlight connection points as clickable markers
- Frontend: show snap preview when two points are selected
- **Milestone**: User can select connections on two parts and see a valid preview

### Phase 3: Assembly & Serialization (Weeks 7-9)

**Goal**: Multi-part assemblies with persistent state

- Assembly tree manager (CRUD, transforms)
- Session persistence (save/load to SQLite)
- Frontend assembly builder UI
- Assembly hierarchy visualization (tree view)
- Undo/redo stack
- Motor joint configuration UI (mark connections as motors, set limits)
- **Milestone**: User can build a 5+ part assembly and save it

### Phase 4: USD Export (Weeks 10-12)

**Goal**: Generate Isaac Sim-compatible USD files

- USD exporter using `pxr` Python bindings
- Xform hierarchy with mesh references
- `PhysicsRevoluteJoint` for motors (axis, limits, drive)
- Physics properties: mass, center-of-mass, friction, restitution
- Export download UI with USD code preview
- Validation: import into Isaac Sim, verify joints work
- **Milestone**: Exported `.usda` opens in Isaac Sim with working motor joints

### Phase 5: Polish & Scale (Weeks 13-16)

**Goal**: Performance, UX, deployment

- Drag-and-drop parts in viewport
- Geometry LOD (Level of Detail) for large builds
- Instancing for repeated parts
- Snap-to-grid, copy/paste sub-assemblies
- Unit tests (detection, transforms, USD generation)
- Integration tests (full search-connect-export pipeline)
- Docker containerization
- User documentation
- **Milestone**: Production-ready tool handling 100+ part assemblies

---

## Critical Technical Challenges

### LDraw Parsing Complexity

LDraw files are recursive (parts reference sub-parts via matrix transforms). Pre-flatten all geometry at index time and cache as `.usd` assets. Use `ldraw3` Python library or implement a custom recursive parser.

### Connection Detection at Scale

Geometry-based detection is hard to generalize. Start with a handcrafted JSON catalog for the ~40 Spike Prime parts you actually need (Tier 1), add heuristic detection based on normal vectors and shape primitives (Tier 2), and optionally add ML-based recognition later (Tier 3).

### Coordinate System Alignment

LDraw, LEGO stud pitch, and USD units differ. Establish a canonical transform early:

- 1 LDraw unit = 0.4 mm
- 1 stud = 8 mm horizontal, 9.6 mm vertical
- USD uses meters, Y-up
- Apply consistent transforms throughout the pipeline

### USD Articulation Complexity

OpenUSD's physics and articulation APIs have a steep learning curve. Start with basic Xform hierarchy, then add `PhysicsRevoluteJoint` for motors. Test incrementally: single part → rigid assembly → articulated assembly.

### WebGL Performance

100+ part builds can strain the browser. Use geometry LOD (detailed mesh only for selected parts), instancing for repeated parts, frustum culling, and Web Workers for geometry processing.

---

## Deployment

### Development

```yaml
# docker-compose.yml
services:
  backend:
    build: ./backend
    ports: ["8000:8000"]
    volumes: ["./ldraw_library:/data/ldraw"]
  frontend:
    build: ./frontend
    ports: ["5173:5173"]
  db:
    image: sqlite  # or use file-based SQLite in backend volume
```

### Production Options

- **Web**: Backend on cloud (AWS/GCP), frontend on CDN (Vercel/Netlify)
- **Desktop**: Wrap with Tauri or Electron for offline use
- **Hybrid**: Web frontend + local Python backend (best for USD generation)

---

## Testing Strategy

- **Unit tests**: Connection detection logic, transform math, USD generation
- **Integration tests**: Full pipeline (search → connect → export → validate)
- **Reference models**: Test against known Spike Prime builds (simple gear train, motor-driven arm, complete robot)
- **Isaac Sim validation**: Import every exported USD, verify joint limits and motor axes, run physics simulation
