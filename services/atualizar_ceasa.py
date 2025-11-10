import subprocess
import pandas as pd
from sqlalchemy.orm import Session
from models import Produto, BoletimCeasa
from datetime import datetime
import os

def atualizar_dados_ceasa(db: Session):
    try:
        # 1. Executa o scraper
        caminho_script = os.path.abspath("./scraper.py")
        subprocess.run(["python", caminho_script], check=True)

        # 2. Localiza o CSV gerado
        caminho_csv = "./downloads/boletim_ceasa.csv"
        if not os.path.exists(caminho_csv):
            return {"status": "erro", "mensagem": "Arquivo CSV não encontrado."}

        # 3. Lê o CSV em DataFrame
        df = pd.read_csv(caminho_csv)
        df.columns = [c.strip().lower() for c in df.columns]

        total_inseridos = 0
        total_atualizados = 0
        total_historico = 0

        for _, row in df.iterrows():
            nome_produto = str(row["mercadoria"]).strip().title()
            preco_min = float(row.get("preço mínimo", 0))
            preco_max = float(row.get("preço máximo", 0))
            preco_med = float(row.get("preço médio", 0))
            origem = str(row.get("origem", "")).strip()

            # --- Atualiza produto no banco
            produto_existente = db.query(Produto).filter(Produto.nome == nome_produto).first()
            if produto_existente:
                if produto_existente.preco_venda != preco_max:
                    produto_existente.preco_venda = preco_max
                    db.commit()
                    total_atualizados += 1
            else:
                novo_produto = Produto(
                    nome=nome_produto,
                    categoria="CEASA",
                    unidade="kg",
                    preco_compra=0.0,
                    preco_venda=preco_max,
                    estoque_minimo=0
                )
                db.add(novo_produto)
                db.commit()
                total_inseridos += 1

            # --- Salva no histórico
            boletim = BoletimCeasa(
                data_boletim=datetime.now().date(),
                produto=nome_produto,
                preco_min=preco_min,
                preco_max=preco_max,
                preco_medio=preco_med,
                origem=origem
            )
            db.add(boletim)
            total_historico += 1

        db.commit()

        return {
            "status": "sucesso",
            "inseridos": total_inseridos,
            "atualizados": total_atualizados,
            "historico": total_historico
        }

    except subprocess.CalledProcessError:
        return {"status": "erro", "mensagem": "Falha ao executar o scraper."}
    except Exception as e:
        return {"status": "erro", "mensagem": str(e)}
