from pydantic import BaseModel
from datetime import datetime, date
from typing import Optional, List
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
# ============================================================
# USUÁRIOS
# ============================================================

class UsuarioBase(BaseModel):
    nome: str
    email: str
    cargo: Optional[str] = None
    aniversario: Optional[str] = None


class UsuarioCreate(UsuarioBase):
    senha: str


class UsuarioResponse(UsuarioBase):
    id: int
    data_cadastro: datetime

    class Config:
        from_attributes = True


# ============================================================
# CLIENTES
# ============================================================

class ClienteBase(BaseModel):
    nome: str
    telefone: Optional[str] = None
    endereco: Optional[str] = None
    cidade: Optional[str] = None
    tipo: Optional[str] = None
    aniversario: Optional[str] = None


class ClienteCreate(ClienteBase):
    pass


class ClienteUpdate(BaseModel):
    telefone: Optional[str] = None
    endereco: Optional[str] = None
    cidade: Optional[str] = None
    tipo: Optional[str] = None


class ClienteResponse(ClienteBase):
    id: int
    pedidos: int
    data_cadastro: datetime

    class Config:
        from_attributes = True


# ============================================================
# PRODUTOS
# ============================================================

class ProdutoBase(BaseModel):
    nome: str
    categoria: Optional[str] = None
    unidade: Optional[str] = None
    preco_compra: Optional[float] = 0
    preco_venda: Optional[float] = 0
    estoque_minimo: Optional[int] = 0


class ProdutoCreate(ProdutoBase):
    pass


class ProdutoUpdate(BaseModel):
    preco_venda: Optional[float] = None
    estoque_minimo: Optional[int] = None


class ProdutoResponse(ProdutoBase):
    id: int
    data_cadastro: datetime

    class Config:
        from_attributes = True


# ============================================================
# ESTOQUE
# ============================================================

class EstoqueBase(BaseModel):
    id_produto: int
    quantidade: int
    tipo: Optional[str] = None
    origem: Optional[str] = None
    observacao: Optional[str] = None


class EstoqueCreate(EstoqueBase):
    pass


class EstoqueResponse(EstoqueBase):
    id: int
    data_movimento: datetime

    class Config:
        from_attributes = True


# ============================================================
# VENDAS E ITENS DE VENDA
# ============================================================

class ItemVendaBase(BaseModel):
    id_produto: int
    quantidade: int
    preco_unitario: float


class ItemVendaCreate(ItemVendaBase):
    pass


class ItemVendaResponse(ItemVendaBase):
    id: int

    class Config:
        from_attributes = True


class VendaBase(BaseModel):
    id_cliente: Optional[int] = None
    id_usuario: Optional[int] = None
    forma_pagamento: Optional[str] = None
    status: Optional[str] = "Concluída"


class VendaCreate(VendaBase):
    itens: List[ItemVendaCreate]


class VendaResponse(VendaBase):
    id: int
    data_venda: datetime
    valor_total: float
    itens: List[ItemVendaResponse] = []

    class Config:
        from_attributes = True


# ============================================================
# METAS
# ============================================================

class MetaBase(BaseModel):
    descricao: str
    valor_meta: float
    data_inicio: date
    data_fim: date
    id_usuario: int


class MetaCreate(MetaBase):
    pass


class MetaResponse(MetaBase):
    id: int

    class Config:
        from_attributes = True


# ============================================================
# BOLETINS CEASA
# ============================================================

class BoletimCeasaBase(BaseModel):
    data_boletim: date
    produto: str
    preco_min: Optional[float] = None
    preco_max: Optional[float] = None
    preco_medio: Optional[float] = None
    origem: Optional[str] = None


class BoletimCeasaCreate(BoletimCeasaBase):
    pass


class BoletimCeasaResponse(BoletimCeasaBase):
    id: int
    criado_em: datetime

    class Config:
        from_attributes = True

# === USUARIOS ===
class UsuarioBase(BaseModel):
    nome: str
    email: str
    cargo: Optional[str] = None
    aniversario: Optional[str] = None

class UsuarioCreate(UsuarioBase):
    senha: str

class UsuarioUpdate(BaseModel):
    nome: Optional[str]
    email: Optional[str]
    cargo: Optional[str]
    aniversario: Optional[str]

class UsuarioResponse(UsuarioBase):
    id: int
    data_cadastro: datetime
    class Config:
        from_attributes = True


# === ESTOQUE ===
class EstoqueBase(BaseModel):
    id_produto: int
    quantidade: int
    tipo: str
    origem: Optional[str] = None
    observacao: Optional[str] = None

class EstoqueCreate(EstoqueBase):
    pass

class EstoqueResponse(EstoqueBase):
    id: int
    data_movimento: datetime
    class Config:
        from_attributes = True

# === SALDO DE ESTOQUE ===
class SaldoEstoqueResponse(BaseModel):
    id_produto: int
    produto: str
    categoria: str
    unidade: str
    total_entradas: int
    total_saidas: int
    saldo_atual: int
