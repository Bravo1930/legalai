def test_enqueue_and_get_task(client, auth_headers):
    """Verifica el flujo completo de encolado y consulta de tareas asíncronas."""
    payload = {
        "task_type": "CONTRACT_ANALYSIS",
        "payload": {
            "contract_type": "ARRENDAMIENTO_MERCANTIL",
            "clauses": 15
        }
    }
    # Encolar tarea
    response = client.post("/api/v1/tasks", json=payload, headers=auth_headers)
    assert response.status_code == 200
    task_data = response.json()
    assert task_data["task_type"] == "CONTRACT_ANALYSIS"
    assert task_data["status"] == "PENDING"
    task_id = task_data["id"]

    # Consultar tarea por ID
    get_res = client.get(f"/api/v1/tasks/{task_id}", headers=auth_headers)
    assert get_res.status_code == 200
    assert get_res.json()["id"] == task_id

    # Listar tareas del despacho
    list_res = client.get("/api/v1/tasks", headers=auth_headers)
    assert list_res.status_code == 200
    tasks = list_res.json()
    assert any(t["id"] == task_id for t in tasks)
