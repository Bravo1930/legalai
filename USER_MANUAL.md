# MANUAL DE USUARIO PARA EQUIPOS JURÍDICOS
## Plataforma de Inteligencia Artificial LegalAI México

---

### 1. INTRODUCCIÓN Y ROLES DE USUARIO

LegalAI México es una plataforma diseñada para potenciar la productividad y el rigor técnico de los despachos jurídicos. La plataforma respeta la jerarquía funcional de la abogacía mediante perfiles de acceso:

- **Socio Director (Managing Partner):** Control total de la cartera de clientes, expedientes, asignación de equipos, configuración de reglas internas del despacho y aprobaciones definitivas.
- **Abogado Senior / Asociado:** Análisis documental, redacción de contratos y escritos judiciales, formulación de propuestas de modificación y aprobación definitiva con registro de Cédula Profesional.
- **Revisor Jurídico:** Auditoría técnica de cláusulas, revisión de riesgos contractuales y emisión de dictámenes preliminares.
- **Asistente Jurídico Autorizado:** Carga de documentos, etiquetado inicial de expedientes y solicitudes de corrección bajo supervisión letrada.

---

### 2. ACCESO Y NAVEGACIÓN PRINCIPAL

1. Ingrese a la URL asignada a su despacho (p. ej. `https://legalai.despacho.com` o `http://localhost:3001`).
2. En la pantalla de bienvenida, capture su **Correo Electrónico Institucional** y **Contraseña**.
3. El sistema lo dirigirá al **Dashboard Principal**, desde el cual podrá visualizar:
   - Volumen de documentos recibidos y procesados.
   - Documentos pendientes de revisión y términos procesales próximos a vencer.
   - Riesgos críticos detectados que requieren atención inmediata.
   - Carga de trabajo distribuida entre los abogados del despacho.

---

### 3. GESTIÓN Y CARGA DE DOCUMENTOS JURÍDICOS

#### 3.1. Carga de Archivos en la Bóveda Inmutable (WORM)
1. Diríjase a la sección **Documentos** en la barra de navegación lateral.
2. Haga clic en el botón **"Cargar Documento"** (o "Carga Múltiple" para expedientes voluminosos).
3. Seleccione el archivo en formato **PDF**, **DOCX**, **TXT** o imagen escaneada (**PNG/JPEG/TIFF**).
4. Indique los datos de clasificación:
   - **Título del Documento** (opcional; si se omite, se adoptará el nombre sanitizado del archivo).
   - **Clasificación Jurídica:** Contrato, Convenio, Demanda, Contestación, Escrito Judicial, Poder Notarial, Acta de Asamblea o Identificación.
   - **Expediente / Asunto:** Seleccione el expediente al que pertenece la pieza procesal.
   - **Cliente:** Indique el cliente patrocinado.
5. Haga clic en **"Procesar Documento"**.
6. El sistema validará la integridad del archivo, calculará su firma criptográfica **SHA-256** y extraerá automáticamente el texto íntegro (aplicando OCR óptico si se trata de un documento escaneado).

---

### 4. REVISIÓN Y ANÁLISIS JURÍDICO CON INTELIGENCIA ARTIFICIAL

#### 4.1. Ejecución del Análisis Avanzado
1. Dentro de la ficha del documento, seleccione la pestaña **"Análisis de IA"**.
2. Haga clic en **"Iniciar Análisis Avanzado"**.
3. El motor de agentes jurídicos descompondrá el documento en sus cláusulas constitutivas y evaluará la existencia de defectos o riesgos.

#### 4.2. Visualizador Documental y Resaltado Interactivo
- En el panel izquierdo se desplegará el texto íntegro del documento.
- En el panel derecho se listarán las **Observaciones y Riesgos Detectados**, ordenados por severidad:
  - **Crítico (Rojo):** Violaciones imperativas de ley (p. ej. cláusula penal que excede la obligación principal, Art. 1843 CCF; o renuncia de derechos laborales, Art. 33 LFT).
  - **Alto (Naranja):** Ausencia de cláusulas esenciales (jurisdicción indeterminada, falta de aviso de privacidad LFPDPPP).
  - **Medio (Amarillo):** Ambigüedades en plazos de pago o penalizaciones moratorias no topadas.
  - **Bajo (Azul):** Mejoras de redacción o estilo gramatical.
- **Interacción:** Al hacer clic sobre cualquier observación en la lista, el visor documental **resaltará inmediatamente el fragmento textual original** (*verbatim quote*) en el contrato, permitiéndole corroborar la fuente en contexto.

#### 4.3. Validación Humana en el Bucle (Human-in-the-Loop)
Por cada riesgo detectado, el abogado revisor cuenta con tres opciones:
- **Aceptar Hallazgo:** Confirma la procedencia del riesgo técnico para que se considere en la redacción correctiva.
- **Rechazar / Descartar:** Permite descartar la observación, debiendo ingresar obligatoriamente una breve justificación jurídica (p. ej. *"El cliente asumió expresamente este riesgo comercial por acuerdo preliminar"*).
- **Convertir en Propuesta de Redacción:** Envía el fragmento defectuoso al generador de modificaciones para sustituirlo por una cláusula legalmente válida.

---

### 5. MODIFICACIONES, COMPARADOR DE VERSIONES (REDLINE) Y EXPORTACIÓN

1. Diríjase a la sección **"Modificaciones"**.
2. La plataforma mostrará las propuestas de redacción alternativa generadas:
   - **Panel Original:** Texto defectuoso actual.
   - **Panel Propuesto:** Redacción sugerida corregida conforme al derecho positivo mexicano.
   - **Fundamentación:** Explicación del artículo de ley aplicable.
3. Revise las diferencias resaltadas visualmente (adiciones en verde, supresiones en rojo tachado).
4. El abogado puede editar directamente el texto propuesto antes de aceptarlo.
5. Al aprobar los cambios, presione **"Compilar Nueva Versión"**.
6. El sistema generará una nueva versión derivada (v2, v3, etc.) conservando el original original inmutable, y le permitirá **Exportar a DOCX** o **Exportar a PDF** con membrete formal.

---

### 6. AUTOMATIZACIÓN DE FLUJOS Y APROBACIONES LEGALES

#### 6.1. Ciclo de Vida del Expediente
Todo documento recorre una secuencia procesal controlada:
`Recibido` → `En Procesamiento` → `Análisis Completado` → `Con Observaciones` → `Pendiente de Revisión` → `En Corrección` → `Pendiente de Aprobación` → `Aprobado` (o `Rechazado` / `Archivado`).

#### 6.2. Emisión de Aprobación Definitiva
1. El abogado responsable o socio asignado accede a la sección **"Aprobaciones"**.
2. Verifica que todas las observaciones críticas hayan sido resueltas o justificadas.
3. Para emitir el visto bueno definitivo, capture obligatoriamente:
   - **Cédula Profesional:** Número oficial expedido por la Dirección General de Profesiones (SEP).
   - **Notas de Aprobación:** Dictamen o comentarios para el expediente.
4. Presione **"Emitir Aprobación Definitiva"**.
5. El documento quedará sellado con estatus `APROBADO`, registrando la fecha, hora, Cédula del firmante y el hash criptográfico exacto del documento aprobado.

> [!CAUTION]
> **Regla de Seguridad Jurídica:** Si con posterioridad a la aprobación definitiva cualquier usuario modifica el contenido del documento o carga una nueva versión, el sistema **invalidará automáticamente las aprobaciones previas** (`INVALIDATED_BY_CONTENT_CHANGE`) y devolverá el documento a estado `EN CORRECCIÓN`, garantizando que ninguna alteración circule sin la ratificación formal del abogado titular.
