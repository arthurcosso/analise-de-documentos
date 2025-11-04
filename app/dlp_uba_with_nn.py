import sqlite3
import numpy as np
import pickle
from datetime import datetime
import os  # <-- Import 'os' (já estava presente)

# Tentativa de importar TensorFlow/Keras; se não disponível, usamos fallback
try:
    from tensorflow.keras.models import load_model
    from tensorflow.keras.preprocessing.sequence import pad_sequences
    _TF_AVAILABLE = True
except Exception as _e:
    print(f"[AVISO] TensorFlow/Keras indisponível para a API ({_e}). Usando classificador heurístico temporário.")
    _TF_AVAILABLE = False

# --- Configuração do Modelo de IA (Carregamento) ---

# Define os rótulos
LABEL_MAP = {0: "PUBLICO", 1: "INTERNO", 2: "CONFIDENCIAL"}
# Define o tamanho da sequência (deve ser o MESMO do script de treino)
MAX_SEQUENCE_LEN = 20

# --- [INÍCIO DA CORREÇÃO] ---
# Pega o diretório ONDE ESTE SCRIPT (dlp_uba_with_nn.py) está
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Cria os caminhos completos para os arquivos que estão NA MESMA PASTA
MODEL_PATH = os.path.join(BASE_DIR, 'text_classifier_model.keras')
TOKENIZER_PATH = os.path.join(BASE_DIR, 'tokenizer.pkl')

# Carrega o modelo/tokenizer se TensorFlow estiver disponível e arquivos existirem
MODELO_IA = None
TOKENIZER = None
if _TF_AVAILABLE and os.path.exists(MODEL_PATH) and os.path.exists(TOKENIZER_PATH):
    print(f"Carregando modelo de IA Keras de: {MODEL_PATH}")
    MODELO_IA = load_model(MODEL_PATH)
    print(f"Carregando tokenizer de: {TOKENIZER_PATH}")
    with open(TOKENIZER_PATH, 'rb') as handle:
        TOKENIZER = pickle.load(handle)
    print("IA pronta.")
else:
    print("[AVISO] Modelo/tokenizer não encontrados ou TF indisponível. Ativando modo heurístico.")
# --- [FIM DA CORREÇÃO] ---


# --- Configuração do Banco de Dados (SQLite) ---
# (Idêntico ao seu código original)

def setup_database():
    """Cria o banco de dados e as tabelas necessárias."""
    conn = sqlite3.connect('legal_dlp_uba.db')
    cursor = conn.cursor()
    cursor.execute('''
                   CREATE TABLE IF NOT EXISTS classified_docs
                   (doc_hash TEXT PRIMARY KEY, secrecy_level TEXT, last_classified_date TEXT)''')
    cursor.execute('''
                   CREATE TABLE IF NOT EXISTS access_log
                   (log_id INTEGER PRIMARY KEY AUTOINCREMENT, timestamp TEXT, username TEXT,
                    doc_hash TEXT, doc_secy_level TEXT, action TEXT, anomaly_score INTEGER)''')
    conn.commit()
    conn.close()


# --- Tópico A: Nível de Sigilo (PLN / Rede Neural) ---

def classify_with_neural_network(document_text):
    """Classifica o texto usando o modelo Keras, se disponível; caso contrário, usa heurística simples."""
    if MODELO_IA is not None and TOKENIZER is not None and _TF_AVAILABLE:
        try:
            text_list = [document_text]
            sequences = TOKENIZER.texts_to_sequences(text_list)
            padded_data = pad_sequences(sequences, maxlen=MAX_SEQUENCE_LEN)
            prediction = MODELO_IA.predict(padded_data, verbose=0)
            predicted_class_index = np.argmax(prediction[0])
            return LABEL_MAP.get(predicted_class_index, "ERRO")
        except Exception as e:
            print(f"Erro ao classificar com IA: {e}")
            # fallback abaixo

    # Fallback heurístico: regras simples por palavras-chave
    text = (document_text or '').lower()
    if any(k in text for k in ["segredo de justiça", "sigiloso", "confidencial", "dados sensíveis"]):
        return "CONFIDENCIAL"
    if any(k in text for k in ["interno", "rascunho", "uso interno", "restrito"]):
        return "INTERNO"
    return "PUBLICO"


# --- Tópico B: Análise de Comportamento (UBA / SQLite) ---
# (Idêntico ao seu código original)

def check_behavior_anomaly(conn, username, doc_secy_level):
    """
    [NÚCLEO CONCEITUAL DO UBA]
    Verifica se a ação atual é uma anomalia baseada em regras simples.
    MODIFICADO: Agora retorna alertas.
    """
    anomaly_score = 0
    alerts = []  # <<< NOVO: Lista para guardar alertas

    # Regra 1: Ninguém deve acessar material confidencial fora do horário (ex: noite)
    hour = datetime.now().hour
    if doc_secy_level == "CONFIDENCIAL" and (hour < 8 or hour > 20):
        anomaly_score += 50
        alert_msg = "Alerta UBA (Simples): Acesso 'CONFIDENCIAL' fora de hora!"
        print(f"  -> {alert_msg}")  # Mantém o log do console
        alerts.append(alert_msg)  # <<< NOVO: Adiciona à lista

    # Regra 2: Usuários de baixo privilégio não devem acessar docs confidenciais
    if username == "estagiario" and doc_secy_level == "CONFIDENCIAL":
        anomaly_score += 100
        alert_msg = "Alerta UBA (Simples): Usuário 'estagiario' acessou 'CONFIDENCIAL'!"
        print(f"  -> {alert_msg}")  # Mantém o log do console
        alerts.append(alert_msg)  # <<< NOVO: Adiciona à lista

    return anomaly_score, alerts  # <<< MODIFICADO: Retorna o score E os alertas


def log_access_for_uba(username, doc_hash, classification, action="read"):
    """
    Registra o acesso no SQLite para que o agente UBA possa analisá-lo.
    MODIFICADO: Agora retorna um dicionário com o resultado da análise.
    """
    conn = sqlite3.connect('legal_dlp_uba.db')
    cursor = conn.cursor()

    # 1. Checa anomalia *antes* de registrar
    # <<< MODIFICADO: Captura os valores de retorno
    anomaly_score, alerts = check_behavior_anomaly(conn, username, classification)

    # 2. Registra o log de acesso
    timestamp = datetime.now().isoformat()
    cursor.execute("""
                   INSERT INTO access_log (timestamp, username, doc_hash, doc_secy_level, action, anomaly_score)
                   VALUES (?, ?, ?, ?, ?, ?)
                   """, (timestamp, username, doc_hash, classification, action, anomaly_score))
    conn.commit()
    conn.close()

    is_anomaly = anomaly_score > 50  # Determina se é uma anomalia

    if is_anomaly:
        print(f"\n[!!! ATUADOR: ALERTA DE SEGURANÇA GERADO !!!]")
        print(f"    Usuário: {username}, Documento: {doc_hash}, Risco: {anomaly_score}")

    # <<< NOVO: Retorna um dicionário estruturado para a API
    return {
        "is_anomaly": is_anomaly,
        "anomaly_score": anomaly_score,
        "alerts": alerts
    }


# --- Função Principal do Agente (Simulado) ---

def process_document_access(username, document_path):
    """
    Simula um usuário acessando um documento.
    Este é o "Agente" em ação.
    """
    print(f"\n--- Processando Acesso ---")
    print(f"Usuário: {username}")
    print(f"Arquivo: {document_path}")

    try:
        with open(document_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        print(f"Erro ao ler arquivo: {e}")
        return

    doc_hash = f"hash_do_{document_path}"

    # AGENTE (Passo 1: Classificação - PLN / Rede Neural)
    # *** MUDANÇA PRINCIPAL AQUI ***
    print("Executando classificador de sigilo (Rede Neural Keras)...")
    secrecy_level = classify_with_neural_network(content)
    print(f"  -> Nível de Sigilo determinado: {secrecy_level}")

    # AGENTE (Passo 2: Análise e Log - UBA / SQLite)
    print("Registrando acesso e analisando comportamento (UBA/SQLite)...")
    log_access_for_uba(username, doc_hash, secrecy_level, action="read")

    print("--- Processamento Concluído ---")


# --- Exemplo de Execução ---

def run_main_simulation():
    # 0. Limpar banco de dados antigo, se existir
    if os.path.exists('legal_dlp_uba.db'):
        os.remove('legal_dlp_uba.db')

    # # 1. Criar os arquivos de teste
    # with open("caso_publico.txt", "w", encoding='utf-8') as f:
    #     f.write("A audiência foi marcada para o dia 10.")
    #
    # with open("caso_interno.txt", "w", encoding='utf-8') as f:
    #     f.write("Este é um rascunho da petição, favor revisar. Processo interno.")
    #
    # with open("caso_critico.txt", "w", encoding='utf-8') as f:
    #     f.write("Este caso corre em segredo de justiça. Não revelar a terceiros.")

    # 2. Configurar o banco de dados
    setup_database()

    # 3. Simular acessos
    process_document_access("advogado_senior", "caso_publico.txt")
    process_document_access("advogado_senior", "caso_interno.txt")

    # 4. Simular acesso ANÔMALO (Estagiário acessando doc crítico)
    process_document_access("estagiario", "caso_critico.txt")