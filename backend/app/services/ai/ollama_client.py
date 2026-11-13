import time
import json
import httpx
from typing import List, Dict, Any, Optional
from app.core.config import settings
from app.core.logging import logger
from app.core.errors import AppException


class OllamaClient:
    """Cliente HTTP asíncrono para inferencia con modelos locales en Ollama."""

    def __init__(self, base_url: Optional[str] = None):
        self.base_url = (base_url or settings.OLLAMA_BASE_URL).rstrip("/")
        self.timeout = settings.OLLAMA_TIMEOUT_SECONDS

    async def list_models(self) -> List[Dict[str, Any]]:
        """Consulta los modelos instalados en la instancia local de Ollama."""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                res = await client.get(f"{self.base_url}/api/tags")
                if res.status_code != 200:
                    raise AppException(f"Ollama respondió con código HTTP {res.status_code}")
                data = res.json()
                return data.get("models", [])
        except Exception as e:
            logger.error(f"Error al listar modelos en Ollama: {e}")
            return []

    async def select_optimal_model(self, preferred_model: Optional[str] = None) -> str:
        """
        Selecciona dinámicamente el mejor modelo disponible comprobando las capacidades reales.
        No asume la existencia de un modelo fijo; tiene lista de preferencias seguras.
        """
        available = await self.list_models()
        available_names = [m["name"] for m in available]

        if not available_names:
            logger.warning("No se detectaron modelos en Ollama. Usando fallback configurado.")
            return preferred_model or settings.OLLAMA_LLM_MODEL

        # 1. Si el usuario solicitó uno específico y existe
        if preferred_model and preferred_model in available_names:
            return preferred_model

        # 2. Preferencia de modelos de análisis jurídico probados que caben en la GPU local (6GB VRAM)
        priority_list = [
            "qwen3.5:4b",
            "qwen2.5-coder:7b",
            "hermes3:latest",
            "gemma3:4b",
            "qwen2.5-coder:1.5b"
        ]

        for cand in priority_list:
            if cand in available_names:
                return cand

        # 3. Si ninguno coincide, seleccionar el primer modelo con capacidad de completion
        for m in available:
            caps = m.get("capabilities", [])
            if "completion" in caps or not caps:
                return m["name"]

        return available_names[0]

    async def generate_chat(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.1,
        num_ctx: int = 16384,
        format_json: bool = True,
        max_retries: int = 2
    ) -> Dict[str, Any]:
        """
        Ejecuta inferencia de chat con reintentos y captura de métricas de tokens y latencia.
        """
        target_model = await self.select_optimal_model(model)
        start_time = time.time()

        payload: Dict[str, Any] = {
            "model": target_model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_ctx": num_ctx,
                "top_p": 0.9,
            }
        }

        if format_json:
            payload["format"] = "json"

        last_error = None
        for attempt in range(max_retries + 1):
            try:
                async with httpx.AsyncClient(timeout=float(self.timeout)) as client:
                    resp = await client.post(f"{self.base_url}/api/chat", json=payload)
                    
                    if resp.status_code == 200:
                        data = resp.json()
                        latency_ms = int((time.time() - start_time) * 1000)
                        
                        message_content = data.get("message", {}).get("content", "")
                        
                        # Tokens y estadísticas de Ollama
                        prompt_eval_count = data.get("prompt_eval_count", 0)
                        eval_count = data.get("eval_count", 0)

                        return {
                            "content": message_content,
                            "model": target_model,
                            "tokens_prompt": prompt_eval_count,
                            "tokens_completion": eval_count,
                            "latency_ms": latency_ms,
                            "raw": data
                        }
                    else:
                        last_error = f"HTTP {resp.status_code}: {resp.text}"
            except Exception as e:
                last_error = str(e)
                logger.warning(f"Reintento {attempt + 1}/{max_retries} en llamada a Ollama ({target_model}): {e}")
                time.sleep(1.0 * (attempt + 1))

        raise AppException(
            f"Fallo de inferencia en Ollama tras {max_retries + 1} intentos: {last_error}"
        )


ollama_client = OllamaClient()
