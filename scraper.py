from datetime import datetime
import xml.etree.ElementTree as ET
import re
import requests

# URL de tu Webhook de Make
MAKE_WEBHOOK_URL = "https://hook.eu1.make.com/tg93wwof55r5krw31joysyih2wv5qt0w"

MUNICIPIOS_SEVILLA = [
    "sevilla", "seville", "dos hermanas", "alcalá de guadaíra", "alcala de guadaira",
    "utrera", "mairena del aljarafe", "écija", "ecija", "la rinconada", "los palacios",
    "camas", "tomares", "bormujos", "aljarafe", "san juan de aznalfarache", "lebrija",
    "coria del río", "coria del rio", "morón de la frontera", "carmona", "espartinas",
    "castilleja de la cuesta", "gines", "mairena del alcor", "el viso del alcor",
    "osuna", "sanlúcar la mayor", "marchena", "lora del río", "arahal"
]

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "application/rss+xml, application/xml, text/xml, */*",
}


def crear_oferta(titulo, link, portal, categoria, fecha_hoy):
    return {
        "job_title": titulo,
        "job_type": "fulltime",
        "company_name": f"Empresa local ({portal})",
        "company_url": link,
        "company_logo": "",
        "job_location": "onsite",
        "office_location": "Sevilla, España",
        "location_limits": "España",
        "description": f"<p>Oferta publicada en Sevilla: <strong>{titulo}</strong>. Inscríbete en <a href='{link}'>{portal}</a>.</p>",
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
        "category_name": categoria,
    }


def buscar_tecnoempleo_rss(fecha_hoy):
    """Extrae ofertas usando el feed RSS oficial de Tecnoempleo."""
    ofertas = []
    url = "https://www.tecnoempleo.com/feeds/rss-empleo-sevilla.xml"
    print("Obteniendo RSS Tecnoempleo Sevilla...")
    try:
        res = requests.get(url, headers=HEADERS, timeout=12)
        if res.status_code == 200:
            root = ET.fromstring(res.content)
            vistos = set()
            for item in root.findall(".//item"):
                title_elem = item.find("title")
                link_elem = item.find("link")
                if title_elem is not None and link_elem is not None:
                    tit = title_elem.text.strip() if title_elem.text else ""
                    link = link_elem.text.strip() if link_elem.text else ""
                    if link not in vistos and len(tit) > 3:
                        vistos.add(link)
                        ofertas.append(crear_oferta(tit, link, "Tecnoempleo", "Tecnología / IT", fecha_hoy))
    except Exception as e:
        print(f"Error en RSS Tecnoempleo: {e}")
    return ofertas


def buscar_jooble_sevilla(fecha_hoy):
    """Consulta ofertas de Sevilla a través de agregador abierto."""
    ofertas = []
    url = "https://es.jooble.org/api/feed/sevilla"
    print("Obteniendo Feed Jooble Sevilla...")
    try:
        res = requests.get(url, headers=HEADERS, timeout=12)
        if res.status_code == 200:
            html = res.text
            matches = re.findall(r'<a[^>]+href=["\']([^"\']*)["\'][^>]*>(.*?)</a>', html, re.IGNORECASE)
            vistos = set()
            for link, titulo in matches:
                tit = re.sub(r'<[^>]+>', '', titulo).strip()
                if "job" in link.lower() and link not in vistos and len(tit) > 5:
                    vistos.add(link)
                    ofertas.append(crear_oferta(tit, link, "Jooble España", "General", fecha_hoy))
    except Exception as e:
        print(f"Error en Jooble Sevilla: {e}")
    return ofertas


def main():
    fecha_hoy = datetime.now().strftime("%Y-%m-%d")
    print("Iniciando rastreador inmune a bloqueos (Sevilla)...")

    ofertas = []
    
    # 1. Tecnoempleo RSS
    tecno_jobs = buscar_tecnoempleo_rss(fecha_hoy)
    print(f"-> Tecnoempleo RSS: {len(tecno_jobs)} ofertas")
    ofertas.extend(tecno_jobs)

    # 2. Jooble Sevilla
    jooble_jobs = buscar_jooble_sevilla(fecha_hoy)
    print(f"-> Jooble Sevilla: {len(jooble_jobs)} ofertas")
    ofertas.extend(jooble_jobs)

    print(f"\nTOTAL OFERTAS EXTRAÍDAS: {len(ofertas)}")

    if not ofertas:
        print("No se encontraron ofertas en esta ronda.")
        return

    print("Enviando ofertas a Make...")
    try:
        res = requests.post(MAKE_WEBHOOK_URL, json={"jobs": ofertas}, timeout=15)
        print(f"Respuesta Webhook Make: {res.status_code}")
    except Exception as e:
        print(f"Error enviando a Make: {e}")


if __name__ == "__main__":
    main()
