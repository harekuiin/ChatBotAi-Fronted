# -*- coding: utf-8 -*-
"""Script para ejecutar el servidor de desarrollo"""

import uvicorn
from app.config import settings

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=settings.service_host,
        port=settings.service_port,
        reload=settings.reload
    )

