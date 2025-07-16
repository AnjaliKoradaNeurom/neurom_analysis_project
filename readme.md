# === Backend ===

cd backend
python -m venv venv
venv\Scripts\activate # (Windows)
pip install -r requirements.txt
pip install openai==0.28
uvicorn main:app --reload
python -m uvicorn main:app --reload

# === Frontend ===

cd ../frontend
npm install
pip install -r requirements-debug.txt
python scripts/install_dependencies.py
python scripts/debug_environment_differences.py
python scripts/fix_environment_consistency.py

npm start

cd backend
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8000 --reload

npm install
npm install --legacy-peer-deps
npm run dev

schema.org
