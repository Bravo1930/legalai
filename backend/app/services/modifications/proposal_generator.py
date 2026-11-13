import re
import difflib
from typing import List, Dict, Any, Optional
from app.models.advanced_analysis import LegalFinding, FindingIssueType


class ProposalGenerator:
    """
    Generador de propuestas y alternativas de redacción jurídica para México.
    
    REGLAS ESTRICTAS:
    1. Cero alucinación o invención de hechos, nombres, cantidades o fechas no acreditadas.
    2. Los datos faltantes se identifican con placeholders explícitos: [PENDIENTE: ...].
    3. Ninguna propuesta sustituye el documento original; se presentan como alternativas para el abogado.
    """

    @classmethod
    def generate_proposals_from_findings(
        cls,
        document_text: str,
        findings: List[LegalFinding]
    ) -> List[Dict[str, Any]]:
        """
        Genera propuestas de redacción jurídica fundamentadas para cada hallazgo o problema detectado.
        """
        proposals = []

        for finding in findings:
            issue = finding.issue_type
            orig_text = finding.original_fragment or ""
            clause_ref = finding.clause_ref or "Cláusula Observada"

            if issue == FindingIssueType.CONTRADICTION:
                prop = cls._draft_jurisdiction_reconciliation(finding, orig_text, clause_ref)
            elif issue == FindingIssueType.EXCESSIVE_PENALTY:
                prop = cls._draft_penalty_moderation(finding, orig_text, clause_ref)
            elif issue == FindingIssueType.UNBALANCED_OBLIGATION:
                prop = cls._draft_balanced_reciprocity(finding, orig_text, clause_ref)
            elif issue == FindingIssueType.OMISSION and "confidencial" in finding.title.lower():
                prop = cls._draft_confidentiality_clause(finding)
            elif issue == FindingIssueType.DATA_PROTECTION_DEFECT:
                prop = cls._draft_data_protection_clause(finding)
            elif issue == FindingIssueType.OMISSION and ("rescisi" in finding.title.lower() or "terminaci" in finding.title.lower()):
                prop = cls._draft_termination_clause(finding)
            else:
                prop = cls._draft_generic_clarity_improvement(finding, orig_text, clause_ref)

            proposals.append(prop)

        return proposals

    @classmethod
    def _draft_jurisdiction_reconciliation(cls, finding: LegalFinding, orig_text: str, clause_ref: str) -> Dict[str, Any]:
        proposed = (
            "Para la interpretación, cumplimiento y solución de cualquier controversia derivada del presente contrato, "
            "las partes se someten de manera expresa e irrevocable a la jurisdicción y competencia de los Tribunales "
            "competentes de la Ciudad de México, renunciando formal y expresamente a cualquier otro fuero que por razón "
            "de sus domicilios presentes, futuros o por cualquier otra causa pudiera corresponderles."
        )

        alt_1 = (
            "Cualquier controversia que derive del presente contrato será resuelta de manera definitiva mediante arbitraje "
            "administrado por el Centro de Arbitraje de México (CAM) o la Cámara Nacional de Comercio de la Ciudad de México (CANACO), "
            "de conformidad con su Reglamento de Arbitraje. La sede del arbitraje será la Ciudad de México y el idioma será el español."
        )

        alt_2 = (
            "Para cualquier controversia judicial, las partes se someten a los juzgados de la Ciudad de México; no obstante, "
            "la parte actora se reserva la facultad potestativa de interponer su demanda ante los tribunales del domicilio "
            "del demandado al momento de promoverse el juicio."
        )

        diff = cls._compute_diff_summary(orig_text, proposed)

        return {
            "finding_id": finding.id,
            "clause_title": clause_ref,
            "problem_explanation": "Contradicción o ambigüedad de fueros judiciales detectada. El artículo 1093 del Código de Comercio exige sumisión expresa y unívoca para prorrogar válidamente la competencia.",
            "original_text": orig_text or "Cláusula con señalamientos de fueros judiciales divergentes o ambiguos.",
            "proposed_text": proposed,
            "alternative_options": [
                {"label": "Opción Estándar (Tribunales CDMX)", "text": proposed},
                {"label": "Opción Arbitral (CANACO / CAM)", "text": alt_1},
                {"label": "Opción Mixta (Elección de Parte Actora)", "text": alt_2}
            ],
            "missing_data_placeholders": ["[PENDIENTE: Domicilio procesal en Ciudad de México para notificaciones judiciales]"],
            "legal_foundation": "Art. 1093 del Código de Comercio",
            "diff_summary": diff
        }

    @classmethod
    def _draft_penalty_moderation(cls, finding: LegalFinding, orig_text: str, clause_ref: str) -> Dict[str, Any]:
        proposed = (
            "En caso de incumplimiento total o parcial de las obligaciones a cargo de cualquiera de las partes, "
            "la parte incumplida pagará a la contraparte afectada una pena convencional equivalente al 15% (quince por ciento) "
            "del valor de la mensualidad o saldo efectivamente insoluto, sin que en ningún caso el monto acumulado de dicha pena "
            "pueda exceder el valor total de la obligación principal, en estricto acatamiento al artículo 1843 del Código Civil Federal."
        )

        alt_1 = (
            "En caso de mora en el pago de las contraprestaciones convenidas, la parte deudora cubrirá un interés moratorio "
            "calculado a razón de la Tasa de Interés Interbancaria de Equilibrio (TIIE) a 28 días, incrementada en 4 (cuatro) puntos porcentuales "
            "anuales, calculada sobre el saldo vencido por el tiempo que dure la mora."
        )

        alt_2 = (
            "Si la demora no excede de 15 (quince) días naturales, se aplicará una pena del 5% sobre el importe vencido. "
            "Transcurrido dicho periodo sin subsanarse el incumplimiento, se aplicará una pena del 15% y la parte afectada "
            "podrá demandar la rescisión inmediata del contrato."
        )

        diff = cls._compute_diff_summary(orig_text, proposed)

        return {
            "finding_id": finding.id,
            "clause_title": clause_ref,
            "problem_explanation": "Pena convencional excesiva o desproporcionada que contraviene el artículo 1843 del Código Civil Federal y criterios jurisprudenciales de la SCJN contra estipulaciones leoninas o usurarias.",
            "original_text": orig_text or "Estipulación de pena convencional de cuantía desmedida.",
            "proposed_text": proposed,
            "alternative_options": [
                {"label": "Opción Cláusula Penal Topada (15% Legal)", "text": proposed},
                {"label": "Opción Interés Moratorio Referenciado (TIIE)", "text": alt_1},
                {"label": "Opción Escalonada con Periodo de Gracia", "text": alt_2}
            ],
            "missing_data_placeholders": ["[PENDIENTE: Monto exacto de contraprestación base en Moneda Nacional ($ MXN)]"],
            "legal_foundation": "Art. 1843 del Código Civil Federal y Tesis Jurisprudenciales SCJN sobre Usura Mercantil",
            "diff_summary": diff
        }

    @classmethod
    def _draft_balanced_reciprocity(cls, finding: LegalFinding, orig_text: str, clause_ref: str) -> Dict[str, Any]:
        proposed = (
            "Cualquiera de las partes podrá dar por terminado anticipadamente el presente contrato sin necesidad de resolución judicial, "
            "mediando notificación por escrito entregada con al menos 30 (treinta) días naturales de anticipación a la fecha efectiva de terminación, "
            "siempre y cuando se encuentre al corriente en el cumplimiento de todas las obligaciones devengadas a su cargo."
        )

        alt_1 = (
            "El presente contrato solo podrá darse por terminado ante el incumplimiento grave de cualquiera de las partes. "
            "La parte afectada notificará por escrito a la incumplida, otorgándole un plazo perentorio de 15 (quince) días naturales "
            "para subsanar la falta. Si fenecido el plazo no se ha subsanado, el contrato se tendrá por rescindido de pleno derecho."
        )

        diff = cls._compute_diff_summary(orig_text, proposed)

        return {
            "finding_id": finding.id,
            "clause_title": clause_ref,
            "problem_explanation": "La redacción actual deja la terminación al arbitrio unilateral de una sola parte, contraviniendo el artículo 1797 del Código Civil Federal (inadmisibilidad de condiciones puramente potestativas).",
            "original_text": orig_text or "Facultad discrecional asimétrica sin reciprocidad.",
            "proposed_text": proposed,
            "alternative_options": [
                {"label": "Opción Terminación Anticipada Bilateral Equitativa (Aviso 30 días)", "text": proposed},
                {"label": "Opción Rescisión Causal con Plazo de Subsanación (15 días)", "text": alt_1}
            ],
            "missing_data_placeholders": ["[PENDIENTE: Correo electrónico o domicilio formal para notificaciones de terminación]"],
            "legal_foundation": "Art. 1796 y 1797 del Código Civil Federal",
            "diff_summary": diff
        }

    @classmethod
    def _draft_confidentiality_clause(cls, finding: LegalFinding) -> Dict[str, Any]:
        proposed = (
            "CLÁUSULA DE CONFIDENCIALIDAD Y SECRETO INDUSTRIAL: Toda la información técnica, comercial, operativa, financiera o jurídica "
            "que las partes se revelen o transmitan con motivo del presente instrumento tendrá el carácter estricto de información confidencial "
            "y constituirá, cuando corresponda, un Secreto Industrial al amparo de los artículos 82, 83, 85 y 86 de la Ley Federal de Protección "
            "a la Propiedad Industrial (LFPPI). Las partes se obligan a no divulgar, reproducir ni transmitir a terceros dicha información sin "
            "consentimiento previo y por escrito, manteniendo esta obligación vigente durante toda la vida del contrato y por un periodo no menor "
            "a 5 (cinco) años posteriores a su terminación."
        )

        diff = "Adición de cláusula omitida de reserva y secreto industrial bajo la LFPPI."

        return {
            "finding_id": finding.id,
            "clause_title": "CLÁUSULA DE CONFIDENCIALIDAD (OMISIÓN DETECTADA)",
            "problem_explanation": "Omisión de pacto expreso de confidencialidad y custodia de secretos industriales conforme a la legislación mexicana.",
            "original_text": "[CLÁUSULA NO EXISTENTE EN EL DOCUMENTO ORIGINAL]",
            "proposed_text": proposed,
            "alternative_options": [
                {"label": "Opción Integral (LFPPI 5 Años)", "text": proposed},
                {"label": "Opción Acotada (Solo información calificada por escrito como confidencial)", "text": "Las partes guardarán reserva exclusivamente sobre aquellos documentos que ostenten la leyenda visible 'CONFIDENCIAL'."}
            ],
            "missing_data_placeholders": ["[PENDIENTE: Excepciones acordadas a la información confidencial]"],
            "legal_foundation": "Art. 82 a 86 de la Ley Federal de Protección a la Propiedad Industrial",
            "diff_summary": diff
        }

    @classmethod
    def _draft_data_protection_clause(cls, finding: LegalFinding) -> Dict[str, Any]:
        proposed = (
            "PROTECCIÓN DE DATOS PERSONALES: Las partes reconocen que los datos personales de personas físicas (representantes, empleados, apoderados o testigos) "
            "proporcionados para la celebración y ejecución del presente contrato serán tratados en estricto apego a la Ley Federal de Protección de "
            "Datos Personales en Posesión de los Particulares (LFPDPPP). Cada una de las partes manifiesta contar y poner a disposición de la otra su respectivo "
            "Aviso de Privacidad integral en el portal [PENDIENTE: URL o Dirección del Aviso de Privacidad], garantizando el ejercicio de los derechos de Acceso, "
            "Rectificación, Cancelación y Oposición (Derechos ARCO)."
        )

        return {
            "finding_id": finding.id,
            "clause_title": "CLÁUSULA DE PROTECCIÓN DE DATOS (LFPDPPP)",
            "problem_explanation": "Falta de previsión sobre el tratamiento lícito de datos personales y puesta a disposición del Aviso de Privacidad.",
            "original_text": "[CLÁUSULA NO EXISTENTE EN EL DOCUMENTO ORIGINAL]",
            "proposed_text": proposed,
            "alternative_options": [
                {"label": "Opción Estándar LFPDPPP", "text": proposed}
            ],
            "missing_data_placeholders": ["[PENDIENTE: Enlace URL del Aviso de Privacidad de cada parte]"],
            "legal_foundation": "Art. 8, 15 y 16 de la Ley Federal de Protección de Datos Personales en Posesión de los Particulares",
            "diff_summary": "Adición de cláusula obligatoria de aviso de privacidad conforme a la LFPDPPP."
        }

    @classmethod
    def _draft_termination_clause(cls, finding: LegalFinding) -> Dict[str, Any]:
        proposed = (
            "CAUSALES DE RESCISIÓN: Serán causas justificadas de rescisión inmediata del presente contrato, sin necesidad de declaración judicial previa, "
            "las siguientes: a) El incumplimiento total o parcial de cualquiera de las obligaciones contraídas; b) La declaración de concurso mercantil "
            "o disolución de cualquiera de las partes; c) La falta de pago puntual de 2 (dos) o más contraprestaciones mensuales consecutivas; y "
            "d) La cesión no autorizada de los derechos y obligaciones derivados de este instrumento."
        )

        return {
            "finding_id": finding.id,
            "clause_title": "CLÁUSULA DE RESCISIÓN Y TERMINACIÓN CAUSAL",
            "problem_explanation": "Omisión de causales objetivas de rescisión extrajudicial pactada, obligando a entablar juicio ordinario mercantil para dar por terminado el contrato.",
            "original_text": "[CLÁUSULA NO EXISTENTE EN EL DOCUMENTO ORIGINAL]",
            "proposed_text": proposed,
            "alternative_options": [
                {"label": "Opción Causales Objetivas Taxativas", "text": proposed}
            ],
            "missing_data_placeholders": ["[PENDIENTE: Causales específicas del giro comercial del cliente]"],
            "legal_foundation": "Art. 376 del Código de Comercio y Art. 1949 del Código Civil Federal",
            "diff_summary": "Incorporación de catálogo de causales de rescisión pactada."
        }

    @classmethod
    def _draft_generic_clarity_improvement(cls, finding: LegalFinding, orig_text: str, clause_ref: str) -> Dict[str, Any]:
        # Mejora de claridad sintáctica y precisión jurídica
        clean_text = " ".join(orig_text.split())
        proposed = f"Para mayor claridad y certidumbre jurídica, se precisa que: {clean_text}" if clean_text else finding.recommendation

        return {
            "finding_id": finding.id,
            "clause_title": clause_ref,
            "problem_explanation": finding.description,
            "original_text": orig_text or "[Fragmento original no especificado]",
            "proposed_text": proposed,
            "alternative_options": [
                {"label": "Propuesta Aclaratoria", "text": proposed}
            ],
            "missing_data_placeholders": ["[PENDIENTE: Revisar datos precisos]"],
            "legal_foundation": None,
            "diff_summary": "Ajuste de precisión de redacción y eliminación de ambigüedades."
        }

    @classmethod
    def _compute_diff_summary(cls, orig: str, prop: str) -> str:
        words_orig = set(re.findall(r'\b\w{4,}\b', orig.lower()))
        words_prop = set(re.findall(r'\b\w{4,}\b', prop.lower()))
        added = words_prop - words_orig
        removed = words_orig - words_prop

        parts = []
        if added:
            parts.append(f"Términos incorporados: {', '.join(list(added)[:4])}")
        if removed:
            parts.append(f"Términos eliminados: {', '.join(list(removed)[:4])}")

        return " | ".join(parts) if parts else "Reestructuración sintáctica de la cláusula."
