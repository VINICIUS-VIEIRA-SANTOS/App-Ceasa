from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime
from database import SessionLocal
from models import Estoque, Produto
from schemas import EstoqueCreate, EstoqueResponse

router = APIRouter(prefix="/estoque", tags=["Estoque"])


# --- Sessão do banco ---
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# --- Função para recalcular e atualizar o saldo do produto ---
def atualizar_saldo_produto(db: Session, id_produto: int):
    entradas = db.query(func.sum(Estoque.quantidade)).filter(
        Estoque.id_produto == id_produto, Estoque.tipo == "entrada"
    ).scalar() or 0

    saidas = db.query(func.sum(Estoque.quantidade)).filter(
        Estoque.id_produto == id_produto, Estoque.tipo == "saida"
    ).scalar() or 0

    saldo = entradas - saidas

    produto = db.query(Produto).filter(Produto.id == id_produto).first()
    if produto:
        produto.quantidade_disponivel = saldo
        db.commit()


# --- Registrar entrada ou saída ---
@router.post("/", response_model=EstoqueResponse)
def registrar_movimentacao(movimento: EstoqueCreate, db: Session = Depends(get_db)):
    produto = db.query(Produto).filter(Produto.id == movimento.id_produto).first()
    if not produto:
        raise HTTPException(status_code=404, detail="Produto não encontrado.")

    # --- Validação de saída ---
    if movimento.tipo.lower() == "saida":
        if produto.quantidade_disponivel < movimento.quantidade:
            raise HTTPException(
                status_code=400,
                detail=f"Estoque insuficiente. Saldo atual de {produto.nome}: {produto.quantidade_disponivel}."
            )

    # --- Registrar movimento ---
    nova_mov = Estoque(
        id_produto=movimento.id_produto,
        quantidade=movimento.quantidade,
        tipo=movimento.tipo.lower(),
        origem=movimento.origem,
        observacao=movimento.observacao,
        data_movimento=datetime.now()
    )
    db.add(nova_mov)
    db.commit()

    # --- Atualiza saldo do produto ---
    atualizar_saldo_produto(db, movimento.id_produto)
    db.refresh(nova_mov)

    return nova_mov


# --- Listar todas as movimentações ---
@router.get("/", response_model=list[EstoqueResponse])
def listar_movimentacoes(db: Session = Depends(get_db)):
    return db.query(Estoque).order_by(Estoque.data_movimento.desc()).all()


# --- Listar movimentações por produto ---
@router.get("/produto/{id_produto}", response_model=list[EstoqueResponse])
def listar_por_produto(id_produto: int, db: Session = Depends(get_db)):
    movimentos = db.query(Estoque).filter(Estoque.id_produto == id_produto).all()
    if not movimentos:
        raise HTTPException(status_code=404, detail="Nenhuma movimentação encontrada para este produto.")
    return movimentos


# --- Excluir movimentação e atualizar saldo ---
@router.delete("/{movimento_id}")
def excluir_movimentacao(movimento_id: int, db: Session = Depends(get_db)):
    mov = db.query(Estoque).filter(Estoque.id == movimento_id).first()
    if not mov:
        raise HTTPException(status_code=404, detail="Movimentação não encontrada.")

    id_produto = mov.id_produto
    db.delete(mov)
    db.commit()

    # Recalcula saldo após exclusão
    atualizar_saldo_produto(db, id_produto)
    return {"mensagem": "Movimentação excluída e saldo atualizado com sucesso."}


# --- Listar saldo atual de todos os produtos ---
@router.get("/saldo")
def saldo_estoque(db: Session = Depends(get_db)):
    resultados = (
        db.query(
            Produto.id.label("id_produto"),
            Produto.nome.label("produto"),
            Produto.categoria,
            Produto.unidade,
            Produto.quantidade_disponivel,
        ).all()
    )

    if not resultados:
        raise HTTPException(status_code=404, detail="Nenhum produto encontrado.")

    return [
        {
            "id_produto": r.id_produto,
            "produto": r.produto,
            "categoria": r.categoria,
            "unidade": r.unidade,
            "saldo_atual": int(r.quantidade_disponivel or 0),
        }
        for r in resultados
    ]
