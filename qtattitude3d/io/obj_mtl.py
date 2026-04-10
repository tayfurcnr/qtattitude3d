from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List

import numpy as np

from ..models import Material


@dataclass
class MaterialGroup:
    material_names: List[str]
    material: Material
    faces: np.ndarray


@dataclass
class ModelScene:
    vertices: np.ndarray
    groups: List[MaterialGroup]
    source_path: Path


class ObjMtlModelLoader:
    @staticmethod
    def load(obj_path, model_scale=1.0):
        obj_path = Path(obj_path).resolve()
        vertices, material_faces, materials = ObjMtlModelLoader._parse_obj_geometry(obj_path)
        vertices = ObjMtlModelLoader._transform_vertices(vertices, model_scale=model_scale)
        groups = ObjMtlModelLoader._merge_material_groups(material_faces, materials)
        return ModelScene(vertices=vertices, groups=groups, source_path=obj_path)

    @staticmethod
    def _parse_mtl_materials(mtl_path):
        materials: Dict[str, Material] = {}
        active_material = None
        current = None

        with open(mtl_path, "r", encoding="utf-8", errors="ignore") as file:
            for line in file:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue

                if line.startswith("newmtl "):
                    if active_material is not None and current is not None:
                        materials[active_material] = current
                    active_material = line.split(maxsplit=1)[1]
                    current = Material.default()
                elif active_material and current:
                    parts = line.split()
                    key = parts[0]
                    if key in ("Ka", "Kd", "Ks") and len(parts) >= 4:
                        values = np.array(list(map(float, parts[1:4])), dtype=np.float32)
                        if key == "Ka":
                            current = Material(values, current.diffuse, current.specular, current.shininess, current.opacity)
                        elif key == "Kd":
                            current = Material(current.ambient, values, current.specular, current.shininess, current.opacity)
                        elif key == "Ks":
                            current = Material(current.ambient, current.diffuse, values, current.shininess, current.opacity)
                    elif key == "Ns" and len(parts) >= 2:
                        current = Material(current.ambient, current.diffuse, current.specular, float(parts[1]), current.opacity)
                    elif key == "d" and len(parts) >= 2:
                        current = Material(current.ambient, current.diffuse, current.specular, current.shininess, float(parts[1]))
                    elif key == "Tr" and len(parts) >= 2:
                        current = Material(current.ambient, current.diffuse, current.specular, current.shininess, 1.0 - float(parts[1]))

        if active_material is not None and current is not None:
            materials[active_material] = current

        return materials

    @staticmethod
    def _parse_obj_geometry(obj_path):
        mtl_file = None
        active_material = "default"
        vertices = []
        material_faces: Dict[str, List[List[int]]] = {}

        with open(obj_path, "r", encoding="utf-8", errors="ignore") as file:
            for line in file:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue

                if line.startswith("mtllib "):
                    mtl_file = line.split(maxsplit=1)[1].strip()
                elif line.startswith("v "):
                    x, y, z = map(float, line.split()[1:4])
                    vertices.append([x, y, z])
                elif line.startswith("usemtl "):
                    active_material = line.split(maxsplit=1)[1].strip()
                    material_faces.setdefault(active_material, [])
                elif line.startswith("f "):
                    face_indices = []
                    for token in line.split()[1:]:
                        vertex_token = token.split("/")[0]
                        vertex_index = int(vertex_token)
                        if vertex_index < 0:
                            vertex_index = len(vertices) + vertex_index
                        else:
                            vertex_index -= 1
                        face_indices.append(vertex_index)

                    for index in range(1, len(face_indices) - 1):
                        triangle = [face_indices[0], face_indices[index], face_indices[index + 1]]
                        material_faces.setdefault(active_material, []).append(triangle)

        if not mtl_file:
            raise ValueError("OBJ icinde mtllib satiri bulunamadi.")

        mtl_path = (obj_path.parent / mtl_file).resolve()
        if not mtl_path.exists():
            raise FileNotFoundError(f"MTL dosyasi bulunamadi: {mtl_path}")

        return (
            np.array(vertices, dtype=np.float32),
            material_faces,
            ObjMtlModelLoader._parse_mtl_materials(mtl_path),
        )

    @staticmethod
    def _transform_vertices(vertices, model_scale=1.0):
        transformed = vertices.copy()
        transformed -= transformed.mean(axis=0)
        transformed[:, 1] *= -1.0

        max_size = np.max(transformed.max(axis=0) - transformed.min(axis=0))
        if max_size > 0:
            transformed *= (20.0 / max_size) * float(model_scale)

        return transformed

    @staticmethod
    def _merge_material_groups(material_faces, materials):
        merged = {}

        for material_name, faces in material_faces.items():
            if not faces:
                continue

            material = materials.get(material_name, Material.default())
            group = merged.setdefault(
                material.signature(),
                {"material_names": [], "material": material, "faces": []},
            )
            group["material_names"].append(material_name)
            group["faces"].extend(faces)

        return [
            MaterialGroup(
                material_names=group["material_names"],
                material=group["material"],
                faces=np.array(group["faces"], dtype=np.int32),
            )
            for group in merged.values()
        ]
