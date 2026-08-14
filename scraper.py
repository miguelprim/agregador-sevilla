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
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,application/json;q=0.8,*/*;q=0.7",
}


def crear_oferta(titulo, link, empresa, ubicacion, descripcion, fecha_hoy):
    """Estructura estandarizada limpia para Iglubit / Jobboardly."""
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
# 1. PERSONIO XML FEEDS (Empresas en España y Andalucía)
# ===========================================================================
def extraer_personio(empresas, fecha_hoy):
    ofertas = []
    print("-> Escaneando Personio XML Feeds...")
    for emp_nombre, slug in empresas:
        url = f"https://{slug}.personio.de/xml"
        try:
            res = requests.get(url, headers=HEADERS, timeout=8)
            if res.status_code == 200:
                positions = re.findall(
                    r"<position>(.*?)</position>", res.text, re.DOTALL
                )
                cont = 0
                for pos in positions:
                    titulo_m = re.search(
                        r"<name><!\[CDATA\[(.*?)\]\]></name>", pos
                    ) or re.search(r"<name>(.*?)</name>", pos)
                    id_m = re.search(r"<id>(.*?)</id>", pos)
                    office_m = re.search(
                        r"<office><!\[CDATA\[(.*?)\]\]></office>", pos
                    ) or re.search(r"<office>(.*?)</office>", pos)

                    if titulo_m and id_m:
                        titulo = titulo_m.group(1).strip()
                        job_id = id_m.group(1).strip()
                        office = (
                            office_m.group(1).strip()
                            if office_m
                            else "España"
                        )
                        link = f"https://{slug}.personio.de/job/{job_id}"
                        desc = f"Puesto corporativo publicado por {emp_nombre} a través de su canal oficial."

                        ofertas.append(
                            crear_oferta(
                                titulo,
                                link,
                                emp_nombre,
                                office,
                                desc,
                                fecha_hoy,
                            )
                        )
                        cont += 1
                print(f"   [+] {emp_nombre}: {cont} ofertas.")
        except Exception as e:
            print(f"   [!] Error en {emp_nombre}: {e}")
    return ofertas


# ===========================================================================
# 2. GREENHOUSE JSON FEEDS LIBRES
# ===========================================================================
def extraer_greenhouse(empresas, fecha_hoy):
    ofertas = []
    print("-> Escaneando Greenhouse Board Feeds...")
    for emp_nombre, board_token in empresas:
        url = f"https://boards-api.greenhouse.io/v1/boards/{board_token}/jobs"
        try:
            res = requests.get(url, headers=HEADERS, timeout=8)
            if res.status_code == 200:
                data = res.json()
                jobs = data.get("jobs", [])
                cont = 0
                for job in jobs:
                    titulo = job.get("title", "").strip()
                    link = job.get("absolute_url", "")
                    loc = job.get("location", {}).get("name", "España")

                    desc = f"Oferta corporativa oficial en {emp_nombre}."
                    ofertas.append(
                        crear_oferta(
                            titulo, link, emp_nombre, loc, desc, fecha_hoy
                        )
                    )
                    cont += 1
                print(f"   [+] {emp_nombre}: {cont} ofertas.")
        except Exception as e:
            print(f"   [!] Error en {emp_nombre}: {e}")
    return ofertas


# ===========================================================================
# 3. LEVER POSTINGS API LIBRE
# ===========================================================================
def extraer_lever(empresas, fecha_hoy):
    ofertas = []
    print("-> Escaneando Lever API Feeds...")
    for emp_nombre, slug in empresas:
        url = f"https://api.lever.co/v0/postings/{slug}?mode=json"
        try:
            res = requests.get(url, headers=HEADERS, timeout=8)
            if res.status_code == 200:
                jobs = res.json()
                for job in jobs:
                    titulo = job.get("text", "").strip()
                    link = job.get("hostedUrl", "")
                    loc = job.get("categories", {}).get(
                        "location", "España / Remoto"
                    )
                    desc = f"Vacante oficial en {emp_nombre} vía portal corporativo."

                    ofertas.append(
                        crear_oferta(
                            titulo, link, emp_nombre, loc, desc, fecha_hoy
                        )
                    )
                print(f"   [+] {emp_nombre}: {len(jobs)} ofertas.")
        except Exception as e:
            print(f"   [!] Error en {emp_nombre}: {e}")
    return ofertas


# ===========================================================================
# 4. WORKABLE WIDGET ENDPOINTS (PÚBLICOS POR EMBED)
# ===========================================================================
def extraer_workable_embed(empresas, fecha_hoy):
    ofertas = []
    print("-> Escaneando Workable Embed Feeds...")
    for emp_nombre, slug in empresas:
        url = f"https://apply.workable.com/api/v1/widget/accounts/{slug}"
        try:
            res = requests.get(url, headers=HEADERS, timeout=8)
            if res.status_code == 200:
                data = res.json()
                jobs = data.get("jobs", [])
                for job in jobs:
                    titulo = job.get("title", "").strip()
                    job_shortcode = job.get("shortcode", "")
                    link = f"https://apply.workable.com/{slug}/j/{job_shortcode}/"
                    city = job.get("city", "")
                    country = job.get("country", "")
                    loc = f"{city}, {country}".strip(", ")

                    desc = f"Oferta publicada en el portal de empleo de {emp_nombre}."
                    ofertas.append(
                        crear_oferta(
                            titulo, link, emp_nombre, loc, desc, fecha_hoy
                        )
                    )
                print(f"   [+] {emp_nombre}: {len(jobs)} ofertas.")
        except Exception as e:
            print(f"   [!] Error en {emp_nombre}: {e}")
    return ofertas


# ===========================================================================
# EJECUCIÓN PRINCIPAL
# ===========================================================================
def main():
    fecha_hoy = datetime.now().strftime("%Y-%m-%d")
    print("=== EXTRACCIÓN DIRECTA DESDE FEEDS RSS/XML PÚBLICOS ===")

    todas_ofertas = []

    # 1. Directorio Personio (Empresas con presencia en España/Andalucía)
    EMPRESAS_PERSONIO = [
        ("CoverManager", "covermanager"),
        ("Ghenova", "ghenova"),
        ("Emergya", "emergya"),
        ("Tier1", "tier1"),
        ("Scalpers", "scalpers"),
        ("Inerco", "inerco"),
        ("Galgus", "galgus"),
        ("Clikalia", "clikalia"),
        ("Tradeinn", "tradeinn"),
    ]

    # 2. Directorio Greenhouse
    EMPRESAS_GREENHOUSE = [
        ("Cabify", "cabify"),
        ("Glovo", "glovo"),
        ("Jobandtalent", "jobandtalent"),
        ("Carto", "carto"),
    ]

    # 3. Directorio Lever
    EMPRESAS_LEVER = [
        ("Z1 Digital", "z1"),
        ("Typeform", "typeform"),
        ("Flywire", "flywire"),
        ("Factorial", "factorial"),
    ]

    # 4. Directorio Workable (Vía Embed)
    EMPRESAS_WORKABLE = [
        ("RevenueCat", "revenuecat"),
        ("Holded", "holded"),
    ]

    # Ejecutamos las extracciones
    todas_ofertas.extend(extraer_personio(EMPRESAS_PERSONIO, fecha_hoy))
    todas_ofertas.extend(extraer_greenhouse(EMPRESAS_GREENHOUSE, fecha_hoy))
    todas_ofertas.extend(extraer_lever(EMPRESAS_LEVER, fecha_hoy))
    todas_ofertas.extend(extraer_workable_embed(EMPRESAS_WORKABLE, fecha_hoy))

    print(
        f"\n>>> TOTAL ABSOLUTO EXTRAÍDO SIN REGISTROS: {len(todas_ofertas)} OFERTAS <<<"
    )

    if todas_ofertas:
        # Enviar en paquetes de 50 a Make
        LOTE = 50
        print("\nEnviando datos al Webhook de Make...")
        for i in range(0, len(todas_ofertas), LOTE):
            chunk = todas_ofertas[i : i + LOTE]
            try:
                r = requests.post(
                    MAKE_WEBHOOK_URL, json={"jobs": chunk}, timeout=15
                )
                print(
                    f"   [+] Lote enviado (ofertas {i+1} a {i+len(chunk)}). Respuesta Make: {r.status_code}"
                )
            except Exception as e:
                print(f"   [!] Error enviando a Make: {e}")


if __name__ == "__main__":
    main()
