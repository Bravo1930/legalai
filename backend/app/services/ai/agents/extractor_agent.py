from typing import Dict, Any, Optional
from app.services.ai.agents.base_agent import BaseLegalAgent
from app.services.ai.ollama_client import ollama_client


class InformationExtractorAgent(BaseLegalAgent):
    AGENT_TYPE = "EXTRACTOR"
    ROLE_DESCRIPTION = "Agente Especialista en Extracción de Entidades y Hechos Jurídicos Estructurados"

    SYSTEM_PROMPT = """Eres un abogado perito en análisis documental en México.
Tu tarea es extraer con total fidelidad todas las entidades, términos y datos objetivos del documento legal.

Debes responder ÚNICAMENTE en formato JSON válido con la siguiente estructura:
{
  "parties": [
    {"name": "Nombre o Razón Social", "role": "ARRENDADOR / ACTOR / etc.", "rfc": "RFC si aparece o null", "legal_rep": "Representante si aparece"}
  ],
  "effective_date": "Fecha de firma o inicio",
  "expiration_date": "Fecha de vencimiento o null si es indefinido",
  "subject_matter": "Resumen claro del objeto del acto o demanda",
  "financial_terms": {
    "total_amount": "Monto principal si aplica",
    "periodic_payment": "Pago periódico si aplica",
    "currency": "MXN / USD / etc.",
    "penalty_clause": "Monto o porcentaje de pena convencional si existe"
  },
  "key_obligations": [
    {"party": "Parte obligada", "obligation": "Descripción de la obligación sustancial"}
  ],
  "jurisdiction_clause": "Tribunales acordados o fuero invocado",
  "signers": [
    {"name": "Nombre de quien firma", "capacity": "En calidad de qué firma", "professional_license": "Cédula si aparece"}
  ],
  "facts": ["Lista de hechos verificables explícitos en el texto"],
  "inferences": ["Deducciones lógicas a partir de los datos"],
  "hypotheses": ["Supuestos condicionales si faltan anexos o datos"],
  "recommendations": ["Recomendaciones para completar datos faltantes"]
}

Reglas obligatorias:
1. No inventes montos, nombres ni fechas; si no aparecen pon null.
2. Todo lo que esté en 'facts' debe tener sustento textual directo."""

    @classmethod
    async def run(
        cls,
        document_text: str,
        user_prompt: Optional[str] = None,
        model: Optional[str] = None,
        temperature: float = 0.1
    ) -> Dict[str, Any]:
        wrapped_doc = cls.wrap_document_content(document_text)
        user_msg = (user_prompt or "Extrae todas las entidades jurídicas, partes, montos y fechas del documento.") + "\n\n" + wrapped_doc

        messages = [
            {"role": "system", "content": cls.SYSTEM_PROMPT},
            {"role": "user", "content": user_msg}
        ]

        resp = await ollama_client.generate_chat(
            messages=messages,
            model=model,
            temperature=temperature,
            format_json=True
        )

        parsed = cls.parse_strict_json(resp["content"])
        return {
            "agent": cls.AGENT_TYPE,
            "model_used": resp["model"],
            "structured_output": parsed,
            "tokens_prompt": resp["tokens_prompt"],
            "tokens_completion": resp["tokens_completion"],
            "latency_ms": resp["latency_ms"],
            "prompt_template": cls.SYSTEM_PROMPT
        }
