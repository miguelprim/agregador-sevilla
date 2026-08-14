from datetime import datetime
import os
import re
from bs4 import BeautifulSoup
import requests

# URL de tu Webhook de Make
MAKE_WEBHOOK_URL = os.getenv(
    "MAKE_WEBHOOK_URL",
    "https://hook.eu1.make.com/tg93wwof55r5krw31joysyih2wv5qt0w",
)

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
    ),
    "Accept-Language": "es-ES,es;q=0.9,en;q=0.8",
}


def es_de_sevilla(texto):
    """Comprueba si un texto menciona a Sevilla o a sus municipios."""
    if not texto:
        return False
    texto_l = texto.lower()
    return any(m in texto_l for m in MUNICIPIOS_SEVILLA)


def obtener_tecnoempleo_sevilla(fecha_hoy):
    """Scrapea directamente las ofertas en la provincia de Sevilla desde Tecnoempleo."""
    ofertas = []
    url = "https://www.tecnoempleo.com/busqueda-empleo.asp?te=sevilla"
    
    try:
        res = requests.get(url, headers=HEADERS, timeout=15)
        if res.status_code == 200:
            soup = BeautifulSoup(res.text, "html.parser")
            
            # Buscamos los enlaces a las ofertas en el listado
            enlaces = soup.find_all("a", href=re.compile(r"/-/[a-z0-9-]+/rf-"))
            
            vistos = set()
            for a in enlaces:
                titulo = a.text.strip()
                link = a["href"]
                if not link.startswith("http"):
                    link = "https://www.tecnoempleo.com/" + link.lstrip("/")
                
                if link in vistos or not titulo:
                    continue
                vistos.add(link)

                # Extraer empresa si está cerca en el DOM
                parent = a.find_parent(["div", "tr", "td"])
                empresa = "Empresa en Sevilla"
                if parent:
                    emp_elem = parent.find(class_=re.compile(r"text-muted|small|empresa"))
                    if emp_elem:
                        empresa = emp_elem.text.strip()

                ofertas.append({
                    "job_title": titulo,
                    "job_type": "fulltime",
                    "company_name": empresa,
                    "company_url": link,
                    "company_logo": "",
                    "job_location": "onsite",
                    "office_location": "Sevilla, España",
                    "location_limits": "España",
                    "description": f"<p>Oferta: {titulo} en Sevilla. Ver en <a href='{link}'>Tecnoempleo</a>.</p>",
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
        print(f"Error scraping Tecnoempleo: {e}")
        
    return ofertas


def obtener_jobicy_remoto_espana(fecha_hoy):
    """Consulta la API de Jobicy filtrando ofertas remotas para España / Sevilla."""
    ofertas = []
    url = "https://jobicy.com/api/v2/remote-jobs?geo=spain"
    
    try:
        res = requests.get(url, headers=HEADERS, timeout=15)
        if res.status_code == 200:
            data = res.json().get("jobs", [])
            for j in data:
                loc = j.get("jobGeo", "")
                tit = j.get("jobTitle", "")
                desc = j.get("jobExcerpt", "")
                
                # Acepta si es para España o menciona Sevilla
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
        print(f"Error en API Jobicy: {e}")
        
    return ofertas


def main():
    fecha_hoy = datetime.now().strftime("%Y-%m-%d")
    print("Iniciando rastreador consolidado para Sevilla y España...")

    ofertas = []
    
    # 1. Scraping directo de Sevilla
    tecno_jobs = obtener_tecnoempleo_sevilla(fecha_hoy)
    print(f"-> Encontradas en Tecnoempleo (Sevilla): {len(tecno_jobs)}")
    ofertas.extend(tecno_jobs)

    # 2. Puestos remotos en España
    remote_jobs = obtener_jobicy_remoto_espana(fecha_hoy)
    print(f"-> Encontradas en Jobicy (Remoto España): {len(remote_jobs)}")
    ofertas.extend(remote_jobs)

    if not ofertas:
        print("No se encontraron ofertas en esta ejecución.")
        return

    print(f"Total de ofertas listas para enviar a Make: {len(ofertas)}")
    
    # Envío a Make
    payload = {"jobs": ofertas}
    res = requests.post(MAKE_WEBHOOK_URL, json=payload, timeout=15)
    print(f"Resultado envío a Webhook Make: {res.status_code}")


if __name__ == "__main__":
    main()
