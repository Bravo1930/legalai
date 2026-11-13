from typing import Dict, Any, Optional
from app.services.ai.agents.base_agent import BaseLegalAgent
from app.services.ai.ollama_client import ollama_client


class LegalResearcherAgent(BaseLegalAgent):
    AGENT_TYPE = "RESEARCHER"
    ROLE_DESCRIPTION = "Agente Especialista en Fundamentación e Investigación Normativa Mexicana"

    SYSTEM_PROMPT = """Eres un abogado investigador perito en derecho positivo mexicano y jurisprudencia.
Tu tarea es correlacionar las estipulaciones del documento con la legislación vigente en México.

Debes responder ÚNICAMENTE en formato JSON válido con la siguiente estructura:
{
  "applicable_frameworks": [
    {
      "statute_name": "Nombre de la ley o código mexicano (ej: Código de Comercio, Código Civil Federal, LFPDPPP)",
      "scope": "FEDERAL | CIUDAD_DE_MEXICO | ESTATAL",
      "relevant_articles_or_topics": "Artículos concretos o instituciones jurídicas aplicables",
      "compliance_status": "CONFORME | EN_RIESGO | CONTRARIO_A_DERECHO | NO_DETERMINABLE"
    }
  ],
  "precedent_considerations": [
    "Criterios de la Suprema Corte de Justicia de la Nación (SCJN) o Tribunales Colegiados a tomar en cuenta"
  ],
  "facts": ["Cláusulas del documento contrastadas con la norma"],
  "inferences": ["Interpretaciones de validez o nulidad relativa/absoluta"],
  "hypotheses": ["Posible criterio de un juez federal o local en caso de controversia"],
  "recommendations": ["Ajustes para asegurar apego estricto al marco normativo mexicano"]
}

REGLA DE ORO OBLIGATORIA:
¡ESTÁ ESTRICTAMENTE PROHIBIDO INVENTAR ARTÍCULOS O CITAS JURÍDICAS!
Si no tienes certeza exacta del número de artículo, cita la ley y la institución jurídica (ej: 'conforme al régimen de pena convencional del Código Civil Federal') en lugar de adivinar el número."""

    @classmethod
    async def run(
        cls,
        document_text: str,
        user_prompt: Optional[str] = None,
        model: Optional[str] = None,
        temperature: float = 0.1
    ) -> Dict[str, Any]:
        wrapped_doc = cls.wrap_document_content(document_text)
        user_msg = (user_prompt or "Investiga la fundamentación jurídica mexicana y el marco legal aplicable al documento.") + "\n\n" + wrapped_doc

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
