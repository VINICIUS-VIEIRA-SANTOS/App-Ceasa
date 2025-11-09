# analise_ceasa.py
import os
import pandas as pd
from datetime import datetime

DOWNLOAD_DIR = "downloads"


# -------------------------------------------------
# utilidades de arquivo
# -------------------------------------------------
def listar_boletins(pasta=DOWNLOAD_DIR):
    pasta_abs = os.path.abspath(pasta)
    arquivos = [
        os.path.join(pasta_abs, f)
        for f in os.listdir(pasta_abs)
        if f.startswith("boletim_") and f.endswith(".xlsx")
    ]
    # mais recente primeiro
    arquivos.sort(key=os.path.getmtime, reverse=True)
    return arquivos


# -------------------------------------------------
# detecção e categorização
# -------------------------------------------------
def detectar_coluna_produto(df: pd.DataFrame) -> str:
    for nome in df.columns:
        low = str(nome).lower()
        if "prod" in low or "produto" in low or "espec" in low or "descr" in low:
            return nome
    return df.columns[0]


def categorizar_produto(nome: str) -> str:
    if not isinstance(nome, str):
        return "Outros"
    n = nome.lower()

    frutas_kw = [
        "banana", "mamão", "mamao", "maçã", "maca", "laranja", "tangerina",
        "uva", "melancia", "melão", "melao", "abacaxi", "pera", "goiaba",
        "limão", "limao", "maracujá", "maracuja", "acerola", "kiwi", "pitaya",
        "abacate", "caju"
    ]
    if any(k in n for k in frutas_kw):
        return "Frutas"

    peixes_kw = [
        "peixe", "pescada", "tilápia", "tilapia", "corvina", "cação", "cacao",
        "sardinha", "atum", "bacalhau", "merluza", "bagre", "camarão", "camarao"
    ]
    if any(k in n for k in peixes_kw):
        return "Peixes"

    cereais_kw = [
        "arroz", "feijão", "feijao", "milho", "soja", "trigo", "aveia", "fubá", "fuba"
    ]
    if any(k in n for k in cereais_kw):
        return "Cereais"

    return "Hortifruti"


def subcategorizar_hortifruti(nome: str) -> str:
    if not isinstance(nome, str):
        return "Outros"
    n = nome.lower()

    # folhas
    verdura_kw = [
        "alface", "rúcula", "rucula", "couve", "repolho", "agrião", "agriao",
        "espinafre", "almeirão", "almeirao", "acelga", "cebolinha", "coentro", "salsa"
    ]
    if any(k in n for k in verdura_kw):
        return "Verdura/Folha"

    # raízes
    raiz_kw = [
        "batata", "cenoura", "beterraba", "mandioca", "aipim", "inhame",
        "batata-doce", "batata doce", "cará", "cara"
    ]
    if any(k in n for k in raiz_kw):
        return "Raiz/Tubérculo"

    # frutos
    fruto_kw = [
        "tomate", "pimentão", "pimentao", "abobrinha", "abóbora", "abobora",
        "pepino", "chuchu", "berinjela", "vagem", "quiabo", "maxixe"
    ]
    if any(k in n for k in fruto_kw):
        return "Hortaliça de Fruto"

    return "Outros Hortifruti"


# -------------------------------------------------
# preços
# -------------------------------------------------
def escolher_coluna_preco(df: pd.DataFrame) -> str | None:
    # você pediu pra considerar MAX pra tudo
    for col in ["MAX", "M.C.", "MIN"]:
        if col in df.columns:
            return col
    return None


def corrigir_casas_decimais(serie: pd.Series) -> pd.Series:
    """
    Corrige só os valores que vieram 100x menores (0.0455 -> 4.55).
    Regras:
      - converte pra número
      - se 0 < valor < 1 → multiplica por 100
    """
    serie = pd.to_numeric(serie, errors="coerce")
    mask = (serie > 0) & (serie < 1)
    serie.loc[mask] = serie.loc[mask] * 100
    return serie


# -------------------------------------------------
# abas básicas
# -------------------------------------------------
def montar_abas_basicas(writer, df: pd.DataFrame, col_prod: str):
    workbook = writer.book
    header_fmt = workbook.add_format({"bold": True, "bg_color": "#D9D9D9"})
    num_fmt = workbook.add_format({"num_format": "#,##0.00"})

    # ITENS
    cols_itens = [c for c in [
        col_prod, "Categoria", "Subcategoria", "MIN", "M.C.", "MAX", "Data"
    ] if c in df.columns]
    df[cols_itens].to_excel(writer, sheet_name="Itens", index=False)
    ws_itens = writer.sheets["Itens"]
    for i, col in enumerate(cols_itens):
        ws_itens.write(0, i, col, header_fmt)
        ws_itens.set_column(i, i, 20)
    for col in ["MIN", "M.C.", "MAX"]:
        if col in cols_itens:
            idx = cols_itens.index(col)
            ws_itens.set_column(idx, idx, 12, num_fmt)

    # RESUMO
    resumo_df = pd.DataFrame()
    resumo_df.loc["Total de itens", "Valor"] = len(df)
    for col in ["MIN", "M.C.", "MAX"]:
        if col in df.columns and pd.api.types.is_numeric_dtype(df[col]):
            resumo_df.loc[f"Média {col}", "Valor"] = df[col].mean()
    resumo_df.to_excel(writer, sheet_name="Resumo")
    ws_resumo = writer.sheets["Resumo"]
    ws_resumo.write(0, 0, "Métrica", header_fmt)
    ws_resumo.write(0, 1, "Valor", header_fmt)
    ws_resumo.set_column(0, 0, 30)
    ws_resumo.set_column(1, 1, 20, num_fmt)

    # TOP 10
    col_preco = escolher_coluna_preco(df)
    if col_preco:
        top10 = (
            df[[col_prod, col_preco, "Categoria", "Subcategoria"]]
            .dropna(subset=[col_preco])
            .sort_values(col_preco, ascending=False)
            .head(10)
        )
        top10.to_excel(writer, sheet_name="Top10", index=False)
        ws_top = writer.sheets["Top10"]
        for i, col in enumerate(top10.columns):
            ws_top.write(0, i, col, header_fmt)
            ws_top.set_column(i, i, 25)
        ws_top.set_column(1, 1, 14, num_fmt)

        chart = workbook.add_chart({"type": "column"})
        chart.add_series({
            "name": col_preco,
            "categories": ["Top10", 1, 0, len(top10), 0],
            "values": ["Top10", 1, 1, len(top10), 1],
        })
        chart.set_title({"name": f"Top 10 por {col_preco}"})
        chart.set_x_axis({"name": col_prod})
        chart.set_y_axis({"name": col_preco})
        ws_top.insert_chart(1, 5, chart)


# -------------------------------------------------
# comparação com o boletim anterior
# -------------------------------------------------
def comparar_com_anterior(df_hoje: pd.DataFrame, df_antigo: pd.DataFrame):
    col_prod_hoje = detectar_coluna_produto(df_hoje)
    col_prod_ant = detectar_coluna_produto(df_antigo)

    col_preco_hoje = escolher_coluna_preco(df_hoje)
    col_preco_ant = escolher_coluna_preco(df_antigo)
    if not col_preco_hoje or not col_preco_ant:
        return None, None

    # corrige casas decimais de cada série separadamente
    df_hoje[col_preco_hoje] = corrigir_casas_decimais(df_hoje[col_preco_hoje])
    df_antigo[col_preco_ant] = corrigir_casas_decimais(df_antigo[col_preco_ant])

    # chave de junção
    df_hoje["_key_prod"] = df_hoje[col_prod_hoje].astype(str).str.strip().str.lower()
    df_antigo["_key_prod"] = df_antigo[col_prod_ant].astype(str).str.strip().str.lower()

    df_join = pd.merge(
        df_hoje,
        df_antigo[["_key_prod", col_preco_ant]].rename(
            columns={col_preco_ant: "preco_anterior"}
        ),
        on="_key_prod",
        how="left",
    )

    df_join = df_join.rename(columns={col_preco_hoje: "preco_hoje"})
    df_join["dif_abs"] = df_join["preco_hoje"] - df_join["preco_anterior"]
    df_join["dif_pct"] = (df_join["dif_abs"] / df_join["preco_anterior"]) * 100

    def status(row):
        old = row["preco_anterior"]
        new = row["preco_hoje"]
        if pd.isna(old):
            return "NOVO"
        if new > old:
            return "SUBIU"
        if new < old:
            return "CAIU"
        return "IGUAL"

    df_join["status"] = df_join.apply(status, axis=1)
    df_join["Produto"] = df_join[col_prod_hoje]

    return df_join, col_prod_hoje


# -------------------------------------------------
# plano de venda / markup
# -------------------------------------------------
def classificar_classe(categoria: str, subcategoria: str, preco_max: float) -> str:
    # VERDE: durável ou barato
    if categoria == "Cereais":
        return "Verde"
    if subcategoria == "Raiz/Tubérculo":
        return "Verde"
    if preco_max is not None and preco_max <= 6:
        return "Verde"

    # VERMELHA: sensível/caro
    if categoria == "Peixes":
        return "Vermelha"
    if preco_max is not None and preco_max > 10:
        return "Vermelha"

    # resto
    return "Amarela"


def adicionar_aba_plano_venda(writer, df_base: pd.DataFrame, df_comp: pd.DataFrame | None, col_prod: str):
    wb = writer.book
    ws = wb.add_worksheet("Plano_Venda")
    header = wb.add_format({"bold": True, "bg_color": "#D9D9D9"})
    money = wb.add_format({"num_format": "#,##0.00"})
    pct = wb.add_format({"num_format": "0.00%"})

    markup_por_classe = {
        "Verde": 0.30,
        "Amarela": 0.35,
        "Vermelha": 0.50,
    }

    col_preco = escolher_coluna_preco(df_base)
    if col_preco is None:
        col_preco = "MAX"

    # montar dicionário de alertas a partir do comparativo
    alerta_por_prod = {}
    if df_comp is not None:
        for _, r in df_comp.iterrows():
            key = str(r["Produto"]).strip().lower()
            st = r["status"]
            if st == "SUBIU":
                alerta_por_prod[key] = "Atenção"
            elif st == "CAIU":
                alerta_por_prod[key] = "Promo"
            else:
                alerta_por_prod[key] = "Venda normal"

    colunas = [
        "Produto", "Categoria", "Subcategoria", "Classe",
        "Quantidade_sugerida", "Custo_base", "Markup_%", "Valor_venda", "Alerta"
    ]
    for i, c in enumerate(colunas):
        ws.write(0, i, c, header)

    row = 1
    for _, r in df_base.iterrows():
        produto = r[col_prod]
        cat = r.get("Categoria", "")
        subcat = r.get("Subcategoria", "")
        preco_base = r.get(col_preco, 0)
        try:
            preco_base = float(preco_base)
        except Exception:
            preco_base = 0.0

        classe = classificar_classe(cat, subcat, preco_base)
        markup = markup_por_classe.get(classe, 0.30)
        valor_venda = preco_base * (1 + markup)
        qtd = 20

        alerta = "Venda normal"
        key = str(produto).strip().lower()
        if key in alerta_por_prod:
            alerta = alerta_por_prod[key]

        ws.write(row, 0, produto)
        ws.write(row, 1, cat)
        ws.write(row, 2, subcat)
        ws.write(row, 3, classe)
        ws.write_number(row, 4, qtd)
        ws.write_number(row, 5, preco_base, money)
        ws.write_number(row, 6, markup, pct)
        ws.write_number(row, 7, valor_venda, money)
        ws.write(row, 8, alerta)

        row += 1

    ws.set_column(0, 0, 30)
    ws.set_column(1, 3, 18)
    ws.set_column(4, 4, 10)
    ws.set_column(5, 7, 14)
    ws.set_column(8, 8, 15)


# -------------------------------------------------
# montar tudo
# -------------------------------------------------
def montar_relatorio_unificado(df_hoje: pd.DataFrame, df_antigo: pd.DataFrame | None, caminho_saida: str):
    os.makedirs(os.path.dirname(caminho_saida), exist_ok=True)

    col_prod = detectar_coluna_produto(df_hoje)

    # cria categorias
    df_hoje["Categoria"] = df_hoje[col_prod].apply(categorizar_produto)
    df_hoje["Subcategoria"] = df_hoje.apply(
        lambda r: subcategorizar_hortifruti(r[col_prod]) if r["Categoria"] == "Hortifruti" else "",
        axis=1,
    )

    with pd.ExcelWriter(caminho_saida, engine="xlsxwriter") as writer:
        # abas principais
        montar_abas_basicas(writer, df_hoje, col_prod)

        df_comp = None
        if df_antigo is not None:
            df_comp, _ = comparar_com_anterior(df_hoje.copy(), df_antigo.copy())
            if df_comp is not None:
                df_comp.to_excel(writer, sheet_name="Comparativo", index=False)
                df_comp[df_comp["status"] == "SUBIU"].to_excel(writer, sheet_name="Subiu", index=False)
                df_comp[df_comp["status"] == "CAIU"].to_excel(writer, sheet_name="Caiu", index=False)
                df_comp[df_comp["status"] == "NOVO"].to_excel(writer, sheet_name="Novos", index=False)

        # plano de venda (usa comparativo se tiver)
        adicionar_aba_plano_venda(writer, df_hoje, df_comp, col_prod)

    print(f"✅ Relatório unificado salvo em: {caminho_saida}")


# -------------------------------------------------
# main
# -------------------------------------------------
if __name__ == "__main__":
    boletins = listar_boletins()
    if not boletins:
        raise SystemExit("Nenhum boletim encontrado em downloads/")

    caminho_hoje = boletins[0]
    df_hoje = pd.read_excel(caminho_hoje, sheet_name="Boletim")

    df_antigo = None
    if len(boletins) > 1:
        df_antigo = pd.read_excel(boletins[1], sheet_name="Boletim")

    # se quiser evitar erro de arquivo aberto, pode colocar timestamp:
    # data_str = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    # saida = os.path.join(DOWNLOAD_DIR, f"relatorio_ceasa_{data_str}.xlsx")
    saida = os.path.join(DOWNLOAD_DIR, "relatorio_ceasa.xlsx")

    montar_relatorio_unificado(df_hoje, df_antigo, saida)
