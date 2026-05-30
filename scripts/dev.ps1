param(
  [switch]$Docker
)

if ($Docker) {
  docker compose up --build
  exit $LASTEXITCODE
}

Write-Host "Use duas abas de terminal para desenvolvimento local:"
Write-Host "1. cd backend; python -m venv .venv; .\.venv\Scripts\Activate.ps1; pip install -r requirements.txt; uvicorn app.main:app --reload"
Write-Host "2. cd frontend; npm install; npm run dev"

