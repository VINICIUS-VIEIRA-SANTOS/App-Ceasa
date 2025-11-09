from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
import os

# from scraper import extrair_boletim  # Caso queira rodar o scraper automaticamente

app = FastAPI(title="API CEASA Boletim")

# Permite o acesso do Flutter (CORS liberado)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # depois você pode restringir
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {"status": "online", "mensagem": "API CEASA rodando com sucesso"}

@app.get("/boletim")
def get_boletim():
    # Caminho da pasta onde o scraper salva os boletins
    pasta = r"D:\ceasa_app\downloads"

    # Verifica se há arquivos Excel na pasta
    arquivos = [f for f in os.listdir(pasta) if f.endswith(".xlsx")]
    if not arquivos:
        raise FileNotFoundError("Nenhum boletim encontrado na pasta de downloads.")

    # Localiza o arquivo mais recente (último boletim)
    arquivo_recente = max(arquivos, key=lambda f: os.path.getmtime(os.path.join(pasta, f)))
    caminho_excel = os.path.join(pasta, arquivo_recente)

    # Lê o conteúdo do Excel
    df = pd.read_excel(caminho_excel)
    df = df.fillna("")

    # Padroniza nomes de colunas (opcional)
    df.columns = [str(col).strip().replace(" ", "_").upper() for col in df.columns]

    # Metadados da resposta
    meta = {
        "mercado": "CEASA Grande Vitória",
        "data": arquivo_recente.split("_")[1] if "_" in arquivo_recente else "Data desconhecida",
        "total": len(df)
    }

    # Converte o DataFrame em lista de dicionários
    dados = df.to_dict(orient="records")

    # Retorna o JSON completo com metadados e dados
    return {**meta, "dados": dados}
