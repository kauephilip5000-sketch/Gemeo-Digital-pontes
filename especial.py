import streamlit as st

from datetime import date

from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    ForeignKey,
    UniqueConstraint,
)

from database import Base, SessionLocal
import models

from classificacao import (
    calcular_classificacao_consolidada,
    verificar_andamento_classificacao,
)


# ============================================================
# INSPEÇÃO ESPECIAL
# ABNT NBR 9452:2023
#
# Referência técnica principal:
# - item 4.3;
# - Anexo D (normativo).
#
# O módulo procura reproduzir no sistema o fluxo técnico
# previsto para a inspeção especial.
#
# IMPORTANTE:
#
# O software:
# - organiza informações;
# - controla o preenchimento;
# - relaciona campanhas;
# - acompanha anomalias;
# - apoia o registro de ensaios;
# - acompanha classificações.
#
# O software NÃO substitui:
# - diagnóstico de engenharia;
# - interpretação técnica dos ensaios;
# - decisão de intervenção;
# - responsabilidade técnica do profissional.
# ============================================================


# ============================================================
# REGISTRO ESPECIALIZADO DA INSPEÇÃO ESPECIAL
#
# Esta tabela é uma decisão de arquitetura do software.
#
# Ela complementa:
#
# models.Inspecao
# models.DetalheInspecao
#
# sem eliminar a estrutura já existente.
# ============================================================

class RegistroEspecial(Base):

    __tablename__ = "registros_especial"

    __table_args__ = (
        UniqueConstraint(
            "inspecao_id",
            name="uq_registro_especial_inspecao",
        ),
    )

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    inspecao_id = Column(
        Integer,
        ForeignKey("inspecoes.id"),
        nullable=False,
    )


    # ========================================================
    # D.3 - LOCALIZAÇÃO
    # ========================================================

    rodovia_ferrovia = Column(
        String,
        nullable=True,
    )

    nome_obra = Column(
        String,
        nullable=True,
    )

    quilometro = Column(
        String,
        nullable=True,
    )

    coordenadas = Column(
        String,
        nullable=True,
    )

    sentido = Column(
        String,
        nullable=True,
    )

    jurisdicao = Column(
        String,
        nullable=True,
    )

    localizacao_verificada = Column(
        String,
        nullable=True,
    )


    # ========================================================
    # D.4 - DESCRIÇÃO DA OBRA
    # ========================================================

    descricao_obra = Column(
        Text,
        nullable=True,
    )

    cadastro_geometrico = Column(
        Text,
        nullable=True,
    )

    fotos_vistas_verificadas = Column(
        String,
        nullable=True,
    )

    historico_obra = Column(
        Text,
        nullable=True,
    )

    classe_portante = Column(
        String,
        nullable=True,
    )

    desenhos_memoriais = Column(
        Text,
        nullable=True,
    )

    diferencas_projeto_original = Column(
        Text,
        nullable=True,
    )

    condicoes_ambientais = Column(
        Text,
        nullable=True,
    )

    caracteristicas_trafego = Column(
        Text,
        nullable=True,
    )

    descricao_obra_verificada = Column(
        String,
        nullable=True,
    )


    # ========================================================
    # D.5 - INSPEÇÃO
    # ========================================================

    equipamentos_acesso = Column(
        Text,
        nullable=True,
    )

    condicoes_acesso = Column(
        Text,
        nullable=True,
    )

    limitacoes_inspecao = Column(
        Text,
        nullable=True,
    )

    legendas_convencoes = Column(
        Text,
        nullable=True,
    )

    mapeamento_anomalias = Column(
        Text,
        nullable=True,
    )

    elementos_acessorios = Column(
        Text,
        nullable=True,
    )

    inspecao_subaquatica = Column(
        String,
        nullable=True,
    )

    observacoes_subaquaticas = Column(
        Text,
        nullable=True,
    )

    localizacao_fotos_croqui = Column(
        Text,
        nullable=True,
    )

    vistoria_verificada = Column(
        String,
        nullable=True,
    )


    # ========================================================
    # PATOLOGIA / ANOMALIAS
    #
    # As anomalias individualizadas permanecem nas tabelas:
    #
    # AnomaliaPermanente
    # ObservacaoAnomalia
    #
    # Aqui armazenamos a síntese técnica da inspeção especial.
    # ========================================================

    sintese_patologia = Column(
        Text,
        nullable=True,
    )

    mecanismo_deterioracao = Column(
        Text,
        nullable=True,
    )

    causas_provaveis = Column(
        Text,
        nullable=True,
    )

    anomalias_verificadas = Column(
        String,
        nullable=True,
    )


    # ========================================================
    # D.6 - ENSAIOS
    # ========================================================

    ensaios_necessarios = Column(
        String,
        nullable=True,
    )

    descricao_ensaios = Column(
        Text,
        nullable=True,
    )

    localizacao_ensaios = Column(
        Text,
        nullable=True,
    )

    resultados_ensaios = Column(
        Text,
        nullable=True,
    )

    metodologia_ensaios = Column(
        Text,
        nullable=True,
    )

    normas_referencia_ensaios = Column(
        Text,
        nullable=True,
    )

    interpretacao_ensaios = Column(
        Text,
        nullable=True,
    )

    ensaios_verificados = Column(
        String,
        nullable=True,
    )


    # ========================================================
    # D.7 - DIAGNÓSTICO / TERAPIA / PROJETO DE REPAROS
    # ========================================================

    diagnostico = Column(
        Text,
        nullable=True,
    )

    resumo_analise_estrutural = Column(
        Text,
        nullable=True,
    )

    terapia_recomendada = Column(
        Text,
        nullable=True,
    )

    metodologia_recuperacao = Column(
        Text,
        nullable=True,
    )

    reparos_recomendados = Column(
        Text,
        nullable=True,
    )

    recuperacao_recomendada = Column(
        Text,
        nullable=True,
    )

    reforco_recomendado = Column(
        Text,
        nullable=True,
    )

    conclusoes_recomendacoes = Column(
        Text,
        nullable=True,
    )

    parecer_verificado = Column(
        String,
        nullable=True,
    )


    # ========================================================
    # D.8 - RELATÓRIOS TÉCNICOS COMPLEMENTARES
    # ========================================================

    necessidade_relatorios_complementares = Column(
        String,
        nullable=True,
    )

    relatorios_complementares = Column(
        Text,
        nullable=True,
    )

    justificativa_relatorios = Column(
        Text,
        nullable=True,
    )

    complementares_verificados = Column(
        String,
        nullable=True,
    )


    # ========================================================
    # CONTROLE DO SOFTWARE
    #
    # Não representa classificação automática da NBR.
    # ========================================================

    conclusao_preenchimento = Column(
        String,
        nullable=True,
    )



# ============================================================
# VERIFICAÇÃO DOS COMPONENTES NA INSPEÇÃO ESPECIAL
#
# DECISÃO DE ARQUITETURA DO SOFTWARE
#
# A NBR 9452:2023 exige inspeção pormenorizada e
# identificação/mapeamento das anomalias por elemento.
#
# Esta tabela permite registrar quais componentes cadastrados
# foram efetivamente verificados durante cada campanha
# especial.
#
# Ela NÃO atribui diagnóstico ou classificação automática.
# ============================================================

class VerificacaoComponenteEspecial(Base):

    __tablename__ = "verificacoes_componentes_especial"

    __table_args__ = (
        UniqueConstraint(
            "inspecao_id",
            "componente_id",
            name="uq_verificacao_componente_especial",
        ),
    )

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    inspecao_id = Column(
        Integer,
        ForeignKey("inspecoes.id"),
        nullable=False,
    )

    componente_id = Column(
        Integer,
        ForeignKey("componentes.id"),
        nullable=False,
    )

    situacao = Column(
        String,
        nullable=False,
        default="Não verificado",
    )

    observacoes = Column(
        Text,
        nullable=True,
    )


# ============================================================
# CONSTANTES DE INTERFACE
# ============================================================

STATUS_VERIFICACAO = [
    "Não verificado",
    "Verificado",
    "Não se aplica",
]


STATUS_SIM_NAO = [
    "Não verificado",
    "Sim",
    "Não",
]


STATUS_SUBAQUATICA = [
    "Não verificado",
    "Realizada",
    "Não se aplica",
]


STATUS_ENSAIOS = [
    "Não verificado",
    "Ensaios necessários",
    "Ensaios realizados",
    "Não se aplica",
]

STATUS_COMPONENTE_ESPECIAL = [
    "Não verificado",
    "Verificado - sem anomalias",
    "Verificado - com anomalias",
    "Não acessível",
]


# ============================================================
# CONSULTAS DE INSPEÇÕES
# ============================================================

def buscar_inspecoes_especiais(
    oae_id,
):

    db = SessionLocal()

    dados = (
        db.query(models.Inspecao)
        .filter(
            models.Inspecao.oae_id
            == oae_id
        )
        .filter(
            models.Inspecao.tipo_inspecao
            == "Especial"
        )
        .order_by(
            models.Inspecao.data_inspecao.desc(),
            models.Inspecao.id.desc(),
        )
        .all()
    )

    db.close()

    return dados


def buscar_todas_inspecoes_cronologicas(
    oae_id,
):

    db = SessionLocal()

    dados = (
        db.query(models.Inspecao)
        .filter(
            models.Inspecao.oae_id
            == oae_id
        )
        .order_by(
            models.Inspecao.data_inspecao.asc(),
            models.Inspecao.id.asc(),
        )
        .all()
    )

    db.close()

    return dados


def buscar_ultima_especial_antes_da_data(
    oae_id,
    data_referencia,
):

    if data_referencia is None:

        return None

    db = SessionLocal()

    anterior = (
        db.query(models.Inspecao)
        .filter(
            models.Inspecao.oae_id
            == oae_id
        )
        .filter(
            models.Inspecao.tipo_inspecao
            == "Especial"
        )
        .filter(
            models.Inspecao.data_inspecao
            < data_referencia
        )
        .order_by(
            models.Inspecao.data_inspecao.desc(),
            models.Inspecao.id.desc(),
        )
        .first()
    )

    db.close()

    return anterior


def inspecao_eh_anterior(
    candidata,
    referencia,
):

    return (
        candidata.data_inspecao
        < referencia.data_inspecao
        or (
            candidata.data_inspecao
            == referencia.data_inspecao
            and candidata.id
            < referencia.id
        )
    )


# ============================================================
# REGISTRO ESPECIALIZADO
# ============================================================

def buscar_registro_especial(
    inspecao_id,
):

    if inspecao_id is None:

        return None

    db = SessionLocal()

    registro = (
        db.query(RegistroEspecial)
        .filter(
            RegistroEspecial.inspecao_id
            == inspecao_id
        )
        .first()
    )

    db.close()

    return registro


def garantir_registro_especial(
    inspecao_id,
):

    registro = buscar_registro_especial(
        inspecao_id
    )

    if registro is not None:

        return registro

    db = SessionLocal()

    novo = RegistroEspecial(
        inspecao_id=inspecao_id
    )

    db.add(
        novo
    )

    db.commit()

    db.close()

    return buscar_registro_especial(
        inspecao_id
    )


# ============================================================
# PERIODICIDADE DA INSPEÇÃO ESPECIAL
#
# A NBR 9452:2023 estabelece:
#
# - periodicidade de 5 anos;
#
# - possibilidade de postergação para até 8 anos somente
#   quando atendidas simultaneamente as condições previstas;
#
# - possibilidade de antecipação nas situações previstas
#   no item 4.3.
#
# O software apresenta alertas.
# Ele não substitui a avaliação do responsável técnico.
# ============================================================

def adicionar_anos(
    data_original,
    quantidade_anos,
):

    if data_original is None:

        return None

    try:

        return data_original.replace(
            year=(
                data_original.year
                + quantidade_anos
            )
        )

    except ValueError:

        return data_original.replace(
            year=(
                data_original.year
                + quantidade_anos
            ),
            day=28,
        )


def mostrar_periodicidade_especial(
    ultima_especial,
    data_nova,
):

    st.markdown(
        "#### Referência de periodicidade"
    )

    if ultima_especial is None:

        st.info(
            "Não existe inspeção especial anterior "
            "cadastrada para esta OAE."
        )

        return

    limite_cinco_anos = adicionar_anos(
        ultima_especial.data_inspecao,
        5,
    )

    limite_oito_anos = adicionar_anos(
        ultima_especial.data_inspecao,
        8,
    )

    st.write(
        "**Última inspeção especial:** "
        f"{ultima_especial.data_inspecao.strftime('%d/%m/%Y')}"
    )

    st.write(
        "**Referência de 5 anos:** "
        f"{limite_cinco_anos.strftime('%d/%m/%Y')}"
    )

    st.write(
        "**Limite de 8 anos condicionado aos requisitos "
        "da NBR:** "
        f"{limite_oito_anos.strftime('%d/%m/%Y')}"
    )

    if data_nova <= limite_cinco_anos:

        st.success(
            "A data informada está dentro do intervalo "
            "de cinco anos em relação à última "
            "inspeção especial cadastrada."
        )

    elif data_nova <= limite_oito_anos:

        st.warning(
            "O intervalo ultrapassa cinco anos. "
            "A postergação para até oito anos somente "
            "é admitida se forem atendidas simultaneamente "
            "as condições estabelecidas na NBR 9452:2023."
        )

    else:

        st.error(
            "A data informada ultrapassa oito anos em "
            "relação à última inspeção especial cadastrada."
        )


# ============================================================
# NOVA INSPEÇÃO ESPECIAL
# ============================================================

def mostrar_nova_inspecao_especial(
    oae_ativa,
):

    st.subheader(
        "🟨 Nova inspeção especial"
    )

    st.info(
        "A inspeção especial possui caráter pormenorizado "
        "e deve permitir o mapeamento gráfico e quantitativo "
        "das anomalias dos elementos aparentes e/ou "
        "acessíveis da OAE."
    )

    st.write(
        f"**OAE:** "
        f"{oae_ativa.id} - "
        f"{oae_ativa.nome}"
    )

    data_inspecao = st.date_input(
        "Data da inspeção",
        value=date.today(),
        format="DD/MM/YYYY",
        key="esp_nova_data",
    )

    ultima_especial = (
        buscar_ultima_especial_antes_da_data(
            oae_ativa.id,
            data_inspecao,
        )
    )

    mostrar_periodicidade_especial(
        ultima_especial,
        data_inspecao,
    )

    st.divider()

    motivo = st.selectbox(
        "Motivo / enquadramento da inspeção especial",
        [
            "Inspeção especial periódica",
            (
                "Antecipada - classificação de intervenção "
                "em curto prazo"
            ),
            (
                "Antecipada - adequação de grande porte"
            ),
        ],
        key="esp_nova_motivo",
    )

    if (
        motivo
        ==
        "Antecipada - classificação de intervenção "
        "em curto prazo"
    ):

        st.warning(
            "Confira a inspeção anterior. A antecipação "
            "prevista na NBR está relacionada às notas "
            "1 ou 2 nos parâmetros estrutural e de "
            "durabilidade."
        )

    elif (
        motivo
        ==
        "Antecipada - adequação de grande porte"
    ):

        st.warning(
            "Este enquadramento contempla situações como "
            "alargamentos, prolongamentos, reforços ou "
            "elevação da classe portante."
        )

    responsavel = st.text_input(
        "Inspetor responsável",
        placeholder="Ex.: João da Silva",
        key="esp_nova_responsavel",
    )

    registro_profissional = st.text_input(
        "Registro profissional",
        placeholder="Ex.: CREA-GO 123456/D",
        key="esp_nova_registro",
    )

    observacoes = st.text_area(
        "Observações iniciais",
        placeholder=(
            "Registre informações iniciais relevantes "
            "para esta campanha."
        ),
        key="esp_nova_observacoes",
    )

    salvar = st.button(
        "Criar inspeção especial",
        type="primary",
        key="esp_criar_inspecao",
    )

    if not salvar:

        return

    if responsavel.strip() == "":

        st.error(
            "Informe o inspetor responsável."
        )

        return

    observacoes_completas = (
        "Enquadramento da inspeção especial: "
        f"{motivo}."
    )

    if observacoes.strip() != "":

        observacoes_completas += (
            "\n\n"
            + observacoes.strip()
        )

    db = SessionLocal()

    nova = models.Inspecao(
        oae_id=oae_ativa.id,
        tipo_inspecao="Especial",
        data_inspecao=data_inspecao,
        responsavel=responsavel,
        registro_profissional=
            registro_profissional,
        observacoes=observacoes_completas,
    )

    db.add(
        nova
    )

    db.flush()

    detalhe = models.DetalheInspecao(
        inspecao_id=nova.id,
        procedimento_utilizado="",
        ensaios_previstos="",
        diagnostico="",
        recomendacoes="",
    )

    db.add(
        detalhe
    )

    registro_especial = RegistroEspecial(
        inspecao_id=nova.id,
        rodovia_ferrovia=(
            oae_ativa.rodovia
            or ""
        ),
        nome_obra=(
            oae_ativa.nome
            or ""
        ),
    )

    db.add(
        registro_especial
    )

    db.commit()

    db.refresh(
        nova
    )

    novo_id = nova.id

    db.close()

    st.session_state.inspecao_ativa_id = (
        novo_id
    )

    st.success(
        "Inspeção especial criada com sucesso."
    )

    st.rerun()


# ============================================================
# 1 - LOCALIZAÇÃO E HISTÓRICO
#
# Base normativa:
# Anexo D - D.1 e D.3.
# ============================================================

def mostrar_localizacao_historico(
    oae_ativa,
    inspecao_ativa,
    registro,
):

    st.subheader(
        "1️⃣ Localização e histórico"
    )

    st.caption(
        "Dados da localização da OAE e histórico das "
        "inspeções cadastradas no sistema."
    )

    st.markdown(
        "#### Dados existentes no cadastro da OAE"
    )

    c1, c2, c3 = st.columns(3)

    with c1:

        st.write(
            "**OAE:**"
        )

        st.write(
            oae_ativa.nome
            or "Não informado"
        )

        st.write(
            "**Código:**"
        )

        st.write(
            oae_ativa.codigo
            or "Não informado"
        )

    with c2:

        st.write(
            "**Rodovia/Ferrovia:**"
        )

        st.write(
            oae_ativa.rodovia
            or "Não informado"
        )

        st.write(
            "**Município/UF:**"
        )

        local = (
            f"{oae_ativa.municipio or ''}"
        )

        if oae_ativa.uf:

            if local:

                local += " - "

            local += oae_ativa.uf

        st.write(
            local
            or "Não informado"
        )

    with c3:

        st.write(
            "**Data da inspeção:**"
        )

        st.write(
            inspecao_ativa
            .data_inspecao
            .strftime("%d/%m/%Y")
        )

        st.write(
            "**Responsável:**"
        )

        st.write(
            inspecao_ativa.responsavel
            or "Não informado"
        )

    st.divider()

    st.markdown(
        "#### Histórico das inspeções"
    )

    inspecoes = (
        buscar_todas_inspecoes_cronologicas(
            oae_ativa.id
        )
    )

    anteriores = [
        item
        for item in inspecoes
        if inspecao_eh_anterior(
            item,
            inspecao_ativa,
        )
    ]

    cadastrais = [
        item
        for item in anteriores
        if item.tipo_inspecao
        == "Cadastral"
    ]

    rotineiras = [
        item
        for item in anteriores
        if item.tipo_inspecao
        == "Rotineira"
    ]

    especiais = [
        item
        for item in anteriores
        if item.tipo_inspecao
        == "Especial"
    ]

    c1, c2, c3 = st.columns(3)

    with c1:

        st.metric(
            "Última cadastral",
            (
                cadastrais[-1]
                .data_inspecao
                .strftime("%d/%m/%Y")
                if len(cadastrais) > 0
                else "Não localizada"
            ),
        )

    with c2:

        st.metric(
            "Última rotineira",
            (
                rotineiras[-1]
                .data_inspecao
                .strftime("%d/%m/%Y")
                if len(rotineiras) > 0
                else "Não localizada"
            ),
        )

    with c3:

        st.metric(
            "Última especial",
            (
                especiais[-1]
                .data_inspecao
                .strftime("%d/%m/%Y")
                if len(especiais) > 0
                else "Não localizada"
            ),
        )

    st.divider()

    st.markdown(
        "#### Localização para o relatório especial"
    )

    rodovia_ferrovia = st.text_input(
        "Rodovia ou ferrovia",
        value=(
            registro.rodovia_ferrovia
            or oae_ativa.rodovia
            or ""
        ),
        key="esp_loc_rodovia",
    )

    nome_obra = st.text_input(
        "Nome da obra",
        value=(
            registro.nome_obra
            or oae_ativa.nome
            or ""
        ),
        key="esp_loc_nome",
    )

    c1, c2 = st.columns(2)

    with c1:

        quilometro = st.text_input(
            "Quilômetro (km)",
            value=(
                registro.quilometro
                or ""
            ),
            placeholder="Ex.: km 127+500",
            key="esp_loc_km",
        )

        sentido = st.text_input(
            "Sentido",
            value=(
                registro.sentido
                or ""
            ),
            placeholder="Ex.: crescente",
            key="esp_loc_sentido",
        )

    with c2:

        coordenadas = st.text_input(
            "Coordenadas",
            value=(
                registro.coordenadas
                or ""
            ),
            placeholder=(
                "Ex.: latitude e longitude"
            ),
            key="esp_loc_coordenadas",
        )

        jurisdicao = st.text_input(
            "Jurisdição",
            value=(
                registro.jurisdicao
                or ""
            ),
            placeholder=(
                "Ex.: DNIT, concessão ou outro"
            ),
            key="esp_loc_jurisdicao",
        )

    atual = (
        registro.localizacao_verificada
        or "Não verificado"
    )

    if atual not in STATUS_VERIFICACAO:

        atual = "Não verificado"

    situacao = st.selectbox(
        "Situação da conferência da localização",
        STATUS_VERIFICACAO,
        index=STATUS_VERIFICACAO.index(
            atual
        ),
        key="esp_loc_status",
    )

    salvar = st.button(
        "💾 Salvar localização e histórico",
        type="primary",
        key="esp_salvar_localizacao",
    )

    if salvar:

        if (
            situacao == "Verificado"
            and
            (
                rodovia_ferrovia.strip() == ""
                or nome_obra.strip() == ""
                or quilometro.strip() == ""
                or coordenadas.strip() == ""
            )
        ):

            st.error(
                "Para marcar esta etapa como Verificada, "
                "preencha rodovia/ferrovia, nome da obra, "
                "quilômetro e coordenadas."
            )

            return

        db = SessionLocal()

        dado = (
            db.query(RegistroEspecial)
            .filter(
                RegistroEspecial.id
                == registro.id
            )
            .first()
        )

        dado.rodovia_ferrovia = (
            rodovia_ferrovia
        )

        dado.nome_obra = (
            nome_obra
        )

        dado.quilometro = (
            quilometro
        )

        dado.coordenadas = (
            coordenadas
        )

        dado.sentido = (
            sentido
        )

        dado.jurisdicao = (
            jurisdicao
        )

        dado.localizacao_verificada = (
            situacao
        )

        db.commit()

        db.close()

        st.success(
            "Localização e histórico atualizados."
        )

        st.rerun()


# ============================================================
# 2 - DESCRIÇÃO DA OBRA
#
# Base normativa:
# Anexo D - D.4.
# ============================================================

def mostrar_descricao_obra(
    registro,
):

    st.subheader(
        "2️⃣ Descrição da obra"
    )

    st.info(
        "Esta etapa reúne as informações descritivas "
        "da OAE previstas no roteiro da inspeção especial."
    )

    descricao = st.text_area(
        "Descritivo da obra",
        value=(
            registro.descricao_obra
            or ""
        ),
        placeholder=(
            "Descreva a concepção estrutural, principais "
            "características e organização da OAE."
        ),
        key="esp_desc_obra",
    )

    cadastro_geometrico = st.text_area(
        "Cadastro geométrico / prancha de referência",
        value=(
            registro.cadastro_geometrico
            or ""
        ),
        placeholder=(
            "Informe a prancha ou referência do cadastro "
            "geométrico disponível."
        ),
        key="esp_desc_geometrico",
    )

    fotos_atual = (
        registro.fotos_vistas_verificadas
        or "Não verificado"
    )

    if fotos_atual not in STATUS_VERIFICACAO:

        fotos_atual = "Não verificado"

    fotos_vistas = st.selectbox(
        "Vistas superior, inferior e lateral verificadas",
        STATUS_VERIFICACAO,
        index=STATUS_VERIFICACAO.index(
            fotos_atual
        ),
        help=(
            "Este campo registra a conferência das vistas "
            "fotográficas previstas na descrição da obra. "
            "Os arquivos fotográficos continuam sendo "
            "armazenados no módulo 📷 Fotografias."
        ),
        key="esp_desc_fotos",
    )

    historico = st.text_area(
        "Histórico da obra",
        value=(
            registro.historico_obra
            or ""
        ),
        placeholder=(
            "Registre intervenções, alterações, reforços, "
            "ocorrências ou informações históricas relevantes."
        ),
        key="esp_desc_historico",
    )

    classe_portante = st.text_input(
        "Classe portante provável",
        value=(
            registro.classe_portante
            or ""
        ),
        placeholder=(
            "Ex.: TT45, TT36, TT24 ou outra"
        ),
        key="esp_desc_classe",
    )

    desenhos_memoriais = st.text_area(
        "Desenhos e memoriais de referência",
        value=(
            registro.desenhos_memoriais
            or ""
        ),
        placeholder=(
            "Informe códigos ou referências dos desenhos "
            "e memoriais disponíveis."
        ),
        key="esp_desc_memoriais",
    )

    diferencas = st.text_area(
        "Diferenças em relação ao projeto original",
        value=(
            registro.diferencas_projeto_original
            or ""
        ),
        placeholder=(
            "Registre diferenças identificadas no cadastro "
            "geométrico, quando o projeto original estiver "
            "disponível."
        ),
        key="esp_desc_diferencas",
    )

    condicoes = st.text_area(
        "Condições ambientais e microambientais",
        value=(
            registro.condicoes_ambientais
            or ""
        ),
        placeholder=(
            "Descreva condições ambientais relevantes "
            "para a durabilidade e comportamento da OAE."
        ),
        key="esp_desc_ambientais",
    )

    trafego = st.text_area(
        "Características do tráfego sobre e sob a OAE",
        value=(
            registro.caracteristicas_trafego
            or ""
        ),
        placeholder=(
            "Ex.: veículos, trens, embarcações ou outras "
            "condições de tráfego."
        ),
        key="esp_desc_trafego",
    )

    atual = (
        registro.descricao_obra_verificada
        or "Não verificado"
    )

    if atual not in STATUS_VERIFICACAO:

        atual = "Não verificado"

    situacao = st.selectbox(
        "Conferência da etapa",
        STATUS_VERIFICACAO,
        index=STATUS_VERIFICACAO.index(
            atual
        ),
        key="esp_desc_status",
    )

    salvar = st.button(
        "💾 Salvar descrição da obra",
        type="primary",
        key="esp_salvar_descricao",
    )

    if salvar:

        if (
            situacao == "Verificado"
            and descricao.strip() == ""
        ):

            st.error(
                "Informe o descritivo da obra antes de "
                "marcar a etapa como Verificada."
            )

            return

        db = SessionLocal()

        dado = (
            db.query(RegistroEspecial)
            .filter(
                RegistroEspecial.id
                == registro.id
            )
            .first()
        )

        dado.descricao_obra = (
            descricao
        )

        dado.cadastro_geometrico = (
            cadastro_geometrico
        )

        dado.fotos_vistas_verificadas = (
            fotos_vistas
        )

        dado.historico_obra = (
            historico
        )

        dado.classe_portante = (
            classe_portante
        )

        dado.desenhos_memoriais = (
            desenhos_memoriais
        )

        dado.diferencas_projeto_original = (
            diferencas
        )

        dado.condicoes_ambientais = (
            condicoes
        )

        dado.caracteristicas_trafego = (
            trafego
        )

        dado.descricao_obra_verificada = (
            situacao
        )

        db.commit()

        db.close()

        st.success(
            "Descrição da obra atualizada."
        )

        st.rerun()


# ============================================================
# 3 - INSPEÇÃO / VISTORIA
#
# Base normativa:
# Anexo D - D.5.
#
# O cadastro individual das anomalias permanece no módulo
# ⚠️ Anomalias.
# ============================================================

def mostrar_vistoria(
    registro,
):

    st.subheader(
        "3️⃣ Inspeção e vistoria"
    )

    st.info(
        "Registre aqui as condições e procedimentos gerais "
        "da vistoria. As anomalias individualizadas devem "
        "continuar sendo cadastradas no módulo ⚠️ Anomalias."
    )

    equipamentos = st.text_area(
        "Equipamentos utilizados para acesso",
        value=(
            registro.equipamentos_acesso
            or ""
        ),
        placeholder=(
            "Ex.: plataforma elevatória, caminhão-lança, "
            "andaime, acesso por corda ou outros."
        ),
        key="esp_vist_equipamentos",
    )

    condicoes_acesso = st.text_area(
        "Condições de acesso",
        value=(
            registro.condicoes_acesso
            or ""
        ),
        placeholder=(
            "Descreva as condições encontradas para acesso "
            "aos elementos da estrutura."
        ),
        key="esp_vist_acesso",
    )

    limitacoes = st.text_area(
        "Limitações da inspeção",
        value=(
            registro.limitacoes_inspecao
            or ""
        ),
        placeholder=(
            "Informe elementos ou regiões que não puderam "
            "ser completamente vistoriados e os motivos."
        ),
        key="esp_vist_limitacoes",
    )

    legendas = st.text_area(
        "Legendas e convenções adotadas",
        value=(
            registro.legendas_convencoes
            or ""
        ),
        placeholder=(
            "Registre as convenções utilizadas nos croquis "
            "e mapeamentos."
        ),
        key="esp_vist_legendas",
    )

    mapeamento = st.text_area(
        "Referência do mapeamento de anomalias",
        value=(
            registro.mapeamento_anomalias
            or ""
        ),
        placeholder=(
            "Informe os croquis, desenhos ou referências "
            "utilizados para o mapeamento por elemento."
        ),
        key="esp_vist_mapeamento",
    )

    elementos_acessorios = st.text_area(
        "Inspeção dos elementos acessórios",
        value=(
            registro.elementos_acessorios
            or ""
        ),
        placeholder=(
            "Registre a inspeção de pavimento, juntas, "
            "aparelhos de apoio, guarda-rodas, guarda-corpos "
            "e outros elementos aplicáveis."
        ),
        key="esp_vist_acessorios",
    )

    subaquatica_atual = (
        registro.inspecao_subaquatica
        or "Não verificado"
    )

    if (
        subaquatica_atual
        not in STATUS_SUBAQUATICA
    ):

        subaquatica_atual = (
            "Não verificado"
        )

    subaquatica = st.selectbox(
        "Inspeção subaquática",
        STATUS_SUBAQUATICA,
        index=STATUS_SUBAQUATICA.index(
            subaquatica_atual
        ),
        help=(
            "Quando existirem elementos submersos aplicáveis, "
            "a NBR 9452 remete ao Anexo F."
        ),
        key="esp_vist_subaquatica",
    )

    observacoes_subaquaticas = (
        st.text_area(
            "Observações sobre a inspeção subaquática",
            value=(
                registro
                .observacoes_subaquaticas
                or ""
            ),
            key="esp_vist_obs_subaquatica",
        )
    )

    fotos_croqui = st.text_area(
        "Localização das fotografias em croqui",
        value=(
            registro.localizacao_fotos_croqui
            or ""
        ),
        placeholder=(
            "Registre a referência do croqui utilizado "
            "para localizar as fotografias."
        ),
        key="esp_vist_fotos_croqui",
    )

    atual = (
        registro.vistoria_verificada
        or "Não verificado"
    )

    if atual not in STATUS_VERIFICACAO:

        atual = "Não verificado"

    situacao = st.selectbox(
        "Situação da vistoria",
        STATUS_VERIFICACAO,
        index=STATUS_VERIFICACAO.index(
            atual
        ),
        key="esp_vist_status",
    )

    salvar = st.button(
        "💾 Salvar dados da vistoria",
        type="primary",
        key="esp_salvar_vistoria",
    )

    if salvar:

        if (
            situacao == "Verificado"
            and equipamentos.strip() == ""
        ):

            st.error(
                "Informe os equipamentos ou recursos de "
                "acesso utilizados antes de marcar esta "
                "etapa como Verificada."
            )

            return

        db = SessionLocal()

        dado = (
            db.query(RegistroEspecial)
            .filter(
                RegistroEspecial.id
                == registro.id
            )
            .first()
        )

        dado.equipamentos_acesso = (
            equipamentos
        )

        dado.condicoes_acesso = (
            condicoes_acesso
        )

        dado.limitacoes_inspecao = (
            limitacoes
        )

        dado.legendas_convencoes = (
            legendas
        )

        dado.mapeamento_anomalias = (
            mapeamento
        )

        dado.elementos_acessorios = (
            elementos_acessorios
        )

        dado.inspecao_subaquatica = (
            subaquatica
        )

        dado.observacoes_subaquaticas = (
            observacoes_subaquaticas
        )

        dado.localizacao_fotos_croqui = (
            fotos_croqui
        )

        dado.vistoria_verificada = (
            situacao
        )

        db.commit()

        db.close()

        st.success(
            "Dados da vistoria atualizados."
        )

        st.rerun()



# ============================================================
# CONSULTAS PARA PATOLOGIA DA INSPEÇÃO ESPECIAL
# ============================================================

def buscar_componentes_especial(
    oae_id,
):

    db = SessionLocal()

    componentes = (
        db.query(models.Componente)
        .filter(
            models.Componente.oae_id
            == oae_id
        )
        .order_by(
            models.Componente.categoria,
            models.Componente.id,
        )
        .all()
    )

    db.close()

    return componentes


def buscar_verificacao_componente_especial(
    inspecao_id,
    componente_id,
):

    db = SessionLocal()

    verificacao = (
        db.query(VerificacaoComponenteEspecial)
        .filter(
            VerificacaoComponenteEspecial.inspecao_id
            == inspecao_id
        )
        .filter(
            VerificacaoComponenteEspecial.componente_id
            == componente_id
        )
        .first()
    )

    db.close()

    return verificacao


def garantir_verificacao_componente_especial(
    inspecao_id,
    componente_id,
):

    verificacao = (
        buscar_verificacao_componente_especial(
            inspecao_id,
            componente_id,
        )
    )

    if verificacao is not None:

        return verificacao

    db = SessionLocal()

    nova = VerificacaoComponenteEspecial(
        inspecao_id=inspecao_id,
        componente_id=componente_id,
        situacao="Não verificado",
    )

    db.add(
        nova
    )

    db.commit()

    db.close()

    return (
        buscar_verificacao_componente_especial(
            inspecao_id,
            componente_id,
        )
    )


def buscar_anomalias_componente_especial(
    oae_id,
    componente_id,
    inspecao_ativa,
):

    db = SessionLocal()

    anomalias = (
        db.query(models.AnomaliaPermanente)
        .join(
            models.Inspecao,
            models.Inspecao.id
            ==
            models.AnomaliaPermanente.inspecao_origem_id,
        )
        .filter(
            models.AnomaliaPermanente.oae_id
            == oae_id
        )
        .filter(
            models.AnomaliaPermanente.componente_id
            == componente_id
        )
        .filter(
            models.AnomaliaPermanente.ativa
            == 1
        )
        .filter(
            (
                models.Inspecao.data_inspecao
                < inspecao_ativa.data_inspecao
            )
            |
            (
                (
                    models.Inspecao.data_inspecao
                    == inspecao_ativa.data_inspecao
                )
                &
                (
                    models.Inspecao.id
                    <= inspecao_ativa.id
                )
            )
        )
        .order_by(
            models.AnomaliaPermanente.id
        )
        .all()
    )

    db.close()

    return anomalias


def buscar_observacao_especial(
    anomalia_id,
    inspecao_id,
):

    db = SessionLocal()

    observacao = (
        db.query(models.ObservacaoAnomalia)
        .filter(
            models.ObservacaoAnomalia.anomalia_id
            == anomalia_id
        )
        .filter(
            models.ObservacaoAnomalia.inspecao_id
            == inspecao_id
        )
        .first()
    )

    db.close()

    return observacao


def contar_componentes_especial(
    oae_id,
    inspecao_id,
):

    componentes = buscar_componentes_especial(
        oae_id
    )

    total = len(
        componentes
    )

    resolvidos = 0

    nao_acessiveis = 0

    for componente in componentes:

        verificacao = (
            buscar_verificacao_componente_especial(
                inspecao_id,
                componente.id,
            )
        )

        if verificacao is None:

            continue

        if (
            verificacao.situacao
            in [
                "Verificado - sem anomalias",
                "Verificado - com anomalias",
                "Não acessível",
            ]
        ):

            resolvidos += 1

        if (
            verificacao.situacao
            == "Não acessível"
        ):

            nao_acessiveis += 1

    return (
        total,
        resolvidos,
        nao_acessiveis,
    )


# ============================================================
# 4 - PATOLOGIA E MAPEAMENTO DAS ANOMALIAS
#
# Base normativa:
#
# ABNT NBR 9452:2023
# - item 4.3;
# - Anexo D;
# - D.5.
#
# A NBR exige inspeção pormenorizada e mapeamento
# das anomalias por elemento estrutural.
#
# O cadastro das anomalias continua sendo realizado
# no módulo ⚠️ Anomalias.
#
# Aqui o módulo Especial:
#
# - acompanha cada componente;
# - apresenta as anomalias vinculadas;
# - verifica se existe observação na campanha;
# - apresenta dados quantitativos já cadastrados;
# - registra a situação da verificação do componente;
# - registra a síntese técnica da manifestação patológica.
# ============================================================

def mostrar_patologia_especial(
    oae_ativa,
    inspecao_ativa,
    registro,
):

    st.subheader(
        "4️⃣ Patologia e mapeamento das anomalias"
    )

    st.info(
        "A inspeção especial deve ser pormenorizada. "
        "Utilize esta etapa para verificar cada componente "
        "da OAE e acompanhar as anomalias registradas "
        "na campanha."
    )

    st.warning(
        "O cadastro, localização detalhada, medições e "
        "evolução das anomalias continuam sendo realizados "
        "no módulo ⚠️ Anomalias. Esta tela controla a "
        "abrangência da inspeção especial."
    )

    componentes = buscar_componentes_especial(
        oae_ativa.id
    )

    if len(componentes) == 0:

        st.error(
            "Não existem componentes cadastrados para esta "
            "OAE. Cadastre os componentes estruturais antes "
            "de concluir a inspeção especial."
        )

        return

    total_componentes = len(
        componentes
    )

    componentes_resolvidos = 0

    total_anomalias = 0

    total_observadas = 0

    for componente in componentes:

        verificacao = (
            garantir_verificacao_componente_especial(
                inspecao_ativa.id,
                componente.id,
            )
        )

        anomalias = (
            buscar_anomalias_componente_especial(
                oae_ativa.id,
                componente.id,
                inspecao_ativa,
            )
        )

        quantidade_anomalias = len(
            anomalias
        )

        total_anomalias += (
            quantidade_anomalias
        )

        observadas_componente = 0

        for anomalia in anomalias:

            observacao = (
                buscar_observacao_especial(
                    anomalia.id,
                    inspecao_ativa.id,
                )
            )

            if observacao is not None:

                observadas_componente += 1
                total_observadas += 1

        if (
            verificacao.situacao
            in [
                "Verificado - sem anomalias",
                "Verificado - com anomalias",
                "Não acessível",
            ]
        ):

            componentes_resolvidos += 1

        titulo = (
            f"{componente.id} - "
            f"{componente.nome}"
        )

        with st.expander(
            titulo,
            expanded=False,
        ):

            c1, c2, c3 = st.columns(3)

            with c1:

                st.write(
                    "**Categoria:**"
                )

                st.write(
                    componente.categoria
                    or "Não informado"
                )

            with c2:

                st.write(
                    "**Relevância:**"
                )

                st.write(
                    componente.classificacao_elemento
                    or "Não informado"
                )

            with c3:

                st.metric(
                    "Anomalias ativas",
                    quantidade_anomalias,
                )

            if quantidade_anomalias == 0:

                st.info(
                    "Nenhuma anomalia ativa está vinculada "
                    "a este componente no sistema."
                )

            else:

                st.markdown(
                    "#### Anomalias vinculadas"
                )

                dados = []

                for anomalia in anomalias:

                    observacao = (
                        buscar_observacao_especial(
                            anomalia.id,
                            inspecao_ativa.id,
                        )
                    )

                    if observacao is None:

                        situacao_campanha = (
                            "Sem observação nesta campanha"
                        )

                        abertura = "—"
                        extensao = "—"

                    else:

                        situacao_campanha = (
                            observacao.situacao_observada
                            or "Observada"
                        )

                        abertura = (
                            observacao.abertura_fissura_mm
                            if (
                                observacao
                                .abertura_fissura_mm
                                is not None
                            )
                            else "—"
                        )

                        extensao = (
                            observacao.extensao_anomalia_cm
                            if (
                                observacao
                                .extensao_anomalia_cm
                                is not None
                            )
                            else "—"
                        )

                    origem = (
                        "Atual"
                        if (
                            anomalia.inspecao_origem_id
                            == inspecao_ativa.id
                        )
                        else "Anterior"
                    )

                    dados.append(
                        {
                            "ID":
                                anomalia.id,

                            "Origem":
                                origem,

                            "Anomalia":
                                anomalia.tipo_anomalia,

                            "Localização":
                                anomalia.localizacao_referencia,

                            "Situação":
                                situacao_campanha,

                            "Abertura (mm)":
                                abertura,

                            "Extensão (cm)":
                                extensao,
                        }
                    )

                st.dataframe(
                    dados,
                    width="stretch",
                    hide_index=True,
                )

                st.caption(
                    f"Observadas nesta campanha: "
                    f"{observadas_componente}/"
                    f"{quantidade_anomalias}"
                )

                if (
                    observadas_componente
                    < quantidade_anomalias
                ):

                    st.warning(
                        "Existem anomalias ativas deste "
                        "componente sem observação na inspeção "
                        "especial atual."
                    )

            situacao_atual = (
                verificacao.situacao
                or "Não verificado"
            )

            if (
                situacao_atual
                not in STATUS_COMPONENTE_ESPECIAL
            ):

                situacao_atual = (
                    "Não verificado"
                )

            situacao = st.selectbox(
                "Situação da verificação do componente",
                STATUS_COMPONENTE_ESPECIAL,
                index=(
                    STATUS_COMPONENTE_ESPECIAL.index(
                        situacao_atual
                    )
                ),
                key=(
                    f"esp_pat_status_"
                    f"{inspecao_ativa.id}_"
                    f"{componente.id}"
                ),
            )

            observacoes = st.text_area(
                "Observações da inspeção deste componente",
                value=(
                    verificacao.observacoes
                    or ""
                ),
                placeholder=(
                    "Registre limitações de acesso, "
                    "condições observadas ou informações "
                    "relevantes deste elemento."
                ),
                key=(
                    f"esp_pat_obs_"
                    f"{inspecao_ativa.id}_"
                    f"{componente.id}"
                ),
            )

            if (
                situacao
                == "Verificado - sem anomalias"
                and quantidade_anomalias > 0
            ):

                st.warning(
                    "Este componente possui anomalias ativas "
                    "registradas no sistema. A situação "
                    "'sem anomalias' é incompatível."
                )

            if (
                situacao
                == "Verificado - com anomalias"
                and quantidade_anomalias == 0
            ):

                st.warning(
                    "Nenhuma anomalia ativa está cadastrada "
                    "para este componente."
                )

            if (
                situacao == "Não acessível"
            ):

                st.warning(
                    "Registre obrigatoriamente nas observações "
                    "o motivo pelo qual este elemento não pôde "
                    "ser acessado ou inspecionado."
                )

            salvar_componente = st.button(
                "💾 Salvar verificação do componente",
                type="primary",
                key=(
                    f"esp_pat_salvar_"
                    f"{inspecao_ativa.id}_"
                    f"{componente.id}"
                ),
            )

            if salvar_componente:

                if (
                    situacao
                    == "Verificado - sem anomalias"
                    and quantidade_anomalias > 0
                ):

                    st.error(
                        "Não é possível registrar este "
                        "componente como sem anomalias porque "
                        "existem anomalias ativas vinculadas."
                    )

                    return

                if (
                    situacao
                    == "Verificado - com anomalias"
                    and quantidade_anomalias == 0
                ):

                    st.error(
                        "Cadastre a anomalia no módulo "
                        "⚠️ Anomalias antes de concluir "
                        "este componente."
                    )

                    return

                if (
                    situacao
                    == "Verificado - com anomalias"
                    and observadas_componente
                    < quantidade_anomalias
                ):

                    st.error(
                        "Existem anomalias ativas sem "
                        "observação nesta inspeção. Registre "
                        "a situação atual delas no módulo "
                        "⚠️ Anomalias."
                    )

                    return

                if (
                    situacao == "Não acessível"
                    and observacoes.strip() == ""
                ):

                    st.error(
                        "Informe o motivo da impossibilidade "
                        "de acesso ao componente."
                    )

                    return

                db = SessionLocal()

                dado = (
                    db.query(
                        VerificacaoComponenteEspecial
                    )
                    .filter(
                        VerificacaoComponenteEspecial.id
                        == verificacao.id
                    )
                    .first()
                )

                dado.situacao = (
                    situacao
                )

                dado.observacoes = (
                    observacoes
                )

                db.commit()

                db.close()

                st.success(
                    "Verificação do componente salva."
                )

                st.rerun()

    st.divider()

    st.markdown(
        "### Síntese da manifestação patológica"
    )

    c1, c2, c3 = st.columns(3)

    with c1:

        st.metric(
            "Componentes",
            total_componentes,
        )

    with c2:

        st.metric(
            "Componentes verificados",
            (
                f"{componentes_resolvidos}/"
                f"{total_componentes}"
            ),
        )

    with c3:

        st.metric(
            "Anomalias observadas",
            (
                f"{total_observadas}/"
                f"{total_anomalias}"
            ),
        )

    sintese = st.text_area(
        "Síntese do relatório de patologia",
        value=(
            registro.sintese_patologia
            or ""
        ),
        placeholder=(
            "Apresente uma síntese técnica das manifestações "
            "patológicas identificadas e de sua distribuição "
            "na OAE."
        ),
        key="esp_pat_sintese",
    )

    mecanismo = st.text_area(
        "Mecanismos de deterioração identificados",
        value=(
            registro.mecanismo_deterioracao
            or ""
        ),
        placeholder=(
            "Preenchimento e interpretação pelo profissional "
            "responsável."
        ),
        key="esp_pat_mecanismo",
    )

    causas = st.text_area(
        "Causas prováveis",
        value=(
            registro.causas_provaveis
            or ""
        ),
        placeholder=(
            "Registre as causas prováveis identificadas "
            "pela avaliação técnica."
        ),
        key="esp_pat_causas",
    )

    atual = (
        registro.anomalias_verificadas
        or "Não verificado"
    )

    if atual not in STATUS_VERIFICACAO:

        atual = "Não verificado"

    situacao_geral = st.selectbox(
        "Situação geral da etapa de patologia",
        STATUS_VERIFICACAO,
        index=STATUS_VERIFICACAO.index(
            atual
        ),
        key="esp_pat_status_geral",
    )

    total_real, resolvidos_real, nao_acessiveis = (
        contar_componentes_especial(
            oae_ativa.id,
            inspecao_ativa.id,
        )
    )

    if (
        resolvidos_real < total_real
    ):

        st.warning(
            "Ainda existem componentes sem conclusão da "
            "verificação nesta inspeção especial."
        )

    if nao_acessiveis > 0:

        st.warning(
            f"{nao_acessiveis} componente(s) foram "
            "registrados como não acessíveis. As justificativas "
            "devem permanecer documentadas para avaliação "
            "do responsável técnico."
        )

    salvar_sintese = st.button(
        "💾 Salvar síntese de patologia",
        type="primary",
        key="esp_pat_salvar_sintese",
    )

    if salvar_sintese:

        total_real, resolvidos_real, _ = (
            contar_componentes_especial(
                oae_ativa.id,
                inspecao_ativa.id,
            )
        )

        if (
            situacao_geral == "Verificado"
            and resolvidos_real < total_real
        ):

            st.error(
                "Ainda existem componentes sem verificação "
                "concluída."
            )

            return

        if (
            situacao_geral == "Verificado"
            and sintese.strip() == ""
        ):

            st.error(
                "Informe a síntese do relatório de patologia "
                "antes de concluir esta etapa."
            )

            return

        db = SessionLocal()

        dado = (
            db.query(RegistroEspecial)
            .filter(
                RegistroEspecial.id
                == registro.id
            )
            .first()
        )

        dado.sintese_patologia = (
            sintese
        )

        dado.mecanismo_deterioracao = (
            mecanismo
        )

        dado.causas_provaveis = (
            causas
        )

        dado.anomalias_verificadas = (
            situacao_geral
        )

        db.commit()

        db.close()

        st.success(
            "Síntese de patologia salva."
        )

        st.rerun()


# ============================================================
# 5 - ENSAIOS
#
# Base normativa:
# ABNT NBR 9452:2023 - Anexo D, item D.6.
#
# Quando houver ensaios, o registro deve contemplar:
# - localização em croqui;
# - resultados com interpretação;
# - metodologia, quando necessária;
# - normas de referência.
#
# A interpretação dos resultados permanece sob
# responsabilidade do profissional responsável.
# ============================================================

def mostrar_ensaios_especial(
    inspecao_ativa,
    registro,
):

    st.subheader(
        "5️⃣ Ensaios e investigações"
    )

    st.info(
        "Registre os ensaios e investigações associados à "
        "inspeção especial. Quando realizados, devem ser "
        "documentados com sua localização, resultados, "
        "interpretação, metodologia aplicável e normas de "
        "referência."
    )

    atual = (
        registro.ensaios_necessarios
        or "Não verificado"
    )

    if atual not in STATUS_ENSAIOS:

        atual = "Não verificado"

    situacao_ensaios = st.selectbox(
        "Situação dos ensaios",
        STATUS_ENSAIOS,
        index=STATUS_ENSAIOS.index(
            atual
        ),
        key="esp_ens_situacao",
    )

    descricao = st.text_area(
        "Ensaios previstos ou realizados",
        value=(
            registro.descricao_ensaios
            or ""
        ),
        placeholder=(
            "Ex.: esclerometria, ultrassom, potencial de "
            "corrosão, pacometria ou outros ensaios definidos "
            "pelo responsável técnico."
        ),
        key="esp_ens_descricao",
    )

    localizacao = st.text_area(
        "Localização dos ensaios em croqui",
        value=(
            registro.localizacao_ensaios
            or ""
        ),
        placeholder=(
            "Informe o croqui, desenho, elemento e posição "
            "dos pontos onde os ensaios foram executados."
        ),
        key="esp_ens_localizacao",
    )

    resultados = st.text_area(
        "Resultados dos ensaios",
        value=(
            registro.resultados_ensaios
            or ""
        ),
        placeholder=(
            "Registre ou referencie os resultados obtidos."
        ),
        key="esp_ens_resultados",
    )

    interpretacao = st.text_area(
        "Interpretação dos resultados",
        value=(
            registro.interpretacao_ensaios
            or ""
        ),
        placeholder=(
            "Apresente a interpretação técnica dos resultados "
            "obtidos nos ensaios."
        ),
        help=(
            "A interpretação técnica deve ser realizada ou "
            "validada pelo profissional responsável."
        ),
        key="esp_ens_interpretacao",
    )

    metodologia = st.text_area(
        "Metodologia utilizada, quando necessária",
        value=(
            registro.metodologia_ensaios
            or ""
        ),
        placeholder=(
            "Descreva os procedimentos, equipamentos e "
            "metodologia empregados, quando necessário."
        ),
        key="esp_ens_metodologia",
    )

    normas = st.text_area(
        "Normas e referências aplicáveis",
        value=(
            registro.normas_referencia_ensaios
            or ""
        ),
        placeholder=(
            "Informe as normas técnicas e referências "
            "utilizadas nos ensaios."
        ),
        key="esp_ens_normas",
    )

    status_atual = (
        registro.ensaios_verificados
        or "Não verificado"
    )

    if status_atual not in STATUS_VERIFICACAO:

        status_atual = "Não verificado"

    status_etapa = st.selectbox(
        "Situação da etapa de ensaios",
        STATUS_VERIFICACAO,
        index=STATUS_VERIFICACAO.index(
            status_atual
        ),
        key="esp_ens_status_etapa",
    )

    if (
        situacao_ensaios == "Ensaios realizados"
        and (
            descricao.strip() == ""
            or localizacao.strip() == ""
            or resultados.strip() == ""
            or interpretacao.strip() == ""
            or normas.strip() == ""
        )
    ):

        st.warning(
            "Para ensaios realizados, preencha a descrição, "
            "localização, resultados, interpretação e normas "
            "de referência antes de concluir a etapa."
        )

    if (
        situacao_ensaios == "Ensaios necessários"
        and descricao.strip() == ""
    ):

        st.warning(
            "Foram indicados ensaios necessários, mas ainda "
            "não há descrição dos ensaios previstos."
        )

    salvar = st.button(
        "💾 Salvar ensaios",
        type="primary",
        key="esp_salvar_ensaios",
    )

    if salvar:

        if (
            status_etapa == "Verificado"
            and situacao_ensaios == "Não verificado"
        ):

            st.error(
                "Defina a situação dos ensaios antes de "
                "marcar esta etapa como Verificada."
            )

            return

        if (
            status_etapa == "Verificado"
            and situacao_ensaios == "Ensaios necessários"
        ):

            st.error(
                "A etapa não pode ser concluída enquanto "
                "existirem ensaios indicados como necessários "
                "e ainda não realizados."
            )

            return

        if (
            status_etapa == "Verificado"
            and situacao_ensaios == "Ensaios realizados"
            and (
                descricao.strip() == ""
                or localizacao.strip() == ""
                or resultados.strip() == ""
                or interpretacao.strip() == ""
                or normas.strip() == ""
            )
        ):

            st.error(
                "Complete o registro dos ensaios realizados: "
                "descrição, localização em croqui, resultados, "
                "interpretação e normas de referência."
            )

            return

        db = SessionLocal()

        dado = (
            db.query(RegistroEspecial)
            .filter(
                RegistroEspecial.id
                == registro.id
            )
            .first()
        )

        dado.ensaios_necessarios = (
            situacao_ensaios
        )

        dado.descricao_ensaios = (
            descricao
        )

        dado.localizacao_ensaios = (
            localizacao
        )

        dado.resultados_ensaios = (
            resultados
        )

        dado.interpretacao_ensaios = (
            interpretacao
        )

        dado.metodologia_ensaios = (
            metodologia
        )

        dado.normas_referencia_ensaios = (
            normas
        )

        dado.ensaios_verificados = (
            status_etapa
        )

        detalhe = (
            db.query(models.DetalheInspecao)
            .filter(
                models.DetalheInspecao.inspecao_id
                == inspecao_ativa.id
            )
            .first()
        )

        if detalhe is not None:

            detalhe.ensaios_previstos = (
                descricao
            )

            detalhe.procedimento_utilizado = (
                metodologia
            )

        db.commit()

        db.close()

        st.success(
            "Ensaios atualizados."
        )

        st.rerun()


# ============================================================
# 6 - CLASSIFICAÇÃO DA OAE
# ============================================================

def contar_fotografias_especial(
    oae_id,
    inspecao_id,
):

    db = SessionLocal()

    quantidade = (
        db.query(models.Fotografia)
        .filter(
            models.Fotografia.oae_id
            == oae_id
        )
        .filter(
            models.Fotografia.inspecao_id
            == inspecao_id
        )
        .count()
    )

    db.close()

    return quantidade


def mostrar_classificacao_especial(
    oae_ativa,
    inspecao_ativa,
):

    st.subheader(
        "6️⃣ Classificação da OAE"
    )

    st.info(
        "A classificação da inspeção especial utiliza o "
        "módulo ⭐ Classificação já existente no sistema, "
        "mantendo uma única fonte para as notas estrutural, "
        "funcional e de durabilidade."
    )

    andamento = (
        verificar_andamento_classificacao(
            oae_ativa.id,
            inspecao_ativa.id,
        )
    )

    notas = (
        calcular_classificacao_consolidada(
            oae_ativa.id,
            inspecao_ativa.id,
        )
    )

    c1, c2, c3 = st.columns(3)

    with c1:

        st.metric(
            "Componentes cadastrados",
            andamento["total"],
        )

    with c2:

        st.metric(
            "Componentes avaliados",
            andamento["avaliados"],
        )

    with c3:

        pendentes = max(
            andamento["total"]
            - andamento["avaliados"],
            0,
        )

        st.metric(
            "Pendentes",
            pendentes,
        )

    if andamento["concluida"]:

        st.success(
            "A classificação dos componentes está concluída "
            "nesta inspeção especial."
        )

    else:

        st.warning(
            "Ainda existem componentes pendentes de "
            "classificação no módulo ⭐ Classificação."
        )

    if notas is not None:

        st.markdown(
            "#### Classificação consolidada atual"
        )

        c1, c2, c3 = st.columns(3)

        with c1:

            st.metric(
                "Estrutural",
                (
                    notas["estrutural"]
                    if notas["estrutural"] is not None
                    else "—"
                ),
            )

        with c2:

            st.metric(
                "Funcional",
                (
                    notas["funcional"]
                    if notas["funcional"] is not None
                    else "NA"
                ),
            )

        with c3:

            st.metric(
                "Durabilidade",
                (
                    notas["durabilidade"]
                    if notas["durabilidade"] is not None
                    else "—"
                ),
            )

    st.caption(
        "As notas e justificativas são registradas no módulo "
        "⭐ Classificação. O módulo Especial apenas acompanha "
        "os dados vinculados à campanha selecionada."
    )


# ============================================================
# 7 - RELATÓRIO II - DIAGNÓSTICO, TERAPIA E REPAROS
# ============================================================

def mostrar_terapia_especial(
    inspecao_ativa,
    registro,
):

    st.subheader(
        "7️⃣ Diagnóstico, terapia e projeto de reparos"
    )

    st.info(
        "Registre o diagnóstico das anomalias, eventuais "
        "informações de análise estrutural, a terapia e a "
        "metodologia de recuperação, além das conclusões e "
        "recomendações da inspeção especial."
    )

    diagnostico = st.text_area(
        "Diagnóstico das anomalias",
        value=(
            registro.diagnostico
            or ""
        ),
        placeholder=(
            "Apresente o diagnóstico técnico das anomalias "
            "mapeadas na inspeção."
        ),
        key="esp_ter_diagnostico",
    )

    resumo_analise = st.text_area(
        "Resumo da análise estrutural, quando realizada",
        value=(
            registro.resumo_analise_estrutural
            or ""
        ),
        placeholder=(
            "Quando houver análise estrutural, apresente aqui "
            "uma síntese. O memorial de cálculo detalhado "
            "permanece como documento à parte."
        ),
        key="esp_ter_analise",
    )

    terapia = st.text_area(
        "Terapia recomendada",
        value=(
            registro.terapia_recomendada
            or ""
        ),
        placeholder=(
            "Registre a terapia definida para as anomalias "
            "avaliadas."
        ),
        key="esp_ter_terapia",
    )

    metodologia = st.text_area(
        "Metodologia de recuperação",
        value=(
            registro.metodologia_recuperacao
            or ""
        ),
        placeholder=(
            "Descreva a metodologia de recuperação aplicável."
        ),
        key="esp_ter_metodologia",
    )

    reparos = st.text_area(
        "Necessidade / recomendações de reparo",
        value=(
            registro.reparos_recomendados
            or ""
        ),
        key="esp_ter_reparos",
    )

    recuperacao = st.text_area(
        "Necessidade / recomendações de recuperação",
        value=(
            registro.recuperacao_recomendada
            or ""
        ),
        key="esp_ter_recuperacao",
    )

    reforco = st.text_area(
        "Necessidade / recomendações de reforço",
        value=(
            registro.reforco_recomendado
            or ""
        ),
        key="esp_ter_reforco",
    )

    conclusoes = st.text_area(
        "Conclusões e recomendações",
        value=(
            registro.conclusoes_recomendacoes
            or ""
        ),
        placeholder=(
            "Registre as conclusões da inspeção, recomendações "
            "e a necessidade de avaliações complementares."
        ),
        key="esp_ter_conclusoes",
    )

    atual = (
        registro.parecer_verificado
        or "Não verificado"
    )

    if atual not in STATUS_VERIFICACAO:

        atual = "Não verificado"

    situacao = st.selectbox(
        "Situação do Relatório II",
        STATUS_VERIFICACAO,
        index=STATUS_VERIFICACAO.index(
            atual
        ),
        key="esp_ter_status",
    )

    salvar = st.button(
        "💾 Salvar diagnóstico e terapia",
        type="primary",
        key="esp_salvar_terapia",
    )

    if salvar:

        if (
            situacao == "Verificado"
            and diagnostico.strip() == ""
        ):

            st.error(
                "Informe o diagnóstico antes de concluir "
                "esta etapa."
            )

            return

        if (
            situacao == "Verificado"
            and terapia.strip() == ""
            and reparos.strip() == ""
            and recuperacao.strip() == ""
            and reforco.strip() == ""
        ):

            st.error(
                "Registre a terapia ou a indicação de reparo, "
                "recuperação e/ou reforço antes de concluir "
                "esta etapa."
            )

            return

        if (
            situacao == "Verificado"
            and conclusoes.strip() == ""
        ):

            st.error(
                "Registre as conclusões e recomendações antes "
                "de concluir esta etapa."
            )

            return

        db = SessionLocal()

        dado = (
            db.query(RegistroEspecial)
            .filter(
                RegistroEspecial.id
                == registro.id
            )
            .first()
        )

        dado.diagnostico = diagnostico
        dado.resumo_analise_estrutural = resumo_analise
        dado.terapia_recomendada = terapia
        dado.metodologia_recuperacao = metodologia
        dado.reparos_recomendados = reparos
        dado.recuperacao_recomendada = recuperacao
        dado.reforco_recomendado = reforco
        dado.conclusoes_recomendacoes = conclusoes
        dado.parecer_verificado = situacao

        detalhe = (
            db.query(models.DetalheInspecao)
            .filter(
                models.DetalheInspecao.inspecao_id
                == inspecao_ativa.id
            )
            .first()
        )

        if detalhe is not None:

            detalhe.diagnostico = diagnostico

            detalhe.recomendacoes = (
                conclusoes
            )

        db.commit()
        db.close()

        st.success(
            "Diagnóstico e terapia atualizados."
        )

        st.rerun()


# ============================================================
# 8 - RELATÓRIOS TÉCNICOS COMPLEMENTARES
# ============================================================

def mostrar_complementares_especial(
    registro,
):

    st.subheader(
        "8️⃣ Relatórios técnicos complementares"
    )

    st.info(
        "Registre a necessidade de avaliações técnicas "
        "complementares por especialistas e suas justificativas."
    )

    necessidade_atual = (
        registro.necessidade_relatorios_complementares
        or "Não verificado"
    )

    if necessidade_atual not in STATUS_SIM_NAO:

        necessidade_atual = "Não verificado"

    necessidade = st.selectbox(
        "Há necessidade de relatórios técnicos complementares?",
        STATUS_SIM_NAO,
        index=STATUS_SIM_NAO.index(
            necessidade_atual
        ),
        key="esp_comp_necessidade",
    )

    relatorios = st.text_area(
        "Relatórios / avaliações complementares indicados",
        value=(
            registro.relatorios_complementares
            or ""
        ),
        placeholder=(
            "Ex.: análise estrutural, estudo hidráulico-"
            "hidrológico, estudo geotécnico, ensaios "
            "tecnológicos, instrumentação, prova de carga "
            "ou outro estudo aplicável."
        ),
        key="esp_comp_relatorios",
    )

    justificativa = st.text_area(
        "Justificativa técnica",
        value=(
            registro.justificativa_relatorios
            or ""
        ),
        placeholder=(
            "Justifique a necessidade dos serviços "
            "complementares indicados."
        ),
        key="esp_comp_justificativa",
    )

    atual = (
        registro.complementares_verificados
        or "Não verificado"
    )

    if atual not in STATUS_VERIFICACAO:

        atual = "Não verificado"

    situacao = st.selectbox(
        "Conferência da etapa",
        STATUS_VERIFICACAO,
        index=STATUS_VERIFICACAO.index(
            atual
        ),
        key="esp_comp_status",
    )

    salvar = st.button(
        "💾 Salvar relatórios complementares",
        type="primary",
        key="esp_salvar_complementares",
    )

    if salvar:

        if (
            situacao == "Verificado"
            and necessidade == "Não verificado"
        ):

            st.error(
                "Informe se há necessidade de relatórios "
                "técnicos complementares."
            )

            return

        if (
            situacao == "Verificado"
            and necessidade == "Sim"
            and relatorios.strip() == ""
        ):

            st.error(
                "Informe quais relatórios ou avaliações "
                "complementares são necessários."
            )

            return

        if (
            situacao == "Verificado"
            and necessidade == "Sim"
            and justificativa.strip() == ""
        ):

            st.error(
                "Informe a justificativa técnica dos "
                "relatórios complementares."
            )

            return

        db = SessionLocal()

        dado = (
            db.query(RegistroEspecial)
            .filter(
                RegistroEspecial.id
                == registro.id
            )
            .first()
        )

        dado.necessidade_relatorios_complementares = (
            necessidade
        )

        dado.relatorios_complementares = (
            relatorios
        )

        dado.justificativa_relatorios = (
            justificativa
        )

        dado.complementares_verificados = (
            situacao
        )

        db.commit()
        db.close()

        st.success(
            "Relatórios complementares atualizados."
        )

        st.rerun()


# ============================================================
# 9 - ANDAMENTO DA INSPEÇÃO ESPECIAL
# ============================================================

def mostrar_andamento_especial(
    oae_ativa,
    inspecao_ativa,
    registro,
):

    st.subheader(
        "9️⃣ Andamento da inspeção especial"
    )

    total_componentes, componentes_resolvidos, nao_acessiveis = (
        contar_componentes_especial(
            oae_ativa.id,
            inspecao_ativa.id,
        )
    )

    andamento_classificacao = (
        verificar_andamento_classificacao(
            oae_ativa.id,
            inspecao_ativa.id,
        )
    )

    fotos = contar_fotografias_especial(
        oae_ativa.id,
        inspecao_ativa.id,
    )

    localizacao_ok = (
        registro.localizacao_verificada
        == "Verificado"
    )

    descricao_ok = (
        registro.descricao_obra_verificada
        == "Verificado"
    )

    vistoria_ok = (
        registro.vistoria_verificada
        == "Verificado"
    )

    patologia_ok = (
        registro.anomalias_verificadas
        == "Verificado"
        and total_componentes > 0
        and componentes_resolvidos
        == total_componentes
    )

    ensaios_ok = (
        registro.ensaios_verificados
        in [
            "Verificado",
            "Não se aplica",
        ]
    )

    classificacao_ok = (
        andamento_classificacao["concluida"]
    )

    terapia_ok = (
        registro.parecer_verificado
        == "Verificado"
    )

    complementares_ok = (
        registro.complementares_verificados
        in [
            "Verificado",
            "Não se aplica",
        ]
    )

    fotografias_ok = (
        fotos > 0
        and bool(
            (
                registro.localizacao_fotos_croqui
                or ""
            ).strip()
        )
    )

    etapas = [
        localizacao_ok,
        descricao_ok,
        vistoria_ok,
        patologia_ok,
        ensaios_ok,
        classificacao_ok,
        terapia_ok,
        complementares_ok,
        fotografias_ok,
    ]

    concluidas = sum(
        1
        for item in etapas
        if item
    )

    c1, c2, c3 = st.columns(3)

    with c1:

        st.metric(
            "Etapas atendidas",
            f"{concluidas}/{len(etapas)}",
        )

    with c2:

        st.metric(
            "Componentes verificados",
            (
                f"{componentes_resolvidos}/"
                f"{total_componentes}"
            ),
        )

    with c3:

        st.metric(
            "Fotografias vinculadas",
            fotos,
        )

    st.divider()

    st.checkbox(
        "Localização verificada",
        value=localizacao_ok,
        disabled=True,
        key=f"esp_and_loc_{inspecao_ativa.id}",
    )

    st.checkbox(
        "Descrição da obra verificada",
        value=descricao_ok,
        disabled=True,
        key=f"esp_and_desc_{inspecao_ativa.id}",
    )

    st.checkbox(
        "Inspeção / vistoria verificada",
        value=vistoria_ok,
        disabled=True,
        key=f"esp_and_vist_{inspecao_ativa.id}",
    )

    st.checkbox(
        "Patologia e componentes verificados",
        value=patologia_ok,
        disabled=True,
        key=f"esp_and_pat_{inspecao_ativa.id}",
    )

    st.checkbox(
        "Ensaios verificados ou não aplicáveis",
        value=ensaios_ok,
        disabled=True,
        key=f"esp_and_ens_{inspecao_ativa.id}",
    )

    st.checkbox(
        "Classificação concluída",
        value=classificacao_ok,
        disabled=True,
        key=f"esp_and_class_{inspecao_ativa.id}",
    )

    st.checkbox(
        "Diagnóstico e terapia verificados",
        value=terapia_ok,
        disabled=True,
        key=f"esp_and_ter_{inspecao_ativa.id}",
    )

    st.checkbox(
        "Relatórios complementares verificados",
        value=complementares_ok,
        disabled=True,
        key=f"esp_and_comp_{inspecao_ativa.id}",
    )

    st.checkbox(
        "Documentação fotográfica vinculada e localizada",
        value=fotografias_ok,
        disabled=True,
        key=f"esp_and_fotos_{inspecao_ativa.id}",
    )

    if nao_acessiveis > 0:

        st.warning(
            f"Há {nao_acessiveis} componente(s) registrado(s) "
            "como não acessível(is). Confira as justificativas "
            "antes da validação técnica da campanha."
        )

    st.divider()

    if concluidas == len(etapas):

        st.success(
            "Todas as verificações de preenchimento da "
            "inspeção especial foram atendidas."
        )

        if (
            registro.conclusao_preenchimento
            != "Concluído"
        ):

            concluir = st.button(
                "✅ Registrar preenchimento como concluído",
                type="primary",
                key="esp_concluir_preenchimento",
            )

            if concluir:

                db = SessionLocal()

                dado = (
                    db.query(RegistroEspecial)
                    .filter(
                        RegistroEspecial.id
                        == registro.id
                    )
                    .first()
                )

                dado.conclusao_preenchimento = (
                    "Concluído"
                )

                db.commit()
                db.close()

                st.rerun()

        else:

            st.success(
                "Preenchimento registrado como concluído."
            )

    else:

        st.warning(
            "Ainda existem etapas pendentes nesta "
            "inspeção especial."
        )

    st.info(
        "O status de preenchimento é um controle do software. "
        "Ele não substitui a avaliação, validação ou "
        "responsabilidade técnica do profissional."
    )


# ============================================================
# PREENCHIMENTO DA INSPEÇÃO ESPECIAL
# ============================================================

def mostrar_preenchimento_especial(
    oae_ativa,
    inspecao_ativa,
):

    if inspecao_ativa is None:

        st.info(
            "Selecione uma inspeção especial."
        )

        return

    if (
        inspecao_ativa.tipo_inspecao
        != "Especial"
    ):

        st.warning(
            "A inspeção selecionada não é do "
            "tipo Especial."
        )

        return

    registro = garantir_registro_especial(
        inspecao_ativa.id
    )

    st.write(
        "**Inspeção:** "
        f"{inspecao_ativa.data_inspecao.strftime('%d/%m/%Y')}"
    )

    st.write(
        "**Responsável:** "
        f"{inspecao_ativa.responsavel or 'Não informado'}"
    )

    if inspecao_ativa.registro_profissional:

        st.write(
            "**Registro profissional:** "
            f"{inspecao_ativa.registro_profissional}"
        )

    st.divider()

    st.caption(
        "Os campos de conteúdo são preenchidos diretamente. Os seletores de "
        "conferência indicam apenas se a etapa foi verificada/concluída e não "
        "bloqueiam a digitação dos demais campos."
    )

    abas = st.tabs(
        [
            "📍 Localização",
            "🌉 Descrição da obra",
            "🔎 Inspeção / vistoria",
            "⚠️ Patologia",
            "🧪 Ensaios",
            "⭐ Classificação",
            "🛠️ Terapia",
            "📑 Complementares",
            "✅ Andamento",
        ]
    )

    with abas[0]:

        mostrar_localizacao_historico(
            oae_ativa,
            inspecao_ativa,
            registro,
        )

    with abas[1]:

        mostrar_descricao_obra(
            registro,
        )

    with abas[2]:

        mostrar_vistoria(
            registro,
        )

    with abas[3]:

        mostrar_patologia_especial(
            oae_ativa,
            inspecao_ativa,
            registro,
        )

    with abas[4]:

        mostrar_ensaios_especial(
            inspecao_ativa,
            registro,
        )

    with abas[5]:

        mostrar_classificacao_especial(
            oae_ativa,
            inspecao_ativa,
        )

    with abas[6]:

        mostrar_terapia_especial(
            inspecao_ativa,
            registro,
        )

    with abas[7]:

        mostrar_complementares_especial(
            registro,
        )

    with abas[8]:

        mostrar_andamento_especial(
            oae_ativa,
            inspecao_ativa,
            registro,
        )


# ============================================================
# MÓDULO PRINCIPAL
# ============================================================

def mostrar_modulo_especial(
    oae_ativa,
    inspecao_ativa=None,
):

    st.header(
        "🟨 Inspeção Especial"
    )

    st.caption(
        "Módulo de inspeção pormenorizada da OAE, "
        "estruturado com base na ABNT NBR 9452:2023."
    )

    if oae_ativa is None:

        st.warning(
            "Selecione ou cadastre uma OAE."
        )

        return

    tab_nova, tab_preencher = st.tabs(
        [
            "➕ Nova inspeção especial",
            "📝 Preencher inspeção especial",
        ]
    )

    with tab_nova:

        mostrar_nova_inspecao_especial(
            oae_ativa
        )

    with tab_preencher:

        especiais = (
            buscar_inspecoes_especiais(
                oae_ativa.id
            )
        )

        if len(especiais) == 0:

            st.info(
                "Nenhuma inspeção especial "
                "cadastrada para esta OAE."
            )

            return

        ids = [
            item.id
            for item in especiais
        ]

        ordenadas = sorted(
            especiais,
            key=lambda item: (item.data_inspecao, item.id)
        )

        mapa = {
            item.id:
                (
                    f"{numero} - "
                    f"{item.data_inspecao.strftime('%d/%m/%Y')}"
                )
            for numero, item in enumerate(ordenadas, start=1)
        }

        id_padrao = ids[0]

        if (
            inspecao_ativa is not None
            and inspecao_ativa.id in ids
        ):

            id_padrao = (
                inspecao_ativa.id
            )

        selecionada_id = st.selectbox(
            "Inspeção especial",
            options=ids,
            format_func=lambda x:
                mapa[x],
            index=ids.index(
                id_padrao
            ),
            key="especial_selecionada",
        )

        db = SessionLocal()

        selecionada = (
            db.query(models.Inspecao)
            .filter(
                models.Inspecao.id
                == selecionada_id
            )
            .first()
        )

        db.close()

        mostrar_preenchimento_especial(
            oae_ativa,
            selecionada,
        )
