import time
import json
import httpx
import ipaddress
import urllib.parse
from typing import List, Dict, Any, Optional
from app.core.config import settings
from app.core.logging import logger
from app.core.errors import AppException, ForbiddenException


class OllamaClient:
    """Cliente HTTP asíncrono para inferencia privada con modelos locales en Ollama."""

    def __init__(self, base_url: Optional[str] = None, allow_public_ips: Optional[bool] = None):
        self.base_url = (base_url or settings.OLLAMA_BASE_URL).rstrip("/")
        self.allow_public_ips = settings.OLLAMA_ALLOW_PUBLIC_IPS if allow_public_ips is None else allow_public_ips
        self.timeout = settings.OLLAMA_TIMEOUT_SECONDS
        self._verify_private_endpoint(self.base_url)

    def _verify_private_endpoint(self, url: str) -> None:
        """
        Barrera de Soberanía de Datos (Zero-Cloud-Egress Policy):
        Garantiza que la URL de inferencia de IA no apunte a endpoints públicos ni a nubes
        comerciales de IA no autorizadas para preservar el secreto profesional.
        """
        parsed = urllib.parse.urlparse(url)
        hostname = (parsed.hostname or "").lower()

        trusted_hosts = {"localhost", "127.0.0.1", "::1", "host.docker.internal", "ollama", "private-ollama"}
        if hostname in trusted_hosts:
            return

        # Si no se permiten IPs públicas explícitamente, validar rango privado RFC1918
        if not self.allow_public_ips:
            try:
                ip = ipaddress.ip_address(hostname)
                if not (ip.is_private or ip.is_loopback):
                    raise ForbiddenException(
                        f"Violación de política de soberanía de datos: La IP de inferencia '{hostname}' es pública. "
                        "El motor de IA debe residir en localhost o en una red privada autorizada."
                    )
            except ValueError:
                # Es un FQDN; bloquear proveedores públicos de IA y dominios no autorizados
                blocked_domains = [
                    "openai.com", "anthropic.com", "amazonaws.com", 
                    "azure.com", "googleapis.com", "groq.com", "cohere.com"
                ]
                if any(blocked in hostname for blocked in blocked_domains):
                    raise ForbiddenException(
                        f"Violación de confidencialidad jurídica: Está prohibido enviar documentos legales a proveedores externos ({hostname})."
                    )
                # Si es un FQDN que no pertenece a un espacio privado reconocido
                private_suffixes = (".internal", ".local", ".lan", ".corp", ".priv", ".home.arpa")
                if not (hostname.endswith(private_suffixes) or "." not in hostname):
                    raise ForbiddenException(
                        f"Violación de política de soberanía de datos: El host de inferencia '{hostname}' no es un dominio privado reconocido."
                    )

    def _get_headers(self) -> Dict[str, str]:
        """Genera encabezados con token de autenticación para proxies privados."""
        headers = {
            "Content-Type": "application/json",
            "X-Legal-Client": "LegalAI-Mexico-Production"
        }
        if settings.OLLAMA_API_KEY:
            headers["Authorization"] = f"Bearer {settings.OLLAMA_API_KEY}"
        return headers

    async def list_models(self) -> List[Dict[str, Any]]:
        """Consulta los modelos instalados en la instancia local de Ollama."""
        try:
            async with httpx.AsyncClient(
                timeout=5.0,
                verify=settings.OLLAMA_VERIFY_SSL,
                headers=self._get_headers()
            ) as client:
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
                async with httpx.AsyncClient(
                    timeout=float(self.timeout),
                    verify=settings.OLLAMA_VERIFY_SSL,
                    headers=self._get_headers()
                ) as client:
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
