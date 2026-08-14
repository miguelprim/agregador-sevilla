from datetime import datetime
import xml.etree.ElementTree as ET
import requests

MAKE_WEBHOOK_URL = "https://hook.eu1.make.com/tg93wwof55r5krw31joysyih2wv5qt0w"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json, application/xml, text/html",
}

# ---------------------------------------------------------------------------
# MAPA AMPLIADO DE EMPRESAS Y ATS REALES CON OFERTAS EN SEVILLA / ESPAÑA
# ---------------------------------------------------------------------------
TARGET_COMPANIES = [
    # --- TECH, CONSULTORÍA Y CARTUJA (Personio / Greenhouse / Lever) ---
    {"name": "CoverManager", "ats": "personio", "slug": "covermanager"},
    {"name": "Emergya", "ats": "personio", "slug": "emergya"},
    {"name": "Galgus", "ats": "personio", "slug": "galgus"},
    {"name": "Tier1", "ats": "personio", "slug": "tier1"},
    {"name": "Factorial", "ats": "greenhouse", "slug": "factorial"},
    {"name": "Jobandtalent", "ats": "lever", "slug": "jobandtalent"},
    {"name": "Cabify", "ats": "lever", "slug": "cabify"},
    {"name": "Typeform", "ats": "lever", "slug": "typeform"},
    
    # --- RECRUITEE (APIs públicas sin bloqueos) ---
    {"name": "Heineken España", "ats": "recruitee", "slug": "heineken"},
    {"name": "Ayesa", "ats": "recruitee", "slug": "ayesa"},

    # --- SMARTRECRUITERS (Muy usado por grandes industriales) ---
    {"name": "Inerco", "ats": "smartrecruiters", "slug": "Inerco"},
    {"name": "Schneider Electric", "ats": "smartrecruiters", "slug": "SchneiderElectric"},
]


def crear_oferta(titulo, link, empresa, ubicacion, descripcion, fecha_hoy):
    """Estructura estandarizada para Iglubit."""
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
# PARSERS POR ATS (Sistemas de Empleo)
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


def parse_recruitee(company, fecha_hoy):
    ofertas = []
    url = f"https://{company['slug']}.recruitee.com/api/offers"
    try:
        res = requests.get(url, headers=HEADERS, timeout=8)
        if res.status_code == 200:
            data = res.json()
            for job in data.get("offers", []):
                titulo = job.get("title", "").strip()
                link = job.get("careers_url", "")
                location = job.get("location", "")

                if any(k in str(location).lower() for k in ["sevilla", "spain", "españa", "remote"]) or not location:
                    desc = f"Puesto publicado en el portal de empleo de {company['name']}."
                    ofertas.append(crear_oferta(titulo, link, company['name'], str(location), desc, fecha_hoy))
    except Exception:
        pass
    return ofertas


def parse_smartrecruiters(company, fecha_hoy):
    ofertas = []
    url = f"https://api.smartrecruiters.com/v1/companies/{company['slug']}/postings"
    try:
        res = requests.get(url, headers=HEADERS, timeout=8)
        if res.status_code == 200:
            data = res.json()
            for job in data.get("content", []):
                titulo = job.get("name", "").strip()
                job_id = job.get("id", "")
                link = f"https://jobs.smartrecruiters.com/{company['slug']}/{job_id}"
                city = job.get("location", {}).get("city", "")
                country = job.get("location", {}).get("country", "")

                loc_str = f"{city}, {country}".strip(", ")
                if any(k in loc_str.lower() for k in ["sevilla", "es", "spain", "españa"]) or not loc_str:
                    desc = f"Vacante corporativa oficial en {company['name']}."
                    ofertas.append(crear_oferta(titulo, link, company['name'], loc_str, desc, fecha_hoy))
    except Exception:
        pass
    return ofertas


# ---------------------------------------------------------------------------
# EJECUCIÓN PRINCIPAL
# ---------------------------------------------------------------------------

def main():
    fecha_hoy = datetime.now().strftime("%Y-%m-%d")
    print(f"Iniciando escaneo multi-ATS ({len(TARGET_COMPANIES)} empresas)...")

    todas_ofertas = []

    for comp in TARGET_COMPANIES:
        ats_type = comp["ats"]
        res = []

        if ats_type == "personio":
            res = parse_personio(comp, fecha_hoy)
        elif ats_type == "greenhouse":
            res = parse_greenhouse(comp, fecha_hoy)
        elif ats_type == "lever":
            res = parse_lever(comp, fecha_hoy)
        elif ats_type == "recruitee":
            res = parse_recruitee(comp, fecha_hoy)
        elif ats_type == "smartrecruiters":
            res = parse_smartrecruiters(comp, fecha_hoy)

        if res:
            print(f" -> {comp['name']}: {len(res)} vacantes encontradas.")
            todas_ofertas.extend(res)

    print(f"\nTOTAL OFERTAS CORPORATIVAS ENCONTRADAS: {len(todas_ofertas)}")

    if not todas_ofertas:
        print("No se obtuvieron vacantes directas en esta ejecución.")
        return

    print("Enviando resultados a Make...")
    try:
        r = requests.post(MAKE_WEBHOOK_URL, json={"jobs": todas_ofertas}, timeout=15)
        print(f"Respuesta Webhook Make: {r.status_code}")
    except Exception as e:
        print(f"Error enviando a Make: {e}")


if __name__ == "__main__":
    main()
