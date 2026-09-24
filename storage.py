"""
Storage manager for Academic AI Interaction Protocol Logger.
Handles configuration defaults, document storage scanning, and .ailog file I/O.
"""

from __future__ import annotations
import os
import sys
import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
from models import ProtocolDocument, ProtocolMetadata, get_current_cest_time


DEFAULT_STUDENT_NAME = "Sven Várszegi, B.A."
DEFAULT_DEGREE_PROGRAM = "Master Digital Business Management (FH OÖ / JKU)"
DEFAULT_PRIMARY_MODELS = "Anthropic Claude, Google Gemini"
DEFAULT_SECONDARY_MODELS = "Google NotebookLM"

DEFAULT_AFFIDAVIT_EN = (
    "I hereby declare that this interaction log represents an authentic and complete record of "
    "all generative artificial intelligence systems and tools utilized in the preparation of this academic submission. "
    "All AI-generated suggestions, code, drafts, and structural outlines were critically reviewed, verified for factual "
    "accuracy, and intellectually adapted under my sole academic responsibility."
)

DEFAULT_AFFIDAVIT_DE = (
    "Ich erkläre hiermit ehrenwörtlich, dass dieses Interaktionsprotokoll eine wahrheitsgetreue und vollständige "
    "Dokumentation aller generativen KI-Systeme und -Werkzeuge darstellt, die bei der Erstellung dieser wissenschaftlichen "
    "Arbeit eingesetzt wurden. Sämtliche durch KI generierten Vorschläge, Textentwürfe, Code-Fragmente und Gliederungen "
    "wurden von mir eigenständig kritisch geprüft, auf Richtigkeit verifiziert und unter voller wissenschaftlicher Eigenverantwortung weiterverarbeitet."
)


def get_app_data_dir() -> Path:
    """Returns application data directory appropriate for the current platform (macOS, Windows, Linux)."""
    if sys.platform == "darwin":
        path = Path.home() / "Library" / "Application Support" / "BlaBlAI"
    elif sys.platform == "win32":
        local_app_data = os.environ.get("LOCALAPPDATA")
        if local_app_data:
            path = Path(local_app_data) / "BlaBlAI"
        else:
            path = Path.home() / "AppData" / "Local" / "BlaBlAI"
    else:  # Linux / Unix
        xdg_data = os.environ.get("XDG_DATA_HOME")
        if xdg_data:
            path = Path(xdg_data) / "blablai"
        else:
            path = Path.home() / ".local" / "share" / "blablai"

    path.mkdir(parents=True, exist_ok=True)

    # Legacy migration: Check if older AcademicAILogger folder exists on Windows
    if sys.platform == "win32":
        local_app_data = os.environ.get("LOCALAPPDATA")
        if local_app_data:
            legacy_dir = Path(local_app_data) / "AcademicAILogger"
            if legacy_dir.exists():
                legacy_cfg = legacy_dir / "config.json"
                new_cfg = path / "config.json"
                if legacy_cfg.exists() and not new_cfg.exists():
                    try:
                        import shutil
                        shutil.copy2(legacy_cfg, new_cfg)
                    except Exception:
                        pass
    return path


def get_default_documents_dir() -> Path:
    """Returns standard user Documents folder sub-directory for BlaBlAI protocols."""
    docs_dir = Path.home() / "Documents" / "BlaBlAI_Protocols"
    docs_dir.mkdir(parents=True, exist_ok=True)

    # Fallback/migration check if older directory exists
    old_dir = Path.home() / "Documents" / "AcademicAILogs"
    if old_dir.exists():
        try:
            for f in old_dir.glob("*.ailog"):
                target = docs_dir / f.name
                if not target.exists():
                    import shutil
                    shutil.copy2(f, target)
        except Exception:
            pass
    return docs_dir


class StorageManager:
    CONFIG_FILE_NAME = "config.json"

    def __init__(self, app_dir: Optional[Path | str] = None, storage_dir: Optional[Path | str] = None):
        self.app_dir = Path(app_dir).resolve() if app_dir else get_app_data_dir()
        self.config_path = self.app_dir / self.CONFIG_FILE_NAME
        self.config: Dict[str, Any] = self._load_config()
        if storage_dir is not None:
            self.storage_dir = storage_dir

    def _load_config(self) -> Dict[str, Any]:
        default_cfg = {
            "default_student_name": DEFAULT_STUDENT_NAME,
            "default_degree_program": DEFAULT_DEGREE_PROGRAM,
            "matriculation_number": "",
            "last_used_engine": "Anthropic Claude",
            "default_storage_dir": str(get_default_documents_dir()),
            "default_primary_models": DEFAULT_PRIMARY_MODELS,
            "default_secondary_models": DEFAULT_SECONDARY_MODELS,
            "custom_affidavit_en": DEFAULT_AFFIDAVIT_EN,
            "custom_affidavit_de": DEFAULT_AFFIDAVIT_DE,
            "ui_theme": "dark",  # "dark", "light", "system"
            "ui_locale": "en",   # "en", "de"
            "onboarding_completed": False,
            "recent_files": [],
        }
        if self.config_path.exists():
            try:
                with open(self.config_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    default_cfg.update(data)
            except Exception:
                pass
        return default_cfg

    def save_config(self) -> None:
        """Persists settings to config.json."""
        try:
            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Warning: Failed to save config: {e}")

    @property
    def storage_dir(self) -> Path:
        """Returns current document storage directory. Falls back to Documents if path doesn't exist."""
        path_str = self.config.get("default_storage_dir")
        if not path_str:
            path = get_default_documents_dir()
        else:
            path = Path(path_str)
            if not path.exists():
                path = get_default_documents_dir()
                self.config["default_storage_dir"] = str(path)
                self.save_config()

        path.mkdir(parents=True, exist_ok=True)
        return path

    @storage_dir.setter
    def storage_dir(self, new_path: str | Path) -> None:
        self.config["default_storage_dir"] = str(Path(new_path).resolve())
        self.save_config()

    @property
    def student_name(self) -> str:
        return self.config.get("default_student_name", DEFAULT_STUDENT_NAME)

    @student_name.setter
    def student_name(self, val: str) -> None:
        self.config["default_student_name"] = val
        self.save_config()

    @property
    def degree_program(self) -> str:
        return self.config.get("default_degree_program", DEFAULT_DEGREE_PROGRAM)

    @degree_program.setter
    def degree_program(self, val: str) -> None:
        self.config["default_degree_program"] = val
        self.save_config()

    @property
    def matriculation_number(self) -> str:
        return self.config.get("matriculation_number", "")

    @matriculation_number.setter
    def matriculation_number(self, val: str) -> None:
        self.config["matriculation_number"] = val
        self.save_config()

    @property
    def last_used_engine(self) -> str:
        return self.config.get("last_used_engine", "Anthropic Claude")

    @last_used_engine.setter
    def last_used_engine(self, val: str) -> None:
        self.config["last_used_engine"] = val
        self.save_config()

    @property
    def custom_affidavit_en(self) -> str:
        return self.config.get("custom_affidavit_en", DEFAULT_AFFIDAVIT_EN)

    @custom_affidavit_en.setter
    def custom_affidavit_en(self, val: str) -> None:
        self.config["custom_affidavit_en"] = val
        self.save_config()

    @property
    def custom_affidavit_de(self) -> str:
        return self.config.get("custom_affidavit_de", DEFAULT_AFFIDAVIT_DE)

    @custom_affidavit_de.setter
    def custom_affidavit_de(self, val: str) -> None:
        self.config["custom_affidavit_de"] = val
        self.save_config()

    @property
    def primary_models(self) -> str:
        return self.config.get("default_primary_models", DEFAULT_PRIMARY_MODELS)

    @primary_models.setter
    def primary_models(self, val: str) -> None:
        self.config["default_primary_models"] = val
        self.save_config()

    @property
    def secondary_models(self) -> str:
        return self.config.get("default_secondary_models", DEFAULT_SECONDARY_MODELS)

    @secondary_models.setter
    def secondary_models(self, val: str) -> None:
        self.config["default_secondary_models"] = val
        self.save_config()

    @property
    def ui_theme(self) -> str:
        return self.config.get("ui_theme", "dark")

    @ui_theme.setter
    def ui_theme(self, val: str) -> None:
        self.config["ui_theme"] = val
        self.save_config()

    @property
    def ui_locale(self) -> str:
        return self.config.get("ui_locale", "en")

    @ui_locale.setter
    def ui_locale(self, val: str) -> None:
        self.config["ui_locale"] = val
        self.save_config()

    @property
    def onboarding_completed(self) -> bool:
        return bool(self.config.get("onboarding_completed", False))

    @onboarding_completed.setter
    def onboarding_completed(self, val: bool) -> None:
        self.config["onboarding_completed"] = bool(val)
        self.save_config()

    def generate_default_document_title(self) -> str:
        """Generates a clean default document title like NewAI_Log_Sven_Varszegi_2026-09-24."""
        from models import get_current_date
        import re
        import unicodedata
        raw_name = self.student_name.split(",")[0].strip()
        # Transliterate umlauts / accents (á -> a, ä -> a, etc.)
        norm_name = unicodedata.normalize("NFKD", raw_name).encode("ASCII", "ignore").decode("ASCII")
        safe_name = re.sub(r"[^A-Za-z0-9]+", "_", norm_name).strip("_") or "User"
        date_str = get_current_date()
        return f"NewAI_Log_{safe_name}_{date_str}"

    def list_documents(self) -> List[Dict[str, Any]]:
        """
        Scans storage_dir for all .ailog files and returns summaries
        sorted by most recently modified.
        """
        folder = self.storage_dir
        results: List[Dict[str, Any]] = []

        if not folder.exists():
            return results

        for item in folder.glob("*.ailog"):
            try:
                stat = item.stat()
                mod_time = datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M")
                
                # Read quick summary without loading huge text
                with open(item, "r", encoding="utf-8") as f:
                    data = json.load(f)

                title = data.get("title", item.stem)
                meta = data.get("metadata", {})
                course = meta.get("course_code_title", "General / Undefined Course")
                drops_count = len(data.get("drops", []))
                
                results.append({
                    "file_path": str(item.resolve()),
                    "file_name": item.name,
                    "title": title,
                    "course": course,
                    "assignment_scope": meta.get("assignment_scope", ""),
                    "student_name": meta.get("student_name", ""),
                    "drops_count": drops_count,
                    "last_modified": mod_time,
                    "mtime_epoch": stat.st_mtime,
                })
            except Exception as e:
                print(f"Error reading {item.name}: {e}")

        # Sort descending by mtime
        results.sort(key=lambda x: x["mtime_epoch"], reverse=True)
        return results

    def save_document(self, doc: ProtocolDocument, target_path: Optional[str] = None) -> str:
        """
        Saves a ProtocolDocument to an .ailog file.
        Updates updated_at timestamp.
        """
        if target_path:
            file_path = Path(target_path)
        elif doc.file_path:
            file_path = Path(doc.file_path)
        else:
            # Generate clean filename from document title
            safe_title = "".join(c for c in doc.title if c.isalnum() or c in (" ", "_", "-")).strip()
            safe_title = safe_title.replace(" ", "_") or "AI_Protocol"
            file_path = self.storage_dir / f"{safe_title}.ailog"

        doc.file_path = str(file_path.resolve())
        doc.updated_at = get_current_cest_time()
        # Compute cryptographic tamper-evident SHA-256 digest on save
        doc.compute_integrity_hash()

        # Write to file atomically
        temp_path = file_path.with_suffix(".tmp")
        with open(temp_path, "w", encoding="utf-8") as f:
            f.write(doc.to_json())
        temp_path.replace(file_path)

        # Track in recent files
        self._add_recent_file(doc.file_path)
        return doc.file_path

    def load_document(self, file_path: str) -> ProtocolDocument:
        """Loads a ProtocolDocument from a .ailog file."""
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        with open(path, "r", encoding="utf-8") as f:
            content = f.read()

        doc = ProtocolDocument.from_json(content, file_path=str(path.resolve()))
        self._add_recent_file(doc.file_path)
        return doc

    def delete_document(self, file_path: str) -> bool:
        """Deletes a .ailog file."""
        path = Path(file_path)
        if path.exists():
            path.unlink()
            return True
        return False

    def create_new_document(
        self,
        title: str,
        course: str = "",
        assignment_scope: str = "Master's Thesis",
        examiner: str = "",
        student_name: Optional[str] = None,
        matriculation_number: Optional[str] = None,
        save_immediately: bool = True,
    ) -> ProtocolDocument:
        """Creates a new ProtocolDocument initialized with user profile defaults and custom affidavits."""
        meta = ProtocolMetadata(
            student_name=student_name if student_name is not None else self.student_name,
            degree_program=self.degree_program,
            matriculation_number=matriculation_number if matriculation_number is not None else self.matriculation_number,
            course_code_title=course,
            assignment_scope=assignment_scope,
            examiner=examiner,
            primary_ai_models=self.primary_models,
            secondary_ai_models=self.secondary_models,
            affidavit_en=self.custom_affidavit_en,
            affidavit_de=self.custom_affidavit_de,
        )
        doc = ProtocolDocument(
            title=title,
            metadata=meta,
        )
        if save_immediately:
            self.save_document(doc)
        return doc

    def _add_recent_file(self, path: str) -> None:
        recents = self.config.get("recent_files", [])
        if path in recents:
            recents.remove(path)
        recents.insert(0, path)
        self.config["recent_files"] = recents[:10]  # keep top 10
        self.save_config()
