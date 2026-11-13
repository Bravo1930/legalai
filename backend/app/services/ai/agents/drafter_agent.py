from typing import Dict, Any, Optional
from app.services.ai.agents.base_agent import BaseLegalAgent
from app.services.ai.ollama_client import ollama_client


class LegalDraftingAgent(BaseLegalAgent):
    AGENT_TYPE = "DRAFTER"
    ROLE_DESCRIPTION = "Agente Especialista en Redacción Jurídica, Enmiendas Contractuales y Cláusulas Equilibradas"

    SYSTEM_PROMPT = """Eres un abogado postulante experto en redacción de contratos, convenios y escritos legales en México.
Tu tarea es proponer mejoras de redacción, cláusulas alternativas equilibradas y adendas para proteger al despacho y su cliente.

Debes responder ÚNICAMENTE en formato JSON válido con la siguiente estructura:
{
  "drafting_proposals": [
    {
      "clause_identifier": "Ej: Cláusula Quinta (Pena Convencional)",
      "current_wording_snippet": "Texto actual observado en el documento",
      "proposed_wording": "Redacción alternativa completa, profesional y jurídicamente robusta en español legal mexicano",
      "legal_benefit": "Qué ventaja procesal, económica o de certidumbre otorga el cambio propuesto"
    }
  ],
  "facts": ["Textos vigentes que motivaron la propuesta de cambio"],
  "inferences": ["Razonamiento sobre cómo la nueva redacción previene controversias"],
  "hypotheses": ["Efecto probatorio de la cláusula propuesta ante un tribunal"],
  "recommendations": ["Sugerencias de negociación con la contraparte para aceptar la redacción"]
}

Reglas obligatorias:
1. Las propuestas de redacción deben apegarse al estilo formal de la técnica jurídica mexicana.
2. Toda propuesta tiene carácter consultivo; requiere validación de un abogado facultado."""

    @classmethod
    async def run(
        cls,
        document_text: str,
        user_prompt: Optional[str] = None,
        model: Optional[str] = None,
        temperature: float = 0.2
    ) -> Dict[str, Any]:
        wrapped_doc = cls.wrap_document_content(document_text)
        user_msg = (user_prompt or "Propón mejoras de redacción y cláusulas equilibradas para los puntos críticos del documento.") + "\n\n" + wrapped_doc

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
