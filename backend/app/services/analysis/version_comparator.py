import difflib
import re
from typing import Dict, Any, List
from app.services.analysis.clause_decomposer import ClauseDecomposer
from app.services.analysis.defect_detector import DefectDetector


class VersionComparator:
    """
    Motor analítico de comparación entre versiones documentales (Redline & Risk Delta).
    Permite identificar adiciones, supresiones, modificaciones de cláusulas y cambios en la matriz de riesgos.
    """

    @classmethod
    def compare_documents(
        cls,
        base_text: str,
        compare_text: str,
        base_label: str = "Versión Base",
        compare_label: str = "Versión Comparada"
    ) -> Dict[str, Any]:
        """
        Ejecuta la comparación integral entre dos textos contractuales o judiciales.
        """
        # 1. Descomponer cláusulas de ambas versiones
        base_clauses = ClauseDecomposer.decompose(base_text)
        comp_clauses = ClauseDecomposer.decompose(compare_text)

        base_titles = {cls._normalize_title(c["title"]): c for c in base_clauses}
        comp_titles = {cls._normalize_title(c["title"]): c for c in comp_clauses}

        added = []
        removed = []
        modified = []

        # Detectar cláusulas eliminadas o modificadas
        for norm_t, b_clause in base_titles.items():
            if norm_t not in comp_titles:
                removed.append({
                    "title": b_clause["title"],
                    "clause_number": b_clause["clause_number"],
                    "summary": b_clause["summary"],
                    "raw_text": b_clause["raw_text"]
                })
            else:
                c_clause = comp_titles[norm_t]
                if cls._has_meaningful_diff(b_clause["raw_text"], c_clause["raw_text"]):
                    diff_snippet = cls._generate_diff_summary(b_clause["raw_text"], c_clause["raw_text"])
                    modified.append({
                        "title": b_clause["title"],
                        "clause_number": b_clause["clause_number"],
                        "change_summary": diff_snippet,
                        "base_text": b_clause["raw_text"][:250],
                        "compare_text": c_clause["raw_text"][:250]
                    })

        # Detectar cláusulas añadidas
        for norm_t, c_clause in comp_titles.items():
            if norm_t not in base_titles:
                added.append({
                    "title": c_clause["title"],
                    "clause_number": c_clause["clause_number"],
                    "summary": c_clause["summary"],
                    "raw_text": c_clause["raw_text"]
                })

        # 2. Análisis del Delta de Riesgos (Risk Delta)
        base_findings = DefectDetector.detect_all(base_text, base_clauses)
        comp_findings = DefectDetector.detect_all(compare_text, comp_clauses)

        base_issues = {f["title"]: f for f in base_findings}
        comp_issues = {f["title"]: f for f in comp_findings}

        mitigated = []
        introduced = []
        persistent = []

        for title, f in base_issues.items():
            if title not in comp_issues:
                mitigated.append({
                    "title": f["title"],
                    "severity": f["severity"],
                    "description": f["description"]
                })
            else:
                persistent.append({
                    "title": f["title"],
                    "severity": f["severity"]
                })

        for title, f in comp_issues.items():
            if title not in base_issues:
                introduced.append({
                    "title": f["title"],
                    "severity": f["severity"],
                    "description": f["description"]
                })

        summary_text = (
            f"Comparativa entre '{base_label}' y '{compare_label}': "
            f"Se identificaron {len(added)} cláusula(s) agregada(s), {len(removed)} suprimida(s) y {len(modified)} modificada(s). "
            f"En términos de riesgos: {len(mitigated)} riesgo(s) fueron mitigados o resueltos, "
            f"{len(introduced)} nuevo(s) riesgo(s) introducidos y {len(persistent)} se mantienen sin variación."
        )

        return {
            "base_version_label": base_label,
            "compare_version_label": compare_label,
            "added_clauses": added,
            "removed_clauses": removed,
            "modified_clauses": modified,
            "risk_delta": {
                "mitigated_risks": mitigated,
                "introduced_risks": introduced,
                "persistent_risks": persistent
            },
            "summary": summary_text
        }

    @staticmethod
    def _normalize_title(title: str) -> str:
        """Normaliza el título de cláusula para emparejar versiones."""
        t = re.sub(r'[\d\.\:\-\s]+', ' ', title.lower()).strip()
        # Tomar las primeras dos palabras clave
        words = t.split()
        return " ".join(words[:3]) if words else "clausula"

    @staticmethod
    def _has_meaningful_diff(text_a: str, text_b: str) -> bool:
        norm_a = " ".join(text_a.split()).lower()
        norm_b = " ".join(text_b.split()).lower()
        return norm_a != norm_b

    @staticmethod
    def _generate_diff_summary(text_a: str, text_b: str) -> str:
        """Calcula una síntesis de cambios de palabras clave."""
        words_a = set(re.findall(r'\b\w{4,}\b', text_a.lower()))
        words_b = set(re.findall(r'\b\w{4,}\b', text_b.lower()))

        added_words = words_b - words_a
        removed_words = words_a - words_b

        changes = []
        if added_words:
            changes.append(f"Términos incorporados: {', '.join(list(added_words)[:5])}")
        if removed_words:
            changes.append(f"Términos suprimidos: {', '.join(list(removed_words)[:5])}")

        return " | ".join(changes) if changes else "Ajustes de redacción y formato general."
