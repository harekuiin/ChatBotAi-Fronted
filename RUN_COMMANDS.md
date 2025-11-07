# MongoDB (Windows PowerShell)
Get-Service -Name MongoDB -ErrorAction SilentlyContinue | ForEach-Object { if ($_.Status -ne 'Running') { Start-Service -Name MongoDB } }

# Backend
cd Microservicio_Openai
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
copy env.example .env
notepad .env
python load_knowledge.py --reset --verbose
python run.py

# Frontend
cd ../frontend
npm install
npm run dev

