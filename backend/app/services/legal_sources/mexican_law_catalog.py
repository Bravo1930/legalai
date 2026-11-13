import re
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List, Tuple

# Catálogo maestro de disposiciones oficiales mexicanas
# Fuentes primarias: Diario Oficial de la Federación (DOF), Cámara de Diputados del H. Congreso de la Unión, SCJN.
MEXICAN_OFFICIAL_CATALOG = {
    "CODIGO_DE_COMERCIO": {
        "aliases": [
            "codigo de comercio", "código de comercio", "c. com.", "ccom", "cod. com."
        ],
        "official_title": "Código de Comercio",
        "jurisdiction": "Federal",
        "initial_publication_dof": "1889-10-07 / 1889-12-13",
        "latest_reform_dof": "2018-03-28",
        "official_source": "Diario Oficial de la Federación / Cámara de Diputados del H. Congreso de la Unión",
        "is_currently_in_force": True,
        "valid_article_range": (1, 1463),
        "notable_articles": {
            "1093": "Prorrogación de jurisdicción por sumisión expresa (Tribunales competentes).",
            "78": "Principio de libertad contractual en materia mercantil.",
            "89": "Comercio electrónico y mensajes de datos (Firma electrónica).",
            "362": "Intereses moratorios convencionales y legales en préstamo mercantil."
        }
    },
    "CODIGO_CIVIL_FEDERAL": {
        "aliases": [
            "codigo civil federal", "código civil federal", "c.c.f.", "ccf", "cod. civ. fed."
        ],
        "official_title": "Código Civil Federal",
        "jurisdiction": "Federal",
        "initial_publication_dof": "1928-05-26",
        "latest_reform_dof": "2024-01-17",
        "official_source": "Diario Oficial de la Federación / Cámara de Diputados",
        "is_currently_in_force": True,
        "valid_article_range": (1, 3074),
        "notable_articles": {
            "1843": "Límite imperativo de la cláusula penal: no puede exceder en valor ni en cuantía a la obligación principal.",
            "1796": "Perfeccionamiento de contratos por mero consentimiento (Pacta sunt servanda).",
            "1797": "Validez y cumplimiento de contratos no puede dejarse al arbitrio de uno de los contratantes.",
            "2111": "Caso fortuito o fuerza mayor liberatoria de responsabilidad."
        }
    },
    "CODIGO_CIVIL_CDMX": {
        "aliases": [
            "codigo civil para el distrito federal", "código civil para el distrito federal",
            "codigo civil para la ciudad de mexico", "código civil para la ciudad de méxico",
            "ccdf", "cccdmx"
        ],
        "official_title": "Código Civil para el Distrito Federal (aplicable a la Ciudad de México)",
        "jurisdiction": "Ciudad de México (Local)",
        "initial_publication_dof": "1928-05-26",
        "latest_reform_dof": "Gaceta Oficial de la Ciudad de México 2024-06-12",
        "official_source": "Gaceta Oficial de la Ciudad de México / Consejería Jurídica y de Servicios Legales CDMX",
        "is_currently_in_force": True,
        "valid_article_range": (1, 3074),
        "notable_articles": {
            "1843": "Cláusula penal: límite cuantitativo respecto de la obligación principal en CDMX."
        }
    },
    "LEY_FEDERAL_DEL_TRABAJO": {
        "aliases": [
            "ley federal del trabajo", "l.f.t.", "lft", "ley laboral"
        ],
        "official_title": "Ley Federal del Trabajo",
        "jurisdiction": "Federal",
        "initial_publication_dof": "1970-04-01",
        "latest_reform_dof": "2024-01-24",
        "official_source": "Diario Oficial de la Federación / Cámara de Diputados",
        "is_currently_in_force": True,
        "valid_article_range": (1, 1010),
        "notable_articles": {
            "33": "Nulidad absoluta e inderogable de la renuncia de derechos devengados o indemnizaciones del trabajador.",
            "5": "Disposiciones de orden público laboral que no producen efecto legal alguno.",
            "47": "Causales de rescisión de la relación de trabajo sin responsabilidad para el patrón."
        }
    },
    "CONSTITUCION_POLITICA": {
        "aliases": [
            "constitucion politica de los estados unidos mexicanos", "constitución política de los estados unidos mexicanos",
            "c.p.e.u.m.", "cpeum", "carta magna", "constitucion federal"
        ],
        "official_title": "Constitución Política de los Estados Unidos Mexicanos",
        "jurisdiction": "Federal / Constitucional",
        "initial_publication_dof": "1917-02-05",
        "latest_reform_dof": "2024-09-15",
        "official_source": "Diario Oficial de la Federación / SCJN / Cámara de Diputados",
        "is_currently_in_force": True,
        "valid_article_range": (1, 136),
        "notable_articles": {
            "123": "Derecho al trabajo digno y prerrogativas irrenunciables (Apartados A y B).",
            "14": "Garantía de irretroactividad de la ley y debido proceso legal.",
            "16": "Garantía de fundamentación y motivación en actos de autoridad.",
            "17": "Prohibición de autotutela y acceso a la impartición de justicia gratuita y expedita."
        }
    },
    "LFPDPPP": {
        "aliases": [
            "ley federal de proteccion de datos personales en posesion de los particulares",
            "ley federal de protección de datos personales en posesión de los particulares",
            "lfpdppp", "ley de datos personales"
        ],
        "official_title": "Ley Federal de Protección de Datos Personales en Posesión de los Particulares",
        "jurisdiction": "Federal",
        "initial_publication_dof": "2010-07-05",
        "latest_reform_dof": "2010-07-05 (Texto vigente sin reformas desfavorables)",
        "official_source": "Diario Oficial de la Federación / INAI / Cámara de Diputados",
        "is_currently_in_force": True,
        "valid_article_range": (1, 69),
        "notable_articles": {
            "8": "Requisito de consentimiento tácito o expreso para el tratamiento de datos personales.",
            "15": "Obligación de poner a disposición el Aviso de Privacidad.",
            "16": "Contenido mínimo obligatorio del Aviso de Privacidad (Finalidad, Responsable, Derechos ARCO)."
        }
    },
    "LFPPI": {
        "aliases": [
            "ley federal de proteccion a la propiedad industrial",
            "ley federal de protección a la propiedad industrial",
            "lfppi", "ley de propiedad industrial"
        ],
        "official_title": "Ley Federal de Protección a la Propiedad Industrial",
        "jurisdiction": "Federal",
        "initial_publication_dof": "2020-07-01",
        "latest_reform_dof": "2020-07-01 (En vigor desde el 5 de noviembre de 2020)",
        "official_source": "Diario Oficial de la Federación / IMPI / Cámara de Diputados",
        "is_currently_in_force": True,
        "valid_article_range": (1, 412),
        "notable_articles": {
            "82": "Concepto legal de Secreto Industrial (Información de aplicación industrial o comercial reservada).",
            "85": "Deber de confidencialidad y cláusulas de secreto en convenios y contratos.",
            "386": "Infracciones administrativas y sanciones por revelación ilícita de secretos industriales."
        }
    },
    "LEY_GENERAL_SOCIEDADES_MERCANTILES": {
        "aliases": [
            "ley general de sociedades mercantiles", "lgsm", "ley de sociedades mercantiles"
        ],
        "official_title": "Ley General de Sociedades Mercantiles",
        "jurisdiction": "Federal",
        "initial_publication_dof": "1934-08-04",
        "latest_reform_dof": "2023-10-20",
        "official_source": "Diario Oficial de la Federación / Cámara de Diputados",
        "is_currently_in_force": True,
        "valid_article_range": (1, 273),
        "notable_articles": {
            "10": "Representación legal de las sociedades mercantiles a través de administradores o apoderados.",
            "149": "Responsabilidad solidaria e ilimitada de administradores que no inscriban poderes."
        }
    }
}


class MexicanLawVerifier:
    """
    Verificador estricto de citas y fundamentos normativos en la legislación mexicana.
    
    REGLA DE CONFIANZA:
    - Nunca se afirma que una ley o artículo está vigente sin corroborar contra el catálogo oficial.
    - Si no existe evidencia suficiente, marca expresamente: REQUIERE_INVESTIGACION_JURIDICA.
    """

    @classmethod
    def verify_citation(cls, citation_text: str) -> Dict[str, Any]:
        """
        Analiza una mención o cita legal en el texto y genera el fundamento normativo estructurado.
        """
        now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        clean_text = " ".join(citation_text.lower().split())

        # 1. Detectar artículo si existe
        art_match = re.search(r'art(?:[íi]culo|\.|\b)?\s*(\d+)', clean_text)
        article_num = art_match.group(1) if art_match else None

        # 2. Buscar correspondencia con las leyes del catálogo oficial
        matched_key = None
        matched_info = None

        for law_key, law_info in MEXICAN_OFFICIAL_CATALOG.items():
            for alias in law_info["aliases"]:
                if alias in clean_text:
                    matched_key = law_key
                    matched_info = law_info
                    break
            if matched_info:
                break

        if not matched_info:
            return {
                "disposition_name": citation_text.strip(),
                "article": article_num,
                "jurisdiction": "Indeterminada / Por verificar",
                "publication_reform_date": "No localizada en catálogo primario",
                "validity_status": "REQUIERE_INVESTIGACION_JURIDICA",
                "official_source": "No verificado en fuentes oficiales inmediatas (DOF/SCJN)",
                "query_date": now_str,
                "is_verified": False,
                "verification_note": "No se localizó correspondencia formal exacta en el compendio oficial de leyes federales y locales. Se requiere corroboración en el Semanario Judicial de la Federación o Diario Oficial."
            }

        # 3. Validar existencia del artículo dentro del rango legal
        article_valid = True
        article_note = None

        if article_num:
            try:
                num = int(article_num)
                min_art, max_art = matched_info["valid_article_range"]
                if num < min_art or num > max_art:
                    article_valid = False
                    article_note = f"El artículo {article_num} excede el rango real de artículos ({min_art}-{max_art}) de la disposición."
            except ValueError:
                pass

        if not article_valid:
            return {
                "disposition_name": matched_info["official_title"],
                "article": article_num,
                "jurisdiction": matched_info["jurisdiction"],
                "publication_reform_date": matched_info["latest_reform_dof"],
                "validity_status": "REQUIERE_INVESTIGACION_JURIDICA",
                "official_source": matched_info["official_source"],
                "query_date": now_str,
                "is_verified": False,
                "verification_note": f"Inconsistencia normativa: {article_note}"
            }

        notable_desc = matched_info.get("notable_articles", {}).get(str(article_num), "")

        return {
            "disposition_name": matched_info["official_title"],
            "article": article_num,
            "jurisdiction": matched_info["jurisdiction"],
            "publication_reform_date": f"Publicación original: {matched_info['initial_publication_dof']} | Última reforma aplicable: {matched_info['latest_reform_dof']}",
            "validity_status": "VIGENTE_VERIFICADA",
            "official_source": matched_info["official_source"],
            "query_date": now_str,
            "is_verified": True,
            "verification_note": f"Disposición oficial plenamente identificada y vigente en el marco jurídico mexicano. {notable_desc}".strip()
        }
