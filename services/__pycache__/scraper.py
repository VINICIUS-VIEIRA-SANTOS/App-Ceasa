# scraper.py
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select, WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import pandas as pd
import time
import os
import io
from datetime import datetime


def achar_select_data(driver, timeout=15):
    tentativas_xpath = [
        "//select[@id='id_sc_field_data']",
        "//select[contains(@id, 'id_sc_field_data')]",
        "//select[contains(@name, 'data')]",
        "//select[contains(@id, 'data')]",
    ]
    fim = time.time() + timeout
    while time.time() < fim:
        for xp in tentativas_xpath:
            elems = driver.find_elements(By.XPATH, xp)
            if elems:
                return elems[0]
        time.sleep(0.5)
    raise Exception("Não consegui encontrar o campo de DATA na página.")


def normalizar_preco_br(df: pd.DataFrame) -> pd.DataFrame:
    colunas_preco = ["MIN", "M.C.", "MAX"]
    for col in colunas_preco:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
            # se parece estar 100x maior (455 em vez de 4,55), divide
            if df[col].max() and df[col].max() > 50:
                df[col] = df[col] / 100
    return df


def salvar_excel_formatado(df: pd.DataFrame, path: str):
    os.makedirs(os.path.dirname(path), exist_ok=True)

    with pd.ExcelWriter(path, engine="xlsxwriter") as writer:
        df.to_excel(writer, index=False, sheet_name="Boletim")
        workbook = writer.book
        ws = writer.sheets["Boletim"]

        header_format = workbook.add_format(
            {"bold": True, "bg_color": "#D9D9D9", "border": 1}
        )
        number_format = workbook.add_format({"num_format": "#,##0.00"})

        # cabeçalho
        for col_num, value in enumerate(df.columns.values):
            ws.write(0, col_num, str(value), header_format)

        # filtro
        ws.autofilter(0, 0, len(df), len(df.columns) - 1)

        # largura
        for i, col in enumerate(df.columns):
            col_str = str(col)
            try:
                max_len = max(
                    [len(str(s)) for s in df[col].astype(str).tolist()] + [len(col_str)]
                )
            except ValueError:
                max_len = len(col_str)
            max_len = min(max_len, 40)
            if pd.api.types.is_numeric_dtype(df[col]):
                ws.set_column(i, i, max_len + 2, number_format)
            else:
                ws.set_column(i, i, max_len + 2)

    print(f"📘 Excel salvo em: {path}")


def extrair_boletim(download_dir="downloads"):
    url = "http://200.198.51.71/detec/filtro_boletim_es/filtro_boletim_es.php"

    os.makedirs(download_dir, exist_ok=True)
    abs_download_dir = os.path.abspath(download_dir)

    options = webdriver.ChromeOptions()
    options.add_argument("--start-maximized")
    options.add_argument("--disable-infobars")
    options.add_argument("--disable-extensions")

    prefs = {
        "download.default_directory": abs_download_dir,
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "plugins.always_open_pdf_externally": True,
    }
    options.add_experimental_option("prefs", prefs)

    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()), options=options
    )
    wait = WebDriverWait(driver, 20)

    print("🌐 Acessando site do CEASA...")
    driver.get(url)

    # mercado
    select_mercado = wait.until(
        EC.presence_of_element_located((By.ID, "id_sc_field_mercado"))
    )
    Select(select_mercado).select_by_visible_text("CEASA GRANDE VITÓRIA")
    print("✅ Mercado selecionado")

    time.sleep(2)

    # data
    print("⏳ Procurando o campo de data (pode demorar alguns segundos)...")
    select_data = achar_select_data(driver, timeout=15)
    opcoes = select_data.find_elements(By.TAG_NAME, "option")

    data_texto = "Data não encontrada"
    if len(opcoes) > 1:
        opcoes[1].click()
        data_texto = opcoes[1].text.strip()
    elif len(opcoes) == 1:
        opcoes[0].click()
        data_texto = opcoes[0].text.strip()
    print(f"✅ Data selecionada: {data_texto}")

    # ok
    botao_ok = wait.until(
        EC.element_to_be_clickable(
            (By.XPATH, "//span[@class='btn-label' and normalize-space(text())='Ok']")
        )
    )
    botao_ok.click()
    print("✅ Botão 'Ok' clicado!")

    # tabela
    time.sleep(5)
    print("📄 Extraindo tabela da página...")
    tabelas = driver.find_elements(By.XPATH, "//table[contains(@class, 'scGridTabela')]")

    dfs = []
    for tabela in tabelas:
        html_tabela = tabela.get_attribute("outerHTML")
        try:
            df = pd.read_html(io.StringIO(html_tabela), header=0)[0]
            dfs.append(df)
        except ValueError:
            pass

    driver.quit()

    if not dfs:
        print("❌ Nenhuma tabela encontrada!")
        return None

    df_final = pd.concat(dfs, ignore_index=True)
    df_final = normalizar_preco_br(df_final)
    df_final["Data"] = data_texto

    # CSV fixo (pode sobrescrever)
    csv_path = os.path.join(abs_download_dir, "boletim_ceasa.csv")
    df_final.to_csv(csv_path, index=False, encoding="utf-8-sig")
    print(f"💾 Dados salvos em '{csv_path}' ({len(df_final)} linhas)")

    # nome único: data do boletim + horário da geração
    try:
        data_dt = datetime.strptime(data_texto, "%d/%m/%Y").date()
        base_data = data_dt.isoformat()
    except Exception:
        base_data = datetime.now().strftime("%Y-%m-%d")

    hora = datetime.now().strftime("%H-%M-%S")
    xlsx_path = os.path.join(
        abs_download_dir, f"boletim_{base_data}_{hora}.xlsx"
    )

    salvar_excel_formatado(df_final, xlsx_path)

    return xlsx_path


if __name__ == "__main__":
    extrair_boletim()
