from datetime import datetime
import re
import requests

MAKE_WEBHOOK_URL = "https://hook.eu1.make.com/tg93wwof55r5krw31joysyih2wv5qt0w"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/json,*/*",
}


def crear_oferta(titulo, link, empresa, ubicacion, descripcion, fecha_hoy):
    """Estructura exacta para Iglubit / Make / Google Sheets."""
    return {
        "job_title": titulo,
        "job_type": "fulltime",
        "company_name": empresa,
        "company_url": link,
        "company_logo": "",
        "job_location": "onsite",
        "office_location": ubicacion if ubicacion else "Sevilla, España",
        "location_limits": "España",
        "description": f"<p>{descripcion}</p><p>Acceso directo al portal de <strong>{empresa}</strong>: <a href='{link}'>Ver vacante oficial</a>.</p>",
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


# ---------------------------------------------------------------------------
# EXTRACTOR NATIVO CON REGEX (SIN BEAUTIFULSOUP)
# ---------------------------------------------------------------------------


def buscar_puestos_en_html(url, empresa_nombre, fecha_hoy):
    """Lee el HTML de cualquier web corporativa y busca enlaces con texto de empleo usando solo Regex nativo."""
    ofertas = []
    try:
        res = requests.get(url, headers=HEADERS, timeout=10)
        if res.status_code == 200:
            html = res.text

            # Busca enlaces HTML de tipo <a href="...">Texto</a>
            patron = r'<a\s+[^>]*href=["\']([^"\']+)["\'][^>]*>(.*?)</a>'
            coincidencias = re.findall(patron, html, re.IGNORECASE | re.DOTALL)

            palabras_clave = [
                "ingeniero",
                "técnico",
                "operario",
                "desarrollador",
                "manager",
                "mantenimiento",
                "vacante",
                "oferta",
                "responsable",
            ]

            for link, texto in coincidencias:
                # Limpiar etiquetas HTML residuales del texto
                texto_limpio = re.sub(r"<[^>]+>", "", texto).strip()

                if any(p in texto_limpio.lower() for p in palabras_clave):
                    if 8 < len(texto_limpio) < 90:
                        url_final = (
                            link
                            if link.startswith("http")
                            else f"{url.rstrip('/')}/{link.lstrip('/')}"
                        )
                        desc = f"Oferta extraída directamente de la web corporativa de {empresa_nombre}."
                        ofertas.append(
                            crear_oferta(
                                texto_limpio,
                                url_final,
                                empresa_nombre,
                                "Sevilla",
                                desc,
                                fecha_hoy,
                            )
                        )
    except Exception as e:
        print(f"No se pudo analizar {empresa_nombre}: {e}")

    return ofertas


# ---------------------------------------------------------------------------
# EJECUCIÓN PRINCIPAL
# ---------------------------------------------------------------------------


def main():
    fecha_hoy = datetime.now().strftime("%Y-%m-%d")
    print("Escaneando directo webs de Sevilla sin librerías externas...")

    todas_ofertas = []

    # Lista de webs oficiales de empleo en Sevilla
    WEBS_SEVILLA = [
        {
            "nombre": "Persán",
            "url": "https://persan.es/trabaja-con-nosotros/",
        },
        {
            "nombre": "Inerco",
            "url": "https://www.inerco.com/es/trabaja-con-nosotros/",
        },
        {
            "nombre": "Grupo Ybarra",
            "url": "https://www.ybarra.es/contacto/",
        },
        {
            "nombre": "Cuadros Eléctricos Nazareno",
            "url": "https://www.cen.es/contacto/",
        },
        {
            "nombre": "Interoliva",
            "url": "https://www.interoliva.com/",
        },
    ]

    for emp in WEBS_SEVILLA:
        print(f"-> Analizando {emp['nombre']}...")
        puestos = buscar_puestos_en_html(emp["url"], emp["nombre"], fecha_hoy)

        # Si no detecta listados dinámicos en el HTML, añade el canal directo oficial
        if not puestos:
            puestos.append(
                crear_oferta(
                    titulo=f"Candidatura / Trabaja en {emp['nombre']}",
                    link=emp["url"],
                    empresa=emp["nombre"],
                    ubicacion="Sevilla",
                    descripcion=f"Acceso al canal oficial de empleo de {emp['nombre']}.",
                    fecha_hoy=fecha_hoy,
                )
            )

        print(f"   Añadidos: {len(puestos)}")
        todas_ofertas.extend(puestos)

    print(f"\nTOTAL ELEMENTOS LISTOS PARA IGLUBIT: {len(todas_ofertas)}")

    if todas_ofertas:
        print("Enviando a Make...")
        try:
            r = requests.post(
                MAKE_WEBHOOK_URL, json={"jobs": todas_ofertas}, timeout=15
            )
            print(f"Respuesta Make: {r.status_code}")
        except Exception as e:
            print(f"Error Make: {e}")


if __name__ == "__main__":
    main()
