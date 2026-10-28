"""
Data models and schemas for Academic AI Interaction Protocol Logger & Exporter.
Supports formal schema versioning and JSON serialization.
"""

from __future__ import annotations
import uuid
import json
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone, timedelta
from typing import List, Optional, Dict, Any


def get_current_cest_time() -> str:
    """Returns current CEST (UTC+2) formatted timestamp."""
    cest = timezone(timedelta(hours=2))
    return datetime.now(cest).strftime("%Y-%m-%d %H:%M CEST")


def get_current_date() -> str:
    """Returns current date formatted as YYYY-MM-DD."""
    cest = timezone(timedelta(hours=2))
    return datetime.now(cest).strftime("%Y-%m-%d")


@dataclass
class ProtocolMetadata:
    student_name: str = "Sven Várszegi, B.A."
    degree_program: str = "Master Digital Business Management (FH OÖ / JKU)"
    matriculation_number: str = ""  # Matrikelnummer / Personenkennzeichen
    course_code_title: str = "DBM-501: Master Thesis Research"
    assignment_scope: str = "Master's Thesis"
    examiner: str = ""
    submission_date: str = field(default_factory=get_current_date)
    primary_ai_models: str = ""
    secondary_ai_models: str = ""
    affidavit_en: str = ""
    affidavit_de: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> ProtocolMetadata:
        if not data:
            return cls()
        return cls(
            student_name=data.get("student_name", "Sven Várszegi, B.A."),
            degree_program=data.get("degree_program", "Master Digital Business Management (FH OÖ / JKU)"),
            matriculation_number=data.get("matriculation_number", ""),
            course_code_title=data.get("course_code_title", ""),
            assignment_scope=data.get("assignment_scope", "Master's Thesis"),
            examiner=data.get("examiner", ""),
            submission_date=data.get("submission_date", get_current_date()),
            primary_ai_models=data.get("primary_ai_models", ""),
            secondary_ai_models=data.get("secondary_ai_models", ""),
            affidavit_en=data.get("affidavit_en", ""),
            affidavit_de=data.get("affidavit_de", ""),
        )


@dataclass
class FactCheckEntry:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    claim: str = ""
    primary_source: str = ""
    status: str = "Confirmed"  # Confirmed, Refuted, Clarified, Disputed, Untestable, or custom string
    rectification_note: str = ""
    drop_reference: str = ""  # e.g., "Drop #1" or "Standalone"
    drop_id: Optional[str] = None  # UUID of linked drop if any
    is_external_file: bool = False  # True if source evidence is an accompanying file

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> FactCheckEntry:
        return cls(
            id=data.get("id", str(uuid.uuid4())),
            claim=data.get("claim", ""),
            primary_source=data.get("primary_source", ""),
            status=data.get("status", "Confirmed"),
            rectification_note=data.get("rectification_note", ""),
            drop_reference=data.get("drop_reference", ""),
            drop_id=data.get("drop_id"),
            is_external_file=bool(data.get("is_external_file", False)),
        )


@dataclass
class CriticalExamination:
    flaws_plausibility: str = ""
    application_decision: str = "N/A"  # N/A, Accepted, Modified, Rejected

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Optional[Dict[str, Any]]) -> Optional[CriticalExamination]:
        if not data:
            return None
        return cls(
            flaws_plausibility=data.get("flaws_plausibility", ""),
            application_decision=data.get("application_decision", "N/A"),
        )


@dataclass
class InteractionDrop:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    drop_number: int = 1
    timestamp: str = field(default_factory=get_current_cest_time)
    title: str = ""  # Optional short descriptive title/summary, e.g. "Visplore Output"
    target_engine: str = "Gemini 1.5 Pro"
    context_scope: str = ""
    core_intent: str = "Synthesis"  # Synthesis, Method Check, Drafting, Brainstorming, Verification, Other
    raw_prompt: str = ""
    raw_output: str = ""
    output_file_reference: str = ""
    is_retroactive: bool = False
    critical_examination: Optional[CriticalExamination] = None
    fact_checks: List[FactCheckEntry] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "drop_number": self.drop_number,
            "timestamp": self.timestamp,
            "title": self.title,
            "target_engine": self.target_engine,
            "context_scope": self.context_scope,
            "core_intent": self.core_intent,
            "raw_prompt": self.raw_prompt,
            "raw_output": self.raw_output,
            "output_file_reference": self.output_file_reference,
            "is_retroactive": self.is_retroactive,
            "critical_examination": self.critical_examination.to_dict() if self.critical_examination else None,
            "fact_checks": [fc.to_dict() for fc in self.fact_checks],
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> InteractionDrop:
        crit_data = data.get("critical_examination")
        crit_exam = CriticalExamination.from_dict(crit_data) if crit_data else None
        fact_checks = [FactCheckEntry.from_dict(fc) for fc in data.get("fact_checks", [])]
        return cls(
            id=data.get("id", str(uuid.uuid4())),
            drop_number=data.get("drop_number", 1),
            timestamp=data.get("timestamp", get_current_cest_time()),
            title=data.get("title", ""),
            target_engine=data.get("target_engine", "Gemini 1.5 Pro"),
            context_scope=data.get("context_scope", ""),
            core_intent=data.get("core_intent", "Synthesis"),
            raw_prompt=data.get("raw_prompt", ""),
            raw_output=data.get("raw_output", ""),
            output_file_reference=data.get("output_file_reference", ""),
            is_retroactive=bool(data.get("is_retroactive", False)),
            critical_examination=crit_exam,
            fact_checks=fact_checks,
        )


@dataclass
class ProtocolDocument:
    schema_version: str = "academic-ai-protocol/v1"
    version: str = "1.0.0"
    doc_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    file_path: Optional[str] = None
    title: str = "New Academic AI Protocol"
    created_at: str = field(default_factory=get_current_cest_time)
    updated_at: str = field(default_factory=get_current_cest_time)
    integrity_hash: str = ""
    hash_timestamp: str = ""
    metadata: ProtocolMetadata = field(default_factory=ProtocolMetadata)
    drops: List[InteractionDrop] = field(default_factory=list)
    standalone_fact_checks: List[FactCheckEntry] = field(default_factory=list)

    def compute_integrity_hash(self) -> str:
        """Computes cryptographic SHA-256 hash over document content for tamper evidence."""
        import hashlib
        self.renumber_drops()
        # Build canonical payload for hashing (excluding volatile hash field itself)
        payload = {
            "title": self.title,
            "created_at": self.created_at,
            "metadata": self.metadata.to_dict(),
            "drops": [d.to_dict() for d in self.drops],
            "standalone_fact_checks": [fc.to_dict() for fc in self.standalone_fact_checks],
        }
        canonical_str = json.dumps(payload, sort_keys=True, ensure_ascii=False)
        hasher = hashlib.sha256(canonical_str.encode("utf-8"))
        self.integrity_hash = f"sha256:{hasher.hexdigest()}"
        self.hash_timestamp = get_current_cest_time()
        return self.integrity_hash

    def renumber_drops(self) -> None:
        """Ensures chronological interactions have consecutive sequential numbering starting at 1."""
        drop_map = {}
        for i, drop in enumerate(self.drops, start=1):
            drop.drop_number = i
            label = f"Interaction #{i}"
            drop_map[drop.id] = label
            for fc in drop.fact_checks:
                fc.drop_id = drop.id
                fc.drop_reference = label

        for sfc in self.standalone_fact_checks:
            if sfc.drop_id and sfc.drop_id in drop_map:
                sfc.drop_reference = drop_map[sfc.drop_id]
            elif not sfc.drop_id:
                sfc.drop_reference = "Standalone"

    def remove_drop(self, drop: InteractionDrop) -> None:
        """Removes a drop, automatically preserving any attached fact checks by moving them to standalone."""
        if drop in self.drops:
            for fc in drop.fact_checks:
                fc.drop_id = None
                fc.drop_reference = "Standalone"
                self.standalone_fact_checks.append(fc)
            self.drops.remove(drop)
            self.renumber_drops()

    def assign_fact_check(self, fc: FactCheckEntry, target_drop_id: Optional[str]) -> None:
        """Assigns a fact check to a specific drop or marks it as standalone, moving it between containers."""
        if fc in self.standalone_fact_checks:
            self.standalone_fact_checks.remove(fc)
        for d in self.drops:
            if fc in d.fact_checks:
                d.fact_checks.remove(fc)

        fc.drop_id = target_drop_id
        if target_drop_id:
            target_drop = next((d for d in self.drops if d.id == target_drop_id), None)
            if target_drop:
                fc.drop_reference = f"Interaction #{target_drop.drop_number}"
                target_drop.fact_checks.append(fc)
            else:
                fc.drop_id = None
                fc.drop_reference = "Standalone"
                self.standalone_fact_checks.append(fc)
        else:
            fc.drop_reference = "Standalone"
            self.standalone_fact_checks.append(fc)

    def get_all_models_used(self) -> str:
        """Collects unique AI models used across all drops in this document."""
        models: List[str] = []
        for drop in self.drops:
            eng = drop.target_engine.strip()
            if eng and eng not in models:
                models.append(eng)
        if models:
            return ", ".join(models)
        return self.metadata.primary_ai_models.strip() or "None recorded"

    def get_all_fact_checks(self) -> List[FactCheckEntry]:
        """Collects all fact checks from drops and standalone matrix entries."""
        all_checks: List[FactCheckEntry] = []
        for drop in self.drops:
            for fc in drop.fact_checks:
                if not fc.drop_reference:
                    fc.drop_reference = f"Drop #{drop.drop_number}"
                all_checks.append(fc)
        for sfc in self.standalone_fact_checks:
            if not sfc.drop_reference:
                sfc.drop_reference = "Standalone"
            all_checks.append(sfc)
        return all_checks

    def to_dict(self) -> Dict[str, Any]:
        self.renumber_drops()
        if not self.integrity_hash:
            self.compute_integrity_hash()
        return {
            "$schema": self.schema_version,
            "version": self.version,
            "doc_id": self.doc_id,
            "title": self.title,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "integrity_hash": self.integrity_hash,
            "hash_timestamp": self.hash_timestamp,
            "metadata": self.metadata.to_dict(),
            "drops": [d.to_dict() for d in self.drops],
            "standalone_fact_checks": [fc.to_dict() for fc in self.standalone_fact_checks],
        }

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False)

    @classmethod
    def from_dict(cls, data: Dict[str, Any], file_path: Optional[str] = None) -> ProtocolDocument:
        meta = ProtocolMetadata.from_dict(data.get("metadata", {}))
        drops = [InteractionDrop.from_dict(d) for d in data.get("drops", [])]
        standalone = [FactCheckEntry.from_dict(fc) for fc in data.get("standalone_fact_checks", [])]
        doc = cls(
            schema_version=data.get("$schema", "academic-ai-protocol/v1"),
            version=data.get("version", "1.0.0"),
            doc_id=data.get("doc_id", str(uuid.uuid4())),
            file_path=file_path,
            title=data.get("title", "Academic AI Protocol"),
            created_at=data.get("created_at", get_current_cest_time()),
            updated_at=data.get("updated_at", get_current_cest_time()),
            integrity_hash=data.get("integrity_hash", ""),
            hash_timestamp=data.get("hash_timestamp", ""),
            metadata=meta,
            drops=drops,
            standalone_fact_checks=standalone,
        )
        doc.renumber_drops()
        return doc

    @classmethod
    def from_json(cls, json_str: str, file_path: Optional[str] = None) -> ProtocolDocument:
        data = json.loads(json_str)
        return cls.from_dict(data, file_path=file_path)
