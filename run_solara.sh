#!/bin/bash
# sources the .env file and runs the Solara app
# Usage: ./run_solara.sh [filename]
# If no filename is provided, defaults to solara_app.py

SOLARA_FILE="${1:-solara_app.py}"

while IFS= read -r line; do
  [[ $line =~ ^#.*$ || -z $line ]] && continue
  
  if [[ $line =~ ^([^=]+)=(.*)$ ]]; then
    name="${BASH_REMATCH[1]}"
    value="${BASH_REMATCH[2]}"
    
    # Remove quotes if present
    value="${value#\'}"
    value="${value%\'}"
    value="${value#\"}"
    value="${value%\"}"
    
    export "$name=$value"
  fi
done < .env

solara run "$SOLARA_FILE" --port 8900 --no-open
# solara run "$SOLARA_FILE" --port 8900 --no-open --log-level debug
