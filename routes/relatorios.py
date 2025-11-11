from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import SessionLocal
from models import Venda, Produto, ItemVenda
from datetime import datetime, timedelta
from sqlalchemy import func

router = APIRouter(prefix="/relatorios", tags=["Relatórios"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/vendas-por-periodo")
def vendas_por_periodo(dias: int = 7, db: Session = Depends(get_db)):
    """Total de vendas nos últimos X dias"""
    data_limite = datetime.utcnow() - timedelta(days=dias)
    total = db.query(func.sum(Venda.total)).filter(Venda.data_venda >= data_limite).scalar()
    return {"periodo": f"Últimos {dias} dias", "total_vendas": total or 0}


@router.get("/top-produtos")
def produtos_mais_vendidos(db: Session = Depends(get_db)):
    """Top 5 produtos mais vendidos"""
    resultado = (
        db.query(
            Produto.nome,
            func.sum(ItemVenda.quantidade).label("total_vendido")
        )
        .join(ItemVenda)
        .group_by(Produto.nome)
        .order_by(func.sum(ItemVenda.quantidade).desc())
        .limit(5)
        .all()
    )
    return [{"produto": r[0], "quantidade_vendida": r[1]} for r in resultado]


@router.get("/estoque-baixo")
def estoque_baixo(db: Session = Depends(get_db)):
    """Lista produtos com estoque abaixo de 10"""
    produtos = db.query(Produto).filter(Produto.estoque < 10).all()
    return produtos
