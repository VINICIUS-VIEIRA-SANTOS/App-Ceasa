from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from database import SessionLocal
from models import Cliente
from schemas import ClienteCreate, ClienteUpdate, ClienteResponse
from typing import List

router = APIRouter(prefix="/clientes", tags=["Clientes"])


# Dependência para obter conexão com o banco
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Criar cliente
@router.post("/", response_model=ClienteResponse)
def criar_cliente(cliente: ClienteCreate, db: Session = Depends(get_db)):
    cliente_existente = db.query(Cliente).filter(Cliente.nome == cliente.nome).first()
    if cliente_existente:
        raise HTTPException(status_code=400, detail="Cliente já cadastrado")

    novo_cliente = Cliente(**cliente.dict())
    db.add(novo_cliente)
    db.commit()
    db.refresh(novo_cliente)
    return novo_cliente


# Listar todos os clientes
@router.get("/", response_model=List[ClienteResponse])
def listar_clientes(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    clientes = db.query(Cliente).offset(skip).limit(limit).all()
    return clientes


# Buscar cliente por ID
@router.get("/{cliente_id}", response_model=ClienteResponse)
def obter_cliente(cliente_id: int, db: Session = Depends(get_db)):
    cliente = db.query(Cliente).filter(Cliente.id == cliente_id).first()
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente não encontrado")
    return cliente


# Atualizar cliente
@router.put("/{cliente_id}", response_model=ClienteResponse)
def atualizar_cliente(cliente_id: int, cliente: ClienteUpdate, db: Session = Depends(get_db)):
    cliente_db = db.query(Cliente).filter(Cliente.id == cliente_id).first()
    if not cliente_db:
        raise HTTPException(status_code=404, detail="Cliente não encontrado")

    for chave, valor in cliente.dict(exclude_unset=True).items():
        setattr(cliente_db, chave, valor)

    db.commit()
    db.refresh(cliente_db)
    return cliente_db


# Excluir cliente
@router.delete("/{cliente_id}")
def excluir_cliente(cliente_id: int, db: Session = Depends(get_db)):
    cliente = db.query(Cliente).filter(Cliente.id == cliente_id).first()
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente não encontrado")

    db.delete(cliente)
    db.commit()
    return {"mensagem": f"Cliente '{cliente.nome}' excluído com sucesso."}
