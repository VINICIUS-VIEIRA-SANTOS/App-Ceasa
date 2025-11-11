from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime
from database import SessionLocal
from models import Venda, ItemVenda, Produto, Cliente, Estoque
from schemas import VendaCreate, VendaResponse
from sqlalchemy import func

router = APIRouter(prefix="/vendas", tags=["Vendas"])


# Sessão do banco
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# --- Função auxiliar: atualiza saldo do produto ---
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


# --- Criar venda ---
@router.post("/", response_model=VendaResponse)
def criar_venda(venda: VendaCreate, db: Session = Depends(get_db)):
    nova_venda = Venda(
        id_cliente=venda.cliente_id,
        id_usuario=venda.usuario_id,
        forma_pagamento=venda.forma_pagamento,
        data_venda=datetime.now(),
        valor_total=0
    )
    db.add(nova_venda)
    db.commit()
    db.refresh(nova_venda)

    total = 0

    for item in venda.itens:
        produto = db.query(Produto).filter(Produto.id == item.produto_id).first()
        if not produto:
            raise HTTPException(status_code=404, detail=f"Produto ID {item.produto_id} não encontrado.")

        # Validação de estoque
        if produto.quantidade_disponivel < item.quantidade:
            raise HTTPException(
                status_code=400,
                detail=f"Estoque insuficiente para {produto.nome}. Saldo atual: {produto.quantidade_disponivel}"
            )

        subtotal = item.quantidade * item.preco_unitario
        total += subtotal

        # Criar item da venda
        item_venda = ItemVenda(
            id_venda=nova_venda.id,
            id_produto=item.produto_id,
            quantidade=item.quantidade,
            preco_unitario=item.preco_unitario
        )
        db.add(item_venda)

        # Registrar saída no estoque
        saida = Estoque(
            id_produto=item.produto_id,
            quantidade=item.quantidade,
            tipo="saida",
            origem="Venda",
            observacao=f"Venda ID {nova_venda.id}",
            data_movimento=datetime.now()
        )
        db.add(saida)

    # Atualizar valor total
    nova_venda.valor_total = total
    db.commit()

    # Atualizar saldo dos produtos
    for item in venda.itens:
        atualizar_saldo_produto(db, item.produto_id)

    # Atualizar contador de pedidos do cliente
    if nova_venda.id_cliente:
        cliente = db.query(Cliente).filter(Cliente.id == nova_venda.id_cliente).first()
        if cliente:
            cliente.pedidos = (cliente.pedidos or 0) + 1
            db.commit()

    db.refresh(nova_venda)
    return nova_venda


# --- Listar vendas ---
@router.get("/", response_model=list[VendaResponse])
def listar_vendas(db: Session = Depends(get_db)):
    return db.query(Venda).order_by(Venda.data_venda.desc()).all()


# --- Obter venda por ID ---
@router.get("/{venda_id}", response_model=VendaResponse)
def obter_venda(venda_id: int, db: Session = Depends(get_db)):
    venda = db.query(Venda).filter(Venda.id == venda_id).first()
    if not venda:
        raise HTTPException(status_code=404, detail="Venda não encontrada")
    return venda


# --- Excluir venda ---
@router.delete("/{venda_id}")
def deletar_venda(venda_id: int, db: Session = Depends(get_db)):
    venda = db.query(Venda).filter(Venda.id == venda_id).first()
    if not venda:
        raise HTTPException(status_code=404, detail="Venda não encontrada")

    # Reverter estoque
    itens = db.query(ItemVenda).filter(ItemVenda.id_venda == venda_id).all()
    for item in itens:
        entrada = Estoque(
            id_produto=item.id_produto,
            quantidade=item.quantidade,
            tipo="entrada",
            origem="Cancelamento de venda",
            observacao=f"Venda ID {venda.id} cancelada",
            data_movimento=datetime.now()
        )
        db.add(entrada)
        atualizar_saldo_produto(db, item.id_produto)

    db.delete(venda)
    db.commit()
    return {"mensagem": "Venda excluída e estoque restaurado com sucesso"}

