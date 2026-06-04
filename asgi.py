"""
ASGI entrypoint for production serving (Dokploy / Docker / uvicorn).

Local dev:   python main.py            (opens in your browser)
Production:  uvicorn asgi:app --host 0.0.0.0 --port 8550

no_cdn=True serves the web client assets from the app itself instead of a CDN,
so the deployment has no external runtime dependency.
"""
import flet as ft
from main import main

app = ft.run(main, view=ft.AppView.WEB_BROWSER, export_asgi_app=True, no_cdn=True)
