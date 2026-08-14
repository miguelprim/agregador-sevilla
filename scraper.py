from datetime import datetime
import os
import requests

# ⚠️ IMPORTANTE: Pega aquí la URL de tu Webhook de Make
MAKE_WEBHOOK_URL = "https://hook.eu1.make.com/AQUI_TU_WEBHOOK_DE_MAKE"

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
]


def es_oferta_de_sevilla(texto):
  if not texto:
    return False
  texto_minusc = texto.lower()
  return any(municipio in texto_minusc for municipio in MUNICIPIOS_SEVILLA)


def buscar_empleos():
  print("Buscando empleos para Sevilla...")
  ofertas_encontradas = []
  fecha_hoy = datetime.now().strftime("%Y-%m-%d")

  try:
    url = "https://www.arbeitnow.com/api/job-board-api"
    respuesta = requests.get(url, timeout=10)

    if respuesta.status_code == 200:
      datos = respuesta.json()
      for puesto in datos.get("data", []):
        ubicacion = puesto.get("location", "")
        titulo = puesto.get("title", "")

        if es_oferta_de_sevilla(ubicacion) or es_oferta_de_sevilla(titulo):
          remote = puesto.get("remote", False)
          job_location = "remote" if remote else "onsite"

          ofertas_encontradas.append({
    "job_title": "Desarrollador Software Test Sevilla",
    "job_type": "fulltime",
    "company_name": "Iglubit Test Tech",
    "company_url": "https://iglubit.com",
    "company_logo": "",
    "job_location": "onsite",
    "office_location": "Sevilla, España",
    "location_limits": "España",
    "description": "<p>Esta es una oferta de prueba para verificar la integración con Google Sheets.</p>",
    "apply_url": "https://iglubit.com",
    "apply_email": "contacto@iglubit.com",
    "salary_min": "35000",
    "salary_maximum": "45000",
    "salary_currency": "EUR",
    "salary_schedule": "yearly",
    "highlighted": "FALSE",
    "sticky": "FALSE",
    "post_length": "30",
    "post_state": "published",
    "date_posted": fecha_hoy,
    "category_name": "Desarrollo",
})
  except Exception as e:
    print(f"Error al buscar en API: {e}")

  return ofertas_encontradas


def enviar_a_make(ofertas):
  if not ofertas:
    print("No se encontraron ofertas nuevas de Sevilla.")
    return

  payload = {"jobs": ofertas}
  respuesta = requests.post(MAKE_WEBHOOK_URL, json=payload, timeout=10)
  print(
      f"Enviadas {len(ofertas)} ofertas a Make. Respuesta: {respuesta.status_code}"
  )


if __name__ == "__main__":
  empleos = buscar_empleos()
  enviar_a_make(empleos)
