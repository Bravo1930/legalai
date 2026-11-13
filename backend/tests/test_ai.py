import io
import pytest
from app.services.ai.ollama_client import ollama_client
from app.services.ai.agents.classifier_agent import DocumentClassifierAgent
from app.services.ai.agents.risk_detector_agent import RiskDetectorAgent
from app.services.ai.agents.verifier_agent import ResultVerifierAgent


@pytest.mark.asyncio
async def test_ollama_list_models_live():
    """Verifica que el cliente consulte los modelos reales de Ollama local."""
    models = await ollama_client.list_models()
    assert isinstance(models, list)
    model_names = [m["name"] for m in models]
    # Comprobar que detecta alguno de los modelos instalados en la máquina
    assert any(m in model_names for m in ["bge-m3:latest", "qwen3.5:4b", "qwen2.5-coder:7b", "hermes3:latest"])


@pytest.mark.asyncio
async def test_select_optimal_model():
    """Verifica que seleccione dinámicamente un modelo adecuado sin errores."""
    chosen = await ollama_client.select_optimal_model()
    assert chosen is not None
    assert isinstance(chosen, str)


def test_api_list_ai_models(client, lawyer_headers):
    """Verifica el endpoint GET /api/v1/ai/models."""
    response = client.get("/api/v1/ai/models", headers=lawyer_headers)
    assert response.status_code == 200
    models = response.json()
    assert isinstance(models, list)
    assert len(models) > 0
    assert "name" in models[0]
    assert "capabilities" in models[0]


def test_ai_analyze_document_endpoint(client, lawyer_headers):
    """Prueba la ejecución de un agente de IA en vivo a través de la API."""
    # 1. Cargar contrato de prueba
    contract_text = """
    CONTRATO DE PRESTACIÓN DE SERVICIOS LEGALES
    En Guadalajara, Jalisco, a los 10 de febrero de 2026, celebran:
    CLIENTE: Constructora de Occidente S.A. de C.V.
    PRESTADOR: Bufete Jurídico México & Asociados S.C.
    PRIMERA. OBJETO: Auditoría legal ambiental y corporativa.
    SEGUNDA. HONORARIOS: $120,000.00 M.N. pagaderos en dos parcialidades.
    TERCERA. JURISDICCIÓN: Tribunales competentes de la Ciudad de México.
    Firmado por el apoderado con cédula profesional 1234567.
    """
    files = {"file": ("contrato_servicios.txt", io.BytesIO(contract_text.encode("utf-8")), "text/plain")}
    upload_res = client.post(
        "/api/v1/documents/upload",
        files=files,
        data={"title": "Contrato de Servicios Legales 2026", "doc_type": "CONTRATO"},
        headers=lawyer_headers
    )
    assert upload_res.status_code == 200
    doc_id = upload_res.json()["id"]

    # 2. Ejecutar agente CLASSIFIER vía API
    analysis_res = client.post(
        f"/api/v1/ai/analyze/{doc_id}",
        json={"agent_type": "CLASSIFIER"},
        headers=lawyer_headers
    )
    assert analysis_res.status_code == 200
    data = analysis_res.json()
    assert data["agent_type"] == "CLASSIFIER"
    assert data["document_id"] == doc_id
    assert "structured_output" in data
    assert "model_used" in data
    assert data["latency_ms"] >= 0

    # 3. Comprobar distinción epistémica obligatoria en la salida
    output = data["structured_output"]
    assert "facts" in output or "document_type" in output

    # 4. Consultar historial de análisis del documento
    history_res = client.get(f"/api/v1/ai/analyses/{doc_id}", headers=lawyer_headers)
    assert history_res.status_code == 200
    history = history_res.json()
    assert len(history) >= 1
    assert any(a["id"] == data["id"] for a in history)


def test_superadmin_blocked_from_ai_analysis(client, auth_headers):
    """Verifica que SUPER_ADMIN tenga prohibido ejecutar análisis sobre documentos de despachos."""
    fake_doc_id = "00000000-0000-0000-0000-000000000001"
    res = client.post(
        f"/api/v1/ai/analyze/{fake_doc_id}",
        json={"agent_type": "CLASSIFIER"},
        headers=auth_headers
    )
    assert res.status_code == 403
    assert res.json()["error"]["code"] == "FORBIDDEN"
