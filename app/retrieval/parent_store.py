import json
from pathlib import Path
from typing import Dict, Optional, List
from app.chunking.schema import ParentSection


class ParentSectionStore:
    def __init__(self):
        self.sections: Dict[str, ParentSection] = {}

    def add_sections(self, sections: List[ParentSection]):
        for s in sections:
            self.sections[s.section_id] = s

    def get(self, section_id: str) -> Optional[ParentSection]:
        return self.sections.get(section_id)

    def save(self, index_dir: Path):
        index_dir = Path(index_dir)
        index_dir.mkdir(parents=True, exist_ok=True)
        data = {sec_id: sec.model_dump() for sec_id, sec in self.sections.items()}
        with open(index_dir / "parent_sections.json", "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    @classmethod
    def load(cls, index_dir: Path) -> "ParentSectionStore":
        index_dir = Path(index_dir)
        path = index_dir / "parent_sections.json"
        if not path.exists():
            raise FileNotFoundError(f"Parent sections file missing at {path}")

        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        store = cls()
        store.sections = {k: ParentSection(**v) for k, v in data.items()}
        return store
