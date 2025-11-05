# app/__init__.py

from flask import Flask, Blueprint, send_from_directory
from flask_restx import Api
from flask_cors import CORS
from werkzeug.middleware.proxy_fix import ProxyFix
import os
import sys

# --- CRIAÇÃO DO APP ---
app = Flask(__name__)
CORS(app)
app.wsgi_app = ProxyFix(app.wsgi_app)

# Configurar rota para servir arquivos estáticos
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATIC_DIR = os.path.join(BASE_DIR, 'static')
MODELS_DIR = os.path.join(BASE_DIR, 'models')
MODEL_PATH = os.path.join(MODELS_DIR, 'text_classifier_model.keras')
TOKENIZER_PATH = os.path.join(MODELS_DIR, 'tokenizer.pkl')


def check_dependencies():
    """
    Verifica se as dependências necessárias estão instaladas.
    """
    missing_deps = []
    
    try:
        import tensorflow
    except ImportError:
        missing_deps.append("tensorflow")
    
    try:
        import numpy
    except ImportError:
        missing_deps.append("numpy")
    
    try:
        import sklearn
    except ImportError:
        missing_deps.append("scikit-learn")
    
    try:
        import matplotlib
    except ImportError:
        missing_deps.append("matplotlib")
    
    return missing_deps


def check_and_train_model():
    """
    Verifica se o modelo existe. Se não existir, oferece treinar automaticamente.
    """
    if not os.path.exists(MODEL_PATH) or not os.path.exists(TOKENIZER_PATH):
        print("\n" + "="*60)
        print("⚠️  ATENÇÃO: Modelo de IA não encontrado!")
        print("="*60)
        print(f"Modelo esperado em: {MODEL_PATH}")
        print(f"Tokenizer esperado em: {TOKENIZER_PATH}")
        
        # Verifica dependências antes de tentar treinar
        missing_deps = check_dependencies()
        
        if missing_deps:
            print("\n❌ Dependências faltando:")
            for dep in missing_deps:
                print(f"   - {dep}")
            print("\n📦 Para instalar as dependências, execute:")
            print("   pip install -r requirements.txt")
            print("\nOu instale manualmente:")
            print(f"   pip install {' '.join(missing_deps)}")
            print("\n⚠️  O sistema usará um classificador heurístico como fallback.")
            print("    (Menos preciso, mas funcional para testes básicos)")
            print("="*60 + "\n")
            return
        
        print("\nO sistema usará um classificador heurístico como fallback.")
        print("Para melhor precisão, treine o modelo primeiro:")
        print("  python app/main.py")
        print("\nDeseja treinar o modelo agora? (s/n): ", end='')
        
        # Em modo não-interativo (produção), apenas avisa
        try:
            resposta = input().strip().lower()
            if resposta == 's' or resposta == 'sim':
                print("\nIniciando treinamento do modelo...")
                print("Isso pode levar alguns minutos...\n")
                
                # Executa o treinamento como subprocesso
                import subprocess
                
                # Executa o script de treinamento como subprocesso para manter output limpo
                result = subprocess.run(
                    [sys.executable, os.path.join(BASE_DIR, "app", "main.py")],
                    cwd=BASE_DIR,
                    capture_output=False
                )
                
                if result.returncode == 0:
                    print("\n✅ Treinamento concluído! Modelo salvo.")
                    print("="*60 + "\n")
                else:
                    print("\n❌ Erro durante o treinamento. Verifique os logs acima.")
                    print("   O sistema continuará com classificador heurístico.")
                    print("="*60 + "\n")
            else:
                print("\nContinuando com classificador heurístico...\n")
        except (EOFError, KeyboardInterrupt):
            # Modo não-interativo (ex: quando rodado como serviço)
            print("\nModo não-interativo detectado. Continuando com classificador heurístico...\n")

@app.route('/')
def index():
    """Serve a página HTML principal."""
    return send_from_directory(STATIC_DIR, 'index.html')


# --- [INÍCIO DA CORREÇÃO] ---

# 1. Crie o blueprint primeiro, DEFININDO O PREFIXO DA URL NELE
blueprint = Blueprint('api', __name__, url_prefix='/api')

# 2. Anexe o 'Api' (flask-restx) AO BLUEPRINT, não ao 'app'
#    Remova o 'prefix' daqui, pois ele já está no url_prefix do blueprint.
api = Api(blueprint,
          title='Análise de documentos jurídicos',
          version='1.0',
          description='Api para análise de documentos para verificar se é confidencial e gerar logs, utilizando IA')

# 3. Verificar e treinar modelo se necessário (antes de importar controllers)
check_and_train_model()

# 4. Importe o Controller DEPOIS de criar o 'api'
#    (O controller vai adicionar seus 'namespaces' ao objeto 'api')
from .controller import ProcessaDocumentoController

# 5. Registre o blueprint (que agora contém as rotas do Swagger) no app principal
app.register_blueprint(blueprint)

# --- [FIM DA CORREÇÃO] ---