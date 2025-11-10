from pydantic import BaseModel
from typing import Optional
from datetime import datetime, date


# ======================================================
# ESQUEMAS DE PRODUTOS
# ======================================================

class ProdutoBase(BaseModel):
    nome: str
    categoria: Optional[str] = None
    unidade: Optional[str] = None
    preco_compra: Optional[float] = 0.0
    preco_venda: Optional[float] = 0.0
    estoque_minimo: Optional[int] = 0


class ProdutoCreate(ProdutoBase):
    pass


class ProdutoUpdate(ProdutoBase):
    pass


class ProdutoResponse(ProdutoBase):
    id: int
    data_cadastro: datetime

    model_config = {"from_attributes": True}


# ======================================================
# ESQUEMAS DE CLIENTES
# ======================================================

class ClienteBase(BaseModel):
    nome: str
    telefone: Optional[str] = None
    email: Optional[str] = None
    endereco: Optional[str] = None
    data_aniversario: Optional[date] = None  # Apenas dia e mês são usados
    pedidos: Optional[int] = 0


class ClienteCreate(ClienteBase):
    pass


class ClienteUpdate(ClienteBase):
    pass


class ClienteResponse(ClienteBase):
    id: int
    data_cadastro: datetime

    model_config = {"from_attributes": True}
