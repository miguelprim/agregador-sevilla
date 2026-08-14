from datetime import datetime
import os
import requests

# URL real de tu Webhook de Make (tomada por variable de entorno o fallback)
MAKE_WEBHOOK_URL = os.getenv(
    "MAKE_WEBHOOK_URL",
    "https://hook.eu1.make.com/tg93wwof55r5krw31joysyih2wv5qt0w",
)

# Cobertura completa de la provincia de Sevilla (Capital, Aljarafe, Vega del Guadalquivir, Campiña, Sierra, etc.)
MUNICIPIOS_SEVILLA = [
    "sevilla",
    "seville",
    "dos hermanas",
    "alcalá de guadaíra",
    "alcala de guadaira",
    "utrera",
    "mairena del aljarafe",
    "écija",
    "ecija",
    "la rinconada",
    "los palacios",
    "camas",
    "tomares",
    "bormujos",
    "aljarafe",
    "san juan de aznalfarache",
    "lebrija",
    "coria del río",
    "coria del rio",
    "morón de la frontera",
    "moron de la frontera",
    "carmona",
    "espartinas",
    "castilleja de la cuesta",
    "gines",
    "mairena del alcor",
    "el viso del alcor",
    "osuna",
    "sanlúcar la mayor",
    "sanlucar la mayor",
    "marchena",
    "lora del río",
    "lora del rio",
    "arahal",
    "provincia de sevilla",
    "sevilla, españa",
    "sevilla, spain",
]


def es_oferta_de_sevilla(*textos):
    """
    Comprueba si alguno de los textos pasados contiene mención a los municipios/zonas de Sevilla.
    """
    for texto in textos:
        if not texto:
            continue
        texto_minusc = texto.lower()
        if any(municipio in texto_minusc for municipio in MUNICIPIOS_SEVILLA):
            return True
    return False


def buscar_empleos():
    print("Iniciando rastreo de empleos para toda la provincia de Sevilla...")
    ofertas_encontradas = []
    fecha_hoy = datetime.now().strftime("%Y-%m-%d")

    # BÚSQUEDA EN API (Recorremos hasta 3 páginas para abarcar más ofertas globales)
    base_url = "https://www.arbeitnow.com/api/job-board-api"
    
    for page in range(1, 4):
        try:
            url = f"{base_url}?page={page}"
            respuesta = requests.get(url, timeout=10)

            if respuesta.status_code == 200:
                datos = respuesta.json()
                puestos = datos.get("data", [])
                
                if not puestos:
                    break

                for puesto in puestos:
                    ubicacion = puesto.get("location", "")
                    titulo = puesto.get("title", "")
                    descripcion = puesto.get("description", "")

                    # Evaluamos ubicación, título y descripción por si mencionan la zona
                    if es_oferta_de_sevilla(ubicacion, titulo, descripcion):
                        remote = puesto.get("remote", False)
                        job_location = "remote" if remote else "onsite"

                        ofertas_encontradas.append({
                            "job_title": puesto.get("title", ""),
                            "job_type": "fulltime",
                            "company_name": puesto.get("company_name", ""),
                            "company_url": puesto.get("url", ""),
                            "company_logo": "",
                            "job_location": job_location,
                            "office_location": ubicacion if ubicacion else "Sevilla, España",
                            "location_limits": "España",
                            "description": puesto.get("description", ""),
                            "apply_url": puesto.get("url", ""),
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
                        })
        except Exception as e:
            print(f"Error al consultar la página {page} de la API: {e}")

    return ofertas_encontradas


def enviar_a_make(ofertas):
    if not ofertas:
        print("No se encontraron ofertas reales nuevas para la provincia de Sevilla en este pase.")
        return

    payload = {"jobs": ofertas}
    respuesta = requests.post(MAKE_WEBHOOK_URL, json=payload, timeout=10)
    print(
        f"Enviadas {len(ofertas)} ofertas reales a Make. Respuesta servidor: {respuesta.status_code}"
    )


if __name__ == "__main__":
    empleos = buscar_empleos()
    enviar_a_make(empleos)
