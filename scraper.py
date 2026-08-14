from datetime import datetime
import os
import re
import requests

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
        "Chrome/122.0.0.0 Safari/537.36"
    )
}


def es_de_sevilla(texto):
    if not texto:
        return False
    texto_l = texto.lower()
    return any(m in texto_l for m in MUNICIPIOS_SEVILLA)


def buscar_tecnoempleo(fecha_hoy):
    ofertas = []
    url = "https://www.tecnoempleo.com/busqueda-empleo.asp?te=sevilla"
    
    try:
        res = requests.get(url, headers=HEADERS, timeout=15)
        if res.status_code == 200:
            html = res.text
            # Regex nativo para extraer títulos y links de ofertas
            patron = r'<a[^>]+href=["\']([^"\']*/-/[^"\']+)["\'][^>]*>(.*?)</a>'
            coincidencias = re.findall(patron, html, re.IGNORECASE)

            vistos = set()
            for link, titulo in coincidencias:
                titulo_limpio = re.sub(r'<[^>]+>', '', titulo).strip()
                if not link.startswith("http"):
                    link = "https://www.tecnoempleo.com/" + link.lstrip("/")

                if link in vistos or not titulo_limpio or len(titulo_limpio) < 3:
                    continue
                vistos.add(link)

                ofertas.append({
                    "job_title": titulo_limpio,
                    "job_type": "fulltime",
                    "company_name": "Empresa en Sevilla",
                    "company_url": link,
                    "company_logo": "",
                    "job_location": "onsite",
                    "office_location": "Sevilla, España",
                    "location_limits": "España",
                    "description": f"<p>Puesto de trabajo: {titulo_limpio} en Sevilla. Más información en <a href='{link}'>Tecnoempleo</a>.</p>",
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
                    "category_name": "Tecnología / Informática",
                })
    except Exception as e:
        print(f"Error procesando Tecnoempleo: {e}")

    return ofertas


def buscar_jobicy_remoto(fecha_hoy):
    ofertas = []
    url = "https://jobicy.com/api/v2/remote-jobs?geo=spain"

    try:
        res = requests.get(url, headers=HEADERS, timeout=15)
        if res.status_code == 200:
            datos = res.json().get("jobs", [])
            for j in datos:
                loc = j.get("jobGeo", "")
                tit = j.get("jobTitle", "")
                desc = j.get("jobExcerpt", "")

                if "spain" in loc.lower() or "españa" in loc.lower() or es_de_sevilla(f"{loc} {tit} {desc}"):
                    ofertas.append({
                        "job_title": tit,
                        "job_type": "fulltime",
                        "company_name": j.get("companyName", "Empresa Remota"),
                        "company_url": j.get("url", ""),
                        "company_logo": j.get("companyLogo", ""),
                        "job_location": "remote",
                        "office_location": "Sevilla / Remoto España",
                        "location_limits": "España",
                        "description": desc if desc else f"<p>Puesto remoto en España: {tit}</p>",
                        "apply_url": j.get("url", ""),
                        "apply_email": "",
                        "salary_min": j.get("annualSalaryMin", ""),
                        "salary_maximum": j.get("annualSalaryMax", ""),
                        "salary_currency": "EUR",
                        "salary_schedule": "yearly",
                        "highlighted": "FALSE",
                        "sticky": "FALSE",
                        "post_length": "30",
                        "post_state": "published",
                        "date_posted": fecha_hoy,
                        "category_name": j.get("jobCategory", "General"),
                    })
    except Exception as e:
        print(f"Error procesando Jobicy: {e}")

    return ofertas


def main():
    fecha_hoy = datetime.now().strftime("%Y-%m-%d")
    print("Iniciando escaneo de empleos Sevilla/España...")

    ofertas = []
    ofertas.extend(buscar_tecnoempleo(fecha_hoy))
    ofertas.extend(buscar_jobicy_remoto(fecha_hoy))

    if not ofertas:
        print("No se han obtenido ofertas en esta ronda.")
        return

    print(f"Ofertas recopiladas: {len(ofertas)}. Enviando a Make...")
    res = requests.post(MAKE_WEBHOOK_URL, json={"jobs": ofertas}, timeout=15)
    print(f"Petición enviada. Respuesta HTTP: {res.status_code}")


if __name__ == "__main__":
    main()
