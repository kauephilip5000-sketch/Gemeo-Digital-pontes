from sqlalchemy import Column, Integer, String, Float, Text, ForeignKey
from database import Base


class OAE(Base):
    __tablename__ = "oae"

    id = Column(Integer, primary_key=True, index=True)

    nome = Column(String, nullable=False)
    codigo = Column(String, nullable=True)
    rodovia = Column(String, nullable=True)
    municipio = Column(String, nullable=True)
    uf = Column(String, nullable=True)

    ano_construcao = Column(Integer, nullable=True)

    tipo_estrutura = Column(String, nullable=True)

    numero_vaos = Column(Integer, nullable=True)

    comprimento_total = Column(Float, nullable=True)
    largura = Column(Float, nullable=True)

    tipo_protensao = Column(String, nullable=True)

    observacoes = Column(Text, nullable=True)


class Componente(Base):
    __tablename__ = "componentes"

    id = Column(Integer, primary_key=True, index=True)

    oae_id = Column(
        Integer,
        ForeignKey("oae.id"),
        nullable=False
    )

    categoria = Column(
        String,
        nullable=False
    )

    nome = Column(
        String,
        nullable=False
    )

    classificacao_elemento = Column(
        String,
        nullable=True
    )

    observacoes = Column(
        Text,
        nullable=True
    )