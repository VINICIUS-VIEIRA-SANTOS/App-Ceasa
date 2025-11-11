from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import SessionLocal
from models import Usuario
from passlib.context import CryptContext
import jwt, datetime

router = APIRouter(prefix="/auth", tags=["Autenticação"])

SECRET_KEY = "chave_super_secreta_ceasa"
ALGORITHM = "HS256"
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def verificar_senha(senha: str, senha_hash: str):
    return pwd_context.verify(senha, senha_hash)


def gerar_hash(senha: str):
    return pwd_context.hash(senha)


@router.post("/registrar")
def registrar_usuario(nome: str, email: str, senha: str, db: Session = Depends(get_db)):
    """Cria um novo usuário no sistema"""
    usuario_existente = db.query(Usuario).filter(Usuario.email == email).first()
    if usuario_existente:
        raise HTTPException(status_code=400, detail="Email já cadastrado")

    novo_usuario = Usuario(
        nome=nome,
        email=email,
        senha=gerar_hash(senha),
        cargo="Padrão"
    )
    db.add(novo_usuario)
    db.commit()
    db.refresh(novo_usuario)
    return {"mensagem": "Usuário registrado com sucesso!", "id": novo_usuario.id}


@router.post("/login")
def login(email: str, senha: str, db: Session = Depends(get_db)):
    """Autentica um usuário e retorna um token JWT"""
    usuario = db.query(Usuario).filter(Usuario.email == email).first()
    if not usuario or not verificar_senha(senha, usuario.senha):
        raise HTTPException(status_code=401, detail="Credenciais inválidas")

    token = jwt.encode({
        "sub": usuario.email,
        "nome": usuario.nome,
        "cargo": usuario.cargo,
        "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=8)
    }, SECRET_KEY, algorithm=ALGORITHM)

    return {"access_token": token, "token_type": "bearer"}


@router.get("/verificar-token")
def verificar_token(token: str):
    """Verifica se o token JWT é válido"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return {"valido": True, "dados": payload}
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expirado")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Token inválido")
