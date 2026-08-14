from datetime import datetime
import re
import requests

MAKE_WEBHOOK_URL = "https://hook.eu1.make.com/tg93wwof55r5krw31joysyih2wv5qt0w"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "application/json, text/javascript, */*; q=0.01",
}


def crear_oferta(titulo, link, portal, categoria, fecha_hoy):
    return {
        "job_title": titulo,
        "job_type": "fulltime",
        "company_name": f"Empresa España ({portal})",
        "company_url": link,
        "company_logo": "",
        "job_location": "onsite",
        "office_location": "Sevilla, España",
        "location_limits": "España",
        "description": f"<p>Oferta publicada en España/Sevilla: <strong>{titulo}</strong>. Inscríbete a través de <a href='{link}'>{portal}</a>.</p>",
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


def buscar_remotive_spain(fecha_hoy):
    """Consulta la API pública de Remotive filtrada estrictamente por España."""
    ofertas = []
    url = "https://remotive.com/api/remote-jobs?search=spain"
    print("Consultando API Remotive (Filtro España)...")
    try:
        res = requests.get(url, headers=HEADERS, timeout=12)
        if res.status_code == 200:
            datos = res.json()
            jobs = datos.get("jobs", [])
            for job in jobs[:15]:
                titulo = job.get("title", "").strip()
                url_job = job.get("url", "")
                cat = job.get("category", "Tecnología / IT")
                if titulo and url_job:
                    ofertas.append(crear_oferta(titulo, url_job, "Remotive España", cat, fecha_hoy))
    except Exception as e:
        print(f"Error en Remotive: {e}")
    return ofertas


def main():
    fecha_hoy = datetime.now().strftime("%Y-%m-%d")
    print("Iniciando recopilación de datos directa por API...")

    ofertas = []
    
    # 1. Remotive API España
    remotive_jobs = buscar_remotive_spain(fecha_hoy)
    print(f"-> Ofertas recopiladas de Remotive España: {len(remotive_jobs)}")
    ofertas.extend(remotive_jobs)

    print(f"\nTOTAL FINAL: {len(ofertas)} ofertas")

    if not ofertas:
        print("Atención: No se han obtenido datos de la API.")
        return

    print("Enviando resultados al Webhook de Make...")
    try:
        res = requests.post(MAKE_WEBHOOK_URL, json={"jobs": ofertas}, timeout=15)
        print(f"Respuesta Webhook Make: {res.status_code}")
    except Exception as e:
        print(f"Error en la petición HTTP a Make: {e}")


if __name__ == "__main__":
    main()
