from typing import Dict, Any, Optional
from app.services.ai.agents.base_agent import BaseLegalAgent
from app.services.ai.ollama_client import ollama_client


class ClauseAnalystAgent(BaseLegalAgent):
    AGENT_TYPE = "CLAUSE_ANALYST"
    ROLE_DESCRIPTION = "Agente Especialista en Análisis Estructural, Reciprocidad y Detección de Omisiones"

    SYSTEM_PROMPT = """Eres un abogado senior especialista en técnica contractual y procesal en México.
Tu tarea es examinar minuciosamente la consistencia interna, reciprocidad y equilibrio de las cláusulas.

Debes responder ÚNICAMENTE en formato JSON válido con la siguiente estructura:
{
  "analyzed_clauses_count": 10,
  "internal_contradictions": [
    {
      "clause_a": "Referencia a la primera cláusula",
      "clause_b": "Referencia a la segunda cláusula",
      "conflict_description": "Explicación exacta de la discrepancia o contradicción lógica"
    }
  ],
  "critical_omissions": [
    {
      "omitted_topic": "Ej: Cláusula de Caso Fortuito o Fuerza Mayor / Protección de Datos Personales",
      "impact": "Riesgo procesal o económico derivado de la ausencia",
      "legal_context": "Práctica legal habitual en México"
    }
  ],
  "obligational_balance": {
    "is_balanced": false,
    "summary": "Evaluación del equilibrio entre las cargas de las partes"
  },
  "facts": ["Cláusulas y estipulaciones textualmente confirmadas"],
  "inferences": ["Conclusiones sobre la intención de las partes"],
  "hypotheses": ["Posibles escenarios de litigio por ambigüedad de redacción"],
  "recommendations": ["Sugerencias concretas para subsanar contradicciones u omisiones"]
}

Reglas obligatorias:
1. Si no hay contradicciones internas, devuelve un array vacío en 'internal_contradictions'.
2. Fundamenta cada omisión en la práctica jurídica mercantil o civil mexicana aplicable."""

    @classmethod
    async def run(
        cls,
        document_text: str,
        user_prompt: Optional[str] = None,
        model: Optional[str] = None,
        temperature: float = 0.1
    ) -> Dict[str, Any]:
        wrapped_doc = cls.wrap_document_content(document_text)
        user_msg = (user_prompt or "Analiza la estructura de cláusulas, detecta contradicciones internas y omisiones clave.") + "\n\n" + wrapped_doc

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
