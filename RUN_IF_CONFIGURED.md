# Suposiciones
# - MongoDB instalado
# - Backend con venv + dependencias + .env listo
# - Frontend ya instaló node_modules

# 1) Asegurar MongoDB (no falla si ya está corriendo)
Get-Service -Name MongoDB -ErrorAction SilentlyContinue | ForEach-Object { if ($_.Status -ne 'Running') { Start-Service -Name MongoDB } }

# 2) Backend
cd Microservicio_Openai
venv\Scripts\Activate.ps1
python run.py

# 3) Verificar API (nueva terminal si prefieres)
curl http://localhost:8000/health

# 4) Frontend (otra terminal desde la raíz del repo)
cd frontend
npm run dev

# Abrir: http://localhost:5173

# Recargar vector store si cargaste/alteraste conocimiento
# curl -X POST http://localhost:8000/documents/reload

# Si el servicio MongoDB no existe o requiere permisos:
#  - Ver nombre/estado: Get-Service | Where-Object { $_.Name -like 'MongoDB*' -or $_.DisplayName -like 'MongoDB*' } | ft Name,Status,DisplayName -Auto
#  - Iniciar por DisplayName: Start-Service -DisplayName 'MongoDB Server (MongoDB)'
#  - Ejecutar como Admin: Start-Process PowerShell -Verb RunAs -ArgumentList "Start-Service -Name 'MongoDB'"

