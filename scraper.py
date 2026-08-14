from datetime import datetime
import os
import xml.etree.ElementTree as ET
import requests

MAKE_WEBHOOK_URL = os.getenv(
    "MAKE_WEBHOOK_URL",
    "https://hook.eu1.make.com/tg93wwof55r5krw31joysyih2wv5qt0w",
)

# Ciudades y municipios de la Provincia de Sevilla
MUNICIPIOS_SEVILLA = [
    "sevilla",
    "seville",
    "dos hermanas",
    "alcalá de guadaíra",
    "alcala de guadaira",
    "utrera",
    "mairena del aljarafe",
    "écija",
    "ecija",
    "la rinconada",
    "los palacios",
    "camas",
    "tomares",
    "bormujos",
    "aljarafe",
    "san juan de aznalfarache",
    "lebrija",
    "coria del río",
    "coria del rio",
    "morón de la frontera",
    "moron de la frontera",
    "carmona",
    "espartinas",
    "castilleja de la cuesta",
    "gines",
    "mairena del alcor",
    "el viso del alcor",
    "osuna",
    "sanlúcar la mayor",
    "sanlucar la mayor",
    "marchena",
    "lora del río",
    "lora del rio",
    "arahal",
]


def es_de_sevilla(ubicacion, titulo):
    """Verifica estrictamente si la oferta pertenece a la provincia de Sevilla."""
    texto = f"{ubicacion} {titulo}".lower()
    return any(m in texto for m in MUNICIPIOS_SEVILLA)


def buscar_jooble(fecha_hoy):
    """
    Busca ofertas en Jooble España filtrando directamente por 'Sevilla'.
    (Si tienes API Key de Jooble la puedes pasar por JOOBLE_API_KEY)
    """
    api_key = os.getenv("JOOBLE_API_KEY", "")
    if not api_key:
        return []

    ofertas = []
    try:
        url = f"https://es.jooble.org/api/{api_key}"
        body = {"location": "Sevilla", "keywords": ""}
        headers = {"Content-Type": "application/json"}

        res = requests.post(url, json=body, headers=headers, timeout=10)
        if res.status_code == 200:
            data = res.json()
            for j in data.get("jobs", []):
                tit = j.get("title", "")
                loc = j.get("location", "")

                if es_de_sevilla(loc, tit):
                    ofertas.append(
                        {
                            "job_title": tit,
                            "job_type": "fulltime",
                            "company_name": j.get("company", "Empresa en Sevilla"),
                            "company_url": j.get("link", ""),
                            "company_logo": "",
                            "job_location": "onsite",
                            "office_location": loc if loc else "Sevilla, España",
                            "location_limits": "España",
                            "description": j.get("snippet", ""),
                            "apply_url": j.get("link", ""),
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
                    )
    except Exception as e:
        print(f"Error consultando Jooble: {e}")

    return ofertas


def buscar_feeds_rss_espana(fecha_hoy):
    """
    Rastrea feeds públicos de ofertas de trabajo en España filtrando por Sevilla.
    """
    ofertas = []
    # Lista de feeds RSS de empleo en España
    rss_urls = [
        "https://www.tecnempleo.com/busqueda-empleo.asp?te=sevilla&format=rss",
    ]

    headers = {"User-Agent": "Mozilla/5.0"}

    for feed_url in rss_urls:
        try:
            res = requests.get(feed_url, headers=headers, timeout=10)
            if res.status_code == 200:
                root = ET.fromstring(res.content)
                for item in root.findall(".//item"):
                    tit = item.findtext("title", "")
                    link = item.findtext("link", "")
                    desc = item.findtext("description", "")

                    if es_de_sevilla(tit, desc):
                        ofertas.append(
                            {
                                "job_title": tit,
                                "job_type": "fulltime",
                                "company_name": "Portal Empleo España",
                                "company_url": link,
                                "company_logo": "",
                                "job_location": "onsite",
                                "office_location": "Sevilla, España",
                                "location_limits": "España",
                                "description": desc,
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
                                "category_name": "Empleo",
                            }
                        )
        except Exception as e:
            print(f"Error leyendo feed RSS ({feed_url}): {e}")

    return ofertas


def buscar_empleos():
    fecha_hoy = datetime.now().strftime("%Y-%m-%d")
    print("Iniciando rastreo EXCLUSIVO para la provincia de Sevilla...")

    todas = []
    todas.extend(buscar_jooble(fecha_hoy))
    todas.extend(buscar_feeds_rss_espana(fecha_hoy))

    print(f"Total de ofertas reales encontradas en Sevilla: {len(todas)}")
    return todas


def enviar_a_make(ofertas):
    if not ofertas:
        print("No se han encontrado ofertas nuevas en la provincia de Sevilla hoy.")
        return

    payload = {"jobs": ofertas}
    respuesta = requests.post(MAKE_WEBHOOK_URL, json=payload, timeout=10)
    print(f"Enviadas {len(ofertas)} ofertas a Make. Status: {respuesta.status_code}")


if __name__ == "__main__":
    empleos = buscar_empleos()
    enviar_a_make(empleos)
