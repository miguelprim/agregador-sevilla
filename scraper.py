from datetime import datetime
import xml.etree.ElementTree as ET
import requests

MAKE_WEBHOOK_URL = "https://hook.eu1.make.com/tg93wwof55r5krw31joysyih2wv5qt0w"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "application/json, application/xml, text/html",
}

# ---------------------------------------------------------------------------
# MAPA EXTENDIDO DE EMPRESAS Y ATS (Sevilla & Grandes Multinacionales)
# ---------------------------------------------------------------------------
TARGET_COMPANIES = [
    # 1. TECNOLÓGICAS, PCT LA CARTUJA Y SERVICIOS
    {"name": "CoverManager", "ats": "personio", "slug": "covermanager"},
    {"name": "Emergya", "ats": "personio", "slug": "emergya"},
    {"name": "Tier1", "ats": "personio", "slug": "tier1"},
    {"name": "Galgus", "ats": "personio", "slug": "galgus"},
    {"name": "Factorial Sevilla", "ats": "greenhouse", "slug": "factorial"},
    {"name": "Sovos", "ats": "greenhouse", "slug": "sovos"},
    {"name": "Jobandtalent", "ats": "lever", "slug": "jobandtalent"},
    
    # 2. INGENIERÍA, INDUSTRIA Y ENERGÍA (La Isla, Cartuja, Aerópolis)
    {"name": "Inerco", "ats": "personio", "slug": "inerco"},
    {"name": "Ghenova Ingeniería", "ats": "personio", "slug": "ghenova"},
    {"name": "Cox (Abengoa)", "ats": "personio", "slug": "coxabengoa"},
    {"name": "Prodiel", "ats": "personio", "slug": "prodiel"},
    {"name": "MP Ascensores", "ats": "personio", "slug": "mpascensores"},

    # 3. MULTINACIONALES Y QUÍMICAS (Brenntag, Airbus, Renault, Elecnor, Telefónica, Endesa)
    # Algunas de estas usan Workday, SmartRecruiters o Lever a nivel global con sedes en Sevilla
    {"name": "Brenntag", "ats": "greenhouse", "slug": "brenntag"},
    {"name": "Airbus Group", "ats": "lever", "slug": "airbus"},
    {"name": "Elecnor", "ats": "personio", "slug": "elecnor"},
    {"name": "Telefónica Tech", "ats": "greenhouse", "slug": "telefonica"},
    {"name": "Endesa / Enel", "ats": "greenhouse", "slug": "endesa"},
    {"name": "Renault Group", "ats": "lever", "slug": "renault"},
]


def crear_oferta(titulo, link, empresa, ubicacion, descripcion, fecha_hoy):
    """Estructura normalizada para Iglubit."""
    return {
        "job_title": titulo,
        "job_type": "fulltime",
        "company_name": empresa,
        "company_url": link,
        "company_logo": "",
        "job_location": "onsite",
        "office_location": ubicacion if ubicacion else "Sevilla, España",
        "location_limits": "España",
        "description": f"<p>{descripcion}</p><p>Inscríbete en la web oficial de <strong>{empresa}</strong>: <a href='{link}'>Ver oferta corporativa</a>.</p>",
        "apply_url": link,
        "apply_email": "",
        "salary_min": "",
        "salary_maximum": "",
        "salary_currency": "EUR",
        "salary_schedule": "yearly",
        "highlighted": "FALSE",
        "sticky": "FALSE",
        "post_length": "30",
        "post_state": "published",
        "date_posted": fecha_hoy,
        "category_name": "General",
    }


# ---------------------------------------------------------------------------
# PARSERS POR SISTEMA DE EMPLEO (ATS)
# ---------------------------------------------------------------------------

def parse_personio(company, fecha_hoy):
    ofertas = []
    url = f"https://{company['slug']}.personio.de/xml"
    try:
        res = requests.get(url, headers=HEADERS, timeout=8)
        if res.status_code == 200:
            root = ET.fromstring(res.content)
            for pos in root.findall(".//position"):
                titulo = pos.findtext("name", "").strip()
                job_id = pos.findtext("id", "").strip()
                office = pos.findtext("office", "").strip()

                # Filtro por ubicación (Sevilla / Andalucía / España)
                if any(k in office.lower() for k in ["sevilla", "spain", "españa", "andalucía", "remote"]) or not office:
                    link = f"https://{company['slug']}.personio.de/job/{job_id}"
                    desc = f"Puesto oficial publicado por {company['name']} ({office})."
                    ofertas.append(crear_oferta(titulo, link, company['name'], office, desc, fecha_hoy))
    except Exception:
        pass
    return ofertas


def parse_greenhouse(company, fecha_hoy):
    ofertas = []
    url = f"https://boards-api.greenhouse.io/v1/boards/{company['slug']}/jobs"
    try:
        res = requests.get(url, headers=HEADERS, timeout=8)
        if res.status_code == 200:
            data = res.json()
            for job in data.get("jobs", []):
                titulo = job.get("title", "").strip()
                link = job.get("absolute_url", "")
                location = job.get("location", {}).get("name", "")

                if any(k in location.lower() for k in ["sevilla", "spain", "españa", "remote"]) or not location:
                    desc = f"Vacante directa en el portal corporativo de {company['name']}."
                    ofertas.append(crear_oferta(titulo, link, company['name'], location, desc, fecha_hoy))
    except Exception:
        pass
    return ofertas


def parse_lever(company, fecha_hoy):
    ofertas = []
    url = f"https://api.lever.co/v0/postings/{company['slug']}?mode=json"
    try:
        res = requests.get(url, headers=HEADERS, timeout=8)
        if res.status_code == 200:
            jobs = res.json()
            for job in jobs:
                titulo = job.get("text", "").strip()
                link = job.get("hostedUrl", "")
                location = job.get("categories", {}).get("location", "")

                if any(k in location.lower() for k in ["sevilla", "spain", "españa", "remote"]) or not location:
                    desc = f"Oferta corporativa oficial en {company['name']}."
                    ofertas.append(crear_oferta(titulo, link, company['name'], location, desc, fecha_hoy))
    except Exception:
        pass
    return ofertas


# ---------------------------------------------------------------------------
# EJECUCIÓN PRINCIPAL
# ---------------------------------------------------------------------------

def main():
    fecha_hoy = datetime.now().strftime("%Y-%m-%d")
    print(f"Iniciando escaneo de {len(TARGET_COMPANIES)} empresas clave (Cartuja, La Isla, Aerópolis)...")

    todas_ofertas = []

    for comp in TARGET_COMPANIES:
        if comp["ats"] == "personio":
            res = parse_personio(comp, fecha_hoy)
        elif comp["ats"] == "greenhouse":
            res = parse_greenhouse(comp, fecha_hoy)
        elif comp["ats"] == "lever":
            res = parse_lever(comp, fecha_hoy)
        else:
            res = []
        
        if res:
            print(f" -> {comp['name']}: {len(res)} vacantes encontradas.")
            todas_ofertas.extend(res)

    print(f"\nTOTAL OFERTAS CORPORATIVAS DIRECTAS: {len(todas_ofertas)}")

    if not todas_ofertas:
        print("No se registraron vacantes nuevas directas en el pase de hoy.")
        return

    print("Enviando resultados a Make...")
    try:
        r = requests.post(MAKE_WEBHOOK_URL, json={"jobs": todas_ofertas}, timeout=15)
        print(f"Respuesta Make: {r.status_code}")
    except Exception as e:
        print(f"Error al enviar a Make: {e}")


if __name__ == "__main__":
    main()
