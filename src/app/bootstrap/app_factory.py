from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware

from app.bootstrap.wiring import (
    attach_services_to_app,
    build_application_services,
    include_api_routers,
    mount_dashboard_ui,
    mount_runtime_static_assets,
    register_root_redirect,
)
from app.infrastructure.logging import configure_logging
from app.infrastructure.settings import ApplicationSettings, get_settings


def _configure_security_middleware(
    app: FastAPI,
    settings: ApplicationSettings,
) -> None:
    if settings.trusted_hosts:
        app.add_middleware(
            TrustedHostMiddleware,
            allowed_hosts=settings.trusted_hosts,
        )

    if settings.enforce_https_redirect:
        app.add_middleware(HTTPSRedirectMiddleware)

    if settings.cors_allow_origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=settings.cors_allow_origins,
            allow_credentials=settings.cors_allow_credentials,
            allow_methods=settings.cors_allow_methods,
            allow_headers=settings.cors_allow_headers,
        )


def create_app() -> FastAPI:
    configure_logging()
    settings = get_settings()
    services = build_application_services(settings)

    app = FastAPI(title=settings.project_name, version="0.1.0")
    _configure_security_middleware(app, settings)

    attach_services_to_app(app, services)
    mount_runtime_static_assets(app, services.project_root)
    include_api_routers(app)
    register_root_redirect(app, settings.dashboard_path)
    mount_dashboard_ui(
        app,
        services,
        settings.dashboard_path,
        settings.default_scenario_id,
    )
    return app