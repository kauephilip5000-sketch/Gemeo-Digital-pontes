from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    Text,
    ForeignKey,
    Date
)

from database import Base


# ============================================================
# OAE
# ============================================================

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


# ============================================================
# COMPONENTES
# ============================================================

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


# ============================================================
# INSPEÇÕES
# ============================================================

class Inspecao(Base):
    __tablename__ = "inspecoes"

    id = Column(Integer, primary_key=True, index=True)

    oae_id = Column(
        Integer,
        ForeignKey("oae.id"),
        nullable=False
    )

    tipo_inspecao = Column(
        String,
        nullable=False
    )

    data_inspecao = Column(
        Date,
        nullable=False
    )

    responsavel = Column(
        String,
        nullable=True
    )

    registro_profissional = Column(
        String,
        nullable=True
    )

    observacoes = Column(
        Text,
        nullable=True
    )


# ============================================================
# ANOMALIAS
# ============================================================

class Anomalia(Base):
    __tablename__ = "anomalias"

    id = Column(Integer, primary_key=True, index=True)

    oae_id = Column(
        Integer,
        ForeignKey("oae.id"),
        nullable=False
    )

    inspecao_id = Column(
        Integer,
        ForeignKey("inspecoes.id"),
        nullable=False
    )

    componente_id = Column(
        Integer,
        ForeignKey("componentes.id"),
        nullable=False
    )

    tipo_anomalia = Column(
        String,
        nullable=False
    )

    descricao = Column(
        Text,
        nullable=True
    )

    localizacao = Column(
        String,
        nullable=True
    )

    observacoes = Column(
        Text,
        nullable=True
    )


# ============================================================
# CLASSIFICAÇÕES
# ============================================================

class Classificacao(Base):
    __tablename__ = "classificacoes"

    id = Column(Integer, primary_key=True, index=True)

    oae_id = Column(
        Integer,
        ForeignKey("oae.id"),
        nullable=False
    )

    inspecao_id = Column(
        Integer,
        ForeignKey("inspecoes.id"),
        nullable=False
    )

    componente_id = Column(
        Integer,
        ForeignKey("componentes.id"),
        nullable=False
    )

    nota_estrutural = Column(
        Integer,
        nullable=False
    )

    justificativa_estrutural = Column(
        Text,
        nullable=True
    )

    nota_funcional = Column(
        Integer,
        nullable=False
    )

    justificativa_funcional = Column(
        Text,
        nullable=True
    )

    nota_durabilidade = Column(
        Integer,
        nullable=False
    )

    justificativa_durabilidade = Column(
        Text,
        nullable=True
    )