from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from routes import produtos, clientes, vendas, relatorios, usuarios, estoque, auth

import time

from database import SessionLocal
from services.atualizar_ceasa import atualizar_dados_ceasa
from routes import produtos, clientes

# ======================================================
# Inicialização do App
# ======================================================

app = FastAPI(
    title="CEASA App API",
    version="1.0",
    description="API do Sistema CEASA - Controle de produtos, clientes e boletins automáticos."
)


# ======================================================
# Conexão com o Banco de Dados
# ======================================================

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ======================================================
# Rotas principais
# ======================================================

@app.get("/")
def home():
    hora = datetime.now().strftime("%H:%M:%S")
    return {
        "status": "ok",
        "mensagem": "API CEASA rodando com sucesso.",
        "hora_servidor": hora
    }


@app.get("/atualizar-boletim/")
def atualizar_boletim(db: Session = Depends(get_db)):
    """
    Executa o scraper CEASA, atualiza produtos e registra histórico de preços.
    """
    resultado = atualizar_dados_ceasa(db)
    return resultado


# ======================================================
# Função agendada automaticamente
# ======================================================

def tarefa_agendada():
    print(f"[{time.strftime('%H:%M:%S')}] Executando atualização CEASA automática...")
    db = SessionLocal()
    try:
        resultado = atualizar_dados_ceasa(db)
        print(f"Atualização automática concluída: {resultado}")
    except Exception as e:
        print(f"Erro na atualização automática: {e}")
    finally:
        db.close()


# ======================================================
# Agendador (APScheduler)
# ======================================================

scheduler = None


def iniciar_agendador():
    global scheduler
    if scheduler is None:
        scheduler = BackgroundScheduler()
        scheduler.add_job(tarefa_agendada, "cron", hour=6, minute=0)
        scheduler.start()
        print("Agendador de atualização automática iniciado (06:00 diariamente).")


@app.on_event("startup")
def startup_event():
    iniciar_agendador()


# ======================================================
# Registro das rotas de módulos
# ======================================================

app.include_router(produtos.router)
app.include_router(clientes.router)
app.include_router(vendas.router)
app.include_router(relatorios.router)
app.include_router(usuarios.router)
app.include_router(estoque.router)
app.include_router(auth.router)



# ======================================================
# Fim do arquivo main.py
# ======================================================
