# LegalAI México ⚖️🇲🇽
### Plataforma Empresarial de Inteligencia Artificial para Gestión y Análisis Documental Jurídico

Plataforma multi-inquilino (*multi-tenant*) con arquitectura *Human-in-the-Loop* (HITL) diseñada específicamente para la práctica jurídica mexicana (Legislación Federal, 32 Entidades Federativas, CDMX, Jurisprudencia SCJN/TCC, TFJA, y normativa mercantil/corporativa).

---

## 🏛️ Principios Rectores
1. **Human-in-the-Loop (HITL):** La IA asiste y propone, pero ninguna conclusión, modificación o aprobación jurídica tiene validez definitiva sin la aprobación y firma explícita de un abogado facultado con cédula profesional.
2. **Cero Alucinaciones:** Toda fundamentación normativa citada proviene de un corpus legal recuperado con trazabilidad exacta (Artículo, Jurisdicción, Materia, Autoridad, Época y Registro Digital de Tesis).
3. **Inmutabilidad y Cadena de Custodia:** El documento original nunca se sobreescribe y se almacena con hash criptográfico SHA-256.
4. **Privacidad y Secreto Profesional:** Inferencia 100% local mediante Ollama en `localhost`. Cero fuga de expedientes confidenciales a servicios externos de terceros.
5. **Aislamiento Multi-Tenant:** Segregación estricta de expedientes, clientes y análisis por despacho.

---

## 📚 Documentación de Arquitectura e Ingeniería
- [Arquitectura Técnica Completa](file:///C:/Users/Asus/proyecto%20legal%20agy/ARCHITECTURE.md)
- [Registro de Decisiones Técnicas (ADR)](file:///C:/Users/Asus/proyecto%20legal%20agy/TECHNICAL_DECISIONS.md)

---

## 💻 Stack Tecnológico
* **Frontend:** Next.js 14/15, TypeScript, Tailwind CSS, Radix UI.
* **Backend:** Python 3.11, FastAPI, Pydantic v2, SQLAlchemy 2.0.
* **Base de Datos:** PostgreSQL 16 con extensión vectorial `pgvector` y soporte de búsqueda textual en español.
* **Motor de IA Local:** Ollama (`127.0.0.1:11434`), con modelos locales `bge-m3` (embeddings) y `qwen3.5:4b` / `qwen2.5-coder:7b` (análisis/extracción) acelerados por GPU NVIDIA GeForce RTX 4050.
* **Almacenamiento:** Almacenamiento local seguro en desarrollo / S3 y MinIO en producción (WORM).
