# /run.py
import os
from app import app # Importa o 'app' criado no __init__.py

if __name__ == '__main__':
    # Define a porta aqui, no ponto de entrada
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=True, host='0.0.0.0', port=port)