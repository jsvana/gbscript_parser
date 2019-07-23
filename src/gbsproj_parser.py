import json
import pathlib
from typing import Any, Dict

from .parsing import Block, parse


class ParseError(Exception):
    def __init__(self, path, message) -> None:
        super().__init__()
        self.path = path
        self.message = message


class GbsProjectMetadata:
    def __init__(
        self, scripts: Dict[str, pathlib.Path], project_file: pathlib.Path
    ) -> None:
        self.scripts = scripts
        self.project_file = project_file

        self.project = GbsProject.from_file(self.project_file)

    def to_json(self) -> str:
        return self.project.to_json()

    @classmethod
    def from_file(cls, path: pathlib.Path) -> "GbsProjectMetadata":
        with path.open("r") as f:
            data = json.load(f)

        scripts = {name: pathlib.Path(path) for name, path in data["scripts"].items()}

        return cls(scripts=scripts, project_file=pathlib.Path(data["project_file"]))

    def parse(self) -> None:
        for scene_name, script_path in self.scripts.items():
            with script_path.open("r") as f:
                try:
                    block = parse(f.read())
                except ValueError as e:
                    raise ParseError(str(script_path), str(e)) from e

                self.project.set_scene_script(scene_name, block)


class GbsProject:
    def __init__(self, data: Dict[str, Any]) -> None:
        self.data = data
        self.scene_names_to_ids: Dict[str, str] = {}
        self.scene_indexes: Dict[str, int] = {}
        for i, scene in enumerate(self.data["scenes"]):
            scene_name = scene["name"]
            if scene_name in self.scene_names_to_ids:
                raise ValueError(f'Scene name "{scene_name}" appears more than once')

            self.scene_names_to_ids[scene_name] = scene["id"]
            self.scene_indexes[scene_name] = i

    def set_scene_script(self, scene_name: str, script: Block) -> None:
        self.data["scenes"][self.scene_indexes[scene_name]]["script"] = script.to_dict(
            self.scene_names_to_ids
        )

    def scene_from_name(self, name: str) -> Dict[str, Any]:
        return self.data["scenes"][self.scene_indexes[name]]

    def to_json(self) -> str:
        return json.dumps(self.data, indent=4, sort_keys=True)

    @classmethod
    def from_file(cls, path: pathlib.Path) -> "GbsProject":
        with path.open("r") as f:
            data = json.load(f)

        return cls(data)
