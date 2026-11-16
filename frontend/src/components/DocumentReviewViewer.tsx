"use client";

import { useState, useEffect, useRef } from "react";
import { api } from "@/lib/api";
import { 
  LegalDocument, 
  DocumentPreview, 
  AdvancedAnalysisSession, 
  LegalFinding 
} from "@/types";
import { 
  Scale, 
  ShieldAlert, 
  AlertTriangle, 
  CheckCircle2, 
  BookOpen, 
  Search, 
  FileText, 
  Check, 
  X, 
  MessageSquare, 
  Clock, 
  ShieldCheck, 
  Sparkles, 
  ExternalLink,
  ChevronRight,
  Filter,
  Eye,
  Info
} from "lucide-react";

interface DocumentReviewViewerProps {
  documents: LegalDocument[];
  initialSelectedDocId?: string;
  userRole?: string;
}

export default function DocumentReviewViewer({
  documents,
  initialSelectedDocId,
  userRole
}: DocumentReviewViewerProps) {
  const [selectedDocId, setSelectedDocId] = useState<string>(initialSelectedDocId || documents[0]?.id || "");
  const [preview, setPreview] = useState<DocumentPreview | null>(null);
  const [analysis, setAnalysis] = useState<AdvancedAnalysisSession | null>(null);
  const [loading, setLoading] = useState(false);
  const [activeFinding, setActiveFinding] = useState<LegalFinding | null>(null);
  const [severityFilter, setSeverityFilter] = useState<string>("ALL");
  const [textSearch, setTextSearch] = useState<string>("");

  // HITL Review State
  const [lawyerNotes, setLawyerNotes] = useState<string>("");
  const [lawyerLicense, setLawyerLicense] = useState<string>("");
  const [reviewing, setReviewing] = useState<boolean>(false);
  const [reviewSuccess, setReviewSuccess] = useState<string | null>(null);
  const [reviewError, setReviewError] = useState<string | null>(null);

  const documentContentRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (selectedDocId) {
      loadDocumentData(selectedDocId);
    }
  }, [selectedDocId]);

  const loadDocumentData = async (docId: string) => {
    setLoading(true);
    setActiveFinding(null);
    setReviewSuccess(null);
    setReviewError(null);
    try {
      const [prevData, analysisData] = await Promise.all([
        api.previewDocument(docId).catch(() => null),
        api.getLatestDocumentAnalysis(docId).catch(() => null)
      ]);
      setPreview(prevData);
      setAnalysis(analysisData);

      if (analysisData && analysisData.findings.length > 0) {
        setActiveFinding(analysisData.findings[0]);
        setLawyerNotes(analysisData.findings[0].reviewer_notes || "");
        setLawyerLicense(analysisData.findings[0].reviewer_license || "");
      }
    } catch (err: any) {
      console.error("Error al cargar visor documental:", err);
    } finally {
      setLoading(false);
    }
  };

  const handleSelectFinding = (finding: LegalFinding) => {
    setActiveFinding(finding);
    setLawyerNotes(finding.reviewer_notes || "");
    setLawyerLicense(finding.reviewer_license || "");
    setReviewSuccess(null);
    setReviewError(null);

    // Scroll to fragment if present
    if (finding.original_fragment && documentContentRef.current) {
      const fragmentText = finding.original_fragment.trim();
      const element = document.getElementById(`highlight-${finding.id}`);
      if (element) {
        element.scrollIntoView({ behavior: "smooth", block: "center" });
      }
    }
  };

  const handleReviewFinding = async (status: "VALIDATED" | "REJECTED" | "MODIFIED") => {
    if (!activeFinding) return;
    setReviewing(true);
    setReviewSuccess(null);
    setReviewError(null);

    try {
      const updated = await api.reviewFinding(
        activeFinding.id,
        status,
        lawyerNotes || (status === "VALIDATED" ? "Hallazgo aceptado por abogado revisor" : "Hallazgo descartado tras análisis de fondo"),
        lawyerLicense || undefined
      );

      setReviewSuccess(`Observación ${updated.finding_code} calificada como "${status}".`);
      
      // Update in memory
      if (analysis) {
        const updatedFindings = analysis.findings.map(f => f.id === updated.id ? updated : f);
        setAnalysis({ ...analysis, findings: updatedFindings });
        setActiveFinding(updated);
      }
    } catch (err: any) {
      setReviewError(err?.message || "Error al registrar dictamen humano.");
    } finally {
      setReviewing(false);
    }
  };

  const filteredFindings = (analysis?.findings || []).filter(f => {
    if (severityFilter === "ALL") return true;
    return f.severity === severityFilter;
  });

  // Render text with highlights
  const renderHighlightedText = () => {
    if (!preview || !preview.raw_text) {
      return (
        <div className="p-8 text-center text-slate-400">
          <FileText className="h-10 w-10 mx-auto mb-2 opacity-30" />
          <p className="text-sm">Texto no disponible para este documento.</p>
        </div>
      );
    }

    const raw = preview.raw_text;
    const activeFragment = activeFinding?.original_fragment?.trim();

    if (!activeFragment || !raw.includes(activeFragment)) {
      // Normal display with paragraphs
      return (
        <div className="space-y-4 font-mono text-xs text-slate-800 leading-relaxed">
          {raw.split("\n\n").map((para, i) => (
            <p key={i} className="hover:bg-amber-50/30 p-1.5 rounded transition-colors">
              {para}
            </p>
          ))}
        </div>
      );
    }

    // Split text around the active fragment
    const parts = raw.split(activeFragment);
    return (
      <div className="font-mono text-xs text-slate-800 leading-relaxed">
        {parts.map((part, index) => (
          <span key={index}>
            {part.split("\n\n").map((p, pIdx) => (
              <span key={pIdx}>
                {p}
                {pIdx < part.split("\n\n").length - 1 && <br className="my-2 block" />}
              </span>
            ))}
            {index < parts.length - 1 && (
              <mark
                id={`highlight-${activeFinding?.id}`}
                className="bg-amber-200 text-slate-900 px-1.5 py-0.5 rounded font-bold border-l-4 border-amber-600 shadow-xs animate-pulse inline-block my-1"
                title={`Hallazgo: ${activeFinding?.finding_code} - ${activeFinding?.title}`}
              >
                {activeFragment}
              </mark>
            )}
          </span>
        ))}
      </div>
    );
  };

  return (
    <div className="space-y-6">
      {/* Top Controls & Document Selector */}
      <div className="bg-white rounded-xl border border-slate-200 p-4 shadow-sm flex flex-col md:flex-row items-center justify-between gap-4">
        <div className="flex items-center space-x-3 w-full md:w-auto">
          <div className="bg-slate-900 text-amber-400 p-2 rounded-lg">
            <BookOpen className="h-5 w-5" />
          </div>
          <div>
            <h2 className="text-base font-bold text-slate-900">Visor de Revisión Jurídica</h2>
            <p className="text-xs text-slate-500 font-mono">
              Contraste 1:1 entre texto íntegro, hallazgos epistémicos y dictamen HITL
            </p>
          </div>
        </div>

        <div className="flex items-center space-x-3 w-full md:w-auto">
          <label className="text-xs font-semibold text-slate-600 whitespace-nowrap">Documento:</label>
          <select
            value={selectedDocId}
            onChange={(e) => setSelectedDocId(e.target.value)}
            className="w-full md:w-80 text-xs p-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-slate-900 bg-white font-medium"
          >
            {documents.map((d) => (
              <option key={d.id} value={d.id}>
                {d.title} ({d.doc_type})
              </option>
            ))}
          </select>
        </div>
      </div>

      {loading ? (
        <div className="bg-white rounded-xl border border-slate-200 p-12 text-center text-slate-500 shadow-sm">
          <Scale className="h-8 w-8 mx-auto mb-3 animate-spin text-amber-600" />
          <p className="text-sm font-semibold">Cargando expediente documental y hallazgos...</p>
        </div>
      ) : (
        /* Split Screen Container */
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
          {/* Left Column: Full Document Text (7 cols) */}
          <div className="lg:col-span-7 bg-white/95 backdrop-blur-md rounded-2xl border border-slate-200/80 shadow-[0_4px_24px_-2px_rgba(15,23,42,0.04)] flex flex-col h-[750px] overflow-hidden">
            {/* Header */}
            <div className="p-3.5 bg-slate-50/80 border-b border-slate-200/80 flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <FileText className="h-4 w-4 text-slate-600" />
                <span className="text-xs font-bold text-slate-800">
                  {preview?.title || "Texto Íntegro del Instrumento"}
                </span>
                <span className="text-[10px] bg-slate-200 text-slate-700 px-1.5 py-0.5 rounded font-mono">
                  {preview?.page_count || 1} pág(s)
                </span>
              </div>
              <div className="text-[10px] text-slate-500 font-mono">
                SHA-256: {preview?.sha256_hash ? preview.sha256_hash.slice(0, 16) + "..." : "N/D"}
              </div>
            </div>

            {/* Document Content Scroll Area */}
            <div 
              ref={documentContentRef}
              className="p-6 overflow-y-auto flex-1 bg-white"
            >
              {renderHighlightedText()}
            </div>

            {/* Footer Status */}
            <div className="p-2.5 bg-slate-50 border-t border-slate-200 text-[11px] text-slate-500 flex items-center justify-between font-mono">
              <span>Bóveda WORM Inmutable</span>
              {activeFinding && (
                <span className="text-amber-700 font-semibold">
                  Fragmento resaltado: Cláusula {activeFinding.clause_ref || "General"}
                </span>
              )}
            </div>
          </div>

          {/* Right Column: Findings & Legal Dossier (5 cols) */}
          <div className="lg:col-span-5 flex flex-col gap-4 h-[750px]">
            {/* Observations List & Filter */}
            <div className="bg-white/95 backdrop-blur-md rounded-2xl border border-slate-200/80 shadow-[0_4px_20px_-2px_rgba(15,23,42,0.03)] p-4 flex flex-col max-h-[340px]">
              <div className="flex items-center justify-between pb-3 border-b border-slate-200 mb-3">
                <div className="flex items-center space-x-2">
                  <ShieldAlert className="h-4 w-4 text-rose-600" />
                  <span className="text-xs font-bold text-slate-900">
                    Observaciones Detectadas ({filteredFindings.length})
                  </span>
                </div>

                <div className="flex items-center space-x-1 text-xs">
                  <Filter className="h-3 w-3 text-slate-400" />
                  <select
                    value={severityFilter}
                    onChange={(e) => setSeverityFilter(e.target.value)}
                    className="text-[11px] py-1 px-1.5 border border-slate-200 rounded bg-white text-slate-700"
                  >
                    <option value="ALL">Todas las severidades</option>
                    <option value="CRITICAL">Crítico</option>
                    <option value="HIGH">Alto</option>
                    <option value="MEDIUM">Medio</option>
                    <option value="LOW">Bajo</option>
                  </select>
                </div>
              </div>

              {filteredFindings.length === 0 ? (
                <div className="p-6 text-center text-slate-400 text-xs">
                  {analysis 
                    ? "No se identificaron observaciones bajo el filtro seleccionado." 
                    : "No hay sesión de análisis ejecutada para este documento."}
                </div>
              ) : (
                <div className="overflow-y-auto space-y-2 pr-1 flex-1">
                  {filteredFindings.map((f) => (
                    <div
                      key={f.id}
                      onClick={() => handleSelectFinding(f)}
                      className={`apple-interactive p-2.5 rounded-xl border text-xs cursor-pointer transition-all ${
                        activeFinding?.id === f.id
                          ? "border-amber-400 bg-amber-50/80 shadow-xs ring-1 ring-amber-400/50"
                          : "border-slate-200/80 hover:border-slate-300 hover:bg-slate-50/80"
                      }`}
                    >
                      <div className="flex items-center justify-between mb-1">
                        <span className="font-mono text-[10px] font-bold text-slate-600">
                          {f.finding_code}
                        </span>
                        <span
                          className={`text-[9px] font-bold px-1.5 py-0.2 rounded-full uppercase ${
                            f.severity === "CRITICAL"
                              ? "bg-rose-100 text-rose-800 border border-rose-200"
                              : f.severity === "HIGH"
                              ? "bg-orange-100 text-orange-800 border border-orange-200"
                              : f.severity === "MEDIUM"
                              ? "bg-amber-100 text-amber-800 border border-amber-200"
                              : "bg-blue-100 text-blue-800 border border-blue-200"
                          }`}
                        >
                          {f.severity}
                        </span>
                      </div>
                      <div className="font-semibold text-slate-900 text-xs truncate">{f.title}</div>
                      <div className="text-[11px] text-slate-500 line-clamp-1 mt-0.5">
                        {f.risk_explanation}
                      </div>
                      <div className="flex items-center justify-between mt-1 text-[10px] text-slate-400 font-mono">
                        <span>Cláusula: {f.clause_ref || "General"}</span>
                        <span className={
                          f.review_status === "VALIDATED" ? "text-emerald-600 font-bold" :
                          f.review_status === "REJECTED" ? "text-slate-500 line-through" : "text-amber-600 font-medium"
                        }>
                          {f.review_status}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Active Finding Dossier Detail & Lawyer Actions */}
            {activeFinding ? (
              <div className="bg-white/95 backdrop-blur-md rounded-2xl border border-slate-200/80 shadow-[0_4px_24px_-2px_rgba(15,23,42,0.04)] p-4 flex-1 overflow-y-auto flex flex-col justify-between">
                <div className="space-y-3">
                  {/* Title & Metadata */}
                  <div className="border-b border-slate-100 pb-2">
                    <div className="flex items-center justify-between">
                      <span className="text-[10px] font-mono font-bold text-slate-500">
                        {activeFinding.finding_code} • {activeFinding.issue_type}
                      </span>
                      <span className="text-[10px] font-bold text-indigo-700 bg-indigo-50 px-2 py-0.5 rounded border border-indigo-200">
                        Confianza: {(activeFinding.confidence_score * 100).toFixed(0)}% ({activeFinding.confidence_level})
                      </span>
                    </div>
                    <h3 className="text-sm font-bold text-slate-900 mt-1">{activeFinding.title}</h3>
                  </div>

                  {/* Legal Analysis */}
                  <div>
                    <h4 className="text-[10px] font-bold uppercase text-slate-500 tracking-wider mb-1">
                      Análisis Jurídico
                    </h4>
                    <p className="text-xs text-slate-700 leading-relaxed bg-slate-50 p-2.5 rounded-lg border border-slate-100">
                      {activeFinding.risk_explanation}
                    </p>
                  </div>

                  {/* Statutory Grounds (Fundamento Jurídico) */}
                  {activeFinding.legal_foundation && (
                    <div className="bg-emerald-50/50 border border-emerald-200 rounded-lg p-2.5">
                      <h4 className="text-[10px] font-bold uppercase text-emerald-800 tracking-wider flex items-center space-x-1 mb-1">
                        <Scale className="h-3 w-3 text-emerald-600" />
                        <span>Fundamento Jurídico (Leyes Mexicanas)</span>
                      </h4>
                      <p className="text-xs text-emerald-950 font-medium">
                        {activeFinding.legal_foundation.disposition_name} {activeFinding.legal_foundation.article && `• ${activeFinding.legal_foundation.article}`}
                      </p>
                      <div className="text-[10px] text-emerald-700 mt-1 flex items-center justify-between font-mono">
                        <span>Fuente: {activeFinding.legal_foundation.official_source}</span>
                        <span className="font-bold">
                          {activeFinding.legal_foundation.validity_status === "VIGENTE_VERIFICADA" ? "Vigente verificada" : "Requiere validación"}
                        </span>
                      </div>
                    </div>
                  )}

                  {/* Recommendation */}
                  <div className="bg-purple-50/50 border border-purple-200 rounded-lg p-2.5">
                    <h4 className="text-[10px] font-bold uppercase text-purple-800 tracking-wider flex items-center space-x-1 mb-1">
                      <Sparkles className="h-3 w-3 text-purple-600" />
                      <span>Recomendación Jurídica</span>
                    </h4>
                    <p className="text-xs text-purple-950 leading-relaxed">
                      {activeFinding.recommendation}
                    </p>
                  </div>

                  {/* Lawyer Review Notes & License */}
                  <div className="space-y-2 pt-1 border-t border-slate-100">
                    <div className="flex items-center justify-between">
                      <label className="text-[10px] font-bold uppercase text-slate-600 tracking-wider">
                        Comentarios / Dictamen del Abogado
                      </label>
                      <input
                        type="text"
                        placeholder="Cédula Profesional"
                        value={lawyerLicense}
                        onChange={(e) => setLawyerLicense(e.target.value)}
                        className="text-[10px] font-mono p-1 border border-slate-200 rounded w-32 focus:outline-none focus:ring-1 focus:ring-slate-900"
                      />
                    </div>
                    <textarea
                      rows={2}
                      value={lawyerNotes}
                      onChange={(e) => setLawyerNotes(e.target.value)}
                      placeholder="Escriba aquí sus observaciones técnicas, excepciones o fundamentos adicionales..."
                      className="w-full text-xs p-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-slate-900"
                    />
                  </div>

                  {reviewSuccess && (
                    <div className="p-2 rounded bg-emerald-50 border border-emerald-200 text-emerald-800 text-xs flex items-center space-x-1.5">
                      <CheckCircle2 className="h-3.5 w-3.5 text-emerald-600 flex-shrink-0" />
                      <span>{reviewSuccess}</span>
                    </div>
                  )}

                  {reviewError && (
                    <div className="p-2 rounded bg-rose-50 border border-rose-200 text-rose-800 text-xs flex items-center space-x-1.5">
                      <AlertTriangle className="h-3.5 w-3.5 text-rose-600 flex-shrink-0" />
                      <span>{reviewError}</span>
                    </div>
                  )}
                </div>

                {/* HITL Action Buttons */}
                <div className="pt-3 border-t border-slate-200 flex items-center justify-between gap-2">
                  <button
                    onClick={() => handleReviewFinding("REJECTED")}
                    disabled={reviewing}
                    className="flex-1 py-1.5 px-3 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-lg text-xs font-semibold flex items-center justify-center space-x-1 transition-all"
                  >
                    <X className="h-3.5 w-3.5 text-slate-500" />
                    <span>Descartar</span>
                  </button>
                  <button
                    onClick={() => handleReviewFinding("VALIDATED")}
                    disabled={reviewing}
                    className="flex-1 py-1.5 px-3 bg-slate-900 hover:bg-slate-800 text-white rounded-lg text-xs font-semibold flex items-center justify-center space-x-1 transition-all shadow-sm"
                  >
                    <Check className="h-3.5 w-3.5 text-emerald-400" />
                    <span>Aceptar Hallazgo</span>
                  </button>
                </div>
              </div>
            ) : (
              <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-8 text-center text-slate-400 text-xs flex-1 flex flex-col items-center justify-center">
                <Info className="h-8 w-8 mb-2 opacity-30 text-slate-500" />
                <p className="font-semibold text-slate-700">Ninguna observación seleccionada</p>
                <p className="mt-1 max-w-xs text-slate-400">
                  Seleccione una observación de la lista superior para inspeccionar el fundamento jurídico y dictaminar.
                </p>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
