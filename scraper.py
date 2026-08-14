from datetime import datetime
import json
import re
import requests

# URL de tu Webhook en Make
MAKE_WEBHOOK_URL = "https://hook.eu1.make.com/tg93wwof55r5krw31joysyih2wv5qt0w"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json, text/html",
}


def crear_oferta(titulo, link, empresa, ubicacion, descripcion, fecha_hoy):
    """Estructura estandarizada para Iglubit / Jobboardly."""
    return {
        "job_title": titulo,
        "job_type": "fulltime",
        "company_name": empresa,
        "company_url": link,
        "company_logo": "",
        "job_location": "onsite",
        "office_location": ubicacion if ubicacion else "Sevilla, España",
        "location_limits": "España",
        "description": (
            f"<p>{descripcion}</p><p>Inscríbete directamente en el portal oficial "
            f"de <strong>{empresa}</strong>: <a href='{link}'>Ver oferta corporativa</a>.</p>"
        ),
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


# ===========================================================================
# MOTOR 1: WORKABLE PUBLIC EXPLORER
# ===========================================================================
def extraer_workable_masivo(fecha_hoy):
    ofertas = []
    print("-> Escaneando motor masivo Workable...")

    terminos_busqueda = ["Sevilla", "Andalucia", "Spain"]

    for termino in terminos_busqueda:
        url = "https://www.workable.com/api/v3/accounts/jobs"
        params = {"query": termino, "state": "published"}

        try:
            res = requests.get(url, headers=HEADERS, params=params, timeout=10)
            if res.status_code == 200:
                data = res.json()
                for job in data.get("jobs", []):
                    titulo = job.get("title", "").strip()
                    empresa = job.get("company", {}).get("name", "Empresa Final")
                    link = job.get("url", "")
                    loc = job.get("location", {})
                    city = loc.get("city", "")
                    country = loc.get("country", "")

                    ubicacion_str = f"{city}, {country}".strip(", ")

                    # Evitamos duplicados locales
                    if not any(o["apply_url"] == link for o in ofertas):
                        desc = f"Puesto corporativo publicado por {empresa} a través de su canal oficial de selección."
                        ofertas.append(
                            crear_oferta(
                                titulo, link, empresa, ubicacion_str, desc, fecha_hoy
                            )
                        )
        except Exception as e:
            print(f"   [Workable Error]: {e}")

    return ofertas


# ===========================================================================
# MOTOR 2: SMARTRECRUITERS PUBLIC SEARCH
# ===========================================================================
def extraer_smartrecruiters_masivo(fecha_hoy):
    ofertas = []
    print("-> Escaneando motor masivo SmartRecruiters...")

    url = "https://api.smartrecruiters.com/v1/companies/postings"
    params = {"country": "es", "limit": 100}

    try:
        res = requests.get(url, headers=HEADERS, params=params, timeout=10)
        if res.status_code == 200:
            data = res.json()
            for job in data.get("content", []):
                titulo = job.get("name", "").strip()
                empresa = job.get("company", {}).get("name", "Empresa Cliente")
                job_id = job.get("id", "")
                company_identifier = job.get("company", {}).get("identifier", "")

                link = f"https://jobs.smartrecruiters.com/{company_identifier}/{job_id}"
                city = job.get("location", {}).get("city", "")
                region = job.get("location", {}).get("region", "")

                ubicacion_str = f"{city}, {region}".strip(", ")

                desc = f"Oferta corporativa oficial en la plataforma de selección de {empresa}."
                ofertas.append(
                    crear_oferta(
                        titulo, link, empresa, ubicacion_str, desc, fecha_hoy
                    )
                )
    except Exception as e:
        print(f"   [SmartRecruiters Error]: {e}")

    return ofertas


# ===========================================================================
# MOTOR 3: PERSONIO BATCH (Empresas con subdominios verificados)
# ===========================================================================
def extraer_personio_batch(fecha_hoy):
    ofertas = []
    print("-> Escaneando lote de portales Personio...")

    SLUGS_PERSONIO = [
        ("CoverManager", "covermanager"),
        ("Emergya", "emergya"),
        ("Tier1", "tier1"),
        ("Galgus", "galgus"),
        ("Inerco", "inerco"),
        ("Ghenova", "ghenova"),
        ("Clikalia", "clikalia"),
        ("Scalpers", "scalpers"),
        ("Tradeinn", "tradeinn"),
        ("Jobandtalent", "jobandtalent"),
    ]

    for nombre, slug in SLUGS_PERSONIO:
        url = f"https://{slug}.personio.de/xml"
        try:
            res = requests.get(url, headers=HEADERS, timeout=6)
            if res.status_code == 200:
                positions = re.findall(
                    r"<position>(.*?)</position>", res.text, re.DOTALL
                )
                for pos in positions:
                    titulo_match = re.search(r"<name><!\[CDATA\[(.*?)\]\]></name>", pos) or re.search(r"<name>(.*?)</name>", pos)
                    id_match = re.search(r"<id>(.*?)</id>", pos)
                    office_match = re.search(r"<office>(.*?)</office>", pos)

                    if titulo_match and id_match:
                        titulo = titulo_match.group(1).strip()
                        job_id = id_match.group(1).strip()
                        office = office_match.group(1).strip() if office_match else "España"

                        link = f"https://{slug}.personio.de/job/{job_id}"
                        desc = f"Puesto corporativo oficial en la web de {nombre}."
                        ofertas.append(
                            crear_oferta(
                                titulo, link, nombre, office, desc, fecha_hoy
                            )
                        )
        except Exception:
            pass

    return ofertas


# ===========================================================================
# EJECUCIÓN PRINCIPAL Y ENVÍO A MAKE
# ===========================================================================
def main():
    fecha_hoy = datetime.now().strftime("%Y-%m-%d")
    print("=== INICIANDO EXTRACCIÓN MASIVA DE PUESTOS DIRECTOS ===")

    todas_ofertas = []

    # 1. Ejecutar Workable
    wk_jobs = extraer_workable_masivo(fecha_hoy)
    print(f"   [+] Workable aportó: {len(wk_jobs)} ofertas.")
    todas_ofertas.extend(wk_jobs)

    # 2. Ejecutar SmartRecruiters
    sr_jobs = extraer_smartrecruiters_masivo(fecha_hoy)
    print(f"   [+] SmartRecruiters aportó: {len(sr_jobs)} ofertas.")
    todas_ofertas.extend(sr_jobs)

    # 3. Ejecutar Personio Batch
    p_jobs = extraer_personio_batch(fecha_hoy)
    print(f"   [+] Personio Batch aportó: {len(p_jobs)} ofertas.")
    todas_ofertas.extend(p_jobs)

    print(f"\n>>> TOTAL ABSOLUTO OBTENIDO: {len(todas_ofertas)} TRABAJOS DE CALIDAD <<<")

    if not todas_ofertas:
        print("No se extrajeron ofertas en este pase.")
        return

    # Enviamos en lotes de 50 para no saturar el webhook
    LOTE_TAMANO = 50
    print(f"\nEnviando a Make en paquetes de {LOTE_TAMANO}...")

    for i in range(0, len(todas_ofertas), LOTE_TAMANO):
        chunk = todas_ofertas[i : i + LOTE_TAMANO]
        try:
            r = requests.post(
                MAKE_WEBHOOK_URL, json={"jobs": chunk}, timeout=20
            )
            print(f"   Lote {i // LOTE_TAMANO + 1} enviado. Respuesta Make: {r.status_code}")
        except Exception as e:
            print(f"   Error enviando lote a Make: {e}")


if __name__ == "__main__":
    main()
