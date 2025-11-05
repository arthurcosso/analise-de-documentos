# /run.py
import os
import sys

print("="*60)
print("🚀 Iniciando servidor de Análise de Documentos DLP/UBA")
print("="*60)

# Importa o 'app' criado no __init__.py (isso também executa a verificação do modelo)
from app import app

if __name__ == '__main__':
    # Define a porta aqui, no ponto de entrada
    port = int(os.environ.get("PORT", 5000))
    print(f"\n✅ Servidor iniciado em http://0.0.0.0:{port}")
    print(f"📄 Interface web: http://127.0.0.1:{port}")
    print(f"📚 API Swagger: http://127.0.0.1:{port}/api/\n")
    app.run(debug=True, host='0.0.0.0', port=port)