from datetime import datetime
import re
import requests

# 1. Tu API Key de SerpApi
SERPAPI_KEY = "a9dfc8ee2c49e1ac9efc61efdaea296636830367fb362b80650411c188a0229e"

# 2. Tu Webhook de Make
MAKE_WEBHOOK_URL = "https://hook.eu1.make.com/tg93wwof55r5krw31joysyih2wv5qt0w"


def formatear_descripcion_html(texto_raw):
    """Limpia el texto plano de la descripción y lo convierte en HTML con párrafos y listas limpias."""
    if not texto_raw:
        return "<p>Sin descripción detallada.</p>"

    # 1. Normalizar líneas y eliminar espacios vacíos repetidos
    lineas = [linea.strip() for linea in texto_raw.splitlines()]

    lineas_limpias = []
    anterior_vacio = False
    for l in lineas:
        if not l:
            if not anterior_vacio:
                lineas_limpias.append("")
                anterior_vacio = True
        else:
            lineas_limpias.append(l)
            anterior_vacio = False

    # 2. Formatear viñetas (•, -, *) y párrafos estándar
    en_lista = False
    html_bloques = []

    for l in lineas_limpias:
        if re.match(r"^[\•\-\*\▪\◦\–]\s*", l):
            l_sin_vineta = re.sub(r"^[\•\-\*\▪\◦\–]\s*", "", l)
            if not en_lista:
                html_bloques.append("<ul>")
                en_lista = True
            html_bloques.append(f"<li>{l_sin_vineta}</li>")
        else:
            if en_lista:
                html_bloques.append("</ul>")
                en_lista = False

            if l != "":
                html_bloques.append(f"<p>{l}</p>")

    if en_lista:
        html_bloques.append("</ul>")

    return "".join(html_bloques)


def crear_oferta(
    titulo, link, empresa, ubicacion, descripcion_raw, fecha_hoy, apply_url
):
    # Formatear la descripción
    descripcion_formateada = formatear_descripcion_html(descripcion_raw)

    descripcion_final = (
        f"{descripcion_formateada}"
        f"<br><hr><p><strong>¿Te interesa esta vacante?</strong> "
        f"Inscríbete directamente en la fuente original: "
        f"<a href='{apply_url}' target='_blank' rel='noopener'>Ver oferta completa y aplicar</a>.</p>"
    )

    return {
        "job_title": titulo,
        "job_type": "fulltime",
        "company_name": empresa,
        "company_url": link,
        "company_logo": "",
        "job_location": "onsite",
        "office_location": ubicacion if ubicacion else "Sevilla, España",
        "location_limits": "España",
        "description": descripcion_final,
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
            descripcion_raw = job.get(
                "description", "Sin descripción detallada."
            )

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
                    descripcion_raw,
                    fecha_hoy,
                    apply_url,
                )
            )

    except Exception as e:
        print(f"Error consultando SerpApi: {e}")

    return ofertas


def main():
    print("=== SCRAPER GOOGLE JOBS (SERPAPI + FORMATO HTML) ===")

    # Búsquedas generales
    busquedas = [
        "empleo Sevilla",
        "trabajo Sevilla",
        "ofertas de trabajo Sevilla",
    ]
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

    print(f"\n>>> TOTAL OFERTAS UNICAS ENCONTRADAS: {len(todas_ofertas)} <<<")

    if todas_ofertas:
        print(f"Enviando {len(todas_ofertas)} ofertas a Make...")
        try:
            r = requests.post(
                MAKE_WEBHOOK_URL, json={"jobs": todas_ofertas}, timeout=15
            )
            print(f"Respuesta de Make: {r.status_code}")
        except Exception as e:
            print(f"Error enviando a Make: {e}")
    else:
        print("No se encontraron ofertas para enviar.")


if __name__ == "__main__":
    main()
