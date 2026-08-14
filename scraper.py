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
    )
}


def crear_oferta(titulo, link, descripcion, fecha_hoy):
    return {
        "job_title": titulo,
        "job_type": "fulltime",
        "company_name": "Empresa local (Sevilla)",
        "company_url": link,
        "company_logo": "",
        "job_location": "onsite",
        "office_location": "Sevilla, España",
        "location_limits": "España",
        "description": f"<p>{descripcion}</p><p>Ver oferta completa e inscribirse en <a href='{link}'>Portal de Empleo</a>.</p>",
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


def buscar_jobrapido_sevilla(fecha_hoy):
    ofertas = []
    # Feed RSS oficial de búsqueda en Sevilla (España)
    url = "https://es.jobrapido.com/rss?w=sevilla"
    print("Escaneando ofertas en Sevilla...")

    try:
        res = requests.get(url, headers=HEADERS, timeout=15)
        if res.status_code == 200:
            root = ET.fromstring(res.content)
            vistos = set()

            for item in root.findall(".//item"):
                tit_elem = item.find("title")
                link_elem = item.find("link")
                desc_elem = item.find("description")

                tit = tit_elem.text.strip() if tit_elem is not None and tit_elem.text else ""
                link = link_elem.text.strip() if link_elem is not None and link_elem.text else ""
                desc = desc_elem.text.strip() if desc_elem is not None and desc_elem.text else "Puesto vacante en Sevilla."

                # Limpiar etiquetas HTML de la descripción
                desc_limpia = re.sub(r'<[^>]+>', '', desc)

                if link and link not in vistos and len(tit) > 3:
                    vistos.add(link)
                    ofertas.append(crear_oferta(tit, link, desc_limpia, fecha_hoy))
        else:
            print(f"Error accediendo a la fuente: {res.status_code}")
    except Exception as e:
        print(f"Error en la consulta: {e}")

    return ofertas


def main():
    fecha_hoy = datetime.now().strftime("%Y-%m-%d")
    print("Iniciando rastreo local directo para Sevilla...")

    ofertas = buscar_jobrapido_sevilla(fecha_hoy)
    print(f"Total ofertas locales obtenidas: {len(ofertas)}")

    if not ofertas:
        print("No se encontraron ofertas en esta ejecución.")
        return

    print("Enviando ofertas a Make...")
    try:
        res = requests.post(MAKE_WEBHOOK_URL, json={"jobs": ofertas}, timeout=15)
        print(f"Respuesta Webhook Make: {res.status_code}")
    except Exception as e:
        print(f"Error al enviar a Make: {e}")


if __name__ == "__main__":
    main()
