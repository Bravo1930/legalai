import re
import unicodedata
from typing import Dict, Any, List, Optional, Tuple
from app.models.document import Document
from app.models.rule import (
    LegalRule, RuleOperator, RuleEvaluationStatus
)


class DeterministicRuleEngine:
    """
    Motor de Reglas Deterministas para Auditoría Contractual y Jurídica.
    
    PRINCIPIOS:
    1. Cero probabilidad: No utiliza LLMs ni modelos neuronales.
    2. Determinismo 100%: Mismo documento + misma regla = idéntico veredicto siempre.
    3. Cero falsas acusaciones: Si una condición no se puede comprobar con certeza absoluta,
       se cataloga como PENDING_HUMAN_REVIEW y NUNCA como NON_COMPLIANT.
    4. Aislamiento por despacho (Multi-tenant) y ámbito documental (Scope).
    """

    @staticmethod
    def normalize_text(text: str, remove_accents: bool = True) -> str:
        """Normaliza espacios, saltos de línea y opcionalmente diacríticos para búsqueda robusta."""
        if not text:
            return ""
        # Normalizar espacios
        normalized = " ".join(text.split())
        if remove_accents:
            # Descomponer diacríticos (ej. 'México' -> 'Mexico')
            normalized = unicodedata.normalize('NFD', normalized)
            normalized = "".join(ch for ch in normalized if unicodedata.category(ch) != 'Mn')
        return normalized.lower()

    @staticmethod
    def extract_snippet(text: str, start_pos: int, end_pos: int, padding: int = 120) -> str:
        """Extrae un fragmento de evidencia contextual alrededor de una coincidencia."""
        left = max(0, start_pos - padding)
        right = min(len(text), end_pos + padding)
        prefix = "..." if left > 0 else ""
        suffix = "..." if right < len(text) else ""
        raw_snippet = text[left:right].strip()
        # Normalizar espacios dentro del fragmento
        cleaned = " ".join(raw_snippet.split())
        return f"{prefix}{cleaned}{suffix}"

    def check_scope(self, rule: LegalRule, document: Document) -> Tuple[bool, Optional[str]]:
        """
        Verifica si el documento entra en el ámbito de aplicación de la regla.
        Retorna (aplica, motivo_no_aplica).
        """
        scope = rule.scope or {}

        # 1. Filtro por tipo documental
        doc_types = scope.get("doc_types")
        if doc_types and "*" not in doc_types:
            normalized_doc_types = [dt.upper() for dt in doc_types]
            current_doc_type = (document.doc_type or "").upper()
            if current_doc_type not in normalized_doc_types:
                return False, f"La regla solo aplica a tipos: {doc_types}. Tipo actual: {current_doc_type}"

        # 2. Filtro por cliente
        client_ids = scope.get("client_ids")
        if client_ids:
            client_id_strs = [str(cid) for cid in client_ids]
            current_client_id = str(document.client_id) if document.client_id else None
            if not current_client_id or current_client_id not in client_id_strs:
                return False, "La regla está restringida a clientes específicos no coincidentes."

        # 3. Filtro por materia jurídica (a través del caso asignado)
        legal_matters = scope.get("legal_matters")
        if legal_matters and "*" not in legal_matters:
            if hasattr(document, "case") and document.case:
                case_matter = (document.case.matter or "").upper()
                allowed_matters = [m.upper() for m in legal_matters]
                if case_matter not in allowed_matters:
                    return False, f"La regla aplica a materias {legal_matters}. Materia del caso: {case_matter}"

        # 4. Filtro por jurisdicción (a través de metadatos del documento)
        jurisdictions = scope.get("jurisdictions")
        if jurisdictions and "*" not in jurisdictions:
            meta = document.metadata_record
            if meta and meta.jurisdiction:
                norm_jurisdiction = meta.jurisdiction.upper()
                allowed_jur = [j.upper() for j in jurisdictions]
                if not any(j in norm_jurisdiction for j in allowed_jur):
                    return False, f"La regla aplica a jurisdicciones {jurisdictions}. Jurisdicción detectada: {meta.jurisdiction}"

        return True, None

    def evaluate_rule(self, rule: LegalRule, raw_text: str, document: Document) -> Dict[str, Any]:
        """
        Evalúa una regla determinista contra el texto y metadatos de un documento.
        Retorna dict con status, matched_evidence y failure_reason.
        """
        applies, not_applicable_reason = self.check_scope(rule, document)
        if not applies:
            return {
                "status": RuleEvaluationStatus.NOT_APPLICABLE,
                "matched_evidence": None,
                "failure_reason": not_applicable_reason
            }

        cond = rule.condition_definition or {}
        operator = cond.get("operator")
        params = cond.get("parameters", {})
        case_sensitive = params.get("case_sensitive", False)

        norm_text = raw_text if case_sensitive else self.normalize_text(raw_text, remove_accents=True)

        if operator == RuleOperator.CONTAINS_ALL_KEYWORDS:
            return self._eval_contains_all(params, raw_text, norm_text, case_sensitive)
        
        elif operator == RuleOperator.CONTAINS_ANY_KEYWORD:
            return self._eval_contains_any(params, raw_text, norm_text, case_sensitive)

        elif operator == RuleOperator.PROHIBITS_KEYWORDS:
            return self._eval_prohibits_keywords(params, raw_text, norm_text, case_sensitive)

        elif operator == RuleOperator.REGEX_MATCH:
            return self._eval_regex(params, raw_text)

        elif operator == RuleOperator.NUMERIC_RANGE:
            return self._eval_numeric_range(params, raw_text, document)

        elif operator == RuleOperator.METADATA_EQUALS:
            return self._eval_metadata_equals(params, document)

        elif operator == RuleOperator.METADATA_EXISTS:
            return self._eval_metadata_exists(params, document)

        else:
            return {
                "status": RuleEvaluationStatus.PENDING_HUMAN_REVIEW,
                "matched_evidence": None,
                "failure_reason": f"Operador determinista '{operator}' no reconocido. Requiere validación manual."
            }

    def _eval_contains_all(self, params: Dict[str, Any], raw_text: str, norm_text: str, case_sensitive: bool) -> Dict[str, Any]:
        keywords = params.get("keywords", [])
        if not keywords:
            return {
                "status": RuleEvaluationStatus.PENDING_HUMAN_REVIEW,
                "matched_evidence": None,
                "failure_reason": "La regla no especifica palabras clave obligatorias."
            }

        missing = []
        evidences = []

        for kw in keywords:
            search_kw = kw if case_sensitive else self.normalize_text(kw, remove_accents=True)
            pos = norm_text.find(search_kw)
            if pos != -1:
                snippet = self.extract_snippet(raw_text, pos, pos + len(search_kw))
                evidences.append(f"Término '{kw}' hallado: \"{snippet}\"")
            else:
                missing.append(kw)

        if not missing:
            return {
                "status": RuleEvaluationStatus.COMPLIANT,
                "matched_evidence": " | ".join(evidences),
                "failure_reason": None
            }
        else:
            return {
                "status": RuleEvaluationStatus.NON_COMPLIANT,
                "matched_evidence": " | ".join(evidences) if evidences else None,
                "failure_reason": f"Omisión de cláusula obligatoria. Términos ausentes en el documento: {', '.join(missing)}"
            }

    def _eval_contains_any(self, params: Dict[str, Any], raw_text: str, norm_text: str, case_sensitive: bool) -> Dict[str, Any]:
        keywords = params.get("keywords", [])
        if not keywords:
            return {
                "status": RuleEvaluationStatus.PENDING_HUMAN_REVIEW,
                "matched_evidence": None,
                "failure_reason": "No se configuraron palabras clave para búsqueda alternativa."
            }

        for kw in keywords:
            search_kw = kw if case_sensitive else self.normalize_text(kw, remove_accents=True)
            pos = norm_text.find(search_kw)
            if pos != -1:
                snippet = self.extract_snippet(raw_text, pos, pos + len(search_kw))
                return {
                    "status": RuleEvaluationStatus.COMPLIANT,
                    "matched_evidence": f"Término aceptado '{kw}' detectado: \"{snippet}\"",
                    "failure_reason": None
                }

        return {
            "status": RuleEvaluationStatus.NON_COMPLIANT,
            "matched_evidence": None,
            "failure_reason": f"Ninguno de los términos requeridos fue encontrado ({', '.join(keywords)})"
        }

    def _eval_prohibits_keywords(self, params: Dict[str, Any], raw_text: str, norm_text: str, case_sensitive: bool) -> Dict[str, Any]:
        keywords = params.get("prohibited_keywords") or params.get("keywords", [])
        if not keywords:
            return {
                "status": RuleEvaluationStatus.PENDING_HUMAN_REVIEW,
                "matched_evidence": None,
                "failure_reason": "No se configuraron términos prohibidos."
            }

        violating_evidences = []
        for kw in keywords:
            search_kw = kw if case_sensitive else self.normalize_text(kw, remove_accents=True)
            pos = norm_text.find(search_kw)
            if pos != -1:
                snippet = self.extract_snippet(raw_text, pos, pos + len(search_kw))
                violating_evidences.append(f"Cláusula/Término prohibido '{kw}' detectado: \"{snippet}\"")

        if violating_evidences:
            return {
                "status": RuleEvaluationStatus.NON_COMPLIANT,
                "matched_evidence": " | ".join(violating_evidences),
                "failure_reason": f"Se detectaron términos prohibidos en el documento ({len(violating_evidences)} coincidencias)."
            }

        return {
            "status": RuleEvaluationStatus.COMPLIANT,
            "matched_evidence": "Verificación determinista: No se detectó ninguna de las expresiones prohibidas.",
            "failure_reason": None
        }

    def _eval_regex(self, params: Dict[str, Any], raw_text: str) -> Dict[str, Any]:
        pattern = params.get("regex_pattern")
        expected_match = params.get("expected_match", True)

        if not pattern:
            return {
                "status": RuleEvaluationStatus.PENDING_HUMAN_REVIEW,
                "matched_evidence": None,
                "failure_reason": "Patrón de expresión regular no definido."
            }

        try:
            compiled = re.compile(pattern, re.IGNORECASE | re.MULTILINE)
        except re.error as err:
            return {
                "status": RuleEvaluationStatus.PENDING_HUMAN_REVIEW,
                "matched_evidence": None,
                "failure_reason": f"Sintaxis regex inválida en la regla: {str(err)}. Requiere corrección técnica."
            }

        match = compiled.search(raw_text)
        if expected_match:
            if match:
                snippet = self.extract_snippet(raw_text, match.start(), match.end())
                return {
                    "status": RuleEvaluationStatus.COMPLIANT,
                    "matched_evidence": f"Patrón encontrado: \"{snippet}\"",
                    "failure_reason": None
                }
            else:
                return {
                    "status": RuleEvaluationStatus.NON_COMPLIANT,
                    "matched_evidence": None,
                    "failure_reason": f"El documento no cumple con el patrón regular obligatorio: /{pattern}/"
                }
        else:
            # Se prohíbe el match
            if match:
                snippet = self.extract_snippet(raw_text, match.start(), match.end())
                return {
                    "status": RuleEvaluationStatus.NON_COMPLIANT,
                    "matched_evidence": f"Coincidencia prohibida encontrada: \"{snippet}\"",
                    "failure_reason": f"El documento contiene una estructura prohibida por el patrón: /{pattern}/"
                }
            else:
                return {
                    "status": RuleEvaluationStatus.COMPLIANT,
                    "matched_evidence": "No se encontraron coincidencias del patrón prohibido.",
                    "failure_reason": None
                }

    def _eval_numeric_range(self, params: Dict[str, Any], raw_text: str, document: Document) -> Dict[str, Any]:
        min_val = params.get("min_value")
        max_val = params.get("max_value")
        regex_extractor = params.get("regex_extractor")
        target_field = params.get("target_field")  # e.g., 'amount_mxn' or 'term_days'

        extracted_val = None
        evidence_snippet = None

        # 1. Intentar extraer mediante regex específico de la regla
        if regex_extractor:
            try:
                rx = re.compile(regex_extractor, re.IGNORECASE)
                m = rx.search(raw_text)
                if m and m.groups():
                    val_str = m.group(1).replace(",", "").replace("$", "").strip()
                    try:
                        extracted_val = float(val_str)
                        evidence_snippet = self.extract_snippet(raw_text, m.start(), m.end())
                    except ValueError:
                        pass
            except re.error:
                pass

        # 2. Si no se obtuvo por regex y hay metadatos estructurados
        if extracted_val is None and target_field and document.metadata_record:
            meta = document.metadata_record
            if target_field == "amount_mxn" and meta.amounts_detected:
                # Tomar el monto más alto o representativo detectado
                for item in meta.amounts_detected:
                    if isinstance(item, dict) and "amount" in item:
                        try:
                            extracted_val = float(item["amount"])
                            evidence_snippet = f"Monto registrado en metadatos: ${extracted_val:,.2f} MXN"
                            break
                        except (ValueError, TypeError):
                            pass

        if extracted_val is None:
            return {
                "status": RuleEvaluationStatus.PENDING_HUMAN_REVIEW,
                "matched_evidence": None,
                "failure_reason": "No se pudo extraer de forma determinista el valor numérico para verificar el límite. Requiere revisión manual del abogado."
            }

        # Validar rangos numéricos
        if min_val is not None and extracted_val < min_val:
            return {
                "status": RuleEvaluationStatus.NON_COMPLIANT,
                "matched_evidence": evidence_snippet or f"Valor extraído: {extracted_val}",
                "failure_reason": f"El valor {extracted_val} es menor al límite mínimo permitido de {min_val}."
            }

        if max_val is not None and extracted_val > max_val:
            return {
                "status": RuleEvaluationStatus.NON_COMPLIANT,
                "matched_evidence": evidence_snippet or f"Valor extraído: {extracted_val}",
                "failure_reason": f"El valor {extracted_val} excede el límite máximo permitido de {max_val}."
            }

        return {
            "status": RuleEvaluationStatus.COMPLIANT,
            "matched_evidence": f"{evidence_snippet or ''} (Valor verificado: {extracted_val} dentro de rango [{min_val or '-inf'}, {max_val or '+inf'}])".strip(),
            "failure_reason": None
        }

    def _eval_metadata_equals(self, params: Dict[str, Any], document: Document) -> Dict[str, Any]:
        field = params.get("target_field")
        expected = params.get("expected_value")

        if not field or expected is None:
            return {
                "status": RuleEvaluationStatus.PENDING_HUMAN_REVIEW,
                "matched_evidence": None,
                "failure_reason": "Parámetros de comparación de metadatos incompletos."
            }

        meta = document.metadata_record
        if not meta:
            return {
                "status": RuleEvaluationStatus.PENDING_HUMAN_REVIEW,
                "matched_evidence": None,
                "failure_reason": "El documento no cuenta con metadatos extraídos. Requiere revisión humana."
            }

        actual_val = getattr(meta, field, None)
        if actual_val is None:
            return {
                "status": RuleEvaluationStatus.PENDING_HUMAN_REVIEW,
                "matched_evidence": None,
                "failure_reason": f"El metadato '{field}' no está presente en el documento. Requiere confirmación manual."
            }

        if str(actual_val).strip().lower() == str(expected).strip().lower():
            return {
                "status": RuleEvaluationStatus.COMPLIANT,
                "matched_evidence": f"Metadato '{field}' coincide: {actual_val}",
                "failure_reason": None
            }
        else:
            return {
                "status": RuleEvaluationStatus.NON_COMPLIANT,
                "matched_evidence": f"Metadato '{field}' actual: '{actual_val}', esperado: '{expected}'",
                "failure_reason": f"El valor del metadato '{field}' no coincide con el requisito determinista."
            }

    def _eval_metadata_exists(self, params: Dict[str, Any], document: Document) -> Dict[str, Any]:
        field = params.get("target_field")
        if not field:
            return {
                "status": RuleEvaluationStatus.PENDING_HUMAN_REVIEW,
                "matched_evidence": None,
                "failure_reason": "No se indicó el campo a comprobar."
            }

        meta = document.metadata_record
        if not meta:
            return {
                "status": RuleEvaluationStatus.PENDING_HUMAN_REVIEW,
                "matched_evidence": None,
                "failure_reason": "Metadatos documentales no disponibles."
            }

        actual_val = getattr(meta, field, None)
        if actual_val:
            return {
                "status": RuleEvaluationStatus.COMPLIANT,
                "matched_evidence": f"Requisito verificado: Campo '{field}' presente con valor válido.",
                "failure_reason": None
            }
        else:
            return {
                "status": RuleEvaluationStatus.NON_COMPLIANT,
                "matched_evidence": None,
                "failure_reason": f"Requisito obligatorio omitido: Campo '{field}' no está registrado o está vacío."
            }

    def evaluate_document(
        self,
        document: LegalDocument if False else Document,
        raw_text: str,
        rules: List[LegalRule]
    ) -> Dict[str, Any]:
        """
        Ejecuta la evaluación determinista de todo el conjunto de reglas aplicables sobre un documento.
        """
        details = []
        passed = 0
        failed = 0
        pending = 0
        not_applicable = 0

        for rule in rules:
            if not rule.is_active:
                continue

            res = self.evaluate_rule(rule, raw_text, document)
            status = res["status"]

            if status == RuleEvaluationStatus.COMPLIANT:
                passed += 1
            elif status == RuleEvaluationStatus.NON_COMPLIANT:
                failed += 1
            elif status == RuleEvaluationStatus.PENDING_HUMAN_REVIEW:
                pending += 1
            elif status == RuleEvaluationStatus.NOT_APPLICABLE:
                not_applicable += 1

            details.append({
                "rule_id": rule.id,
                "rule_code": rule.rule_code,
                "rule_name": rule.name,
                "category": rule.category,
                "severity": rule.severity,
                "status": status,
                "matched_evidence": res.get("matched_evidence"),
                "failure_reason": res.get("failure_reason")
            })

        applicable_total = passed + failed + pending
        compliance_score = round((passed / applicable_total * 100), 2) if applicable_total > 0 else 100.0

        return {
            "total_rules_evaluated": len(details),
            "passed_count": passed,
            "failed_count": failed,
            "pending_count": pending,
            "not_applicable_count": not_applicable,
            "compliance_score": compliance_score,
            "details": details
        }
