from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from database import SessionLocal
from models import Produto
from schemas import ProdutoCreate, ProdutoUpdate, ProdutoResponse
from typing import List

router = APIRouter(prefix="/produtos", tags=["Produtos"])

# Dependência para obter conexão com o banco
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# =======================
# Criar produto
# =======================
@router.post("/", response_model=ProdutoResponse)
def criar_produto(produto: ProdutoCreate, db: Session = Depends(get_db)):
    produto_existente = db.query(Produto).filter(Produto.nome == produto.nome).first()
    if produto_existente:
        raise HTTPException(status_code=400, detail="Produto já cadastrado")

    novo_produto = Produto(**produto.dict())
    db.add(novo_produto)
    db.commit()
    db.refresh(novo_produto)
    return novo_produto

# =======================
# Listar todos os produtos
# =======================
@router.get("/", response_model=List[ProdutoResponse])
def listar_produtos(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    produtos = db.query(Produto).offset(skip).limit(limit).all()
    return produtos

# =======================
# Buscar produto por ID
# =======================
@router.get("/{produto_id}", response_model=ProdutoResponse)
def obter_produto(produto_id: int, db: Session = Depends(get_db)):
    produto = db.query(Produto).filter(Produto.id == produto_id).first()
    if not produto:
        raise HTTPException(status_code=404, detail="Produto não encontrado")
    return produto

# =======================
# Atualizar produto
# =======================
@router.put("/{produto_id}", response_model=ProdutoResponse)
def atualizar_produto(produto_id: int, produto: ProdutoUpdate, db: Session = Depends(get_db)):
    produto_db = db.query(Produto).filter(Produto.id == produto_id).first()
    if not produto_db:
        raise HTTPException(status_code=404, detail="Produto não encontrado")

    for chave, valor in produto.dict(exclude_unset=True).items():
        setattr(produto_db, chave, valor)

    db.commit()
    db.refresh(produto_db)
    return produto_db

# =======================
# Excluir produto
# =======================
@router.delete("/{produto_id}")
def excluir_produto(produto_id: int, db: Session = Depends(get_db)):
    produto = db.query(Produto).filter(Produto.id == produto_id).first()
    if not produto:
        raise HTTPException(status_code=404, detail="Produto não encontrado")

    db.delete(produto)
    db.commit()
    return {"mensagem": f"Produto '{produto.nome}' excluído com sucesso."}
