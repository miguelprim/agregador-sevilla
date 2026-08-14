import asyncio
from datetime import datetime
from playwright.async_api import async_playwright
import requests

# URL de tu Webhook en Make
MAKE_WEBHOOK_URL = "https://hook.eu1.make.com/tg93wwof55r5krw31joysyih2wv5qt0w"


def crear_oferta(titulo, link, empresa, ubicacion, descripcion, fecha_hoy):
    """Estructura estandarizada para Iglubit / Jobboardly."""
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
            f"Inscríbete en la fuente original: <a href='{link}' target='_blank'>Ver oferta completa</a>.</p>"
        ),
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


async def extraer_ofertas_google_jobs(query, limite_scrolls=4):
    fecha_hoy = datetime.now().strftime("%Y-%m-%d")
    ofertas = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
            locale="es-ES",
        )
        page = await context.new_page()

        url = f"https://www.google.com/search?q={query}&ibp=htl;jobs"
        print(f"-> Navegando a Google Jobs: '{query}'...")
        await page.goto(url, wait_until="networkidle")

        # Gestor de cookies
        try:
            btn_cookies = page.locator(
                "button:has-text('Aceptar todo'), button:has-text('Accept all')"
            )
            if await btn_cookies.count() > 0:
                await btn_cookies.first.click()
                await page.wait_for_timeout(1000)
        except Exception:
            pass

        # Scroll para cargar ofertas
        print("   [+] Cargando resultados con scroll...")
        for _ in range(limite_scrolls):
            await page.mouse.wheel(0, 1500)
            await page.wait_for_timeout(1500)

        tarjetas = page.locator("li.iA9if, div.iA9if")
        total_tarjetas = await tarjetas.count()
        print(f"   [+] {total_tarjetas} ofertas encontradas en pantalla.")

        for i in range(min(total_tarjetas, 25)):
            try:
                tarjeta = tarjetas.nth(i)
                await tarjeta.click()
                await page.wait_for_timeout(1000)

                # Extracción de campos
                titulo_el = page.locator("h2.KL423e").first
                titulo = (
                    await titulo_el.inner_text()
                    if await titulo_el.count() > 0
                    else "Oferta de Empleo"
                )

                empresa_el = page.locator("div.vP10Bf").first
                empresa = (
                    await empresa_el.inner_text()
                    if await empresa_el.count() > 0
                    else "Empresa Local"
                )

                ubicacion_el = page.locator("div.Qk8fB").first
                ubicacion = (
                    await ubicacion_el.inner_text()
                    if await ubicacion_el.count() > 0
                    else "Sevilla, España"
                )

                desc_el = page.locator("span.HB8fbe, div.YA129b").first
                descripcion = (
                    await desc_el.inner_html()
                    if await desc_el.count() > 0
                    else "Sin descripción detallada."
                )

                link_el = page.locator(
                    "a.p323ze, a[target='_blank']:has-text('Solicitar')"
                ).first
                link = (
                    await link_el.get_attribute("href")
                    if await link_el.count() > 0
                    else page.url
                )

                ofertas.append(
                    crear_oferta(
                        titulo.strip(),
                        link,
                        empresa.strip(),
                        ubicacion.strip(),
                        descripcion,
                        fecha_hoy,
                    )
                )
                print(f"   [✓] Leída: {titulo.strip()} - {empresa.strip()}")

            except Exception as e:
                print(f"   [!] Error en tarjeta {i}: {e}")

        await browser.close()

    return ofertas


async def main():
    print("=== SCRAPER IGLUBIT GOOGLE JOBS ===")

    BUSQUEDAS = [
        "empleo Sevilla",
        "ofertas trabajo Sevilla",
    ]

    todas_ofertas = []

    for query in BUSQUEDAS:
        ofertas = await extraer_ofertas_google_jobs(query, limite_scrolls=4)
        for o in ofertas:
            if not any(
                x["job_title"] == o["job_title"]
                and x["company_name"] == o["company_name"]
                for x in todas_ofertas
            ):
                todas_ofertas.append(o)

    print(f"\n>>> TOTAL DE OFERTAS: {len(todas_ofertas)} <<<")

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
    asyncio.run(main())
