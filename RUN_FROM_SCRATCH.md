# Requisitos (Windows PowerShell)
# - Python 3.10+
# - Node.js 18+
# - MongoDB Community Server

# 1) MongoDB (ejecuta PowerShell como Administrador)
winget install --id MongoDB.MongoDBServer -e --source winget
# Iniciar solo si no está corriendo
Get-Service -Name MongoDB -ErrorAction SilentlyContinue | ForEach-Object { if ($_.Status -ne 'Running') { Start-Service -Name MongoDB } }

# 2) Backend
cd Microservicio_Openai
python -m venv venv
venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item env.example .env
notepad .env   # Pega tu OPENAI_API_KEY y deja MONGODB_URL=mongodb://localhost:27017
python load_knowledge.py --reset --verbose   # Opcional: carga conocimiento local a Mongo
python run.py

# 3) Verificar API
curl http://localhost:8000/health

# 4) Frontend (nueva terminal)
cd frontend
npm install
npm run dev

# Abrir: http://localhost:5173


