from datetime import datetime
import requests

# 1. Pega tu API Key de SerpApi entre las comillas
SERPAPI_KEY = "TU_API_KEY_AQUI"

# 2. Tu Webhook de Make
MAKE_WEBHOOK_URL = "https://hook.eu1.make.com/tg93wwof55r5krw31joysyih2wv5qt0w"


def crear_oferta(
    titulo, link, empresa, ubicacion, descripcion, fecha_hoy, apply_url
):
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
            f"<div>{descripcion}</div><br><p>Oferta extraída vía Google Jobs. "
            f"Inscríbete en la fuente original: <a href='{apply_url}' target='_blank'>Ver oferta completa</a>.</p>"
        ),
        "apply_url": apply_url,
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


def obtener_ofertas_serpapi(query):
    url = "https://serpapi.com/search.json"
    params = {
        "engine": "google_jobs",
        "q": query,
        "location": "Seville, Andalusia, Spain",
        "hl": "es",
        "gl": "es",
        "api_key": SERPAPI_KEY,
    }

    fecha_hoy = datetime.now().strftime("%Y-%m-%d")
    ofertas = []

    try:
        response = requests.get(url, params=params, timeout=15)
        data = response.json()

        jobs_results = data.get("jobs_results", [])
        print(
            f"-> Búsqueda '{query}': {len(jobs_results)} ofertas encontradas."
        )

        for job in jobs_results:
            titulo = job.get("title", "Oferta de Empleo")
            empresa = job.get("company_name", "Empresa Local")
            ubicacion = job.get("location", "Sevilla, España")
            descripcion = job.get("description", "Sin descripción detallada.")

            # Buscar link de aplicación directa
            apply_options = job.get("apply_options", [])
            apply_url = (
                apply_options[0].get("link", "")
                if apply_options
                else "https://google.com"
            )
            company_link = apply_url

            ofertas.append(
                crear_oferta(
                    titulo,
                    company_link,
                    empresa,
                    ubicacion,
                    descripcion,
                    fecha_hoy,
                    apply_url,
                )
            )

    except Exception as e:
        print(f"Error consultando SerpApi: {e}")

    return ofertas


def main():
    print("=== SCRAPER GOOGLE JOBS (SERPAPI) ===")

    busquedas = ["empleo Sevilla", "trabajo Sevilla"]
    todas_ofertas = []

    for q in busquedas:
        ofertas = obtener_ofertas_serpapi(q)
        for o in ofertas:
            if not any(
                x["job_title"] == o["job_title"]
                and x["company_name"] == o["company_name"]
                for x in todas_ofertas
            ):
                todas_ofertas.append(o)

    print(f"\n>>> TOTAL OFERTAS UNICAS: {len(todas_ofertas)} <<<")

    if todas_ofertas:
        print("Enviando a Make...")
        try:
            r = requests.post(
                MAKE_WEBHOOK_URL, json={"jobs": todas_ofertas}, timeout=15
            )
            print(f"Respuesta de Make: {r.status_code}")
        except Exception as e:
            print(f"Error enviando a Make: {e}")


if __name__ == "__main__":
    main()
