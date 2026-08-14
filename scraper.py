from datetime import datetime
import re
import requests

# URL fija para evitar fallos de entorno en GitHub Actions
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
    "Accept-Language": "es-ES,es;q=0.9",
}


def crear_oferta(titulo, link, portal, categoria, fecha_hoy):
    """Estructura normalizada para Google Sheets y Jobboardly."""
    return {
        "job_title": titulo,
        "job_type": "fulltime",
        "company_name": f"Empresa en Sevilla ({portal})",
        "company_url": link,
        "company_logo": "",
        "job_location": "onsite",
        "office_location": "Sevilla, España",
        "location_limits": "España",
        "description": f"<p>Oferta de empleo publicada en Sevilla: <strong>{titulo}</strong>. Consulta todos los detalles e inscríbete a través de <a href='{link}'>{portal}</a>.</p>",
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


def buscar_tecnoempleo(fecha_hoy):
    ofertas = []
    try:
        res = requests.get("https://www.tecnoempleo.com/busqueda-empleo.asp?te=sevilla", headers=HEADERS, timeout=10)
        if res.status_code == 200:
            matches = re.findall(r'<a[^>]+href=["\']([^"\']*/-/[^"\']+)["\'][^>]*>(.*?)</a>', res.text, re.IGNORECASE)
            vistos = set()
            for link, titulo in matches:
                tit = re.sub(r'<[^>]+>', '', titulo).strip()
                if not link.startswith("http"):
                    link = "https://www.tecnoempleo.com/" + link.lstrip("/")
                if link not in vistos and len(tit) > 3:
                    vistos.add(link)
                    ofertas.append(crear_oferta(tit, link, "Tecnoempleo", "Tecnología / IT", fecha_hoy))
    except Exception as e:
        print(f"Error Tecnoempleo: {e}")
    return ofertas


def buscar_infojobs(fecha_hoy):
    ofertas = []
    try:
        res = requests.get("https://www.infojobs.net/ofertas-trabajo/sevilla", headers=HEADERS, timeout=10)
        if res.status_code == 200:
            matches = re.findall(r'<a[^>]+href=["\']([^"\']*infojobs\.net/of-[^"\']+)["\'][^>]*>(.*?)</a>', res.text, re.IGNORECASE)
            vistos = set()
            for link, titulo in matches:
                tit = re.sub(r'<[^>]+>', '', titulo).strip()
                if link.startswith("//"):
                    link = "https:" + link
                if link not in vistos and len(tit) > 4:
                    vistos.add(link)
                    ofertas.append(crear_oferta(tit, link, "InfoJobs", "General", fecha_hoy))
    except Exception as e:
        print(f"Error InfoJobs: {e}")
    return ofertas


def buscar_turijobs(fecha_hoy):
    ofertas = []
    try:
        res = requests.get("https://www.turijobs.com/ofertas-trabajo-sevilla", headers=HEADERS, timeout=10)
        if res.status_code == 200:
            matches = re.findall(r'<a[^>]+href=["\']([^"\']*/oferta-[^"\']+)["\'][^>]*>(.*?)</a>', res.text, re.IGNORECASE)
            vistos = set()
            for link, titulo in matches:
                tit = re.sub(r'<[^>]+>', '', titulo).strip()
                if not link.startswith("http"):
                    link = "https://www.turijobs.com" + link
                if link not in vistos and len(tit) > 3:
                    vistos.add(link)
                    ofertas.append(crear_oferta(tit, link, "Turijobs", "Turismo y Hostelería", fecha_hoy))
    except Exception as e:
        print(f"Error Turijobs: {e}")
    return ofertas


def buscar_talent_spain(fecha_hoy):
    ofertas = []
    try:
        res = requests.get("https://es.talent.com/jobs?l=Sevilla%2C+Andaluc%C3%ADa", headers=HEADERS, timeout=10)
        if res.status_code == 200:
            matches = re.findall(r'<a[^>]+href=["\']([^"\']*/view\?[^"\']+)["\'][^>]*>(.*?)</a>', res.text, re.IGNORECASE)
            vistos = set()
            for link, titulo in matches:
                tit = re.sub(r'<[^>]+>', '', titulo).strip()
                if not link.startswith("http"):
                    link = "https://es.talent.com" + link
                if link not in vistos and len(tit) > 3:
                    vistos.add(link)
                    ofertas.append(crear_oferta(tit, link, "Talent.com", "General", fecha_hoy))
    except Exception as e:
        print(f"Error Talent.com: {e}")
    return ofertas


def buscar_ticjob(fecha_hoy):
    ofertas = []
    try:
        res = requests.get("https://ticjob.es/esp/busqueda?keywords=sevilla", headers=HEADERS, timeout=10)
        if res.status_code == 200:
            matches = re.findall(r'<a[^>]+href=["\']([^"\']*/esp/trabajo/[^"\']+)["\'][^>]*>(.*?)</a>', res.text, re.IGNORECASE)
            vistos = set()
            for link, titulo in matches:
                tit = re.sub(r'<[^>]+>', '', titulo).strip()
                if not link.startswith("http"):
                    link = "https://ticjob.es" + link
                if link not in vistos and len(tit) > 3:
                    vistos.add(link)
                    ofertas.append(crear_oferta(tit, link, "Ticjob", "Tecnología / IT", fecha_hoy))
    except Exception as e:
        print(f"Error Ticjob: {e}")
    return ofertas


def buscar_monster_spain(fecha_hoy):
    ofertas = []
    try:
        res = requests.get("https://www.monster.es/trabajo/buscar?q=&where=Sevilla", headers=HEADERS, timeout=10)
        if res.status_code == 200:
            matches = re.findall(r'<a[^>]+href=["\']([^"\']*/trabajo/[^"\']+)["\'][^>]*>(.*?)</a>', res.text, re.IGNORECASE)
            vistos = set()
            for link, titulo in matches:
                tit = re.sub(r'<[^>]+>', '', titulo).strip()
                if not link.startswith("http"):
                    link = "https://www.monster.es" + link
                if link not in vistos and len(tit) > 3:
                    vistos.add(link)
                    ofertas.append(crear_oferta(tit, link, "Monster", "General", fecha_hoy))
    except Exception as e:
        print(f"Error Monster: {e}")
    return ofertas


def main():
    fecha_hoy = datetime.now().strftime("%Y-%m-%d")
    print("Iniciando rastreador masivo de empleos en España (Sevilla)...")

    ofertas = []
    fuentes = [
        ("Tecnoempleo", buscar_tecnoempleo),
        ("InfoJobs", buscar_infojobs),
        ("Turijobs", buscar_turijobs),
        ("Talent.com", buscar_talent_spain),
        ("Ticjob", buscar_ticjob),
        ("Monster", buscar_monster_spain),
    ]

    for nombre, funcion in fuentes:
        print(f"-> Escaneando {nombre}...")
        res = funcion(fecha_hoy)
        print(f"   Obtenidas: {len(res)}")
        ofertas.extend(res)

    print(f"\nTOTAL DE OFERTAS LOCALES EXTRAÍDAS: {len(ofertas)}")

    if not ofertas:
        print("No se encontraron ofertas en esta ejecución.")
        return

    print("Enviando paquete completo al Webhook de Make...")
    try:
        res = requests.post(MAKE_WEBHOOK_URL, json={"jobs": ofertas}, timeout=15)
        print(f"Estado de envío a Make: {res.status_code}")
    except Exception as e:
        print(f"Error enviando datos a Make: {e}")


if __name__ == "__main__":
    main()
