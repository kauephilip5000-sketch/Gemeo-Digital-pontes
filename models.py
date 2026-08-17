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
#
# Mantido para compatibilidade com as inspeções já existentes.
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
# INSPEÇÃO CADASTRAL - NBR 9452:2023 - ANEXO A
#
# Tabela específica criada para não alterar as tabelas
# existentes no banco.
#
# Uma inspeção do tipo Cadastral pode ter, no máximo,
# um registro nesta tabela.
# ============================================================

class InspecaoCadastral(Base):
    __tablename__ = "inspecoes_cadastrais"

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

    # ========================================================
    # PARTE I - CADASTRO
    # A - IDENTIFICAÇÃO E LOCALIZAÇÃO
    # ========================================================

    jurisdicao = Column(
        String,
        nullable=True
    )

    administracao = Column(
        String,
        nullable=True
    )

    sentido = Column(
        String,
        nullable=True
    )

    localizacao_quilometro_endereco = Column(
        String,
        nullable=True
    )

    projetista = Column(
        String,
        nullable=True
    )

    construtor = Column(
        String,
        nullable=True
    )

    coordenada_latitude = Column(
        String,
        nullable=True
    )

    coordenada_longitude = Column(
        String,
        nullable=True
    )

    trem_tipo_provavel = Column(
        String,
        nullable=True
    )

    importancia = Column(
        String,
        nullable=True
    )

    finalidade = Column(
        String,
        nullable=True
    )

    desvio_rota_alternativa = Column(
        Text,
        nullable=True
    )

    # ========================================================
    # B - CARACTERÍSTICAS DA ESTRUTURA
    # ========================================================

    largura_total = Column(
        Float,
        nullable=True
    )

    largura_util = Column(
        Float,
        nullable=True
    )

    sistema_construtivo = Column(
        String,
        nullable=True
    )

    natureza_transposicao = Column(
        String,
        nullable=True
    )

    material = Column(
        String,
        nullable=True
    )

    secao_tipo = Column(
        String,
        nullable=True
    )

    tipologia_longitudinal_superestrutura = Column(
        String,
        nullable=True
    )

    tipologia_transversal_superestrutura = Column(
        String,
        nullable=True
    )

    tipologia_mesoestrutura = Column(
        String,
        nullable=True
    )

    tipologia_infraestrutura = Column(
        String,
        nullable=True
    )

    numero_apoios = Column(
        Integer,
        nullable=True
    )

    numero_pilares_por_apoio = Column(
        Integer,
        nullable=True
    )

    comprimento_vao_tipico = Column(
        Float,
        nullable=True
    )

    comprimento_vao_maior = Column(
        Float,
        nullable=True
    )

    altura_pilares = Column(
        Float,
        nullable=True
    )

    aparelhos_apoio = Column(
        Text,
        nullable=True
    )

    juntas_dilatacao = Column(
        Text,
        nullable=True
    )

    encontros = Column(
        Text,
        nullable=True
    )

    taludes = Column(
        Text,
        nullable=True
    )

    outras_peculiaridades = Column(
        Text,
        nullable=True
    )

    # ========================================================
    # C - CARACTERÍSTICAS FUNCIONAIS
    # ========================================================

    caracteristicas_planialtimetricas = Column(
        Text,
        nullable=True
    )

    numero_faixas = Column(
        Integer,
        nullable=True
    )

    largura_faixa = Column(
        Float,
        nullable=True
    )

    acostamento_situacao = Column(
        String,
        nullable=True
    )

    largura_acostamento = Column(
        Float,
        nullable=True
    )

    refugio_situacao = Column(
        String,
        nullable=True
    )

    largura_refugio = Column(
        Float,
        nullable=True
    )

    passeio_passarela_situacao = Column(
        String,
        nullable=True
    )

    largura_passeio_passarela = Column(
        Float,
        nullable=True
    )

    barreira_rigida_situacao = Column(
        String,
        nullable=True
    )

    guarda_corpos_situacao = Column(
        String,
        nullable=True
    )

    pavimento_via_permanente = Column(
        Text,
        nullable=True
    )

    drenos_situacao = Column(
        String,
        nullable=True
    )

    pingadeiras_situacao = Column(
        String,
        nullable=True
    )

    gabarito_vertical_sob_oae = Column(
        Float,
        nullable=True
    )

    gabarito_vertical_sobre_oae = Column(
        Float,
        nullable=True
    )

    gabarito_navegavel_situacao = Column(
        String,
        nullable=True
    )

    gabarito_navegavel_altura = Column(
        Float,
        nullable=True
    )

    gabarito_navegavel_largura = Column(
        Float,
        nullable=True
    )

    # ========================================================
    # TRÁFEGO
    # ========================================================

    frequencia_carga_especial = Column(
        String,
        nullable=True
    )

    pbt_maximo = Column(
        Float,
        nullable=True
    )

    carga_maxima_eixo = Column(
        Float,
        nullable=True
    )

    volume_medio_diario = Column(
        Float,
        nullable=True
    )

    ano_referencia_vmd = Column(
        Integer,
        nullable=True
    )

    # ========================================================
    # PARTE II - CARACTERÍSTICAS AMBIENTAIS
    # ========================================================

    grau_agressividade_ambiental = Column(
        String,
        nullable=True
    )

    curso_agua_aplicavel = Column(
        String,
        nullable=True
    )

    nome_curso_agua = Column(
        String,
        nullable=True
    )

    historico_inundacao = Column(
        Text,
        nullable=True
    )

    # ========================================================
    # INFORMAÇÕES COMPLEMENTARES
    # ========================================================

    informacoes_complementares = Column(
        Text,
        nullable=True
    )

    recomendacoes_terapeuticas = Column(
        Text,
        nullable=True
    )

    # ========================================================
    # CONTROLE DO PREENCHIMENTO
    #
    # Campo do sistema, não da NBR.
    # Serve somente para registrar a situação do formulário.
    # ========================================================

    observacoes_cadastro = Column(
        Text,
        nullable=True
    )


# ============================================================
# DOCUMENTOS DA INSPEÇÃO CADASTRAL
#
# Correspondem à fase inicial prevista no Anexo A:
# projeto, execução, termo de recebimento, inspeções
# anteriores, monitoramento, alterações, reforços etc.
#
# Situações sugeridas pelo software:
#
# - Disponível
# - Não localizado
# - Não se aplica
# - Não verificado
#
# Estas situações são decisão de organização do sistema.
# ============================================================

class DocumentoCadastral(Base):
    __tablename__ = "documentos_cadastrais"

    __table_args__ = (
        UniqueConstraint(
            "inspecao_cadastral_id",
            "tipo_documento",
            name="uq_documento_inspecao_cadastral"
        ),
    )

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    inspecao_cadastral_id = Column(
        Integer,
        ForeignKey("inspecoes_cadastrais.id"),
        nullable=False
    )

    tipo_documento = Column(
        String,
        nullable=False
    )

    situacao = Column(
        String,
        nullable=False
    )

    descricao = Column(
        Text,
        nullable=True
    )

    nome_arquivo = Column(
        String,
        nullable=True
    )

    caminho_arquivo = Column(
        String,
        nullable=True
    )


# ============================================================
# CROQUIS DA INSPEÇÃO CADASTRAL
#
# O Anexo A prevê:
#
# - planta do tabuleiro;
# - corte longitudinal;
# - corte transversal;
# - detalhes adicionais.
#
# O arquivo físico poderá ser incluído posteriormente
# pelo módulo cadastral.
# ============================================================

class CroquiCadastral(Base):
    __tablename__ = "croquis_cadastrais"

    __table_args__ = (
        UniqueConstraint(
            "inspecao_cadastral_id",
            "tipo_croqui",
            name="uq_croqui_inspecao_cadastral"
        ),
    )

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    inspecao_cadastral_id = Column(
        Integer,
        ForeignKey("inspecoes_cadastrais.id"),
        nullable=False
    )

    tipo_croqui = Column(
        String,
        nullable=False
    )

    situacao = Column(
        String,
        nullable=False
    )

    descricao = Column(
        Text,
        nullable=True
    )

    nome_arquivo = Column(
        String,
        nullable=True
    )

    caminho_arquivo = Column(
        String,
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

    # --------------------------------------------------------
    # IMPORTANTE
    #
    # nullable=True porque NULL representa NA quando
    # o parâmetro funcional não se aplica.
    # O banco já foi migrado anteriormente para permitir isso.
    # --------------------------------------------------------

    nota_funcional = Column(
        Integer,
        nullable=True
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
# Tabela já existente no banco.
# anomalia_id permanece para compatibilidade com
# registros anteriores.
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