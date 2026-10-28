"""
Internationalization (i18n) module for Academic AI Protocol Logger.
Supports English (EN) and German (DE).
Maintains internal canonical English keys for storage schema compatibility.
"""

from __future__ import annotations
from typing import Dict, Any, Callable, List

# Active locale: 'en' or 'de'
_CURRENT_LOCALE: str = "en"
_LOCALE_LISTENERS: List[Callable[[str], None]] = []

# Canonical English values used in storage and data models
CANONICAL_INTENTS = [
    "Synthesis",
    "Method Check",
    "Drafting",
    "Brainstorming",
    "Verification",
    "Code Generation",
    "Refinement & Polishing",
    "Other",
]

CANONICAL_DECISIONS = ["N/A", "Accepted", "Modified", "Rejected"]
CANONICAL_STATUSES = ["Confirmed", "Refuted", "Clarified", "Disputed", "Untestable"]

CANONICAL_SCOPES = [
    "Master's Thesis",
    "Bachelor's Thesis",
    "Seminar Paper",
    "Course Project",
    "Case Study / Homework",
    "Other",
]

TRANSLATIONS: Dict[str, Dict[str, str]] = {
    "en": {
        # App Branding
        "app_title": "BlaBlAI",
        "app_subtitle": "",
        "app_window_title": "BlaBlAI — Academic AI Interaction Protocol Logger & Exporter",
        "home_label": "Home",
        
        # Profile & Affidavits
        "user_profile": "User Profile",
        "profile_heading": "User Profile & Academic Identity",
        "profile_subheading": "Your personal academic credentials and default affidavits for protocol header tables.",
        "lbl_matriculation": "Student ID / Matriculation No. (Matrikelnummer)",
        "lbl_affidavit_en": "Academic AI Affidavit Statement (English)",
        "lbl_affidavit_de": "Academic AI Affidavit Statement (German)",
        "btn_reset_affidavits": "Reset Statements to Default",
        
        # Read-Only External Author Guard
        "lbl_external_author": "🔒 External Author (Read-Only)",
        "badge_external_author_hint": "This protocol was authored by {author}. Profile fields are locked to preserve provenance.",
        "btn_unlock_author": "🔓 Unlock Author Fields",
        
        # Tooltips
        "tooltip_engine": "Select or type the generative AI model used for this interaction.",
        "tooltip_intent": "Core cognitive purpose or scholarly intent of this query.",
        "tooltip_scope": "Specific source documents, chapters, or context provided to the AI.",
        "tooltip_prompt": "The exact prompt text submitted to the AI.",
        "tooltip_output": "The complete, unmodified response received from the AI.",
        "tooltip_crit_toggle": "Expand to record plausibility evaluation and logic flaws.",
        "tooltip_fc_toggle": "Expand to audit empirical claims against primary sources.",
        "tooltip_add_drop": "Append this interaction drop to the protocol.",
        "tooltip_reset_drop": "Clear the input fields and prepare a fresh drop.",
        "tooltip_lang": "Toggle interface language between English and Deutsch.",
        "tooltip_theme": "Toggle interface theme between Dark and Light mode.",
        "tooltip_profile": "Configure your name, student ID, degree, and custom affidavits.",
        
        # Audit & Tamper-Evidence
        "audit_block_heading": "Verification & Audit Trail",
        "audit_integrity_hash": "Cryptographic SHA-256 Digest",
        "audit_timestamp": "Audit Timestamp",
        "audit_total_drops": "Total Drops Recorded",
        "audit_total_facts": "Audited Fact-Checks",
        "audit_notice": "This cryptographic SHA-256 digest certifies the authenticity and immutability of the documented interactions. Any post-hoc manual tampering with recorded prompts or outputs invalidates this digest.",
        
        # Navigation & Common
        "btn_back_to_hub": "← Home",
        "btn_save": "Save Changes",
        "btn_cancel": "Cancel",
        "btn_delete": "Delete",
        "btn_edit": "Edit",
        "btn_open": "Open",
        "btn_refresh": "Refresh",
        "btn_theme": "🌓 Theme",
        "btn_about": "ℹ️ About & Help",
        "lbl_autosave_banner": "💾 Continuous Autosave Active — All changes persist instantly to your local .ailog file",
        "btn_tidy_text": "🧹 Clean / Tidy",
        "tooltip_tidy_text": "Normalize bullets, remove nested code blocks, and wrap long lines into clean receipt format",
        "onboarding_welcome_title": "👋 Welcome to BlaBlAI!",
        "onboarding_welcome_desc": "Welcome! Please take a quick moment to verify your academic credentials. These will be automatically prefilled in every new protocol you create.",
        "tooltip_new_doc_title": "Title of your thesis, seminar paper, or project.",
        "tooltip_new_doc_course": "Institutional course code and name (e.g. DBM24-Seminar).",
        "tooltip_new_doc_examiner": "Supervising professor or academic examiner.",
        "tooltip_new_doc_scope": "Scholarly scope or degree level for this submission.",
        "tooltip_profile_name": "Your legal name with academic degrees (e.g. Sven Várszegi, B.A.).",
        "tooltip_profile_degree": "Enrolled degree program and institution.",
        "tooltip_profile_matriculation": "Official student ID / matriculation number.",
        "tooltip_profile_models": "Standard generative AI models you regularly utilize.",
        "status_saved": "● Saved",
        "status_saved_time": "● Saved ({time})",
        "status_save_error": "⚠ Save Error",
        "confirm_delete_title": "Confirm Delete",
        "confirm_delete_doc_msg": "Are you sure you want to delete '{title}'?\nThis cannot be undone.",
        "confirm_delete_drop_msg": "Are you sure you want to delete Interaction #{num}?",
        
        # Hub View
        "hub_storage_folder": "📁 Storage Folder: {folder}",
        "btn_open_explorer": "📂 Open in Explorer",
        "btn_change_folder": "Change Folder...",
        "btn_new_document": "+ New Document",
        "btn_open_external": "📂 Open External .ailog...",
        "hub_recent_docs_title": "Recent Documents ({count})",
        "hub_empty_title": "📄 No AI Interaction Protocols Found",
        "hub_empty_desc": "Click '+ New Document' above to start logging your thesis or seminar paper AI interactions.",
        "btn_create_first": "+ Create First Document",
        "card_course_scope": "Course: {course}  |  Scope: {scope}",
        "card_drops_count": "{count} Interactions Logged",
        "card_modified": "Modified: {time}",
        "dialog_change_folder_title": "Select Storage Folder for AI Protocols",
        "dialog_open_external_title": "Open Academic AI Protocol (.ailog)",
        
        # Editor Tabs
        "tab_drops": "  Interactions  ",
        "tab_matrix": "  Verification Matrix  ",
        "tab_preview": "  Preview & Export  ",
        
        # Metadata Dialog
        "meta_dialog_title_new": "Create New AI Protocol",
        "meta_dialog_title_edit": "Document Information & Academic Metadata",
        "meta_heading": "Academic AI Protocol Details",
        "meta_subheading": "Configure your institutional course details and default generative AI engines.",
        "lbl_doc_title": "Document / Assignment Title",
        "lbl_student_name": "Student Name (with academic title)",
        "lbl_degree_program": "Degree Program & University",
        "lbl_course_code": "Course Code & Title",
        "lbl_assignment_scope": "Assignment Scope",
        "lbl_examiner": "Examiner / Academic Supervisor",
        "lbl_submission_date": "Submission Date (YYYY-MM-DD)",
        "lbl_primary_models": "Primary AI Models",
        "lbl_secondary_models": "Secondary / Auxiliary AI Models",
        "cb_save_defaults": "Save student name, degree program, and models as my permanent defaults",
        "btn_create_doc": "Create Document",
        "btn_edit_info": "⚙ Edit Info",
        
        # Drop Logger
        "log_heading_new": "Log New AI Interaction",
        "log_heading_edit": "Edit Interaction #{num}",
        "lbl_drop_title": "Interaction Title / Short Summary (Optional)",
        "ph_drop_title": "e.g. Visplore Data Output, Literature Synthesis, Architecture Schema",
        "lbl_timestamp": "Timestamp (CEST)*",
        "btn_now": "↺ Now",
        "btn_pick_datetime": "📅",
        "tooltip_pick_datetime": "Open visual calendar and time picker",
        "lbl_retroactive": "Retroactive / Archive",
        "tooltip_retroactive": "Check if this interaction took place earlier or exact time is uncritical (date-only logging).",
        "badge_retroactive": "Retroactive",
        "dt_dialog_title": "Select Date & Time",
        "dt_lbl_date": "Calendar Date",
        "dt_lbl_time": "Time (24h)",
        "dt_lbl_hour": "Hour",
        "dt_lbl_minute": "Minute",
        "dt_btn_apply": "Apply",
        "dt_btn_cancel": "Cancel",
        "dt_btn_now": "↺ Now",
        "lbl_engine": "Target Engine*",
        "lbl_intent": "Core Intent*",
        "lbl_context_scope": "Context Scope (Optional)",
        "ph_context_scope": "e.g. Uploaded PDF chapters, web search",
        "lbl_raw_prompt": "Raw Prompt (Exact query submitted)*",
        "lbl_raw_output": "Raw AI Output (Generated response)*",
        "lbl_file_reference": "Generated Artifact / File Reference (Optional)",
        "ph_file_reference": "e.g. video.mp4, architecture_diagram.png, chart.svg, dataset.csv",
        "tooltip_file_reference": "Reference external media or files created by the AI (e.g. video, images, diagrams, audio, or datasets submitted in your appendix).",
        "toast_sanitized": "✨ Output sanitized & formatted",
        "lbl_critical_section_optional": "Critical Reflection & Application Decision (Optional)",
        "switch_critical": "Add Critical Reflection & Plausibility Audit",
        "crit_heading": "Critical Reflection & Plausibility Audit",
        "crit_subhint_desc": "Reflect on the plausibility, logical coherence, and reasoning quality of the AI's response.",
        "lbl_crit_flaws": "Plausibility Flaws & Logic Gaps",
        "crit_flaws_hint": "Describe any hallucinations, factual errors, reasoning gaps, or bias detected in the output.",
        "lbl_decision": "Application Decision for Assignment",
        "crit_decision_hint": "How did you utilize this output in your academic work?",
        
        "switch_fact_check": "Add Primary Source Fact-Check",
        "fc_subhint_desc": "Verify specific empirical claims or citations against primary literature or official data.",
        "btn_add_drop": "+ Add Interaction to Protocol",
        "btn_update_drop": "✓ Update Interaction #{num}",
        "btn_reset_form": "Reset Form",
        "log_session_drops_title": "Logged Interactions ({count})",
        "log_empty_drops": "No interactions recorded yet.\nFill the form on the left to add your first interaction.",
        "badge_fact_checks": "🔍 {count} Fact-Check",
        "val_prompt_required": "Please enter the Raw Prompt before adding.",
        "val_output_required": "Please enter the Raw Output before adding.",
        
        # Fact-Check Matrix View
        "fc_view_title": "Claim & Source Verification Matrix",
        "fc_view_desc": "Audited empirical claims verified against primary academic literature. These compile into Section B of your exported protocol.",
        "fc_empty": "No verification items recorded.\nUse the form below to audit a claim from an interaction or standalone literature.",
        "fc_th_origin": "Origin / Interaction",
        "fc_th_claim": "Claim / Extracted Fact",
        "fc_th_source": "Verification Sources & Evidence",
        "fc_th_status": "Status",
        "fc_th_note": "Audit Note",
        "fc_th_action": "Action",
        "fc_add_entry_title": "+ Add Verification Entry",
        "fc_edit_entry_title": "✏️ Edit Verification Entry",
        "lbl_fc_link_drop": "Link to Interaction",
        "opt_standalone_drop": "Standalone / General (No specific interaction)",
        "lbl_fc_claim": "Extracted Claim / Statement to Audit*",
        "ph_fc_claim": "What specific factual, numerical, or empirical claim did the AI make?",
        "lbl_fc_source": "Verification Sources & Evidence (URL, DOI, Book, Data)*",
        "ph_fc_source": "e.g. Yin (2018) p. 55, DOI 10.1000/182, Interview Transcript",
        "lbl_fc_is_file": "External Evidence File (e.g. dataset, transcript, appendix)",
        "tooltip_fc_is_file": "Mark if this evidence is an accompanying file rather than a web link or book.",
        "lbl_fc_status": "Verification Status* (Select preset or type custom)",
        "lbl_fc_note": "Audit & Rectification Note (Optional)",
        "ph_fc_note": "How did you correct or contextualize this claim in your thesis text?",
        "btn_add_entry": "+ Add Entry",
        "btn_update_entry": "✓ Update Entry",
        "btn_cancel_edit_fc": "Cancel Edit",
        "badge_file_evidence": "📁 File",
        "val_claim_required": "Please enter a Claim to audit.",
        "val_source_required": "Please enter a Verification Source or evidence.",
        "tooltip_click_edit_fc": "Click or double-click to edit this verification entry in the form below.",
        
        # Preview & Export View
        "prev_title": "Export & Protocol Generation",
        "btn_copy_markdown": "📋 Copy Markdown",
        "btn_copied": "✓ Copied!",
        "btn_save_md": "💾 Save .md",
        "btn_render_pdf": "📄 Render to PDF",
        "status_copied": "Markdown protocol copied to clipboard.",
        "status_pdf_rendered": "PDF rendered: {name}",
        "export_success_title": "Export Successful",
        "export_success_msg": "Markdown protocol exported successfully to:\n{path}",
        "export_failed_title": "Export Failed",
        "pdf_error_title": "PDF Rendering Error",
        
        # About & Help Dialog
        "about_dialog_title": "About BlaBlAI & Scholarly Usage Guide",
        "about_creator_label": "Conceived, Designed & Maintained by:",
        "about_creator_name": "Sven Várszegi, B.A.",
        "about_creator_affiliation": "Master Digital Business Management (FH Oberösterreich / Johannes Kepler Universität Linz)",
        "about_purpose_title": "Academic Purpose & Integrity Receipt",
        "about_purpose_desc": "BlaBlAI serves as an immutable, tamper-evident interaction protocol for generative AI use in higher education. Rather than treating AI as forbidden or concealed, it establishes a verifiable academic audit trail that transparently documents prompts, model outputs, plausibility checks, and primary-source verification. Exported receipts are sealed with a SHA-256 cryptographic digest to certify post-submission authenticity.",
        "about_workflow_title": "3-Step Workflow",
        "about_step1_title": "1. Set Academic Profile",
        "about_step1_desc": "Configure your name, student ID, and degree program once. They prefill every newly created protocol.",
        "about_step2_title": "2. Log While You Work",
        "about_step2_desc": "Whenever you consult an AI engine, log the raw prompt, output, scholarly intent, and any factual corrections. For non-textual outputs (videos, diagrams, datasets), log the reference filename (e.g. video.mp4).",
        "about_step3_title": "3. Export Verified Receipt",
        "about_step3_desc": "Generate a clean, monochrome bilingual PDF or Markdown protocol to attach as a formal appendix to your submission.",
        "about_license": "Academic Free & Open Source Utility | Austrian & European Higher Education AI Guidelines Compliant",
    },
    "de": {
        # App Branding
        "app_title": "BlaBlAI",
        "app_subtitle": "",
        "app_window_title": "BlaBlAI — Akademisches KI-Interaktionsprotokoll: Logger & Exporter",
        "home_label": "Home",
        
        # Profile & Affidavits
        "user_profile": "Benutzerprofil",
        "profile_heading": "Benutzerprofil & Akademische Identität",
        "profile_subheading": "Ihre persönlichen Stammdaten und Standard-Erklärungen für Protokollköpfe.",
        "lbl_matriculation": "Matrikelnummer / Personenkennzeichen",
        "lbl_affidavit_en": "Eidesstattliche Erklärung zu KI (Englisch)",
        "lbl_affidavit_de": "Ehrenwörtliche Erklärung zu KI (Deutsch)",
        "btn_reset_affidavits": "Erklärungen auf Standard zurücksetzen",
        
        # Read-Only External Author Guard
        "lbl_external_author": "🔒 Externer Autor (Schreibgeschützt)",
        "badge_external_author_hint": "Dieses Protokoll stammt von {author}. Autorenfelder sind geschützt.",
        "btn_unlock_author": "🔓 Autorenfelder freischalten",
        
        # Tooltips
        "tooltip_engine": "Wählen oder tippen Sie das verwendete KI-Modell.",
        "tooltip_intent": "Wissenschaftlicher Zweck oder Kernabsicht der Abfrage.",
        "tooltip_scope": "Übergebene Dokumente, Kapitel oder Kontextfenster.",
        "tooltip_prompt": "Der exakt an die KI übermittelte Prompt-Text.",
        "tooltip_output": "Die vollständige, unmodifizierte Antwort der KI.",
        "tooltip_crit_toggle": "Erweitern für Plausibilitätsprüfung und Argumentationsmängel.",
        "tooltip_fc_toggle": "Erweitern für Primärquellen-Verifikation einzelner Aussagen.",
        "tooltip_add_drop": "Diesen Interaktionseintrag zum Protokoll hinzufügen.",
        "tooltip_reset_drop": "Formular zurücksetzen für neuen Eintrag.",
        "tooltip_lang": "Sprache zwischen Englisch und Deutsch umschalten.",
        "tooltip_theme": "Zwischen Dunkel- und Hell-Modus umschalten.",
        "tooltip_profile": "Persönliche Daten und Erklärungen anpassen.",
        
        # Audit & Tamper-Evidence
        "audit_block_heading": "Verifikation & Revisionssicherheit",
        "audit_integrity_hash": "Kryptografischer SHA-256 Hash",
        "audit_timestamp": "Revisionszeitstempel",
        "audit_total_drops": "Erfasste Interaktionseinträge",
        "audit_total_facts": "Geprüfte Faktenbehauptungen",
        "audit_notice": "Dieser kryptografische SHA-256 Digest belegt die Authentizität und Unveränderbarkeit der dokumentierten Interaktionen. Jede nachträgliche manuelle Manipulation aufgezeichneter Prompts oder Ausgaben macht diesen Digest ungültig.",
        
        # Navigation & Common
        "btn_back_to_hub": "← Startseite",
        "btn_save": "Änderungen speichern",
        "btn_cancel": "Abbrechen",
        "btn_delete": "Löschen",
        "btn_edit": "Bearbeiten",
        "btn_open": "Öffnen",
        "btn_refresh": "Aktualisieren",
        "btn_theme": "🌓 Farbmodus",
        "btn_about": "ℹ️ Über & Hilfe",
        "lbl_autosave_banner": "💾 Fortlaufende Autospeicherung aktiv — Alle Änderungen werden sofort in der lokalen .ailog gesichert",
        "btn_tidy_text": "🧹 Bereinigen",
        "tooltip_tidy_text": "Aufzählungen glätten, überflüssige Codeblöcke entfernen und Text als sauberen Beleg formatieren",
        "onboarding_welcome_title": "👋 Willkommen bei BlaBlAI!",
        "onboarding_welcome_desc": "Willkommen! Bitte richten Sie kurz Ihre akademischen Stammdaten ein. Diese werden künftig automatisch in jedes neue Protokoll übernommen.",
        "tooltip_new_doc_title": "Titel Ihrer Abschlussarbeit, Seminararbeit oder Projektaufgabe.",
        "tooltip_new_doc_course": "Offizieller Modul-/Lehrveranstaltungscode und Name (z. B. DBM24-Seminar).",
        "tooltip_new_doc_examiner": "Prüfende(r) oder betreuende(r) Professor(in).",
        "tooltip_new_doc_scope": "Akademischer Umfang bzw. Art der wissenschaftlichen Arbeit.",
        "tooltip_profile_name": "Ihr Name samt akademischer Grade (z. B. Sven Várszegi, B.A.).",
        "tooltip_profile_degree": "Studiengang und Hochschule.",
        "tooltip_profile_matriculation": "Offizielle Matrikelnummer bzw. Personenkennzeichen.",
        "tooltip_profile_models": "Standardmäßige generative KI-Modelle, die Sie primär nutzen.",
        "status_saved": "● Gespeichert",
        "status_saved_time": "● Gespeichert ({time})",
        "status_save_error": "⚠ Speicherfehler",
        "confirm_delete_title": "Löschen bestätigen",
        "confirm_delete_doc_msg": "Möchten Sie '{title}' wirklich unwiderruflich löschen?",
        "confirm_delete_drop_msg": "Möchten Sie Interaktion #{num} wirklich löschen?",
        
        # Hub View
        "hub_storage_folder": "📁 Speicherordner: {folder}",
        "btn_open_explorer": "📂 Im Explorer öffnen",
        "btn_change_folder": "Ordner wechseln...",
        "btn_new_document": "+ Neues Dokument",
        "btn_open_external": "📂 Externe .ailog öffnen...",
        "hub_recent_docs_title": "Aktuelle Dokumente ({count})",
        "hub_empty_title": "📄 Keine KI-Protokolle gefunden",
        "hub_empty_desc": "Klicken Sie oben auf '+ Neues Dokument', um Ihr erstes Interaktionsprotokoll anzulegen.",
        "btn_create_first": "+ Erstes Dokument anlegen",
        "card_course_scope": "Lehrveranstaltung: {course}  |  Art: {scope}",
        "card_drops_count": "{count} Interaktionen protokolliert",
        "card_modified": "Geändert: {time}",
        "dialog_change_folder_title": "Speicherordner für KI-Protokolle auswählen",
        "dialog_open_external_title": "Akademisches KI-Protokoll (.ailog) öffnen",
        
        # Editor Tabs
        "tab_drops": "  Interaktionen  ",
        "tab_matrix": "  Verifikationsmatrix  ",
        "tab_preview": "  Vorschau & Export  ",
        
        # Metadata Dialog
        "meta_dialog_title_new": "Neues KI-Protokoll anlegen",
        "meta_dialog_title_edit": "Dokumenten- & Metadaten bearbeiten",
        "meta_heading": "Akademische Metadaten & Konfiguration",
        "meta_subheading": "Angaben zu Hochschule, Studiengang, Prüfenden und verwendeten KI-Modellen.",
        "lbl_doc_title": "Dokumententitel / Arbeitsthema",
        "lbl_student_name": "Name der Verfasserin / des Verfassers (inkl. Titel)",
        "lbl_degree_program": "Studiengang & Hochschule",
        "lbl_course_code": "Lehrveranstaltung / Modul (Code & Titel)",
        "lbl_assignment_scope": "Art der wissenschaftlichen Arbeit",
        "lbl_examiner": "Prüfende(r) / Erstbetreuung",
        "lbl_submission_date": "Abgabedatum (JJJJ-MM-TT)",
        "lbl_primary_models": "Primäre KI-Modelle",
        "lbl_secondary_models": "Sekundäre / Unterstützende KI-Modelle",
        "cb_save_defaults": "Name, Studiengang und Modelle dauerhaft als Standard speichern",
        "btn_create_doc": "Dokument erstellen",
        "btn_edit_info": "⚙ Info bearbeiten",
        
        # Drop Logger
        "log_heading_new": "Neue KI-Interaktion erfassen",
        "log_heading_edit": "Interaktion #{num} bearbeiten",
        "lbl_drop_title": "Titel / Kurzbeschreibung der Interaktion (optional)",
        "ph_drop_title": "z. B. Visplore Diagramm, Literatursynthese Smith (2023), DB-Architektur",
        "lbl_timestamp": "Zeitstempel (CEST / MEZ)*",
        "btn_now": "↺ Jetzt",
        "btn_pick_datetime": "📅",
        "tooltip_pick_datetime": "Visuelle Kalender- und Zeitauswahl öffnen",
        "lbl_retroactive": "Nachträglich / Archiv",
        "tooltip_retroactive": "Aktivieren, wenn die Interaktion früher stattfand oder die genaue Uhrzeit unkritisch ist (nur Datum).",
        "badge_retroactive": "Nachträglich",
        "dt_dialog_title": "Datum & Uhrzeit auswählen",
        "dt_lbl_date": "Kalenderdatum",
        "dt_lbl_time": "Uhrzeit (24 Std.)",
        "dt_lbl_hour": "Stunde",
        "dt_lbl_minute": "Minute",
        "dt_btn_apply": "Übernehmen",
        "dt_btn_cancel": "Abbrechen",
        "dt_btn_now": "↺ Jetzt",
        "lbl_engine": "Verwendetes KI-Modell / Engine*",
        "lbl_intent": "Primärer Einsatzzweck*",
        "lbl_context_scope": "Kontext / Eingebettete Quellen (optional)",
        "ph_context_scope": "z. B. Hochgeladene PDFs, Skript Kapitel 1-3, Websuche",
        "lbl_raw_prompt": "Unveränderter Prompt (Eingabe)*",
        "lbl_raw_output": "Unveränderte KI-Antwort (Ausgabe)*",
        "lbl_file_reference": "Generierte Datei- / Medienreferenz (optional)",
        "ph_file_reference": "z. B. video.mp4, architektur_diagramm.png, chart.svg, daten.csv",
        "tooltip_file_reference": "Verweisen Sie auf durch die KI erstellte Mediendateien (z. B. Videos, Bilder, Diagramme, Audio oder Datensätze im Anhang Ihrer Arbeit).",
        "toast_sanitized": "✨ KI-Antwort bereinigt & formatiert",
        "lbl_critical_section_optional": "Kritische Reflexion & Übernahmeentscheidung (optional)",
        "switch_critical": "Kritische Reflexion & Plausibilitätsprüfung hinzufügen",
        "crit_heading": "Kritische Reflexion & Plausibilitätsprüfung",
        "crit_subhint_desc": "Reflektieren Sie über die Plausibilität, logische Kohärenz und Qualität der KI-Antwort.",
        "lbl_crit_flaws": "Plausibilitätsmängel & logische Lücken",
        "crit_flaws_hint": "Beschreiben Sie Halluzinationen, sachliche Fehler, logische Brüche oder Verzerrungen.",
        "lbl_decision": "Verwendungsentscheidung für die fertige Arbeit",
        "crit_decision_hint": "Wie haben Sie diese KI-Antwort in Ihrer wissenschaftlichen Arbeit verwendet?",
        
        "switch_fact_check": "Faktenprüfung anhand wissenschaftlicher Primärquellen hinzufügen",
        "fc_subhint_desc": "Überprüfen Sie spezifische empirische Aussagen oder Zitate anhand wissenschaftlicher Primärliteratur.",
        "btn_add_drop": "+ Interaktion zum Protokoll hinzufügen",
        "btn_update_drop": "✓ Interaktion #{num} aktualisieren",
        "btn_reset_form": "Formular leeren",
        "log_session_drops_title": "Protokollierte Interaktionen ({count})",
        "log_empty_drops": "Noch keine Interaktionen erfasst.\nFüllen Sie das Formular links aus, um die erste Interaktion zu erfassen.",
        "badge_fact_checks": "🔍 {count} Faktenprüfung",
        "val_prompt_required": "Bitte geben Sie den unveränderten Prompt ein.",
        "val_output_required": "Bitte geben Sie die unveränderte KI-Antwort ein.",
        
        # Fact-Check Matrix View
        "fc_view_title": "Quellen- & Tatsachenverifikation",
        "fc_view_desc": "Überprüfte empirische Aussagen anhand wissenschaftlicher Fachliteratur. Erscheint in Abschnitt B des Exportprotokolls.",
        "fc_empty": "Noch keine Verifikationseinträge hinterlegt.\nNutzen Sie das Formular unten, um einen Prüfeintrag aus einer Interaktion oder eigenständig anzulegen.",
        "fc_th_origin": "Herkunft / Interaktion",
        "fc_th_claim": "Behauptung / Faktenelement",
        "fc_th_source": "Verifikationsquellen & Belege",
        "fc_th_status": "Status",
        "fc_th_note": "Korrekturanmerkung",
        "fc_th_action": "Aktion",
        "fc_add_entry_title": "+ Neuen Verifikationseintrag anlegen",
        "fc_edit_entry_title": "✏️ Verifikationseintrag bearbeiten",
        "lbl_fc_link_drop": "Zuordnung zu Interaktion",
        "opt_standalone_drop": "Eigenständig / Allgemein (Keine spezifische Interaktion)",
        "lbl_fc_claim": "Extrahierte Behauptung / Zu prüfende Aussage*",
        "ph_fc_claim": "Welche konkrete faktische, numerische oder empirische Aussage traf die KI?",
        "lbl_fc_source": "Verifikationsquellen & Belege (URL, DOI, Buch, Daten)*",
        "ph_fc_source": "z. B. Yin (2018) S. 55, DOI 10.1000/182, Interview-Transkript",
        "lbl_fc_is_file": "Externe Belegdatei (z. B. Datensatz, Transkript, Anhang)",
        "tooltip_fc_is_file": "Aktivieren, wenn dieser Beleg eine eingereichte Datei im Anhang ist.",
        "lbl_fc_status": "Verifikationsstatus* (Vorgabe wählen oder frei eingeben)",
        "lbl_fc_note": "Korrektur- & Richtigstellungsnotiz (optional)",
        "ph_fc_note": "Wie wurde diese Aussage im finalen Text Ihrer Arbeit korrigiert oder eingeordnet?",
        "btn_add_entry": "+ Eintrag anlegen",
        "btn_update_entry": "✓ Eintrag aktualisieren",
        "btn_cancel_edit_fc": "Bearbeitung abbrechen",
        "badge_file_evidence": "📁 Datei",
        "val_claim_required": "Bitte geben Sie eine zu prüfende Behauptung ein.",
        "val_source_required": "Bitte geben Sie eine Verifikationsquelle oder einen Beleg ein.",
        "tooltip_click_edit_fc": "Klicken oder doppelklicken, um diesen Eintrag im Formular unten zu bearbeiten.",
        
        # Preview & Export View
        "prev_title": "Protokollvorschau & Export",
        "btn_copy_markdown": "📋 Markdown kopieren",
        "btn_copied": "✓ Kopiert!",
        "btn_save_md": "💾 Als .md speichern",
        "btn_render_pdf": "📄 PDF erstellen",
        "status_copied": "Markdown-Protokoll in die Zwischenablage kopiert.",
        "status_pdf_rendered": "PDF erstellt: {name}",
        "export_success_title": "Export erfolgreich",
        "export_success_msg": "Markdown-Protokoll erfolgreich gespeichert unter:\n{path}",
        "export_failed_title": "Export Fehlgeschlagen",
        "pdf_error_title": "Fehler bei PDF-Erstellung",
        
        # About & Help Dialog
        "about_dialog_title": "Über BlaBlAI & Wissenschaftliche Anleitung",
        "about_creator_label": "Konzipiert, Entwickelt & Betreut von:",
        "about_creator_name": "Sven Várszegi, B.A.",
        "about_creator_affiliation": "Master Digital Business Management (FH Oberösterreich / Johannes Kepler Universität Linz)",
        "about_purpose_title": "Wissenschaftlicher Zweck & Transparenzbeleg",
        "about_purpose_desc": "BlaBlAI dient als manipulationssicheres Interaktionsprotokoll für generative KI im akademischen Hochschulkontext. Statt den Einsatz von KI zu verschweigen, schafft es einen nachvollziehbaren Prüfpfad: Prompts, KI-Ausgaben, Plausibilitätsprüfungen und Faktenverifikationen werden lückenlos dokumentiert. Exportierte Belege werden mit einer kryptografischen SHA-256 Prüfsumme versiegelt, um die nachträgliche Unverfälschtheit nach der Abgabe zu zertifizieren.",
        "about_workflow_title": "3-Schritte-Workflow",
        "about_step1_title": "1. Akademisches Profil einrichten",
        "about_step1_desc": "Hinterlegen Sie Name, Matrikelnummer und Studiengang einmalig. Diese Daten werden automatisch in jedes neue Protokoll übernommen.",
        "about_step2_title": "2. Begleitend protokollieren",
        "about_step2_desc": "Erfassen Sie während der Recherche und Textarbeit jeden relevanten Prompt, Output, Einsatzzweck und Faktenabgleich. Bei nicht-textuellen Ausgaben (Videos, Diagrammen, Daten) genügt die Dateireferenz (z. B. video.mp4).",
        "about_step3_title": "3. Geprüften Beleg exportieren",
        "about_step3_desc": "Erstellen Sie ein sauberes, monochromes und zweisprachiges PDF oder Markdown als offiziellen Anhang Ihrer Einreichung.",
        "about_license": "Akademisches Open-Source-Werkzeug | Konform mit den Richtlinien österreichischer und europäischer Hochschulen",
    }
}

# Bidirectional translations for select option values (UI display vs canonical internal value)
INTENT_TRANSLATIONS = {
    "en": {
        "Synthesis": "Synthesis",
        "Method Check": "Method Check",
        "Drafting": "Drafting",
        "Brainstorming": "Brainstorming",
        "Verification": "Verification",
        "Code Generation": "Code Generation",
        "Refinement & Polishing": "Refinement & Polishing",
        "Other": "Other",
    },
    "de": {
        "Synthesis": "Synthese & Zusammenfassung",
        "Method Check": "Methodenprüfung",
        "Drafting": "Entwurf & Textformulierung",
        "Brainstorming": "Brainstorming & Ideenfindung",
        "Verification": "Verifikation & Plausibilität",
        "Code Generation": "Code-Generierung",
        "Refinement & Polishing": "Überarbeitung & Feinschliff",
        "Other": "Sonstiges",
    }
}

DECISION_TRANSLATIONS = {
    "en": {
        "N/A": "N/A",
        "Accepted": "Accepted",
        "Modified": "Modified",
        "Rejected": "Rejected",
    },
    "de": {
        "N/A": "N/A",
        "Accepted": "Akzeptiert",
        "Modified": "Modifiziert",
        "Rejected": "Abgelehnt",
    }
}

STATUS_TRANSLATIONS = {
    "en": {
        "Confirmed": "Confirmed",
        "Refuted": "Refuted",
        "Clarified": "Clarified",
        "Disputed": "Disputed",
        "Untestable": "Untestable",
    },
    "de": {
        "Confirmed": "Bestätigt",
        "Refuted": "Widerlegt",
        "Clarified": "Präzisiert",
        "Disputed": "Umstritten",
        "Untestable": "Nicht prüfbar",
    }
}

SCOPE_TRANSLATIONS = {
    "en": {
        "Master's Thesis": "Master's Thesis",
        "Bachelor's Thesis": "Bachelor's Thesis",
        "Seminar Paper": "Seminar Paper",
        "Course Project": "Course Project",
        "Case Study / Homework": "Case Study / Homework",
        "Other": "Other",
    },
    "de": {
        "Master's Thesis": "Masterarbeit",
        "Bachelor's Thesis": "Bachelorarbeit",
        "Seminar Paper": "Seminararbeit",
        "Course Project": "Projektarbeit",
        "Case Study / Homework": "Fallstudie / Hausarbeit",
        "Other": "Sonstiges",
    }
}


def get_current_locale() -> str:
    """Returns current active locale ('en' or 'de')."""
    return _CURRENT_LOCALE


def set_current_locale(locale: str) -> None:
    """Sets active locale and notifies registered listeners."""
    global _CURRENT_LOCALE
    clean = locale.lower().strip()
    if clean in ("de", "german", "deutsch"):
        _CURRENT_LOCALE = "de"
    else:
        _CURRENT_LOCALE = "en"

    for listener in _LOCALE_LISTENERS:
        try:
            listener(_CURRENT_LOCALE)
        except Exception as e:
            print(f"Error in locale listener: {e}")


def add_locale_listener(callback: Callable[[str], None]) -> None:
    """Registers a listener to be notified when language changes."""
    if callback not in _LOCALE_LISTENERS:
        _LOCALE_LISTENERS.append(callback)


def remove_locale_listener(callback: Callable[[str], None]) -> None:
    """Removes a registered locale listener."""
    if callback in _LOCALE_LISTENERS:
        _LOCALE_LISTENERS.remove(callback)


def t(key: str, **kwargs) -> str:
    """Translates a key into current active locale with optional keyword formatting."""
    lang_dict = TRANSLATIONS.get(_CURRENT_LOCALE, TRANSLATIONS["en"])
    text = lang_dict.get(key)
    if text is None:
        # Fallback to English
        text = TRANSLATIONS["en"].get(key, key)
    if kwargs:
        try:
            return text.format(**kwargs)
        except Exception:
            return text
    return text


def get_localized_intents() -> List[str]:
    """Returns list of intent strings localized for current language."""
    mapping = INTENT_TRANSLATIONS.get(_CURRENT_LOCALE, INTENT_TRANSLATIONS["en"])
    return [mapping.get(canonical, canonical) for canonical in CANONICAL_INTENTS]


def canonicalize_intent(localized_intent: str) -> str:
    """Maps a localized or custom intent back to canonical English for storage."""
    mapping = INTENT_TRANSLATIONS.get(_CURRENT_LOCALE, INTENT_TRANSLATIONS["en"])
    for canonical, loc in mapping.items():
        if loc == localized_intent:
            return canonical
    return localized_intent


def localize_intent(canonical_intent: str) -> str:
    """Maps canonical English intent to current localized display string."""
    mapping = INTENT_TRANSLATIONS.get(_CURRENT_LOCALE, INTENT_TRANSLATIONS["en"])
    return mapping.get(canonical_intent, canonical_intent)


def get_localized_decisions() -> List[str]:
    """Returns list of decisions localized for current language."""
    mapping = DECISION_TRANSLATIONS.get(_CURRENT_LOCALE, DECISION_TRANSLATIONS["en"])
    return [mapping.get(canonical, canonical) for canonical in CANONICAL_DECISIONS]


def canonicalize_decision(localized_decision: str) -> str:
    """Maps a localized decision back to canonical English for storage."""
    mapping = DECISION_TRANSLATIONS.get(_CURRENT_LOCALE, DECISION_TRANSLATIONS["en"])
    for canonical, loc in mapping.items():
        if loc == localized_decision:
            return canonical
    return localized_decision


def localize_decision(canonical_decision: str) -> str:
    """Maps canonical English decision to current localized display string."""
    mapping = DECISION_TRANSLATIONS.get(_CURRENT_LOCALE, DECISION_TRANSLATIONS["en"])
    return mapping.get(canonical_decision, canonical_decision)


def get_localized_statuses() -> List[str]:
    """Returns list of statuses localized for current language."""
    mapping = STATUS_TRANSLATIONS.get(_CURRENT_LOCALE, STATUS_TRANSLATIONS["en"])
    return [mapping.get(canonical, canonical) for canonical in CANONICAL_STATUSES]


def canonicalize_status(localized_status: str) -> str:
    """Maps a localized status back to canonical English for storage."""
    mapping = STATUS_TRANSLATIONS.get(_CURRENT_LOCALE, STATUS_TRANSLATIONS["en"])
    for canonical, loc in mapping.items():
        if loc == localized_status:
            return canonical
    return localized_status


def localize_status(canonical_status: str) -> str:
    """Maps canonical English status to current localized display string."""
    mapping = STATUS_TRANSLATIONS.get(_CURRENT_LOCALE, STATUS_TRANSLATIONS["en"])
    return mapping.get(canonical_status, canonical_status)


def get_localized_scopes() -> List[str]:
    """Returns list of assignment scopes localized for current language."""
    mapping = SCOPE_TRANSLATIONS.get(_CURRENT_LOCALE, SCOPE_TRANSLATIONS["en"])
    return [mapping.get(canonical, canonical) for canonical in CANONICAL_SCOPES]


def canonicalize_scope(localized_scope: str) -> str:
    """Maps a localized scope back to canonical English for storage."""
    mapping = SCOPE_TRANSLATIONS.get(_CURRENT_LOCALE, SCOPE_TRANSLATIONS["en"])
    for canonical, loc in mapping.items():
        if loc == localized_scope:
            return canonical
    return localized_scope


def localize_scope(canonical_scope: str) -> str:
    """Maps canonical English scope to current localized display string."""
    mapping = SCOPE_TRANSLATIONS.get(_CURRENT_LOCALE, SCOPE_TRANSLATIONS["en"])
    return mapping.get(canonical_scope, canonical_scope)
