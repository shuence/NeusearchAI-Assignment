"""Scalar API documentation generator."""
from fastapi.responses import HTMLResponse
import json
from app.config.settings import settings


def get_scalar_html(
    openapi_schema: dict,
    title: str = "API Documentation",
) -> HTMLResponse:
    """
    Generate Scalar API documentation HTML.
    
    Args:
        openapi_schema: The OpenAPI schema dictionary
        title: The title for the documentation page
        
    Returns:
        HTMLResponse with Scalar documentation
    """
    config = {
        "theme": settings.SCALAR_THEME,
        "layout": settings.SCALAR_LAYOUT,
        "showSidebar": settings.SCALAR_SHOW_SIDEBAR,
        "hideDownloadButton": settings.SCALAR_HIDE_DOWNLOAD_BUTTON,
        "hideModels": settings.SCALAR_HIDE_MODELS,
        "hideSchema": settings.SCALAR_HIDE_SCHEMA,
    }
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>{title}</title>
        <meta charset="utf-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <style>
            body {{
                margin: 0;
                padding: 0;
            }}
        </style>
    </head>
    <body>
        <script
            id="api-reference"
            data-configuration='{json.dumps(config)}'
        >{json.dumps(openapi_schema)}</script>
        <script src="https://cdn.jsdelivr.net/npm/@scalar/api-reference@latest/dist/browser/standalone.js"></script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)

