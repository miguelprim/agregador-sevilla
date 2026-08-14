from datetime import datetime
from urllib.parse import quote
import re
import requests

MAKE_WEBHOOK_URL = "https://hook.eu1.make.com/tg93wwof55r5krw31joysyih2wv5qt0w"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "es-ES,es;q=0.9",
}


def crear_oferta(titulo, link, empresa, ubicacion, fecha_hoy):
    return {
        "job_title": titulo,
        "job_type": "fulltime",
        "company_name": empresa if empresa else "Empresa en Sevilla",
        "company_url": link,
        "company_logo": "",
        "job_location": "onsite",
        "office_location": ubicacion if ubicacion else "Sevilla, España",
        "location_limits": "España",
        "description": f"<p>Oferta de empleo en Sevilla: <strong>{titulo}</strong> en <strong>{empresa}</strong>.</p><p>Inscríbete directamente en <a href='{link}'>LinkedIn</a>.</p>",
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


def obtener_trabajos_linkedin_sevilla(fecha_hoy):
    """Extrae ofertas reales de la provincia de Sevilla desde el endpoint público de LinkedIn."""
    ofertas = []
    # Búsqueda filtrada: Sevilla, provincia de Sevilla, España (GeoId para Sevilla/Andalucía)
    location = quote("Sevilla, Andalucía, España")
    url = f"https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search?keywords=&location={location}&start=0"

    print("Escaneando ofertas reales en Sevilla (vía LinkedIn)...")

    try:
        res = requests.get(url, headers=HEADERS, timeout=15)
        if res.status_code == 200:
            html = res.text

            # 1. Extraer enlaces directos a las ofertas
            patron_link = r'href=["\'](https://es\.linkedin\.com/jobs/view/[^"\']+)["\']'
            links = re.findall(patron_link, html)

            # 2. Extraer títulos
            patron_titulo = r'<h3 class="base-search-card__title">\s*(.*?)\s*</h3>'
            titulos = re.findall(patron_titulo, html, re.DOTALL)

            # 3. Extraer empresas
            patron_empresa = r'<h4 class="base-search-card__subtitle">\s*<a[^>]*>\s*(.*?)\s*</a>'
            empresas = re.findall(patron_empresa, html, re.DOTALL)

            # Fallback para empresas si no tienen tag <a>
            if not empresas:
                patron_empresa_alt = r'<h4 class="base-search-card__subtitle">\s*(.*?)\s*</h4>'
                empresas = re.findall(patron_empresa_alt, html, re.DOTALL)

            # 4. Extraer ubicación exacta
            patron_ubicacion = r'<span class="job-search-card__location">\s*(.*?)\s*</span>'
            ubicaciones = re.findall(patron_ubicacion, html, re.DOTALL)

            vistos = set()
            total = min(len(links), len(titulos))

            for i in range(total):
                link = links[i].split("?")[0]  # Limpiar parámetros de seguimiento del URL
                tit = re.sub(r'<[^>]+>', '', titulos[i]).strip()

                emp = "Empresa local"
                if i < len(empresas):
                    emp = re.sub(r'<[^>]+>', '', empresas[i]).strip()

                ubi = "Sevilla, España"
                if i < len(ubicaciones):
                    ubi = re.sub(r'<[^>]+>', '', ubicaciones[i]).strip()

                if link not in vistos and len(tit) > 3:
                    vistos.add(link)
                    ofertas.append(crear_oferta(tit, link, emp, ubi, fecha_hoy))

            print(f"-> Puestos locales válidos procesados: {len(ofertas)}")
        else:
            print(f"Error en la petición a LinkedIn: Estado {res.status_code}")

    except Exception as e:
        print(f"Error procesando LinkedIn: {e}")

    return ofertas


def main():
    fecha_hoy = datetime.now().strftime("%Y-%m-%d")
    print("Iniciando rastreador de ofertas locales auténticas...")

    ofertas = obtener_trabajos_linkedin_sevilla(fecha_hoy)

    print(f"\nTOTAL PUESTOS SEVILLA EXTRAÍDOS: {len(ofertas)}")

    if not ofertas:
        print("No se encontraron ofertas en esta ejecución.")
        return

    print("Enviando ofertas reales a Make...")
    try:
        res = requests.post(MAKE_WEBHOOK_URL, json={"jobs": ofertas}, timeout=15)
        print(f"Respuesta Webhook Make: {res.status_code}")
    except Exception as e:
        print(f"Error enviando a Make: {e}")


if __name__ == "__main__":
    main()
