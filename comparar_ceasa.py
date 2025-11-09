import os
from datetime import datetime
import pandas as pd

DOWNLOAD_DIR = "downloads"


def listar_boletins(pasta=DOWNLOAD_DIR):
    pasta_abs = os.path.abspath(pasta)
    arquivos = [
        os.path.join(pasta_abs, f)
        for f in os.listdir(pasta_abs)
        if f.startswith("boletim_") and f.endswith(".xlsx")
    ]
    arquivos.sort(key=os.path.getmtime, reverse=True)
    return arquivos


def detectar_coluna_produto(df: pd.DataFrame) -> str:
    for nome in df.columns:
        low = str(nome).lower()
        if "prod" in low or "produto" in low or "espec" in low or "descr" in low:
            return nome
    return df.columns[0]


def escolher_coluna_preco(df: pd.DataFrame):
    for col in ["M.C.", "MAX", "MIN"]:
        if col in df.columns:
            return col
    return None


def normalizar_col_preco_100(df: pd.DataFrame, col: str):
    """Se a coluna veio como 455 em vez de 4,55, divide por 100."""
    df[col] = pd.to_numeric(df[col], errors="coerce")
    if df[col].max() and df[col].max() > 50:
        df[col] = df[col] / 100
    return df


def carregar_boletim(caminho: str) -> pd.DataFrame:
    df = pd.read_excel(caminho, sheet_name="Boletim")
    col_preco = escolher_coluna_preco(df)
    if col_preco:
        df = normalizar_col_preco_100(df, col_preco)
    return df


def comparar_boletins(df_hoje: pd.DataFrame, df_antigo: pd.DataFrame, n_dias_label="anterior"):
    col_prod_hoje = detectar_coluna_produto(df_hoje)
    col_prod_ant = detectar_coluna_produto(df_antigo)

    col_preco_hoje = escolher_coluna_preco(df_hoje)
    col_preco_ant = escolher_coluna_preco(df_antigo)

    if not col_preco_hoje or not col_preco_ant:
        raise ValueError("Não encontrei coluna de preço em um dos boletins.")

    # normaliza produto pra comparar (mais simples: tudo minúsculo)
    df_hoje["_key_prod"] = df_hoje[col_prod_hoje].astype(str).str.strip().str.lower()
    df_antigo["_key_prod"] = df_antigo[col_prod_ant].astype(str).str.strip().str.lower()

    # faz o merge
    df_join = pd.merge(
        df_hoje,
        df_antigo[["_key_prod", col_preco_ant]].rename(columns={col_preco_ant: f"preco_{n_dias_label}"}),
        on="_key_prod",
        how="left",
    )

    # renomeia o preço de hoje pra ficar claro
    df_join = df_join.rename(columns={col_preco_hoje: "preco_hoje"})

    # calcula diferença
    df_join["dif_abs"] = df_join["preco_hoje"] - df_join[f"preco_{n_dias_label}"]
    df_join["dif_pct"] = (df_join["dif_abs"] / df_join[f"preco_{n_dias_label}"]) * 100

    # status
    def status(row):
        old = row[f"preco_{n_dias_label}"]
        new = row["preco_hoje"]
        if pd.isna(old):
            return "NOVO"
        if pd.isna(new):
            return "SEM PREÇO"
        if new > old:
            return "SUBIU"
        if new < old:
            return "CAIU"
        return "IGUAL"

    df_join["status"] = df_join.apply(status, axis=1)

    # ordena pra ficar bonitinho: quem subiu primeiro
    df_join = df_join.sort_values(["status", "dif_abs"], ascending=[True, False])

    return df_join, col_prod_hoje


def salvar_comparativo(df_comp: pd.DataFrame, col_prod: str, caminho: str):
    os.makedirs(os.path.dirname(caminho), exist_ok=True)
    with pd.ExcelWriter(caminho, engine="xlsxwriter") as writer:
        # planilha principal
        cols = [
            col_prod,
            "preco_hoje",
            "preco_anterior",
            "dif_abs",
            "dif_pct",
            "status",
        ]
        # alguns boletins tem "Data" na planilha original
        if "Data" in df_comp.columns:
            cols.append("Data")

        df_comp.to_excel(writer, sheet_name="Comparativo", index=False, columns=cols)
        wb = writer.book
        ws = writer.sheets["Comparativo"]

        header_fmt = wb.add_format({"bold": True, "bg_color": "#D9D9D9"})
        num_fmt = wb.add_format({"num_format": "#,##0.00"})
        pct_fmt = wb.add_format({"num_format": "0.00%"})

        for i, c in enumerate(cols):
            ws.write(0, i, c, header_fmt)
            ws.set_column(i, i, 18)

        # formata as numéricas
        if "preco_hoje" in cols:
            idx = cols.index("preco_hoje")
            ws.set_column(idx, idx, 12, num_fmt)
        if "preco_anterior" in cols:
            idx = cols.index("preco_anterior")
            ws.set_column(idx, idx, 14, num_fmt)
        if "dif_abs" in cols:
            idx = cols.index("dif_abs")
            ws.set_column(idx, idx, 12, num_fmt)
        if "dif_pct" in cols:
            idx = cols.index("dif_pct")
            ws.set_column(idx, idx, 12, pct_fmt)

        # cria duas abas extras: subiu e caiu
        df_subiu = df_comp[df_comp["status"] == "SUBIU"]
        df_caiu = df_comp[df_comp["status"] == "CAIU"]
        df_novo = df_comp[df_comp["status"] == "NOVO"]

        df_subiu.to_excel(writer, sheet_name="Subiu", index=False)
        df_caiu.to_excel(writer, sheet_name="Caiu", index=False)
        df_novo.to_excel(writer, sheet_name="Novos", index=False)

    print(f"✅ Comparativo salvo em: {caminho}")


if __name__ == "__main__":
    boletins = listar_boletins()
    if len(boletins) < 2:
        print("Só encontrei um boletim. Gere outro amanhã pra comparar 😉")
        raise SystemExit

    # boletim mais recente (hoje)
    caminho_hoje = boletins[0]
    # boletim anterior (ontem/último)
    caminho_ontem = boletins[1]

    print(f"Boletim de hoje:    {caminho_hoje}")
    print(f"Boletim anterior:   {caminho_ontem}")

    df_hoje = carregar_boletim(caminho_hoje)
    df_ontem = carregar_boletim(caminho_ontem)

    # faz a comparação
    df_comp, col_prod = comparar_boletins(df_hoje, df_ontem, n_dias_label="anterior")

    # salva
    saida = os.path.join(DOWNLOAD_DIR, "comparativo_ceasa.xlsx")
    salvar_comparativo(df_comp, col_prod, saida)
