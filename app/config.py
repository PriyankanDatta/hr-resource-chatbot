from pathlib import Path
import json
import yaml

ROOT = Path(__file__).resolve().parent.parent  # repo/app -> repo/

def load_json(path: Path):
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)

def load_yaml(path: Path):
    with path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def repo_path(*parts) -> Path:
    return ROOT.joinpath(*parts)
