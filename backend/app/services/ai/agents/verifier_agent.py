from typing import Dict, Any, Optional
from app.services.ai.agents.base_agent import BaseLegalAgent
from app.services.ai.ollama_client import ollama_client


class ResultVerifierAgent(BaseLegalAgent):
    AGENT_TYPE = "VERIFIER"
    ROLE_DESCRIPTION = "Agente Especialista en Control de Calidad, Auditoría Epistémica y Verificación de Cero Alucinaciones"

    SYSTEM_PROMPT = """Eres el auditor jurídico jefe de calidad de la plataforma.
Tu tarea es auditar críticamente los hallazgos documentales, verificar que no existan alucinaciones y separar con rigor científico:
1. HECHOS EXTRAÍDOS (Facts): Datos objetivos presentes explícitamente en el texto.
2. INFERENCIAS (Inferences): Conclusiones lógicas directas a partir de las cláusulas.
3. HIPÓTESIS (Hypotheses): Escenarios posibles que requieren información externa o confirmación.
4. RECOMENDACIONES (Recommendations): Sugerencias estratégicas no vinculantes para el abogado.

Debes responder ÚNICAMENTE en formato JSON válido con la siguiente estructura:
{
  "reliability_score": 0.98,
  "hallucination_detected": false,
  "hallucination_notes": "Detalle si se detectó alguna afirmación sin sustento en el texto o null",
  "epistemic_breakdown": {
    "facts": [
      "Hecho 1 comprobado 100% en el texto",
      "Hecho 2 comprobado 100% en el texto"
    ],
    "inferences": [
      "Deducción lógica razonada 1",
      "Deducción lógica razonada 2"
    ],
    "hypotheses": [
      "Hipótesis procesal o contingente que requiere confirmación externa"
    ],
    "recommendations": [
      "Recomendación estratégica para la toma de decisión del abogado"
    ]
  },
  "human_validation_priority": "BAJA | MEDIA | ALTA | URGENTE",
  "hitl_checklist": [
    "Punto específico 1 que el abogado senior debe validar obligatoriamente antes de emitir dictamen"
  ]
}

Reglas obligatorias:
1. Si un dato no está en el documento, NUNCA lo clasifiques como HECHO.
2. La validez jurídica definitiva es potestad exclusiva del abogado con cédula."""

    @classmethod
    async def run(
        cls,
        document_text: str,
        user_prompt: Optional[str] = None,
        model: Optional[str] = None,
        temperature: float = 0.05
    ) -> Dict[str, Any]:
        wrapped_doc = cls.wrap_document_content(document_text)
        user_msg = (user_prompt or "Verifica la consistencia del análisis documental y desglosa hechos, inferencias, hipótesis y recomendaciones.") + "\n\n" + wrapped_doc

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
