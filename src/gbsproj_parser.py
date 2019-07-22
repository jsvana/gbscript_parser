import json
import pathlib
from typing import Any, Dict


class GbsProjectMetadata:
    def __init__(self, script_file: pathlib.Path, project_file: pathlib.Path) -> None:
        self.script_file = script_file
        self.project_file = project_file

        self.project = GbsProject.from_file(self.project_file)

    @classmethod
    def from_file(cls, path: pathlib.Path) -> "GbsProjectMetadata":
        with path.open("r") as f:
            data = json.load(f)

        return cls(
            script_file=pathlib.Path(data["script_file"]),
            project_file=pathlib.Path(data["project_file"]),
        )


class GbsProject:
    def __init__(self, data: Dict[str, Any]) -> None:
        self.data = data
        self.scene_names_to_ids: Dict[str, str] = {}
        for scene in self.data["scenes"]:
            self.scene_names_to_ids[scene["name"]] = scene["id"]

    @classmethod
    def from_file(cls, path: pathlib.Path) -> "GbsProject":
        with path.open("r") as f:
            data = json.load(f)

        return cls(data)
