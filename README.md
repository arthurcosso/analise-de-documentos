# Sistema de Análise de Documentos DLP/UBA

Sistema de análise de documentos jurídicos que utiliza Inteligência Artificial (Redes Neurais) para classificação automática de sigilo e análise de comportamento de usuários (UBA - User Behavior Analytics) para detectar anomalias de acesso.

## 🎯 Funcionalidades

- **Classificação Automática de Sigilo**: Utiliza uma rede neural treinada para classificar documentos em três níveis:
  - `PUBLICO`: Documentos de acesso público
  - `INTERNO`: Documentos para uso interno
  - `CONFIDENCIAL`: Documentos confidenciais e sigilosos

- **Análise de Comportamento (UBA)**: Detecta comportamentos anômalos como:
  - Acesso a documentos confidenciais fora do horário comercial
  - Usuários de baixo privilégio acessando documentos confidenciais
  - Geração de alertas de segurança automáticos

- **API REST**: Interface de programação para integração com outros sistemas
- **Interface Web**: Interface HTML para testes e demonstração

## 📁 Estrutura do Projeto

```
analise-de-documentos/
├── app/                          # Código principal da aplicação
│   ├── __init__.py              # Configuração do Flask app
│   ├── main.py                  # Script principal de treinamento (com validação)
│   ├── train_text_classifier.py # Script alternativo de treinamento
│   ├── dlp_uba_with_nn.py       # Lógica de classificação e UBA
│   ├── controller/              # Controllers da API
│   │   └── ProcessaDocumentoController.py
│   ├── caso_publico.txt         # Arquivos de teste
│   ├── caso_interno.txt
│   └── caso_critico.txt
├── training_data/               # Dados de treinamento
│   ├── doc_publico.txt
│   ├── doc_interno.txt
│   └── doc_confidencial.txt
├── models/                      # Modelos treinados (gerados)
│   ├── text_classifier_model.keras
│   ├── tokenizer.pkl
│   ├── grafico_acuracia.png
│   └── grafico_perda.png
├── data/                        # Banco de dados SQLite
│   └── legal_dlp_uba.db
├── static/                      # Arquivos estáticos
│   └── index.html
├── run.py                       # Script de inicialização do servidor
├── requirements.txt             # Dependências Python
└── README.md                    # Este arquivo
```

## 🚀 Instalação

### Pré-requisitos

- Python 3.8 ou superior
- pip (gerenciador de pacotes Python)

### Passo a Passo

1. **Clone ou baixe o repositório**

2. **Crie um ambiente virtual (recomendado)**

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/Mac
python3 -m venv venv
source venv/bin/activate
```

3. **Instale as dependências**

```bash
pip install -r requirements.txt
```

**Nota**: 
- A instalação do TensorFlow pode demorar alguns minutos
- Se você não instalar as dependências, o sistema ainda funcionará com um classificador heurístico (menos preciso)
- O sistema verifica automaticamente se as dependências estão instaladas antes de tentar treinar o modelo

## 📚 Como Usar

### 1. Treinar o Modelo de IA (Opcional)

O sistema pode treinar o modelo automaticamente na primeira inicialização. Você tem duas opções:

**Opção A - Treinamento Automático (Recomendado para primeira vez):**
Simplesmente inicie o servidor. Se o modelo não existir, o sistema perguntará se deseja treinar:
```bash
python run.py
```
Quando solicitado, digite `s` ou `sim` para treinar automaticamente.

**Opção B - Treinamento Manual (Antes de iniciar o servidor):**
Execute um dos scripts de treinamento:

**Script principal (com validação e gráficos):**
```bash
python app/main.py
```

**Script alternativo:**
```bash
python app/train_text_classifier.py
```

O script irá:
- Carregar os dados de treinamento de `training_data/`
- Treinar a rede neural
- Salvar o modelo em `models/text_classifier_model.keras`
- Salvar o tokenizer em `models/tokenizer.pkl`
- Gerar gráficos de acurácia e perda em `models/`

**Tempo estimado**: 1-5 minutos dependendo do hardware.

**Nota**: Se o modelo não existir quando o servidor iniciar, o sistema usará um classificador heurístico como fallback (menos preciso, mas funcional).

### 2. Iniciar o Servidor

```bash
python run.py
```

**Primeira execução**: Se o modelo não existir, o sistema perguntará se deseja treinar. Digite `s` para treinar ou `n` para continuar com o classificador heurístico.

O servidor estará disponível em: `http://127.0.0.1:5000`

### 3. Acessar a Interface Web

Abra seu navegador e acesse:
```
http://127.0.0.1:5000
```

Você verá uma interface onde pode:
- Selecionar um usuário (estagiario ou advogado_senior)
- Enviar um arquivo .txt para análise
- Ver o resultado da classificação e análise UBA

### 4. Usar a API REST

A API está disponível em `/api/processing/process_document`

**Endpoint**: `POST /api/processing/process_document`

**Formato**: `multipart/form-data`

**Parâmetros**:
- `username` (string): Nome do usuário (`estagiario` ou `advogado_senior`)
- `file` (file): Arquivo .txt para análise

**Exemplo com cURL**:
```bash
curl -X POST http://127.0.0.1:5000/api/processing/process_document \
  -F "username=estagiario" \
  -F "file=@caso_critico.txt"
```

**Resposta JSON**:
```json
{
  "username": "estagiario",
  "doc_hash": "abc123...",
  "classified_level": "CONFIDENCIAL",
  "uba_analysis": {
    "is_anomaly": true,
    "anomaly_score": 150,
    "alerts": [
      "Alerta UBA (Simples): Usuário 'estagiario' acessou 'CONFIDENCIAL'!",
      "Alerta UBA (Simples): Acesso 'CONFIDENCIAL' fora de hora!"
    ]
  },
  "processed_filename": "caso_critico.txt"
}
```

**Documentação Swagger**: Acesse `http://127.0.0.1:5000/api/` para ver a documentação interativa da API.

## 🧪 Testando o Sistema

Você pode testar o sistema com os arquivos de exemplo em `app/`:

- `caso_publico.txt`: Deve ser classificado como PUBLICO
- `caso_interno.txt`: Deve ser classificado como INTERNO  
- `caso_critico.txt`: Deve ser classificado como CONFIDENCIAL

### Teste de Anomalia UBA

Para testar a detecção de anomalias, tente:
1. Fazer upload de `caso_critico.txt` com o usuário `estagiario`
2. Fazer upload de um documento confidencial fora do horário comercial (antes das 8h ou após as 20h)

Ambos devem gerar alertas de segurança.

## 📊 Banco de Dados

O sistema utiliza SQLite para armazenar:
- **classified_docs**: Documentos classificados com seus níveis de sigilo
- **access_log**: Logs de acesso com análise de anomalias

O banco de dados é criado automaticamente em `data/legal_dlp_uba.db` na primeira execução.

## 🔧 Configuração

### Modificar Regras UBA

As regras de detecção de anomalias estão em `app/dlp_uba_with_nn.py`, na função `check_behavior_anomaly()`. Você pode adicionar novas regras conforme necessário.

### Ajustar Parâmetros do Modelo

Os parâmetros de treinamento podem ser ajustados em:
- `app/main.py`: Número de épocas, batch size, etc.
- `app/train_text_classifier.py`: Versão alternativa

## 🐛 Troubleshooting

### Erro: "Modelo/tokenizer não encontrados"

**Solução**: Execute o script de treinamento primeiro (`app/main.py`)

### Erro: "TensorFlow/Keras indisponível"

**Solução**: 
```bash
pip install tensorflow
```

### Erro: "Porta 5000 já está em uso"

**Solução**: Altere a porta em `run.py` ou encerre o processo que está usando a porta.

### Modelo não classifica corretamente

**Solução**: 
- Adicione mais exemplos de treinamento em `training_data/`
- Ajuste os parâmetros de treinamento (épocas, batch size)
- Verifique os gráficos gerados para identificar overfitting

## 📝 Notas Técnicas

- O modelo utiliza Embedding + GlobalAveragePooling1D + Dense layers
- O tokenizer é limitado a 1000 palavras mais frequentes
- Sequências são padronizadas para 20 tokens
- O sistema usa validação de 20% dos dados para evitar overfitting

## 📄 Licença

Este projeto é fornecido "como está" para fins educacionais e de demonstração.

## 🤝 Contribuindo

Sinta-se à vontade para abrir issues ou pull requests com melhorias.

---

**Desenvolvido para análise de documentos jurídicos com IA e detecção de anomalias comportamentais.**

