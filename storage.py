import json
import threading
from pathlib import Path


class Storage:
    def __init__(self, path: str = "sent_courses.json"):
        self.path = Path(path)
        self.lock = threading.Lock()
        self._data = self._load()

    def _load(self):
        if not self.path.exists():
            return set()

        try:
            with self.path.open("r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list):
                    return set(data)
        except Exception:
            return set()

        return set()

    def save(self):
        with self.lock:
            try:
                with self.path.open("w", encoding="utf-8") as f:
                    json.dump(sorted(list(self._data)), f, ensure_ascii=False, indent=2)
            except Exception:
                pass

    def has(self, link: str) -> bool:
        return link in self._data

    def add(self, link: str):
        with self.lock:
            self._data.add(link)
            self.save()

    def add_many(self, links):
        new = []
        with self.lock:
            for l in links:
                if l not in self._data:
                    self._data.add(l)
                    new.append(l)
            if new:
                self.save()
        return new
