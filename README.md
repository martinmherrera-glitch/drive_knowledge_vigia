# drive_knowledge_vigia

Scraper en Python que visita una lista de fuentes de noticias, extrae el **HTML completo**, lo limpia (remueve scripts/estilos/iframes) y lo **sube directamente a Google Drive** (sin guardar archivos en disco local).

## Requisitos

- Python 3.10+
- Google Chrome instalado

## Instalación

```bash
pip install -r requirements.txt
```

## Configuración

- Crea una **Service Account** en Google Cloud, habilita **Google Drive API** y descarga el JSON.
- Comparte la carpeta de Drive destino con el email de la Service Account.

Por defecto el script busca el archivo `Credenciales_GCP_20250325.json` en el root del repo.

## Uso

```bash
python news_html_scraper_to_drive.py --credentials "Credenciales_GCP_20250325.json" --drive-folder-id "TU_FOLDER_ID"
```

Opciones útiles:

- `--headless / --no-headless`: correr con o sin UI
- `--max-sources N`: procesa solo las primeras N fuentes (para pruebas rápidas)

También puedes configurar por variables de entorno:

- `GDRIVE_CREDENTIALS`
- `DRIVE_FOLDER_ID`
- `HEADLESS` (por defecto `true`)

## Nota

No comitees credenciales: el repo incluye `.gitignore` para excluir `Credenciales_GCP_*.json` y `credentials*.json`.
