import json
import pathlib
from typing import Any, Dict


class GbsProjectMetadata:
    def __init__(
        self, scripts: Dict[str, pathlib.Path], project_file: pathlib.Path
    ) -> None:
        self.scripts = scripts
        self.project_file = project_file

        self.project = GbsProject.from_file(self.project_file)

    @classmethod
    def from_file(cls, path: pathlib.Path) -> "GbsProjectMetadata":
        with path.open("r") as f:
            data = json.load(f)

        scripts = {name: pathlib.Path(path) for name, path in data["scripts"].items()}

        return cls(scripts=scripts, project_file=pathlib.Path(data["project_file"]))


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
