#!/bin/bash

# Script para ejecutar tests de la web
# Uso: ./run-tests.sh [test-file]

set -e

echo "📦 Instalando dependencias..."
npm install --silent > /dev/null 2>&1

if [ -z "$1" ]; then
  echo "🧪 Ejecutando todos los tests..."
  npm test
else
  echo "🧪 Ejecutando test: $1"
  npm test -- "$1"
fi

echo ""
echo "✅ Tests completados"
