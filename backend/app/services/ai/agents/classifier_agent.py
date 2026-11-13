from typing import Dict, Any, Optional
from app.services.ai.agents.base_agent import BaseLegalAgent
from app.services.ai.ollama_client import ollama_client


class DocumentClassifierAgent(BaseLegalAgent):
    AGENT_TYPE = "CLASSIFIER"
    ROLE_DESCRIPTION = "Agente Especialista en Taxonomía y Clasificación Documental Jurídica Mexicana"

    SYSTEM_PROMPT = """Eres un abogado experto en derecho mexicano y archivonomía procesal.
Tu tarea es clasificar con rigor técnico el documento legal proporcionado.

Debes responder ÚNICAMENTE en formato JSON válido con la siguiente estructura:
{
  "document_type": "CONTRATO | CONVENIO | DEMANDA | CONTESTACION | ESCRITO_JUDICIAL | PODER_NOTARIAL | ACTA_ASAMBLEA | DOCUMENTO_CORPORATIVO | SENTENCIA_ACUERDO | OTRO",
  "subtype": "Nombre específico (ej: Contrato de Arrendamiento Mercantil, Demanda de Amparo Indirecto, etc.)",
  "legal_matter": "MERCANTIL | CIVIL | AMPARO | LABORAL | FISCAL | ADMINISTRATIVO | CORPORATIVO | PENAL | FAMILIAR",
  "jurisdiction": "FEDERAL | CIUDAD_DE_MEXICO | ESTATAL",
  "confidence_score": 0.95,
  "facts": ["Hecho 1 extraído literalmente del texto que fundamenta la clasificación", "Hecho 2"],
  "inferences": ["Deducción lógica basada en las cláusulas"],
  "hypotheses": ["Posible régimen legal aplicable si se cumplen supuestos"],
  "recommendations": ["Recomendación para el abogado responsable"]
}

Reglas obligatorias:
1. No inventes datos que no estén en el documento.
2. Si el texto está incompleto o es ambiguo, indica un confidence_score menor a 0.70.
3. Distingue estrictamente entre hechos observables y tus deducciones jurídicas."""

    @classmethod
    async def run(
        cls,
        document_text: str,
        user_prompt: Optional[str] = None,
        model: Optional[str] = None,
        temperature: float = 0.1
    ) -> Dict[str, Any]:
        wrapped_doc = cls.wrap_document_content(document_text)
        
        user_msg = (user_prompt or "Clasifica este documento legal identificando tipo, materia y jurisdicción.") + "\n\n" + wrapped_doc

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
