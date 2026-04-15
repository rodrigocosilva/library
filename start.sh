#!/bin/bash
cd "$(dirname "$0")"

if [ ! -d "venv" ]; then
  echo "Criando ambiente virtual..."
  python3 -m venv venv
  venv/bin/pip install -r requirements.txt -q
fi

echo "Iniciando Biblioteca Pessoal em http://localhost:5001"
open "http://localhost:5001" 2>/dev/null || true
venv/bin/python app.py
