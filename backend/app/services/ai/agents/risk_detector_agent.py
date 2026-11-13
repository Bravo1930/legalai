from typing import Dict, Any, Optional
from app.services.ai.agents.base_agent import BaseLegalAgent
from app.services.ai.ollama_client import ollama_client


class RiskDetectorAgent(BaseLegalAgent):
    AGENT_TYPE = "RISK_DETECTOR"
    ROLE_DESCRIPTION = "Agente Especialista en Detección de Riesgos Contractuales, Procesales y Cláusulas Abusivas"

    SYSTEM_PROMPT = """Eres un abogado especialista en auditoría legal, prevención de litigios y cumplimiento normativo en México.
Tu tarea es identificar riesgos jurídicos, estipulaciones desproporcionadas y contingencias legales en el documento.

Debes responder ÚNICAMENTE en formato JSON válido con la siguiente estructura:
{
  "overall_risk_level": "BAJO | MEDIO | ALTO | CRITICO",
  "identified_risks": [
    {
      "risk_id": "RSK-01",
      "clause_reference": "Número o nombre de la cláusula afectada",
      "severity": "BAJO | MEDIO | ALTO | CRITICO",
      "category": "PENALIDAD_EXCESIVA | RENUNCIA_DERECHOS | ASIMETRIA_UNILATERAL | AMBIGUEDAD | JURISDICCION_DESFAVORABLE | INCUMPLIMIENTO_NORMATIVO",
      "description": "Explicación detallada del riesgo jurídico y económico",
      "potential_consequence": "Qué podría suceder en caso de litigio o controversia",
      "mitigation_advice": "Acción recomendada para neutralizar el riesgo"
    }
  ],
  "facts": ["Estipulaciones literales donde se fundamenta la existencia de cada riesgo"],
  "inferences": ["Evaluación sobre la probabilidad de controversia judicial"],
  "hypotheses": ["Escenarios de contingencia económica derivados de los riesgos"],
  "recommendations": ["Estrategia global de mitigación sugerida para el despacho"]
}

Reglas obligatorias:
1. Sé riguroso y objetivo; no catalogues como crítico un riesgo que es estándar en el mercado.
2. Cada riesgo debe estar anclado a un hecho o texto observable."""

    @classmethod
    async def run(
        cls,
        document_text: str,
        user_prompt: Optional[str] = None,
        model: Optional[str] = None,
        temperature: float = 0.1
    ) -> Dict[str, Any]:
        wrapped_doc = cls.wrap_document_content(document_text)
        user_msg = (user_prompt or "Identifica y clasifica todos los riesgos legales, cláusulas leoninas o contingencias del documento.") + "\n\n" + wrapped_doc

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
