import pdfplumber
import pandas as pd

def extrair_dados(caminho_pdf):
    dados = []
    with pdfplumber.open(caminho_pdf) as pdf:
        for pagina in pdf.pages:
            tabela = pagina.extract_table()
            if tabela:
                for linha in tabela[1:]:
                    dados.append(linha)

    df = pd.DataFrame(dados, columns=["Produto", "Unidade", "Preço Mínimo", "Preço Médio", "Preço Máximo"])
    return df
