import argparse
import os
import random
import time
from datetime import datetime
from io import BytesIO
from typing import Any, Dict, List, Optional

import undetected_chromedriver as uc
from bs4 import BeautifulSoup
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium_stealth import stealth

# ==========================================
# ⚙️ CONFIGURACIÓN (puedes sobreescribir por CLI/env)
# ==========================================

DEFAULT_DRIVE_FOLDER_ID = "1e4lwWcAbXDWI9jI6qdges8UPiElWnamd"
DEFAULT_CREDENTIALS_FILE = "Credenciales_GCP_20250325.json"

FUENTES: List[Dict[str, str]] = [
    {"nombre": "Diario_Financiero", "url": "https://www.df.cl/ultimas-noticias"},
    {"nombre": "La_Tercera_Pulso", "url": "https://www.latercera.com/canal/pulso/"},
    {"nombre": "Emol_Economia", "url": "https://www.emol.com/economia/"},
    {"nombre": "Bloomberg_Linea", "url": "https://www.bloomberglinea.com/region/chile/"},
    {"nombre": "DF_SUD", "url": "https://dfsud.com/"},
    {"nombre": "Chocale", "url": "https://chocale.cl/"},
    {"nombre": "TrendTIC", "url": "https://trendtic.cl/"},
    {"nombre": "America_Retail", "url": "https://www.america-retail.com/chile/"},
    {"nombre": "FinteChile", "url": "https://fintechile.org/noticias/"},
    {"nombre": "Transbank_Blog", "url": "https://publico.transbank.cl/blog"},
    {"nombre": "CCS_Camara", "url": "https://www.ccs.cl/noticias/"},
    {"nombre": "CNC_Camara", "url": "https://www.cnc.cl/prensa/"},
    {"nombre": "Banco_Central", "url": "https://www.bcentral.cl/noticias"},
    {"nombre": "InvestChile", "url": "https://investchile.gob.cl/es/noticias/"},
    {"nombre": "INE", "url": "https://www.ine.gob.cl/prensa"},
    {"nombre": "CMF_Chile", "url": "https://www.cmfchile.cl/portal/principal/613/w3-propertyvalue-18697.html"},
]


# ==========================================
# 🔧 GOOGLE DRIVE
# ==========================================

def authenticate_drive(credentials_file: str):
    """Autentica con la API de Google Drive usando Service Account."""
    if not os.path.exists(credentials_file):
        raise FileNotFoundError(
            f"No existe el archivo de credenciales: {credentials_file}. "
            "Pásalo por --credentials o colócalo en el root del proyecto."
        )

    scopes = ["https://www.googleapis.com/auth/drive"]
    creds = Credentials.from_service_account_file(credentials_file, scopes=scopes)
    return build("drive", "v3", credentials=creds)


def upload_html_to_drive(service, html_content: str, filename: str, folder_id: str) -> Optional[str]:
    """Sube HTML a Drive sin guardar en disco local."""
    file_metadata = {"name": filename, "parents": [folder_id], "mimeType": "text/html"}

    fh = BytesIO(html_content.encode("utf-8"))
    media = MediaIoBaseUpload(fh, mimetype="text/html", resumable=True)

    file = service.files().create(body=file_metadata, media_body=media, fields="id").execute()
    return file.get("id")


# ==========================================
# 🕵️ STEALTH & BROWSER
# ==========================================

def setup_stealth_driver(headless: bool) -> uc.Chrome:
    """Configura Chrome con opciones anti-detección."""
    options = uc.ChromeOptions()
    options.page_load_strategy = "eager"

    options.add_argument("--window-size=1920,1080")
    options.add_argument("--disable-popup-blocking")
    options.add_argument("--lang=es-CL")

    # Flags típicas para Linux/CI
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    # Headless: en algunos entornos requiere el flag explícito
    if headless:
        options.add_argument("--headless=new")
        options.add_argument("--disable-gpu")

    # use_subprocess=True suele mejorar estabilidad
    try:
        driver = uc.Chrome(options=options, headless=headless, use_subprocess=True)
    except TypeError:
        # Compatibilidad con versiones antiguas de undetected-chromedriver
        driver = uc.Chrome(options=options, use_subprocess=True)

    stealth(
        driver,
        languages=["es-CL", "es", "en-US", "en"],
        vendor="Google Inc.",
        platform="Win32",
        webgl_vendor="Intel Inc.",
        renderer="Intel Iris OpenGL Engine",
        fix_hairline=True,
    )

    return driver


def wait_for_dom_ready(driver, timeout_seconds: int = 25) -> None:
    """Espera a que el DOM esté listo (best-effort)."""

    def _ready(d):
        return d.execute_script("return document.readyState") in ("interactive", "complete")

    WebDriverWait(driver, timeout_seconds).until(_ready)


def human_scroll(driver) -> None:
    """Simula scroll humano para ayudar a cargar Lazy Loading."""
    try:
        last_height = driver.execute_script("return document.body.scrollHeight")
    except Exception:
        return

    steps = random.randint(3, 6)
    for i in range(steps):
        scroll_to = (i + 1) * last_height / steps
        scroll_to += random.randint(-120, 120)
        driver.execute_script("window.scrollTo({top: arguments[0], behavior: 'smooth'});", scroll_to)
        time.sleep(random.uniform(1.0, 2.3))

    driver.execute_script("window.scrollTo(0, 0);")
    time.sleep(random.uniform(0.6, 1.2))


def clean_html(html_content: str) -> str:
    """Limpia scripts/estilos/iframes/etc para reducir tamaño."""
    soup = BeautifulSoup(html_content, "html.parser")
    for element in soup(["script", "style", "svg", "iframe", "noscript"]):
        element.decompose()
    return str(soup)


# ==========================================
# 🚀 EJECUCIÓN
# ==========================================

def run_scraper(
    credentials_file: str,
    drive_folder_id: str,
    headless: bool,
    per_site_pause_range: tuple[float, float] = (3.0, 6.0),
    initial_load_pause_range: tuple[float, float] = (4.0, 7.0),
    max_sources: Optional[int] = None,
) -> None:
    print("🔐 Conectando a Google Drive...")
    drive_service = authenticate_drive(credentials_file)
    print("🔐 Conexión a Google Drive exitosa.")

    print("🔧 Configurando navegador en modo Stealth...")
    driver = setup_stealth_driver(headless=headless)

    timestamp = datetime.now().strftime("%Y-%m-%d")
    fuentes = FUENTES[: max_sources or len(FUENTES)]

    print(f"\n🚀 Iniciando barrido de {len(fuentes)} fuentes de noticias...\n")

    try:
        for idx, fuente in enumerate(fuentes, 1):
            nombre = fuente["nombre"]
            url = fuente["url"]
            print(f"[{idx}/{len(fuentes)}] Procesando: {nombre}")
            print(f"   🔗 URL: {url}")

            try:
                driver.get(url)

                try:
                    wait_for_dom_ready(driver, timeout_seconds=25)
                except TimeoutException:
                    # Igual seguimos: algunos sitios nunca llegan a "complete"
                    pass

                time.sleep(random.uniform(*initial_load_pause_range))
                human_scroll(driver)

                full_html = driver.page_source
                clean_content = clean_html(full_html)

                filename = f"{timestamp}_{nombre}.html"
                file_id = upload_html_to_drive(drive_service, clean_content, filename, drive_folder_id)

                if file_id:
                    print(f"   ☁️  Subido a Drive: {filename} (ID: {file_id})")
                    print("   ✅ Completado.\n")
                else:
                    print("   ❌ Error subiendo a Drive.\n")

                time.sleep(random.uniform(*per_site_pause_range))

            except Exception as e:
                print(f"   ❌ Falló {nombre}: {e}\n")

    finally:
        print("\n🏁 Proceso finalizado. Cerrando navegador.")
        try:
            driver.quit()
        except Exception:
            pass


def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Scraper de portadas/noticias: guarda HTML limpiado y lo sube a Google Drive."
    )

    parser.add_argument(
        "--credentials",
        default=os.environ.get("GDRIVE_CREDENTIALS", DEFAULT_CREDENTIALS_FILE),
        help="Ruta al JSON de Service Account (env: GDRIVE_CREDENTIALS).",
    )

    parser.add_argument(
        "--drive-folder-id",
        default=os.environ.get("DRIVE_FOLDER_ID", DEFAULT_DRIVE_FOLDER_ID),
        help="ID de carpeta de Google Drive (env: DRIVE_FOLDER_ID).",
    )

    parser.add_argument(
        "--headless",
        action=argparse.BooleanOptionalAction,
        default=os.environ.get("HEADLESS", "true").strip().lower() in {"1", "true", "yes", "y"},
        help="Ejecutar Chrome en modo headless (env: HEADLESS).",
    )

    parser.add_argument(
        "--max-sources",
        type=int,
        default=None,
        help="Procesa solo las primeras N fuentes (útil para pruebas rápidas).",
    )

    return parser.parse_args(argv)


def main() -> None:
    args = parse_args()
    run_scraper(
        credentials_file=args.credentials,
        drive_folder_id=args.drive_folder_id,
        headless=args.headless,
        max_sources=args.max_sources,
    )


if __name__ == "__main__":
    main()
