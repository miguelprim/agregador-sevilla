from datetime import datetime
import xml.etree.ElementTree as ET
import re
import requests

MAKE_WEBHOOK_URL = "https://hook.eu1.make.com/tg93wwof55r5krw31joysyih2wv5qt0w"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "es-ES,es;q=0.9",
}


def crear_oferta(titulo, link, fuente, descripcion, fecha_hoy):
    return {
        "job_title": titulo,
        "job_type": "fulltime",
        "company_name": f"Empresa / Entidad Local ({fuente})",
        "company_url": link,
        "company_logo": "",
        "job_location": "onsite",
        "office_location": "Sevilla, España",
        "location_limits": "España",
        "description": f"<p>{descripcion}</p><p>Consulta la convocatoria u oferta oficial en <a href='{link}'>{fuente}</a>.</p>",
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


def buscar_sepe_empleate_sevilla(fecha_hoy):
    """Extrae ofertas del Portal Público Empléate (SEPE / España) para Sevilla."""
    ofertas = []
    url = "https://www.empleate.gob.es/empleo/buscarOfertas.do?provincia=41" # 41 es el código de Sevilla
    print("Consultando Empléate (SEPE - Sevilla)...")
    try:
        res = requests.get(url, headers=HEADERS, timeout=15)
        if res.status_code == 200:
            html = res.text
            # Extraer enlaces a detalles de oferta
            matches = re.findall(r'<a[^>]+href=["\']([^"\']*detalleOferta[^"\']+)["\'][^>]*>(.*?)</a>', html, re.IGNORECASE)
            vistos = set()
            for link, titulo in matches:
                tit = re.sub(r'<[^>]+>', '', titulo).strip()
                if not link.startswith("http"):
                    link = "https://www.empleate.gob.es/empleo/" + link.lstrip("/")
                if link not in vistos and len(tit) > 5:
                    vistos.add(link)
                    ofertas.append(crear_oferta(tit, link, "Empléate (SEPE)", "Oferta de empleo oficial en Sevilla.", fecha_hoy))
    except Exception as e:
        print(f"Error en Empléate SEPE: {e}")
    return ofertas


def buscar_sae_junta_andalucia(fecha_hoy):
    """Extrae vacantes públicas del Servicio Andaluz de Empleo (SAE)."""
    ofertas = []
    url = "https://juntadeandalucia.es/organismos/empleoempresaytrabajoautonomo/sae.html"
    print("Consultando Servicio Andaluz de Empleo (SAE)...")
    try:
        res = requests.get(url, headers=HEADERS, timeout=15)
        if res.status_code == 200:
            matches = re.findall(r'<a[^>]+href=["\']([^"\']*oferta[^"\']+)["\'][^>]*>(.*?)</a>', res.text, re.IGNORECASE)
            vistos = set()
            for link, titulo in matches:
                tit = re.sub(r'<[^>]+>', '', titulo).strip()
                if not link.startswith("http"):
                    link = "https://juntadeandalucia.es" + link
                if link not in vistos and len(tit) > 5:
                    vistos.add(link)
                    ofertas.append(crear_oferta(tit, link, "SAE Junta de Andalucía", "Vacante registrada en la Junta de Andalucía.", fecha_hoy))
    except Exception as e:
        print(f"Error en SAE: {e}")
    return ofertas


def main():
    fecha_hoy = datetime.now().strftime("%Y-%m-%d")
    print("Iniciando rastreo en portales oficiales de empleo (Sevilla / España)...")

    ofertas = []
    
    # 1. Empléate (Gobierno de España - Sevilla)
    sepe_jobs = buscar_sepe_empleate_sevilla(fecha_hoy)
    print(f"-> Empléate SEPE: {len(sepe_jobs)} ofertas")
    ofertas.extend(sepe_jobs)

    # 2. SAE Junta de Andalucía
    sae_jobs = buscar_sae_junta_andalucia(fecha_hoy)
    print(f"-> SAE Junta de Andalucía: {len(sae_jobs)} ofertas")
    ofertas.extend(sae_jobs)

    print(f"\nTOTAL OFERTAS OFICIALES OBTENIDAS: {len(ofertas)}")

    if not ofertas:
        print("No se pudieron extraer ofertas oficiales en este pase.")
        return

    print("Enviando ofertas locales a Make...")
    try:
        res = requests.post(MAKE_WEBHOOK_URL, json={"jobs": ofertas}, timeout=15)
        print(f"Respuesta Webhook Make: {res.status_code}")
    except Exception as e:
        print(f"Error enviando a Make: {e}")


if __name__ == "__main__":
    main()
