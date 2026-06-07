"""Pure-Python model for the command sidebar.

Folders and commands live in ``config.config_data['commands']`` and are flushed
to disk through the :class:`~commando.config.Config` object. No GTK here.
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone

from .defaults import DEFAULT_COMMANDS, DEFAULT_FOLDERS

logger = logging.getLogger(__name__)


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class CommandStore:
    """CRUD + search over folders and command snippets."""

    def __init__(self, config) -> None:
        self._config = config
        self._ensure_defaults()

    # -- internals ---------------------------------------------------------

    def _data(self) -> dict:
        data = self._config.config_data.get("commands")
        if not isinstance(data, dict):
            data = {"folders": [], "commands": [], "defaults_loaded": False}
            self._config.config_data["commands"] = data
        return data

    def _save(self) -> None:
        try:
            self._config.save()
        except Exception as exc:  # pragma: no cover - defensive
            logger.error("Failed to save commands: %s", exc)

    @staticmethod
    def _new_id() -> str:
        return str(uuid.uuid4())

    def _ensure_defaults(self) -> None:
        data = self._data()
        if data.get("defaults_loaded") or data.get("commands"):
            data["defaults_loaded"] = True
            return
        data["folders"] = [dict(f) for f in DEFAULT_FOLDERS]
        data["commands"] = [
            {
                "id": c["id"],
                "name": c["name"],
                "command": c["command"],
                "description": c.get("description", ""),
                "tags": list(c.get("tags", [])),
                "folder_id": c.get("folder_id"),
                "is_favorite": bool(c.get("is_favorite", False)),
                "use_count": 0,
                "last_used": None,
                "has_placeholders": bool(c.get("has_placeholders", False)),
                "created_at": _now_iso(),
            }
            for c in DEFAULT_COMMANDS
        ]
        data["defaults_loaded"] = True
        self._save()

    # -- folders -----------------------------------------------------------

    def get_folders(self) -> list[dict]:
        return list(self._data().get("folders", []))

    def add_folder(self, name: str, parent_id: str | None = None) -> dict:
        folders = self._data().setdefault("folders", [])
        entry = {
            "id": self._new_id(),
            "name": name,
            "parent_id": parent_id,
            "order": len(folders),
            "expanded": True,
        }
        folders.append(entry)
        self._save()
        return entry

    def update_folder(self, folder_id: str, **kwargs) -> None:
        for f in self._data().get("folders", []):
            if f["id"] == folder_id:
                for k in ("name", "expanded", "order", "parent_id"):
                    if k in kwargs:
                        f[k] = kwargs[k]
                self._save()
                return

    def delete_folder(self, folder_id: str) -> None:
        data = self._data()
        data["folders"] = [f for f in data.get("folders", []) if f["id"] != folder_id]
        for cmd in data.get("commands", []):
            if cmd.get("folder_id") == folder_id:
                cmd["folder_id"] = None
        self._save()

    # -- commands ----------------------------------------------------------

    def get_commands(self) -> list[dict]:
        return list(self._data().get("commands", []))

    def add_command(self, name: str, command: str, **kwargs) -> dict:
        entry = {
            "id": self._new_id(),
            "name": name,
            "command": command,
            "description": kwargs.get("description", ""),
            "tags": list(kwargs.get("tags", [])),
            "folder_id": kwargs.get("folder_id"),
            "is_favorite": bool(kwargs.get("is_favorite", False)),
            "use_count": 0,
            "last_used": None,
            "has_placeholders": bool(kwargs.get("has_placeholders", False)),
            "created_at": _now_iso(),
        }
        self._data().setdefault("commands", []).append(entry)
        self._save()
        return entry

    def update_command(self, cmd_id: str, **kwargs) -> None:
        allowed = {"name", "command", "description", "tags", "folder_id",
                   "is_favorite", "has_placeholders"}
        for cmd in self._data().get("commands", []):
            if cmd["id"] == cmd_id:
                for k, v in kwargs.items():
                    if k in allowed:
                        cmd[k] = v
                self._save()
                return

    def delete_command(self, cmd_id: str) -> None:
        data = self._data()
        data["commands"] = [c for c in data.get("commands", []) if c["id"] != cmd_id]
        self._save()

    def duplicate_command(self, cmd_id: str) -> dict | None:
        for cmd in self._data().get("commands", []):
            if cmd["id"] == cmd_id:
                new_cmd = dict(cmd)
                new_cmd["id"] = self._new_id()
                new_cmd["name"] = cmd["name"] + " (copy)"
                new_cmd["use_count"] = 0
                new_cmd["last_used"] = None
                new_cmd["created_at"] = _now_iso()
                self._data().setdefault("commands", []).append(new_cmd)
                self._save()
                return new_cmd
        return None

    def record_use(self, cmd_id: str) -> None:
        for cmd in self._data().get("commands", []):
            if cmd["id"] == cmd_id:
                cmd["use_count"] = cmd.get("use_count", 0) + 1
                cmd["last_used"] = _now_iso()
                self._save()
                return

    # -- queries -----------------------------------------------------------

    def search(self, query: str) -> list[dict]:
        q = query.lower().strip()
        if not q:
            return self.get_commands()
        results = []
        for cmd in self._data().get("commands", []):
            haystack = " ".join([
                cmd.get("name", ""),
                cmd.get("description", ""),
                cmd.get("command", ""),
                " ".join(cmd.get("tags", [])),
            ]).lower()
            if q in haystack:
                results.append(cmd)
        return results

    def get_favorites(self) -> list[dict]:
        return [c for c in self._data().get("commands", []) if c.get("is_favorite")]
