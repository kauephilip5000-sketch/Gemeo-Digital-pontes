from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    Text,
    ForeignKey,
    Date,
    UniqueConstraint
)

from database import Base


# ============================================================
# OAE
# ============================================================

class OAE(Base):
    __tablename__ = "oae"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    nome = Column(
        String,
        nullable=False
    )

    codigo = Column(
        String,
        nullable=True
    )

    rodovia = Column(
        String,
        nullable=True
    )

    municipio = Column(
        String,
        nullable=True
    )

    uf = Column(
        String,
        nullable=True
    )

    ano_construcao = Column(
        Integer,
        nullable=True
    )

    tipo_estrutura = Column(
        String,
        nullable=True
    )

    numero_vaos = Column(
        Integer,
        nullable=True
    )

    comprimento_total = Column(
        Float,
        nullable=True
    )

    largura = Column(
        Float,
        nullable=True
    )

    tipo_protensao = Column(
        String,
        nullable=True
    )

    observacoes = Column(
        Text,
        nullable=True
    )


# ============================================================
# COMPONENTE
# ============================================================

class Componente(Base):
    __tablename__ = "componentes"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

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
# INSPEÇÃO
# ============================================================

class Inspecao(Base):
    __tablename__ = "inspecoes"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

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
# DETALHES ESPECÍFICOS DA INSPEÇÃO
# ============================================================

class DetalheInspecao(Base):
    __tablename__ = "detalhes_inspecoes"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    inspecao_id = Column(
        Integer,
        ForeignKey("inspecoes.id"),
        nullable=False,
        unique=True
    )

    # --------------------------------------------------------
    # CADASTRAL
    # --------------------------------------------------------

    motivo_cadastral = Column(
        String,
        nullable=True
    )

    descricao_alteracao = Column(
        Text,
        nullable=True
    )

    # --------------------------------------------------------
    # ROTINEIRA
    # --------------------------------------------------------

    comentarios_alteracoes = Column(
        Text,
        nullable=True
    )

    # --------------------------------------------------------
    # ESPECIAL
    # --------------------------------------------------------

    procedimento_utilizado = Column(
        Text,
        nullable=True
    )

    ensaios_previstos = Column(
        Text,
        nullable=True
    )

    diagnostico = Column(
        Text,
        nullable=True
    )

    recomendacoes = Column(
        Text,
        nullable=True
    )

    # --------------------------------------------------------
    # EXTRAORDINÁRIA
    # --------------------------------------------------------

    motivo_extraordinaria = Column(
        String,
        nullable=True
    )

    data_evento = Column(
        Date,
        nullable=True
    )

    descricao_evento = Column(
        Text,
        nullable=True
    )

    componente_afetado_id = Column(
        Integer,
        ForeignKey("componentes.id"),
        nullable=True
    )

    terapia_recomendada = Column(
        Text,
        nullable=True
    )


# ============================================================
# ANOMALIA ANTIGA
#
# Mantida temporariamente somente para preservar
# os registros do modelo anterior.
# ============================================================

class Anomalia(Base):
    __tablename__ = "anomalias"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

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
# CLASSIFICAÇÃO
# ============================================================

class Classificacao(Base):
    __tablename__ = "classificacoes"

    __table_args__ = (
        UniqueConstraint(
            "oae_id",
            "inspecao_id",
            "componente_id",
            name="uq_classificacao_oae_inspecao_componente"
        ),
    )

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

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


# ============================================================
# FOTOGRAFIA
#
# Esta é a tabela já existente no banco.
# O campo anomalia_id permanece somente para compatibilidade
# com as fotografias antigas.
# ============================================================

class Fotografia(Base):
    __tablename__ = "fotografias"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

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
        nullable=True
    )

    anomalia_id = Column(
        Integer,
        ForeignKey("anomalias.id"),
        nullable=True
    )

    data_foto = Column(
        Date,
        nullable=False
    )

    tipo_registro = Column(
        String,
        nullable=False
    )

    identificacao = Column(
        String,
        nullable=False
    )

    nome_arquivo = Column(
        String,
        nullable=False
    )

    caminho_arquivo = Column(
        String,
        nullable=False
    )

    observacoes = Column(
        Text,
        nullable=True
    )


# ============================================================
# ANOMALIA PERMANENTE
# ============================================================

class AnomaliaPermanente(Base):
    __tablename__ = "anomalias_permanentes"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    oae_id = Column(
        Integer,
        ForeignKey("oae.id"),
        nullable=False
    )

    componente_id = Column(
        Integer,
        ForeignKey("componentes.id"),
        nullable=False
    )

    inspecao_origem_id = Column(
        Integer,
        ForeignKey("inspecoes.id"),
        nullable=False
    )

    tipo_anomalia = Column(
        String,
        nullable=False
    )

    localizacao_referencia = Column(
        String,
        nullable=False
    )

    descricao_inicial = Column(
        Text,
        nullable=True
    )

    ativa = Column(
        Integer,
        nullable=False,
        default=1
    )


# ============================================================
# OBSERVAÇÃO TEMPORAL DA ANOMALIA
# ============================================================

class ObservacaoAnomalia(Base):
    __tablename__ = "observacoes_anomalias"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    anomalia_id = Column(
        Integer,
        ForeignKey("anomalias_permanentes.id"),
        nullable=False
    )

    inspecao_id = Column(
        Integer,
        ForeignKey("inspecoes.id"),
        nullable=False
    )

    descricao = Column(
        Text,
        nullable=True
    )

    localizacao_detalhada = Column(
        String,
        nullable=True
    )

    abertura_fissura_mm = Column(
        Float,
        nullable=True
    )

    extensao_anomalia_cm = Column(
        Float,
        nullable=True
    )

    situacao_observada = Column(
        String,
        nullable=True
    )

    observacoes = Column(
        Text,
        nullable=True
    )

    __table_args__ = (
        UniqueConstraint(
            "anomalia_id",
            "inspecao_id",
            name="uq_anomalia_inspecao"
        ),
    )


# ============================================================
# VÍNCULO ENTRE FOTOGRAFIA E NOVO MODELO DE ANOMALIAS
#
# Essa nova tabela evita alterar a tabela fotografias existente.
# ============================================================

class VinculoFotografiaAnomalia(Base):
    __tablename__ = "vinculos_fotografias_anomalias"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    fotografia_id = Column(
        Integer,
        ForeignKey("fotografias.id"),
        nullable=False,
        unique=True
    )

    anomalia_permanente_id = Column(
        Integer,
        ForeignKey("anomalias_permanentes.id"),
        nullable=False
    )

    observacao_anomalia_id = Column(
        Integer,
        ForeignKey("observacoes_anomalias.id"),
        nullable=False
    )