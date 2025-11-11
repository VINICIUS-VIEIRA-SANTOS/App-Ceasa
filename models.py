from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, DECIMAL, Date, CheckConstraint
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base


# =======================
# TABELA: USUARIOS
# =======================
class Usuario(Base):
    __tablename__ = "usuarios"

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String(100), nullable=False)
    email = Column(String(150), unique=True, nullable=False)
    senha = Column(String(255), nullable=False)
    cargo = Column(String(50))
    aniversario = Column(String(5))
    data_cadastro = Column(DateTime, default=datetime.now)

    vendas = relationship("Venda", back_populates="usuario")


# =======================
# TABELA: CLIENTES
# =======================
class Cliente(Base):
    __tablename__ = "clientes"

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String(100), nullable=False)
    telefone = Column(String(20))
    endereco = Column(String(200))
    cidade = Column(String(100))
    tipo = Column(String(50))
    aniversario = Column(String(5))
    pedidos = Column(Integer, default=0)
    data_cadastro = Column(DateTime, default=datetime.now)

    vendas = relationship("Venda", back_populates="cliente")


# =======================
# TABELA: PRODUTOS
# =======================
class Produto(Base):
    __tablename__ = "produtos"

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String(100), nullable=False)
    categoria = Column(String(50))
    unidade = Column(String(20))
    preco_compra = Column(DECIMAL(10, 2))
    preco_venda = Column(DECIMAL(10, 2))
    quantidade_disponivel = Column(Integer, default=0)
    estoque_minimo = Column(Integer, default=0)
    data_cadastro = Column(DateTime, default=datetime.now)

    itens = relationship("ItemVenda", back_populates="produto")


# =======================
# TABELA: ESTOQUE
# =======================
class Estoque(Base):
    __tablename__ = "estoque"

    id = Column(Integer, primary_key=True, index=True)
    id_produto = Column(Integer, ForeignKey("produtos.id"), nullable=False)
    quantidade = Column(Integer, nullable=False)
    tipo = Column(String(20))
    origem = Column(String(100))
    data_movimento = Column(DateTime, default=datetime.now)
    observacao = Column(String(200))


# =======================
# TABELA: VENDAS
# =======================
class Venda(Base):
    __tablename__ = "vendas"

    id = Column(Integer, primary_key=True, index=True)
    id_cliente = Column(Integer, ForeignKey("clientes.id"))
    id_usuario = Column(Integer, ForeignKey("usuarios.id"))
    data_venda = Column(DateTime, default=datetime.now)
    valor_total = Column(DECIMAL(10, 2))
    forma_pagamento = Column(String(50))
    status = Column(String(20), default="Concluída")

    cliente = relationship("Cliente", back_populates="vendas")
    usuario = relationship("Usuario", back_populates="vendas")
    itens = relationship("ItemVenda", back_populates="venda")


# =======================
# TABELA: ITENS_VENDA
# =======================
class ItemVenda(Base):
    __tablename__ = "itens_venda"

    id = Column(Integer, primary_key=True, index=True)
    id_venda = Column(Integer, ForeignKey("vendas.id"))
    id_produto = Column(Integer, ForeignKey("produtos.id"))
    quantidade = Column(Integer, nullable=False)
    preco_unitario = Column(DECIMAL(10, 2))

    venda = relationship("Venda", back_populates="itens")
    produto = relationship("Produto", back_populates="itens")


# =======================
# TABELA: METAS
# =======================
class Meta(Base):
    __tablename__ = "metas"

    id = Column(Integer, primary_key=True, index=True)
    descricao = Column(String(150))
    valor_meta = Column(DECIMAL(10, 2))
    data_inicio = Column(Date)
    data_fim = Column(Date)
    id_usuario = Column(Integer, ForeignKey("usuarios.id"))


# =======================
# TABELA: BOLETINS CEASA
# =======================
class BoletimCeasa(Base):
    __tablename__ = "boletins_ceasa"

    id = Column(Integer, primary_key=True, index=True)
    data_boletim = Column(Date, nullable=False)
    produto = Column(String(100))
    preco_min = Column(DECIMAL(10, 2))
    preco_max = Column(DECIMAL(10, 2))
    preco_medio = Column(DECIMAL(10, 2))
    origem = Column(String(100))
    criado_em = Column(DateTime, default=datetime.now)
