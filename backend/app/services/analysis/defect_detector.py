import re
from typing import List, Dict, Any, Optional
from app.models.advanced_analysis import FindingIssueType, FindingSeverity
from app.services.legal_sources.mexican_law_catalog import MexicanLawVerifier


class DefectDetector:
    """
    Detector especializado de defectos contractuales, contradicciones, omisiones,
    penalizaciones excesivas y citas normativas en documentos jurídicos mexicanos.
    """

    @classmethod
    def detect_all(cls, text: str, clauses: List[Dict[str, Any]], doc_type: str = "CONTRATO") -> List[Dict[str, Any]]:
        """Ejecuta la suite integral de detección de vicios y riesgos jurídicos."""
        findings = []

        findings.extend(cls._detect_contradictions(clauses))
        findings.extend(cls._detect_excessive_penalties(clauses, text))
        findings.extend(cls._detect_omissions(clauses, text, doc_type))
        findings.extend(cls._detect_unbalanced_clauses(clauses))
        findings.extend(cls._detect_legal_citations(text))

        return findings

    @classmethod
    def _detect_contradictions(cls, clauses: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Detecta contradicciones expresas entre cláusulas del mismo documento."""
        findings = []

        # 1. Contradicción de Jurisdicción
        # Si una cláusula menciona CDMX y otra menciona otro estado o arbitraje incompatible
        jurisdiction_mentions = []
        for c in clauses:
            raw = c["raw_text"].lower()
            if "tribunales" in raw or "jurisdicci" in raw or "fuero" in raw or "competencia" in raw:
                places = []
                if "ciudad de m" in raw or "cdmx" in raw or "distrito federal" in raw:
                    places.append("Ciudad de México")
                if "monterrey" in raw or "nuevo le" in raw:
                    places.append("Monterrey, Nuevo León")
                if "guadalajara" in raw or "jalisco" in raw:
                    places.append("Guadalajara, Jalisco")
                if "quer" in raw:
                    places.append("Querétaro")
                if places:
                    jurisdiction_mentions.append({
                        "clause": c["title"],
                        "places": places,
                        "raw_snippet": c["raw_text"][:180]
                    })

        all_places = set()
        for jm in jurisdiction_mentions:
            for p in jm["places"]:
                all_places.add(p)

        if len(all_places) > 1:
            clauses_str = " y ".join([f"'{jm['clause']}' ({', '.join(jm['places'])})" for jm in jurisdiction_mentions])
            findings.append({
                "issue_type": FindingIssueType.CONTRADICTION,
                "title": "Contradicción Crítica en Cláusula de Jurisdicción y Competencia",
                "description": f"El documento estipula foros judiciales incompatibles entre diferentes cláusulas: {clauses_str}.",
                "severity": FindingSeverity.CRITICAL,
                "original_fragment": jurisdiction_mentions[0]["raw_snippet"],
                "location": jurisdiction_mentions[0]["clause"],
                "clause_ref": jurisdiction_mentions[0]["clause"],
                "legal_foundation": MexicanLawVerifier.verify_citation("artículo 1093 del código de comercio"),
                "risk_explanation": "La existencia de fueros judiciales contradictorios anula la sumisión expresa conforme al artículo 1093 del Código de Comercio, generando excepciones de incompetencia dilatorias y litigios preliminares en caso de demanda.",
                "recommendation": "Unificar la jurisdicción en una sola cláusula inequívoca renunciando expresamente a cualquier otro fuero presente o futuro.",
                "confidence_score": 0.98,
                "confidence_level": "HIGH"
            })

        # 2. Contradicción de Plazos de Entrega o Cumplimiento
        days_found = []
        for c in clauses:
            m = re.findall(r'(?:plazo|entrega|dentro\s+de\s+los?)\s*(?:un\s+t[ée]rmino\s+de)?\s*(\d+)\s*(?:d[íi]as|meses)', c["raw_text"], re.IGNORECASE)
            if m:
                for d in m:
                    days_found.append({"clause": c["title"], "value": int(d), "snippet": c["raw_text"][:150]})

        if len(days_found) >= 2:
            unique_days = list(set([df["value"] for df in days_found]))
            if len(unique_days) > 1 and max(unique_days) / min(unique_days) >= 2:
                # Discrepancia sustancial (ej. 15 días vs 30 o 60 días)
                findings.append({
                    "issue_type": FindingIssueType.CONTRADICTION,
                    "title": "Discrepancia en Plazos de Cumplimiento",
                    "description": f"Se identificaron términos de ejecución conflictivos: {unique_days[0]} días vs {unique_days[1]} días en diferentes secciones.",
                    "severity": FindingSeverity.HIGH,
                    "original_fragment": days_found[0]["snippet"],
                    "location": days_found[0]["clause"],
                    "clause_ref": days_found[0]["clause"],
                    "legal_foundation": MexicanLawVerifier.verify_citation("artículo 83 del código de comercio"),
                    "risk_explanation": "Incertidumbre jurídica sobre el momento de exigibilidad de la obligación, permitiendo a la contraparte alegar mora prematura o excepción de contrato no cumplido.",
                    "recommendation": "Armonizar los plazos de entrega y vincularlos a un calendario unificado de hitos.",
                    "confidence_score": 0.92,
                    "confidence_level": "HIGH"
                })

        return findings

    @classmethod
    def _detect_excessive_penalties(cls, clauses: List[Dict[str, Any]], full_text: str) -> List[Dict[str, Any]]:
        """Detecta penalizaciones convencionales excesivas o usurarias violatorias de la ley mexicana."""
        findings = []

        # Buscar porcentajes de pena convencional > 50% o superiores al 100%
        penalty_pattern = re.compile(r'pena\s+convencional(?:[^\d%]{1,40})?(\d+)\s*%', re.IGNORECASE)
        for c in clauses:
            m = penalty_pattern.search(c["raw_text"])
            if m:
                percentage = int(m.group(1))
                if percentage > 30:
                    severity = FindingSeverity.CRITICAL if percentage >= 100 else FindingSeverity.HIGH
                    foundation = MexicanLawVerifier.verify_citation("artículo 1843 del código civil federal")
                    findings.append({
                        "issue_type": FindingIssueType.EXCESSIVE_PENALTY,
                        "title": f"Pena Convencional Potencialmente Excesiva o Nula ({percentage}%)",
                        "description": f"La estipulación de una pena convencional del {percentage}% rebasa los límites razonables de equidad contractual y puede ser declarada nula.",
                        "severity": severity,
                        "original_fragment": c["raw_text"][max(0, m.start() - 30):min(len(c["raw_text"]), m.end() + 60)],
                        "location": c["title"],
                        "clause_ref": c["title"],
                        "legal_foundation": foundation,
                        "risk_explanation": "El artículo 1843 del Código Civil Federal (y correlativos estatales) dispone que la cláusula penal no puede exceder en valor ni en cuantía a la obligación principal. Además, la SCJN ha emitido jurisprudencia firme prohibiendo estipulaciones lesivas o usurarias.",
                        "recommendation": f"Moderar la pena convencional a un rango del 10% al 20%, o toparla expresamente al valor total efectivamente insoluto del contrato.",
                        "confidence_score": 0.95,
                        "confidence_level": "HIGH"
                    })

        return findings

    @classmethod
    def _detect_omissions(cls, clauses: List[Dict[str, Any]], full_text: str, doc_type: str) -> List[Dict[str, Any]]:
        """Detecta omisiones de cláusulas esenciales según el tipo documental."""
        findings = []
        norm_text = full_text.lower()

        # 1. Omisión de Cláusula de Confidencialidad
        if "confidencial" not in norm_text and "secreto industrial" not in norm_text:
            foundation = MexicanLawVerifier.verify_citation("artículo 82 de la ley federal de proteccion a la propiedad industrial")
            findings.append({
                "issue_type": FindingIssueType.OMISSION,
                "title": "Omisión de Cláusula de Confidencialidad y Secreto Industrial",
                "description": "El documento no incluye compromisos de reserva, custodia ni sanciones por revelación de secretos comerciales.",
                "severity": FindingSeverity.HIGH,
                "original_fragment": None,
                "location": "Cuerpo General del Contrato",
                "clause_ref": "Cláusula Omitida",
                "legal_foundation": foundation,
                "risk_explanation": "Sin un pacto expreso de confidencialidad, resulta complejo acreditar ante el IMPI o tribunales penales la protección legal de secretos industriales conforme a los artículos 82 a 85 de la LFPPI.",
                "recommendation": "Insertar cláusula de confidencialidad reforzada con vigencia mínima de 3 a 5 años tras la terminación del contrato.",
                "confidence_score": 0.96,
                "confidence_level": "HIGH"
            })

        # 2. Omisión de Aviso de Privacidad / Protección de Datos (LFPDPPP)
        if "datos personales" not in norm_text and "aviso de privacidad" not in norm_text and "lfpdppp" not in norm_text:
            foundation = MexicanLawVerifier.verify_citation("artículo 15 de la ley federal de proteccion de datos personales en posesion de los particulares")
            findings.append({
                "issue_type": FindingIssueType.DATA_PROTECTION_DEFECT,
                "title": "Omisión de Cláusula de Protección de Datos Personales (LFPDPPP)",
                "description": "No se advierte mención al tratamiento lícito ni puesta a disposición del Aviso de Privacidad.",
                "severity": FindingSeverity.MEDIUM,
                "original_fragment": None,
                "location": "Cuerpo General del Contrato",
                "clause_ref": "Cláusula Omitida",
                "legal_foundation": foundation,
                "risk_explanation": "El tratamiento de datos de personas físicas (representantes, firmantes o personal) sin aviso de privacidad acarrea infracciones y multas impuestas por el INAI.",
                "recommendation": "Incluir cláusula de observancia a la LFPDPPP referenciando el enlace o domicilio donde consultar el Aviso de Privacidad integral.",
                "confidence_score": 0.94,
                "confidence_level": "HIGH"
            })

        # 3. Omisión de Cláusula de Terminación Anticipada o Rescisión
        if "rescisi" not in norm_text and "terminaci" not in norm_text:
            foundation = MexicanLawVerifier.verify_citation("artículo 1797 del código civil federal")
            findings.append({
                "issue_type": FindingIssueType.OMISSION,
                "title": "Omisión de Causales de Rescisión y Terminación",
                "description": "No se contemplan causales objetivas para dar por terminado el contrato ante incumplimiento.",
                "severity": FindingSeverity.HIGH,
                "original_fragment": None,
                "location": "Cuerpo General del Contrato",
                "clause_ref": "Cláusula Omitida",
                "legal_foundation": foundation,
                "risk_explanation": "Obliga a las partes a recurrir necesariamente a un juicio ordinario mercantil para solicitar la rescisión judicial, impidiendo la rescisión extrajudicial pactada.",
                "recommendation": "Incorporar cláusula de rescisión inmediata por causas graves con notificación previa de 15 días.",
                "confidence_score": 0.90,
                "confidence_level": "HIGH"
            })

        return findings

    @classmethod
    def _detect_unbalanced_clauses(cls, clauses: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Detecta cláusulas leoninas o pactos desbalanceados contrarios a la buena fe mercantil."""
        findings = []

        unilateral_pattern = re.compile(r'(?:a\s+su\s+entera\s+discreci[óo]n|sin\s+necesidad\s+de\s+justificaci[óo]n|de\s+manera\s+unilateral\s+y\s+sin\s+responsabilidad)', re.IGNORECASE)
        for c in clauses:
            m = unilateral_pattern.search(c["raw_text"])
            if m:
                foundation = MexicanLawVerifier.verify_citation("artículo 1797 del código civil federal")
                findings.append({
                    "issue_type": FindingIssueType.UNBALANCED_OBLIGATION,
                    "title": "Cláusula Potestativa o Asimétrica Unilateral",
                    "description": "Se otorga a una de las partes la facultad potestativa de actuar o rescindir sin causa ni reciprocidad.",
                    "severity": FindingSeverity.HIGH,
                    "original_fragment": c["raw_text"][max(0, m.start() - 20):min(len(c["raw_text"]), m.end() + 40)],
                    "location": c["title"],
                    "clause_ref": c["title"],
                    "legal_foundation": foundation,
                    "risk_explanation": "El artículo 1797 del Código Civil Federal establece que la validez y el cumplimiento de los contratos no puede dejarse al arbitrio de uno de los contratantes. Tales cláusulas son susceptibles de nulidad relativa o absoluta.",
                    "recommendation": "Establecer reciprocidad bilateral y causales objetivas medibles para ambas partes.",
                    "confidence_score": 0.88,
                    "confidence_level": "MEDIUM"
                })

        return findings

    @classmethod
    def _detect_legal_citations(cls, full_text: str) -> List[Dict[str, Any]]:
        """Identifica citas legales explícitas en el texto y corrobora su vigencia y fuente oficial."""
        findings = []

        # Buscar menciones a artículos de leyes mexicanas
        citation_regex = re.compile(r'(?:art[íi]culo\s+\d+\s+de\s+la\s+[^,\.\n]{5,50}|conforme\s+al\s+c[óo]digo\s+[^,\.\n]{5,40})', re.IGNORECASE)
        matches = list(citation_regex.finditer(full_text))

        for m in matches[:4]:  # Procesar hasta las 4 citas principales
            citation_str = m.group(0).strip()
            verified_data = MexicanLawVerifier.verify_citation(citation_str)

            if not verified_data.get("is_verified"):
                findings.append({
                    "issue_type": FindingIssueType.UNVERIFIED_CITATION,
                    "title": "Fundamento Jurídico no Verificado o Incierto",
                    "description": f"Se cita la disposición '{citation_str}', la cual no pudo ser corroborada fehacientemente en fuentes oficiales inmediatas.",
                    "severity": FindingSeverity.REQUIRES_HUMAN_VALIDATION,
                    "original_fragment": citation_str,
                    "location": "Cuerpo del Documento",
                    "clause_ref": "Fundamentación Jurídica",
                    "legal_foundation": verified_data,
                    "risk_explanation": "Citar preceptos normativos erróneos, derogados o imprecisos debilita la posición procesal o la validez contractual en litigio.",
                    "recommendation": "Verificar texto en el Diario Oficial de la Federación o compendio de la Cámara de Diputados antes de emitir versión vinculante.",
                    "confidence_score": 0.80,
                    "confidence_level": "MEDIUM"
                })

        return findings
