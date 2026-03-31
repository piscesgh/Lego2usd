import { useEffect, useState } from "react";
import type { ChangeEvent } from "react";
import { Canvas } from "@react-three/fiber";
import { Grid, OrbitControls } from "@react-three/drei";
import type { AssemblyNode, AssemblyState, PartDefinition, PartSummary, PortDefinition, PreviewResponse } from "../types";
import { connectPart, exportUsd, getPart, previewConnection, searchParts } from "../api";

const EMPTY_ASSEMBLY: AssemblyState = { nodes: [], connections: [] };
const SCENE_SCALE = 40;

const CATEGORY_COLOR: Record<string, string> = {
  hub: "#214e74",
  motor_large: "#d95f32",
  motor_medium: "#cc7f3e",
  frame: "#4c6d3b",
  beam: "#75634a",
};

function matrixTranslation(matrix: number[][]): [number, number, number] {
  return [matrix[0]?.[3] ?? 0, matrix[1]?.[3] ?? 0, matrix[2]?.[3] ?? 0];
}

function worldTranslations(assembly: AssemblyState): Record<string, [number, number, number]> {
  const byParent = new Map<string | null, AssemblyNode[]>();
  for (const node of assembly.nodes) {
    const key = node.parent_instance_id ?? null;
    const entries = byParent.get(key) ?? [];
    entries.push(node);
    byParent.set(key, entries);
  }

  const world: Record<string, [number, number, number]> = {};

  function visit(node: AssemblyNode, parentTranslation: [number, number, number]) {
    const local = matrixTranslation(node.local_transform);
    const current: [number, number, number] = [
      parentTranslation[0] + local[0],
      parentTranslation[1] + local[1],
      parentTranslation[2] + local[2],
    ];
    world[node.instance_id] = current;
    for (const child of byParent.get(node.instance_id) ?? []) {
      visit(child, current);
    }
  }

  for (const root of byParent.get(null) ?? []) {
    visit(root, [0, 0, 0]);
  }

  return world;
}

function portColor(port: PortDefinition): string {
  return port.kind === "motor_output" ? "#d95f32" : "#214e74";
}

function downloadText(filename: string, contents: string) {
  const blob = new Blob([contents], { type: "text/plain;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = filename;
  anchor.click();
  URL.revokeObjectURL(url);
}

export function LegoBuilder() {
  const [query, setQuery] = useState("456");
  const [results, setResults] = useState<PartSummary[]>([]);
  const [partCache, setPartCache] = useState<Record<string, PartDefinition>>({});
  const [assembly, setAssembly] = useState<AssemblyState>(EMPTY_ASSEMBLY);
  const [sourceSelection, setSourceSelection] = useState<{ instanceId: string; portId: string } | null>(null);
  const [stagedSku, setStagedSku] = useState<string | null>(null);
  const [preview, setPreview] = useState<PreviewResponse | null>(null);
  const [status, setStatus] = useState<string>("Select a part by ID to start.");
  const [error, setError] = useState<string>("");
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    let cancelled = false;
    const timer = window.setTimeout(async () => {
      try {
        const next = await searchParts(query);
        if (!cancelled) {
          setResults(next);
        }
      } catch (requestError) {
        if (!cancelled) {
          setError(requestError instanceof Error ? requestError.message : "Search failed");
        }
      }
    }, 120);
    return () => {
      cancelled = true;
      window.clearTimeout(timer);
    };
  }, [query]);

  useEffect(() => {
    const skus = new Set<string>();
    for (const node of assembly.nodes) {
      skus.add(node.sku);
    }
    if (stagedSku) {
      skus.add(stagedSku);
    }
    for (const sku of skus) {
      if (!partCache[sku]) {
        void loadPart(sku);
      }
    }
  }, [assembly, stagedSku, partCache]);

  async function loadPart(sku: string) {
    if (partCache[sku]) {
      return;
    }
    const definition = await getPart(sku);
    setPartCache((current) => ({ ...current, [sku]: definition }));
  }

  async function placeRoot(sku: string) {
    setBusy(true);
    setError("");
    try {
      const updated = await connectPart({ assembly, target_sku: sku });
      setAssembly(updated);
      setStatus(`Placed root ${sku} at world origin.`);
      setStagedSku(null);
      setPreview(null);
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "Root placement failed");
    } finally {
      setBusy(false);
    }
  }

  async function stagePart(sku: string) {
    setError("");
    setPreview(null);
    setStagedSku(sku);
    await loadPart(sku).catch(() => undefined);
    setStatus(`Staged ${sku}. Click one of its ports in the scene to preview a connection.`);
  }

  async function requestPreview(targetPortId: string) {
    if (!stagedSku || !sourceSelection) {
      return;
    }
    setBusy(true);
    setError("");
    try {
      const next = await previewConnection({
        assembly,
        source_instance_id: sourceSelection.instanceId,
        source_port_id: sourceSelection.portId,
        target_sku: stagedSku,
        target_port_id: targetPortId,
      });
      setPreview(next);
      setStatus(
        `Preview ready: ${next.joint_type} via ${next.auto_connector_rule.replace("_", " ")}.`,
      );
    } catch (requestError) {
      setPreview(null);
      setError(requestError instanceof Error ? requestError.message : "Preview failed");
    } finally {
      setBusy(false);
    }
  }

  async function commitConnection() {
    if (!sourceSelection || !stagedSku || !preview) {
      return;
    }
    setBusy(true);
    setError("");
    try {
      const updated = await connectPart({
        assembly,
        source_instance_id: sourceSelection.instanceId,
        source_port_id: sourceSelection.portId,
        target_sku: stagedSku,
        target_port_id: preview.target_port_id,
      });
      setAssembly(updated);
      setStatus(`Connected ${stagedSku} as a ${preview.joint_type} link.`);
      setSourceSelection(null);
      setStagedSku(null);
      setPreview(null);
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "Connect failed");
    } finally {
      setBusy(false);
    }
  }

  async function downloadUsd() {
    setBusy(true);
    setError("");
    try {
      const contents = await exportUsd(assembly);
      downloadText("assembly.usda", contents);
      setStatus("Exported assembly.usda.");
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "Export failed");
    } finally {
      setBusy(false);
    }
  }

  async function handleJsonLoad(event: ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];
    if (!file) {
      return;
    }
    try {
      const text = await file.text();
      const parsed = JSON.parse(text) as AssemblyState;
      setAssembly(parsed);
      setSourceSelection(null);
      setStagedSku(null);
      setPreview(null);
      setStatus("Loaded assembly JSON.");
      setError("");
    } catch {
      setError("Could not parse assembly JSON");
    } finally {
      event.target.value = "";
    }
  }

  const stagedPart = stagedSku ? partCache[stagedSku] : undefined;
  const worlds = worldTranslations(assembly);

  return (
    <div className="app-shell">
      <aside className="panel sidebar">
        <div className="hero">
          <p className="eyebrow">Curated V1 Builder</p>
          <h1>LEGO USD Builder</h1>
          <p>
            Search by part ID, place a root, click a source port, then click a staged port to
            preview and connect.
          </p>
        </div>

        <div className="stack">
          <strong className="section-title">Search Parts</strong>
          <input
            className="search-input"
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            placeholder="Try 45602 or 6016154"
          />
          <div className="mini-list">
            {results.map((part) => (
              <div className="card" key={part.sku}>
                <strong>
                  {part.sku} · {part.label}
                </strong>
                <div className="muted">{part.geometry_asset}</div>
                <div className="actions" style={{ marginTop: 10 }}>
                  {assembly.nodes.length === 0 ? (
                    <button className="button" disabled={busy} onClick={() => void placeRoot(part.sku)}>
                      Place Root
                    </button>
                  ) : (
                    <button
                      className="button"
                      disabled={busy || !sourceSelection}
                      onClick={() => void stagePart(part.sku)}
                    >
                      Stage Part
                    </button>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="stack">
          <strong className="section-title">Build State</strong>
          <div className="pill-row">
            <span className="pill">{assembly.nodes.length} placed parts</span>
            <span className="pill">{assembly.connections.length} connections</span>
            {sourceSelection ? (
              <span className="pill good">
                source {sourceSelection.instanceId}:{sourceSelection.portId}
              </span>
            ) : (
              <span className="pill warn">pick a source port</span>
            )}
            {stagedSku ? <span className="pill good">staged {stagedSku}</span> : null}
            {preview ? <span className="pill good">{preview.joint_type} preview</span> : null}
          </div>
          <div className={error ? "status error" : "status"}>{error || status}</div>
          <div className="actions">
            <button className="button secondary" disabled={!preview || busy} onClick={() => void commitConnection()}>
              Confirm Connection
            </button>
            <button
              className="button ghost"
              disabled={assembly.nodes.length === 0 || busy}
              onClick={() => downloadText("assembly.json", JSON.stringify(assembly, null, 2))}
            >
              Save JSON
            </button>
            <button
              className="button ghost"
              disabled={assembly.nodes.length === 0 || busy}
              onClick={() => void downloadUsd()}
            >
              Export USD
            </button>
          </div>
          <input className="file-input" type="file" accept="application/json" onChange={(event) => void handleJsonLoad(event)} />
        </div>

        <div className="stack">
          <strong className="section-title">Assembly Nodes</strong>
          <div className="mini-list">
            {assembly.nodes.map((node) => (
              <div className="card" key={node.instance_id}>
                <strong className="mono">{node.instance_id}</strong>
                <div>
                  {node.sku} · {partCache[node.sku]?.label ?? "loading..."}
                </div>
                <div className="muted">
                  parent {node.parent_instance_id ?? "root"} · port {node.parent_port_id ?? "origin"}
                </div>
              </div>
            ))}
          </div>
        </div>
      </aside>

      <section className="panel scene-shell">
        <Canvas className="scene-canvas" camera={{ position: [5.5, 4.5, 8.5], fov: 42 }}>
          <color attach="background" args={["#f7f1e6"]} />
          <ambientLight intensity={1.6} />
          <directionalLight position={[6, 8, 5]} intensity={1.4} />
          <directionalLight position={[-4, 5, -2]} intensity={0.6} />
          <Grid
            args={[16, 16]}
            cellColor="#d6cab6"
            sectionColor="#b79f73"
            fadeDistance={18}
            fadeStrength={1.5}
            position={[0, -0.8, 0]}
          />
          <group>
            {assembly.nodes.map((node) => {
              const definition = partCache[node.sku];
              const translation = worlds[node.instance_id];
              if (!definition || !translation) {
                return null;
              }
              return (
                <PlacedPart
                  key={node.instance_id}
                  node={node}
                  part={definition}
                  translation={translation}
                  sourceSelection={sourceSelection}
                  onPortClick={(portId) => {
                    setSourceSelection({ instanceId: node.instance_id, portId });
                    setPreview(null);
                    setStatus(`Selected ${node.instance_id}:${portId}. Stage the next part from search.`);
                    setError("");
                  }}
                />
              );
            })}
            {stagedPart ? (
              <PreviewPart
                part={stagedPart}
                translation={
                  preview
                    ? matrixTranslation(preview.resolved_transform)
                    : sourceSelection && worlds[sourceSelection.instanceId]
                      ? [
                          worlds[sourceSelection.instanceId][0] + 72,
                          worlds[sourceSelection.instanceId][1],
                          worlds[sourceSelection.instanceId][2],
                        ]
                      : [72, 0, 0]
                }
                onPortClick={(portId) => void requestPreview(portId)}
              />
            ) : null}
          </group>
          <OrbitControls makeDefault />
        </Canvas>

        <div className="scene-overlay">
          <div className="overlay-card">
            <strong className="section-title">Connection Rules</strong>
            <div className="muted">
              Structural ports create fixed joints. Only motor output ports create revolute joints.
              Connectors are always implicit.
            </div>
          </div>
          {preview ? (
            <div className="overlay-card">
              <strong className="section-title">Preview</strong>
              <div className="pill-row">
                <span className="pill good">{preview.joint_type}</span>
                <span className="pill">{preview.auto_connector_rule}</span>
              </div>
              <div className="muted" style={{ marginTop: 8 }}>
                {preview.source_instance_id}:{preview.source_port_id} to {preview.target_sku}:{preview.target_port_id}
              </div>
            </div>
          ) : null}
        </div>
      </section>
    </div>
  );
}

function PlacedPart(props: {
  node: AssemblyNode;
  part: PartDefinition;
  translation: [number, number, number];
  sourceSelection: { instanceId: string; portId: string } | null;
  onPortClick: (portId: string) => void;
}) {
  const { node, part, translation, sourceSelection, onPortClick } = props;
  const size = part.render_size.map((value) => value / SCENE_SCALE) as [number, number, number];
  const position = translation.map((value) => value / SCENE_SCALE) as [number, number, number];
  return (
    <group position={position}>
      <mesh>
        <boxGeometry args={size} />
        <meshStandardMaterial color={CATEGORY_COLOR[part.category] ?? "#888"} />
      </mesh>
      {part.ports.map((port) => {
        const local = matrixTranslation(port.local_transform);
        const portPosition = local.map((value) => value / SCENE_SCALE) as [number, number, number];
        const active =
          sourceSelection?.instanceId === node.instance_id && sourceSelection.portId === port.id;
        return (
          <mesh
            key={port.id}
            position={portPosition}
            onClick={(event) => {
              event.stopPropagation();
              onPortClick(port.id);
            }}
          >
            <sphereGeometry args={[active ? 0.16 : 0.12, 24, 24]} />
            <meshStandardMaterial color={active ? "#ffd166" : portColor(port)} emissive={active ? "#a86a00" : "#000000"} />
          </mesh>
        );
      })}
    </group>
  );
}

function PreviewPart(props: {
  part: PartDefinition;
  translation: [number, number, number];
  onPortClick: (portId: string) => void;
}) {
  const { part, translation, onPortClick } = props;
  const size = part.render_size.map((value) => value / SCENE_SCALE) as [number, number, number];
  const position = translation.map((value) => value / SCENE_SCALE) as [number, number, number];
  return (
    <group position={position}>
      <mesh>
        <boxGeometry args={size} />
        <meshStandardMaterial color={CATEGORY_COLOR[part.category] ?? "#888"} transparent opacity={0.56} />
      </mesh>
      {part.ports.map((port) => {
        const local = matrixTranslation(port.local_transform);
        const portPosition = local.map((value) => value / SCENE_SCALE) as [number, number, number];
        return (
          <mesh
            key={port.id}
            position={portPosition}
            onClick={(event) => {
              event.stopPropagation();
              onPortClick(port.id);
            }}
          >
            <sphereGeometry args={[0.14, 24, 24]} />
            <meshStandardMaterial color={portColor(port)} emissive={port.kind === "motor_output" ? "#742b13" : "#0b2137"} />
          </mesh>
        );
      })}
    </group>
  );
}
