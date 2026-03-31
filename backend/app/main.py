from __future__ import annotations

from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse

from backend.app.domain import AssemblyState
from backend.app.services.assembly_service import AssemblyService
from backend.app.services.connection_service import ConnectionService
from backend.app.services.part_registry import PartRegistry
from backend.app.services.usd_exporter import UsdExporter

app = FastAPI(title="LEGO USD Builder API", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

registry = PartRegistry()
assembly_service = AssemblyService()
connection_service = ConnectionService(registry)
usd_exporter = UsdExporter(registry, assembly_service)


def _parse_assembly(payload: dict[str, Any]) -> AssemblyState:
    return AssemblyState.from_dict(payload.get("assembly"))


@app.get("/api/health")
def healthcheck() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/parts")
def list_parts(query: str = "") -> list[dict[str, Any]]:
    return [part.summary_dict() for part in registry.search(query)]


@app.get("/api/parts/{sku}")
def get_part(sku: str) -> dict[str, Any]:
    try:
        return registry.get_part(sku).to_dict()
    except KeyError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error


@app.post("/api/assemblies/preview-connection")
def preview_connection(payload: dict[str, Any]) -> dict[str, Any]:
    try:
        assembly = _parse_assembly(payload)
        source_instance_id = payload["source_instance_id"]
        source_port_id = payload["source_port_id"]
        target_sku = payload["target_sku"]
        target_port_id = payload["target_port_id"]
        world_transforms = assembly_service.build_world_transforms(assembly)
        preview = connection_service.preview_connection(
            assembly,
            world_transforms=world_transforms,
            source_instance_id=source_instance_id,
            source_port_id=source_port_id,
            target_sku=target_sku,
            target_port_id=target_port_id,
        )
        return preview.to_dict()
    except (KeyError, ValueError) as error:
        raise HTTPException(status_code=400, detail=str(error)) from error


@app.post("/api/assemblies/connect")
def connect(payload: dict[str, Any]) -> dict[str, Any]:
    try:
        assembly = _parse_assembly(payload)
        target_sku = payload["target_sku"]
        source_instance_id = payload.get("source_instance_id")
        source_port_id = payload.get("source_port_id")

        registry.get_part(target_sku)
        if not assembly.nodes and source_instance_id is None:
            updated = assembly_service.create_root(assembly, target_sku)
            return updated.to_dict()

        if source_instance_id is None or source_port_id is None:
            raise ValueError("source_instance_id and source_port_id are required")

        target_port_id = payload["target_port_id"]
        world_transforms = assembly_service.build_world_transforms(assembly)
        preview = connection_service.preview_connection(
            assembly,
            world_transforms=world_transforms,
            source_instance_id=source_instance_id,
            source_port_id=source_port_id,
            target_sku=target_sku,
            target_port_id=target_port_id,
        )
        updated = assembly_service.attach_part(assembly, preview)
        return updated.to_dict()
    except (KeyError, ValueError) as error:
        raise HTTPException(status_code=400, detail=str(error)) from error


@app.post("/api/assemblies/export/usd", response_class=PlainTextResponse)
def export_usd(payload: dict[str, Any]) -> PlainTextResponse:
    try:
        assembly = _parse_assembly(payload)
        contents = usd_exporter.export(assembly)
        headers = {"Content-Disposition": 'attachment; filename="assembly.usda"'}
        return PlainTextResponse(contents, headers=headers)
    except (KeyError, ValueError) as error:
        raise HTTPException(status_code=400, detail=str(error)) from error

