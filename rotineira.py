import streamlit as st

from datetime import date
from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    ForeignKey,
    UniqueConstraint,
    and_,
    or_,
)

from database import Base, SessionLocal
import models

from classificacao import (
    calcular_classificacao_consolidada,
    verificar_andamento_classificacao,
)


# ============================================================
# INSPEÇÃO ROTINEIRA
# ABNT NBR 9452:2023
# ITEM 4.2 E ANEXO B
#
# PRINCÍPIOS DE IMPLEMENTAÇÃO:
#
# - a inspeção rotineira acompanha periodicamente a OAE;
# - verifica anomalias anteriores e novas ocorrências;
# - registra intervenções executadas/em andamento;
# - registra recomendações terapêuticas;
# - utiliza os módulos existentes de:
#       Anomalias
#       Fotografias
#       Classificação
# - não repete o cadastro e os croquis da inspeção cadastral;
# - não transforma ausência de registro em ausência de anomalia;
# - não considera a quantidade de fotos, isoladamente,
#   comprovação de levantamento fotográfico completo.
# ============================================================


# ============================================================
# TABELA ESPECIALIZADA DA INSPEÇÃO ROTINEIRA
#
# Tabela nova.
# Não altera as tabelas antigas do banco.
# ============================================================

class RegistroRotineira(Base):

    __tablename__ = "registros_rotineira"

    __table_args__ = (
        UniqueConstraint(
            "inspecao_id",
            name="uq_registro_rotineira_inspecao",
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

    # --------------------------------------------------------
    # PARTE I - INFORMAÇÕES GERAIS
    # --------------------------------------------------------

    informacoes_localizacao_verificadas = Column(
        String,
        nullable=True,
    )

    sistema_estrutural_verificado = Column(
        String,
        nullable=True,
    )

    # --------------------------------------------------------
    # INSPEÇÃO VISUAL
    # --------------------------------------------------------

    tabuleiro_verificado = Column(
        String,
        nullable=True,
    )

    mesoestrutura_verificada = Column(
        String,
        nullable=True,
    )

    infraestrutura_verificada = Column(
        String,
        nullable=True,
    )

    detalhes_verificados = Column(
        String,
        nullable=True,
    )

    observacoes_acesso = Column(
        Text,
        nullable=True,
    )

    # --------------------------------------------------------
    # INTERVENÇÕES
    # --------------------------------------------------------

    reparos = Column(
        Text,
        nullable=True,
    )

    alargamento = Column(
        Text,
        nullable=True,
    )

    reforcos = Column(
        Text,
        nullable=True,
    )

    outras_intervencoes = Column(
        Text,
        nullable=True,
    )

    intervencoes_verificadas = Column(
        String,
        nullable=True,
    )

    # --------------------------------------------------------
    # ANOMALIAS
    # --------------------------------------------------------

    verificacao_anomalias_anteriores = Column(
        String,
        nullable=True,
    )

    verificacao_novas_ocorrencias = Column(
        String,
        nullable=True,
    )

    # --------------------------------------------------------
    # ALTERAÇÕES E INFORMAÇÕES COMPLEMENTARES
    # --------------------------------------------------------

    comentarios_alteracoes = Column(
        Text,
        nullable=True,
    )

    informacoes_complementares = Column(
        Text,
        nullable=True,
    )

    recomendacoes_terapeuticas = Column(
        Text,
        nullable=True,
    )

    informacoes_complementares_verificadas = Column(
        String,
        nullable=True,
    )

    # --------------------------------------------------------
    # FOTOGRAFIAS
    # --------------------------------------------------------

    abrangencia_fotografica = Column(
        String,
        nullable=True,
    )


# ============================================================
# CONSTANTES
# ============================================================

STATUS_VERIFICACAO = [
    "Não verificado",
    "Verificado",
    "Não se aplica",
]


STATUS_ANOMALIAS_ANTERIORES = [
    "Não verificado",
    "Verificadas",
    "Não existem anomalias anteriores em acompanhamento",
]


STATUS_NOVAS_OCORRENCIAS = [
    "Não verificado",
    "Verificado - sem novas ocorrências",
    "Verificado - novas ocorrências registradas",
]


STATUS_FOTOGRAFIAS = [
    "Não verificado",
    "Abrangência verificada pelo inspetor",
]


# ============================================================
# CONSULTAS DE INSPEÇÕES
# ============================================================

def buscar_inspecoes_rotineiras(
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
            == "Rotineira"
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


def buscar_ultima_inspecao_antes_da_data(
    oae_id,
    data_referencia,
):

    db = SessionLocal()

    dado = (
        db.query(models.Inspecao)
        .filter(
            models.Inspecao.oae_id
            == oae_id
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

    return dado


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


def buscar_inspecao_anterior(
    oae_id,
    inspecao_atual,
):

    db = SessionLocal()

    anterior = (
        db.query(models.Inspecao)
        .filter(
            models.Inspecao.oae_id == oae_id
        )
        .filter(
            models.Inspecao.id != inspecao_atual.id
        )
        .filter(
            or_(
                models.Inspecao.data_inspecao
                < inspecao_atual.data_inspecao,
                and_(
                    models.Inspecao.data_inspecao
                    == inspecao_atual.data_inspecao,
                    models.Inspecao.id
                    < inspecao_atual.id,
                ),
            )
        )
        .order_by(
            models.Inspecao.data_inspecao.desc(),
            models.Inspecao.id.desc(),
        )
        .first()
    )

    db.close()

    return anterior

# ============================================================
# REGISTRO ESPECIALIZADO
# ============================================================

def buscar_registro_rotineira(
    inspecao_id,
):

    db = SessionLocal()

    dado = (
        db.query(RegistroRotineira)
        .filter(
            RegistroRotineira.inspecao_id
            == inspecao_id
        )
        .first()
    )

    db.close()

    return dado


def garantir_registro_rotineira(
    inspecao_id,
):

    registro = buscar_registro_rotineira(
        inspecao_id
    )

    if registro is not None:

        return registro

    db = SessionLocal()

    novo = RegistroRotineira(
        inspecao_id=inspecao_id
    )

    db.add(
        novo
    )

    db.commit()

    db.close()

    return buscar_registro_rotineira(
        inspecao_id
    )


# ============================================================
# CONSULTAS DE COMPONENTES
# ============================================================

def buscar_componentes(
    oae_id,
):

    db = SessionLocal()

    dados = (
        db.query(models.Componente)
        .filter(
            models.Componente.oae_id
            == oae_id
        )
        .order_by(
            models.Componente.id
        )
        .all()
    )

    db.close()

    return dados


def buscar_nome_componente(
    componente_id,
):

    if componente_id is None:

        return "Não identificado"

    db = SessionLocal()

    componente = (
        db.query(models.Componente)
        .filter(
            models.Componente.id
            == componente_id
        )
        .first()
    )

    db.close()

    if componente is None:

        return "Não identificado"

    return componente.nome


# ============================================================
# ANOMALIAS
# ============================================================

def buscar_anomalias_anteriores(
    oae_id,
    inspecao_atual,
):

    db = SessionLocal()

    dados = (
        db.query(models.AnomaliaPermanente)
        .join(
            models.Inspecao,
            models.Inspecao.id
            == models.AnomaliaPermanente.inspecao_origem_id,
        )
        .filter(
            models.AnomaliaPermanente.oae_id == oae_id
        )
        .filter(
            models.AnomaliaPermanente.ativa == 1
        )
        .filter(
            or_(
                models.Inspecao.data_inspecao
                < inspecao_atual.data_inspecao,
                and_(
                    models.Inspecao.data_inspecao
                    == inspecao_atual.data_inspecao,
                    models.Inspecao.id
                    < inspecao_atual.id,
                ),
            )
        )
        .order_by(
            models.AnomaliaPermanente.id
        )
        .all()
    )

    db.close()

    return dados



def buscar_observacao_anomalia(
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


def buscar_novas_anomalias(
    oae_id,
    inspecao_id,
):

    db = SessionLocal()

    dados = (
        db.query(models.AnomaliaPermanente)
        .filter(
            models.AnomaliaPermanente.oae_id
            == oae_id
        )
        .filter(
            models.AnomaliaPermanente.inspecao_origem_id
            == inspecao_id
        )
        .order_by(
            models.AnomaliaPermanente.id
        )
        .all()
    )

    db.close()

    return dados


def contar_anomalias_anteriores_verificadas(
    oae_id,
    inspecao_atual,
):

    anteriores = buscar_anomalias_anteriores(
        oae_id,
        inspecao_atual,
    )

    total = len(
        anteriores
    )

    verificadas = 0

    for anomalia in anteriores:

        observacao = buscar_observacao_anomalia(
            anomalia.id,
            inspecao_atual.id,
        )

        if observacao is not None:

            verificadas += 1

    return total, verificadas


# ============================================================
# FOTOGRAFIAS
# ============================================================

def contar_fotografias(
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


# ============================================================
# CLASSIFICAÇÃO
# ============================================================

def buscar_classificacao(
    oae_id,
    inspecao_id,
):

    andamento = (
        verificar_andamento_classificacao(
            oae_id,
            inspecao_id,
        )
    )

    notas = (
        calcular_classificacao_consolidada(
            oae_id,
            inspecao_id,
        )
    )

    return andamento, notas


# ============================================================
# PERIODICIDADE
# ============================================================

def calcular_intervalo_dias(
    data_anterior,
    data_atual,
):

    if (
        data_anterior is None
        or data_atual is None
    ):

        return None

    return (
        data_atual
        - data_anterior
    ).days


def data_limite_um_ano(
    data_anterior,
):

    if data_anterior is None:

        return None

    try:

        return data_anterior.replace(
            year=data_anterior.year + 1
        )

    except ValueError:

        # 29/02 -> 28/02 no ano seguinte, quando não bissexto.
        return data_anterior.replace(
            year=data_anterior.year + 1,
            day=28,
        )


def mostrar_aviso_periodicidade(
    ultima_inspecao,
    data_nova,
):

    if ultima_inspecao is None:

        st.info(
            "Não há inspeção anterior cadastrada "
            "para cálculo do intervalo."
        )

        return

    dias = calcular_intervalo_dias(
        ultima_inspecao.data_inspecao,
        data_nova,
    )

    limite_um_ano = data_limite_um_ano(
        ultima_inspecao.data_inspecao
    )

    st.write(
        "**Inspeção anterior:** "
        f"{ultima_inspecao.tipo_inspecao} - "
        f"{ultima_inspecao.data_inspecao.strftime('%d/%m/%Y')}"
    )

    st.write(
        f"**Intervalo:** {dias} dia(s)"
    )

    if dias < 0:

        st.error(
            "A data informada é anterior à última "
            "inspeção cadastrada."
        )

    elif data_nova <= limite_um_ano:

        st.success(
            "O intervalo informado não ultrapassa um ano "
            "em relação à inspeção anterior."
        )

    else:

        st.warning(
            "O intervalo informado é superior a um ano. "
            "A NBR 9452 estabelece, em regra, intervalo "
            "não superior a um ano para a inspeção rotineira. "
            "Existe condição específica para determinadas "
            "OAE ferroviárias, que deve ser verificada "
            "pelo responsável técnico."
        )

# ============================================================
# NOVA INSPEÇÃO ROTINEIRA
# ============================================================

def mostrar_nova_inspecao_rotineira(
    oae_ativa,
):

    st.subheader(
        "🟩 Nova inspeção rotineira"
    )

    st.info(
        "A inspeção rotineira é o acompanhamento periódico "
        "da OAE e deve verificar a evolução das anomalias "
        "já observadas, bem como novas ocorrências."
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
        key="rot_nova_data",
    )

    ultima_inspecao = (
        buscar_ultima_inspecao_antes_da_data(
            oae_ativa.id,
            data_inspecao,
        )
    )

    mostrar_aviso_periodicidade(
        ultima_inspecao,
        data_inspecao,
    )

    responsavel = st.text_input(
        "Inspetor responsável",
        placeholder="Ex.: João da Silva",
        key="rot_nova_responsavel",
    )

    registro_profissional = st.text_input(
        "Registro profissional",
        placeholder="Ex.: CREA-GO 123456/D",
        help=(
            "Registro profissional do responsável "
            "pela inspeção."
        ),
        key="rot_nova_registro",
    )

    observacoes = st.text_area(
        "Observações iniciais",
        placeholder=(
            "Ex.: inspeção visual realizada em condições "
            "normais de acesso."
        ),
        key="rot_nova_observacoes",
    )

    salvar = st.button(
        "Criar inspeção rotineira",
        type="primary",
        key="rot_criar_inspecao",
    )

    if not salvar:

        return

    if responsavel.strip() == "":

        st.error(
            "Informe o inspetor responsável."
        )

        return

    if (
        ultima_inspecao is not None
        and
        data_inspecao
        < ultima_inspecao.data_inspecao
    ):

        st.error(
            "A data da nova inspeção não pode ser "
            "anterior à inspeção anterior selecionada."
        )

        return

    db = SessionLocal()

    nova = models.Inspecao(
        oae_id=oae_ativa.id,
        tipo_inspecao="Rotineira",
        data_inspecao=data_inspecao,
        responsavel=responsavel,
        registro_profissional=
            registro_profissional,
        observacoes=observacoes,
    )

    db.add(
        nova
    )

    db.flush()

    # --------------------------------------------------------
    # Mantém compatibilidade com a estrutura já existente
    # do software.
    # --------------------------------------------------------

    detalhe = models.DetalheInspecao(
        inspecao_id=nova.id,
        comentarios_alteracoes="",
    )

    db.add(
        detalhe
    )

    registro = RegistroRotineira(
        inspecao_id=nova.id,
    )

    db.add(
        registro
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
        "Inspeção rotineira criada com sucesso."
    )

    st.rerun()


# ============================================================
# IDENTIFICAÇÃO E HISTÓRICO
# ============================================================

def mostrar_identificacao_historico(
    oae_ativa,
    inspecao_ativa,
    registro,
):

    st.subheader(
        "1️⃣ Informações gerais e histórico"
    )

    st.caption(
        "A inspeção rotineira reaproveita os dados cadastrais "
        "da OAE e registra o histórico das inspeções."
    )

    c1, c2, c3 = st.columns(3)

    with c1:

        st.write(
            "**OAE:**",
            oae_ativa.nome,
        )

        st.write(
            "**Código:**",
            oae_ativa.codigo
            or "Não informado",
        )

    with c2:

        st.write(
            "**Rodovia/Ferrovia:**",
            oae_ativa.rodovia
            or "Não informado",
        )

        st.write(
            "**Município/UF:**",
            (
                f"{oae_ativa.municipio or ''}"
                f" - "
                f"{oae_ativa.uf or ''}"
            ),
        )

    with c3:

        st.write(
            "**Data da inspeção:**",
            inspecao_ativa.data_inspecao.strftime(
                "%d/%m/%Y"
            ),
        )

        st.write(
            "**Inspetor:**",
            inspecao_ativa.responsavel
            or "Não informado",
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

    cadastrais = [
        item
        for item in inspecoes
        if item.tipo_inspecao
        == "Cadastral"
        and inspecao_eh_anterior(
            item,
            inspecao_ativa,
        )
    ]

    rotineiras = [
        item
        for item in inspecoes
        if item.tipo_inspecao
        == "Rotineira"
        and inspecao_eh_anterior(
            item,
            inspecao_ativa,
        )
    ]

    especiais = [
        item
        for item in inspecoes
        if item.tipo_inspecao
        == "Especial"
        and inspecao_eh_anterior(
            item,
            inspecao_ativa,
        )
    ]

    c1, c2, c3 = st.columns(3)

    with c1:

        st.write(
            "**Cadastral:**"
        )

        if len(cadastrais) > 0:

            st.write(
                cadastrais[-1]
                .data_inspecao
                .strftime("%d/%m/%Y")
            )

        else:

            st.write(
                "Não localizada"
            )

    with c2:

        st.write(
            "**Última rotineira:**"
        )

        if len(rotineiras) > 0:

            st.write(
                rotineiras[-1]
                .data_inspecao
                .strftime("%d/%m/%Y")
            )

        else:

            st.write(
                "Não localizada"
            )

    with c3:

        st.write(
            "**Especial:**"
        )

        if len(especiais) > 0:

            st.write(
                especiais[-1]
                .data_inspecao
                .strftime("%d/%m/%Y")
            )

        else:

            st.write(
                "Não localizada"
            )

    anterior = buscar_inspecao_anterior(
        oae_ativa.id,
        inspecao_ativa,
    )

    if anterior is not None:

        st.info(
            "Inspeção imediatamente anterior no sistema: "
            f"{anterior.tipo_inspecao} - "
            f"{anterior.data_inspecao.strftime('%d/%m/%Y')}."
        )

    st.divider()

    st.markdown(
        "#### Conferência das informações gerais"
    )

    localizacao = st.selectbox(
        "Identificação e localização",
        STATUS_VERIFICACAO,
        index=(
            STATUS_VERIFICACAO.index(
                registro.informacoes_localizacao_verificadas
            )
            if registro.informacoes_localizacao_verificadas
            in STATUS_VERIFICACAO
            else 0
        ),
        key="rot_info_localizacao",
    )

    sistema = st.selectbox(
        "Sistema estrutural",
        STATUS_VERIFICACAO,
        index=(
            STATUS_VERIFICACAO.index(
                registro.sistema_estrutural_verificado
            )
            if registro.sistema_estrutural_verificado
            in STATUS_VERIFICACAO
            else 0
        ),
        help=(
            "Confirme após confrontar as informações "
            "cadastrais com a condição observada."
        ),
        key="rot_info_sistema",
    )

    salvar = st.button(
        "💾 Salvar conferência das informações gerais",
        type="primary",
        key="rot_salvar_info",
    )

    if salvar:

        db = SessionLocal()

        dado = (
            db.query(RegistroRotineira)
            .filter(
                RegistroRotineira.id
                == registro.id
            )
            .first()
        )

        dado.informacoes_localizacao_verificadas = (
            localizacao
        )

        dado.sistema_estrutural_verificado = (
            sistema
        )

        db.commit()

        db.close()

        st.success(
            "Informações gerais atualizadas."
        )

        st.rerun()


# ============================================================
# INSPEÇÃO VISUAL
# ============================================================

def mostrar_inspecao_visual(
    registro,
):

    st.subheader(
        "2️⃣ Abrangência da inspeção visual"
    )

    st.info(
        "Registre a verificação visual dos tramos do "
        "tabuleiro, mesoestrutura e infraestrutura quando "
        "aparentes, além dos detalhes julgados necessários."
    )

    tabuleiro = st.selectbox(
        "Tramos que compõem o tabuleiro",
        STATUS_VERIFICACAO,
        index=(
            STATUS_VERIFICACAO.index(
                registro.tabuleiro_verificado
            )
            if registro.tabuleiro_verificado
            in STATUS_VERIFICACAO
            else 0
        ),
        key="rot_visual_tabuleiro",
    )

    mesoestrutura = st.selectbox(
        "Elementos da mesoestrutura",
        STATUS_VERIFICACAO,
        index=(
            STATUS_VERIFICACAO.index(
                registro.mesoestrutura_verificada
            )
            if registro.mesoestrutura_verificada
            in STATUS_VERIFICACAO
            else 0
        ),
        help=(
            "Use 'Não se aplica' somente quando "
            "tecnicamente cabível. Se o elemento existe "
            "mas não foi vistoriado, mantenha "
            "'Não verificado'."
        ),
        key="rot_visual_meso",
    )

    infraestrutura = st.selectbox(
        "Elementos da infraestrutura",
        STATUS_VERIFICACAO,
        index=(
            STATUS_VERIFICACAO.index(
                registro.infraestrutura_verificada
            )
            if registro.infraestrutura_verificada
            in STATUS_VERIFICACAO
            else 0
        ),
        help=(
            "A verificação refere-se aos elementos "
            "aparentes/acessíveis."
        ),
        key="rot_visual_infra",
    )

    detalhes = st.selectbox(
        "Detalhes julgados necessários",
        STATUS_VERIFICACAO,
        index=(
            STATUS_VERIFICACAO.index(
                registro.detalhes_verificados
            )
            if registro.detalhes_verificados
            in STATUS_VERIFICACAO
            else 0
        ),
        key="rot_visual_detalhes",
    )

    observacoes_acesso = st.text_area(
        "Observações sobre acesso, visibilidade e limitações",
        value=(
            registro.observacoes_acesso
            or ""
        ),
        placeholder=(
            "Ex.: infraestrutura parcialmente encoberta; "
            "acesso à face inferior realizado somente "
            "pelo encontro."
        ),
        key="rot_visual_acesso",
    )

    salvar = st.button(
        "💾 Salvar abrangência da inspeção visual",
        type="primary",
        key="rot_salvar_visual",
    )

    if salvar:

        db = SessionLocal()

        dado = (
            db.query(RegistroRotineira)
            .filter(
                RegistroRotineira.id
                == registro.id
            )
            .first()
        )

        dado.tabuleiro_verificado = (
            tabuleiro
        )

        dado.mesoestrutura_verificada = (
            mesoestrutura
        )

        dado.infraestrutura_verificada = (
            infraestrutura
        )

        dado.detalhes_verificados = (
            detalhes
        )

        dado.observacoes_acesso = (
            observacoes_acesso
        )

        db.commit()

        db.close()

        st.success(
            "Abrangência da inspeção visual salva."
        )

        st.rerun()


# ============================================================
# INTERVENÇÕES
# ============================================================

def mostrar_intervencoes(
    registro,
):

    st.subheader(
        "3️⃣ Intervenções executadas ou em andamento"
    )

    st.caption(
        "Registre reparos, alargamentos, reforços e outras "
        "intervenções identificadas."
    )

    reparos = st.text_area(
        "Reparos",
        value=registro.reparos or "",
        placeholder=(
            "Ex.: reparo localizado no concreto "
            "da longarina L1."
        ),
        key="rot_interv_reparos",
    )

    alargamento = st.text_area(
        "Alargamento",
        value=registro.alargamento or "",
        placeholder=(
            "Ex.: não observado ou descrever "
            "alargamento existente."
        ),
        key="rot_interv_alargamento",
    )

    reforcos = st.text_area(
        "Reforços",
        value=registro.reforcos or "",
        placeholder=(
            "Ex.: reforço com protensão externa "
            "ou outra intervenção observada."
        ),
        key="rot_interv_reforcos",
    )

    outras = st.text_area(
        "Outras intervenções",
        value=(
            registro.outras_intervencoes
            or ""
        ),
        key="rot_interv_outras",
    )

    situacao = st.selectbox(
        "Conferência da etapa",
        STATUS_VERIFICACAO,
        index=(
            STATUS_VERIFICACAO.index(
                registro.intervencoes_verificadas
            )
            if registro.intervencoes_verificadas
            in STATUS_VERIFICACAO
            else 0
        ),
        help=(
            "Pode ser marcada como Verificado mesmo quando "
            "nenhuma intervenção foi observada."
        ),
        key="rot_interv_status",
    )

    salvar = st.button(
        "💾 Salvar intervenções",
        type="primary",
        key="rot_salvar_intervencoes",
    )

    if salvar:

        db = SessionLocal()

        dado = (
            db.query(RegistroRotineira)
            .filter(
                RegistroRotineira.id
                == registro.id
            )
            .first()
        )

        dado.reparos = reparos
        dado.alargamento = alargamento
        dado.reforcos = reforcos
        dado.outras_intervencoes = outras

        dado.intervencoes_verificadas = (
            situacao
        )

        db.commit()

        db.close()

        st.success(
            "Intervenções atualizadas."
        )

        st.rerun()


# ============================================================
# ANOMALIAS ANTERIORES
# ============================================================

def mostrar_anomalias_anteriores(
    oae_ativa,
    inspecao_ativa,
    registro,
):

    st.subheader(
        "4️⃣ Evolução das anomalias anteriores"
    )

    anteriores = buscar_anomalias_anteriores(
        oae_ativa.id,
        inspecao_ativa,
    )

    total = len(
        anteriores
    )

    verificadas = 0

    if total == 0:

        st.info(
            "Não existem anomalias anteriores ativas "
            "em acompanhamento no sistema."
        )

    else:

        st.write(
            f"**Anomalias anteriores em acompanhamento:** "
            f"{total}"
        )

        dados = []

        for anomalia in anteriores:

            observacao = (
                buscar_observacao_anomalia(
                    anomalia.id,
                    inspecao_ativa.id,
                )
            )

            if observacao is not None:

                verificadas += 1

                situacao = (
                    observacao.situacao_observada
                    or "Registrada"
                )

            else:

                situacao = (
                    "Pendente nesta inspeção"
                )

            dados.append(
                {
                    "ID":
                        anomalia.id,

                    "Componente":
                        buscar_nome_componente(
                            anomalia.componente_id
                        ),

                    "Anomalia":
                        anomalia.tipo_anomalia,

                    "Localização":
                        anomalia.localizacao_referencia,

                    "Situação nesta inspeção":
                        situacao,
                }
            )

        st.dataframe(
            dados,
            width="stretch",
            hide_index=True,
        )

        st.progress(
            verificadas / total
        )

        st.caption(
            f"{verificadas}/{total} anomalia(s) "
            "anterior(es) possuem observação "
            "nesta inspeção."
        )

    if total == 0:

        opcoes_status = [
            "Não verificado",
            (
                "Não existem anomalias anteriores "
                "em acompanhamento"
            ),
        ]

    else:

        opcoes_status = [
            "Não verificado",
            "Verificadas",
        ]

    atual = (
        registro.verificacao_anomalias_anteriores
        or "Não verificado"
    )

    if atual not in opcoes_status:

        atual = "Não verificado"

    status = st.selectbox(
        "Conferência das anomalias anteriores",
        opcoes_status,
        index=opcoes_status.index(
            atual
        ),
        key="rot_anom_ant_status",
    )

    if (
        total > 0
        and
        verificadas < total
        and
        status == "Verificadas"
    ):

        st.warning(
            "Ainda existem anomalias anteriores sem "
            "observação nesta campanha. Registre a evolução "
            "no módulo ⚠️ Anomalias antes de concluir "
            "esta etapa."
        )

    salvar = st.button(
        "💾 Salvar situação das anomalias anteriores",
        type="primary",
        key="rot_salvar_anom_ant",
    )

    if salvar:

        if (
            total > 0
            and
            verificadas < total
            and
            status == "Verificadas"
        ):

            st.error(
                "Não é possível concluir esta etapa enquanto "
                "existirem anomalias anteriores sem observação "
                "na inspeção atual."
            )

            return

        db = SessionLocal()

        dado = (
            db.query(RegistroRotineira)
            .filter(
                RegistroRotineira.id
                == registro.id
            )
            .first()
        )

        dado.verificacao_anomalias_anteriores = (
            status
        )

        db.commit()

        db.close()

        st.success(
            "Verificação das anomalias anteriores salva."
        )

        st.rerun()


# ============================================================
# NOVAS OCORRÊNCIAS
# ============================================================

def mostrar_novas_ocorrencias(
    oae_ativa,
    inspecao_ativa,
    registro,
):

    st.subheader(
        "5️⃣ Novas ocorrências"
    )

    novas = buscar_novas_anomalias(
        oae_ativa.id,
        inspecao_ativa.id,
    )

    quantidade = len(
        novas
    )

    if quantidade == 0:

        st.info(
            "Nenhuma nova anomalia está cadastrada "
            "nesta inspeção."
        )

        st.caption(
            "Isso não significa automaticamente que "
            "não existem novas ocorrências. A verificação "
            "deve ser confirmada pelo inspetor."
        )

    else:

        st.success(
            f"{quantidade} nova(s) ocorrência(s) "
            "registrada(s) nesta inspeção."
        )

        dados = []

        for anomalia in novas:

            dados.append(
                {
                    "ID":
                        anomalia.id,

                    "Componente":
                        buscar_nome_componente(
                            anomalia.componente_id
                        ),

                    "Anomalia":
                        anomalia.tipo_anomalia,

                    "Localização":
                        anomalia.localizacao_referencia,

                    "Descrição inicial":
                        anomalia.descricao_inicial,
                }
            )

        st.dataframe(
            dados,
            width="stretch",
            hide_index=True,
        )

    atual = (
        registro.verificacao_novas_ocorrencias
        or "Não verificado"
    )

    opcoes = STATUS_NOVAS_OCORRENCIAS

    if atual not in opcoes:

        atual = "Não verificado"

    status = st.selectbox(
        "Conferência de novas ocorrências",
        opcoes,
        index=opcoes.index(
            atual
        ),
        key="rot_novas_status",
    )

    if (
        quantidade > 0
        and
        status
        == "Verificado - sem novas ocorrências"
    ):

        st.warning(
            "Existem novas anomalias cadastradas nesta "
            "inspeção. A situação selecionada é incompatível."
        )

    if (
        quantidade == 0
        and
        status
        == "Verificado - novas ocorrências registradas"
    ):

        st.warning(
            "Nenhuma nova anomalia está cadastrada nesta "
            "inspeção."
        )

    salvar = st.button(
        "💾 Salvar verificação de novas ocorrências",
        type="primary",
        key="rot_salvar_novas",
    )

    if salvar:

        if (
            quantidade > 0
            and
            status
            == "Verificado - sem novas ocorrências"
        ):

            st.error(
                "Corrija a situação antes de salvar."
            )

            return

        if (
            quantidade == 0
            and
            status
            == "Verificado - novas ocorrências registradas"
        ):

            st.error(
                "Registre as novas ocorrências no módulo "
                "⚠️ Anomalias antes de concluir."
            )

            return

        db = SessionLocal()

        dado = (
            db.query(RegistroRotineira)
            .filter(
                RegistroRotineira.id
                == registro.id
            )
            .first()
        )

        dado.verificacao_novas_ocorrencias = (
            status
        )

        db.commit()

        db.close()

        st.success(
            "Verificação de novas ocorrências salva."
        )

        st.rerun()


# ============================================================
# FOTOGRAFIAS
# ============================================================

def mostrar_fotografias_rotineira(
    oae_ativa,
    inspecao_ativa,
    registro,
):

    st.subheader(
        "6️⃣ Levantamento fotográfico"
    )

    quantidade = contar_fotografias(
        oae_ativa.id,
        inspecao_ativa.id,
    )

    c1, c2 = st.columns(2)

    with c1:

        st.metric(
            "Fotografias registradas",
            quantidade,
        )

    with c2:

        st.metric(
            "Referência mínima da ficha",
            "8 registros",
        )

    if quantidade >= 8:

        st.success(
            "A quantidade mínima de oito registros "
            "fotográficos foi atingida."
        )

    else:

        st.warning(
            f"Faltam {8 - quantidade} fotografia(s) "
            "para atingir os oito registros previstos "
            "na ficha da inspeção rotineira."
        )

    st.info(
        "A quantidade de fotografias, isoladamente, "
        "não comprova que o levantamento fotográfico está "
        "completo. O profissional deve conferir se as imagens "
        "representam adequadamente a OAE e as anomalias "
        "identificadas."
    )

    atual = (
        registro.abrangencia_fotografica
        or "Não verificado"
    )

    if atual not in STATUS_FOTOGRAFIAS:

        atual = "Não verificado"

    abrangencia = st.selectbox(
        "Abrangência do levantamento fotográfico",
        STATUS_FOTOGRAFIAS,
        index=STATUS_FOTOGRAFIAS.index(
            atual
        ),
        key="rot_fotos_abrangencia",
    )

    salvar = st.button(
        "💾 Salvar verificação fotográfica",
        type="primary",
        key="rot_salvar_fotos",
    )

    if salvar:

        db = SessionLocal()

        dado = (
            db.query(RegistroRotineira)
            .filter(
                RegistroRotineira.id
                == registro.id
            )
            .first()
        )

        dado.abrangencia_fotografica = (
            abrangencia
        )

        db.commit()

        db.close()

        st.success(
            "Verificação fotográfica salva."
        )

        st.rerun()


# ============================================================
# CLASSIFICAÇÃO
# ============================================================

def mostrar_classificacao_rotineira(
    oae_ativa,
    inspecao_ativa,
):

    st.subheader(
        "7️⃣ Classificação da OAE"
    )

    andamento, notas = (
        buscar_classificacao(
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
            "A classificação dos componentes "
            "está concluída nesta inspeção."
        )

    else:

        st.warning(
            "Ainda existem componentes pendentes "
            "de classificação."
        )

    if notas is not None:

        st.markdown(
            "#### Notas consolidadas atuais"
        )

        c1, c2, c3 = st.columns(3)

        with c1:

            st.metric(
                "Estrutural",
                (
                    notas["estrutural"]
                    if notas["estrutural"]
                    is not None
                    else "—"
                ),
            )

        with c2:

            st.metric(
                "Funcional",
                (
                    notas["funcional"]
                    if notas["funcional"]
                    is not None
                    else "NA"
                ),
            )

        with c3:

            st.metric(
                "Durabilidade",
                (
                    notas["durabilidade"]
                    if notas["durabilidade"]
                    is not None
                    else "—"
                ),
            )

    st.info(
        "A classificação é registrada no módulo "
        "⭐ Classificação. O módulo Rotineira apenas "
        "acompanha os registros vinculados à campanha."
    )


# ============================================================
# ALTERAÇÕES, INFORMAÇÕES E TERAPIA
# ============================================================

def mostrar_alteracoes_recomendacoes(
    inspecao_ativa,
    registro,
):

    st.subheader(
        "8️⃣ Alterações, informações complementares "
        "e recomendações"
    )

    st.caption(
        "Registre alterações do estado geral da OAE em "
        "relação à inspeção anterior e recomendações "
        "terapêuticas pertinentes."
    )

    comentarios = st.text_area(
        "Alterações do estado geral em relação "
        "à inspeção anterior",
        value=(
            registro.comentarios_alteracoes
            or ""
        ),
        placeholder=(
            "Ex.: aumento da abertura da fissura existente "
            "na longarina L1; surgimento de deterioração "
            "localizada no pavimento."
        ),
        key="rot_comentarios_alteracoes",
    )

    informacoes = st.text_area(
        "Informações complementares",
        value=(
            registro.informacoes_complementares
            or ""
        ),
        placeholder=(
            "Registre outras informações consideradas "
            "importantes para esta inspeção."
        ),
        key="rot_info_complementares",
    )

    recomendacoes = st.text_area(
        "Recomendações terapêuticas",
        value=(
            registro.recomendacoes_terapeuticas
            or ""
        ),
        placeholder=(
            "Ex.: manter acompanhamento da fissura; "
            "avaliar necessidade de intervenção; "
            "realizar limpeza da drenagem."
        ),
        help=(
            "A recomendação deve ser definida ou validada "
            "pelo profissional responsável."
        ),
        key="rot_recomendacoes",
    )

    atual = (
        registro
        .informacoes_complementares_verificadas
        or "Não verificado"
    )

    if atual not in STATUS_VERIFICACAO:

        atual = "Não verificado"

    status = st.selectbox(
        "Conferência da etapa",
        STATUS_VERIFICACAO,
        index=STATUS_VERIFICACAO.index(
            atual
        ),
        key="rot_info_comp_status",
    )

    salvar = st.button(
        "💾 Salvar alterações e recomendações",
        type="primary",
        key="rot_salvar_complementares",
    )

    if salvar:

        db = SessionLocal()

        dado = (
            db.query(RegistroRotineira)
            .filter(
                RegistroRotineira.id
                == registro.id
            )
            .first()
        )

        dado.comentarios_alteracoes = (
            comentarios
        )

        dado.informacoes_complementares = (
            informacoes
        )

        dado.recomendacoes_terapeuticas = (
            recomendacoes
        )

        dado.informacoes_complementares_verificadas = (
            status
        )

        # ----------------------------------------------------
        # Atualiza também o campo antigo para manter
        # compatibilidade com o restante do app.
        # ----------------------------------------------------

        detalhe = (
            db.query(models.DetalheInspecao)
            .filter(
                models.DetalheInspecao.inspecao_id
                == inspecao_ativa.id
            )
            .first()
        )

        if detalhe is not None:

            detalhe.comentarios_alteracoes = (
                comentarios
            )

        db.commit()

        db.close()

        st.success(
            "Alterações e recomendações salvas."
        )

        st.rerun()


# ============================================================
# ANDAMENTO
# ============================================================

def mostrar_andamento_rotineira(
    oae_ativa,
    inspecao_ativa,
    registro,
):

    st.subheader(
        "9️⃣ Andamento da inspeção rotineira"
    )

    total_anteriores, verificadas_anteriores = (
        contar_anomalias_anteriores_verificadas(
            oae_ativa.id,
            inspecao_ativa,
        )
    )

    novas = buscar_novas_anomalias(
        oae_ativa.id,
        inspecao_ativa.id,
    )

    quantidade_novas = len(
        novas
    )

    fotos = contar_fotografias(
        oae_ativa.id,
        inspecao_ativa.id,
    )

    andamento_classificacao = (
        verificar_andamento_classificacao(
            oae_ativa.id,
            inspecao_ativa.id,
        )
    )

    # --------------------------------------------------------
    # INFORMAÇÕES GERAIS
    # --------------------------------------------------------

    info_ok = (
        registro.informacoes_localizacao_verificadas
        == "Verificado"
        and
        registro.sistema_estrutural_verificado
        == "Verificado"
    )

    # --------------------------------------------------------
    # INSPEÇÃO VISUAL
    # Não verificado não conclui.
    # "Não se aplica" é aceito quando tecnicamente cabível.
    # --------------------------------------------------------

    visual_status = [
        registro.tabuleiro_verificado,
        registro.mesoestrutura_verificada,
        registro.infraestrutura_verificada,
        registro.detalhes_verificados,
    ]

    visual_ok = all(
        item in [
            "Verificado",
            "Não se aplica",
        ]
        for item in visual_status
    )

    # --------------------------------------------------------
    # INTERVENÇÕES
    # --------------------------------------------------------

    intervencoes_ok = (
        registro.intervencoes_verificadas
        in [
            "Verificado",
            "Não se aplica",
        ]
    )

    # --------------------------------------------------------
    # ANOMALIAS ANTERIORES
    # --------------------------------------------------------

    if total_anteriores == 0:

        anomalias_anteriores_ok = (
            registro.verificacao_anomalias_anteriores
            ==
            (
                "Não existem anomalias anteriores "
                "em acompanhamento"
            )
        )

    else:

        anomalias_anteriores_ok = (
            verificadas_anteriores
            == total_anteriores
            and
            registro.verificacao_anomalias_anteriores
            == "Verificadas"
        )

    # --------------------------------------------------------
    # NOVAS OCORRÊNCIAS
    # --------------------------------------------------------

    if quantidade_novas == 0:

        novas_ok = (
            registro.verificacao_novas_ocorrencias
            ==
            "Verificado - sem novas ocorrências"
        )

    else:

        novas_ok = (
            registro.verificacao_novas_ocorrencias
            ==
            "Verificado - novas ocorrências registradas"
        )

    # --------------------------------------------------------
    # FOTOS
    # --------------------------------------------------------

    minimo_fotos_ok = (
        fotos >= 8
    )

    abrangencia_fotos_ok = (
        registro.abrangencia_fotografica
        ==
        "Abrangência verificada pelo inspetor"
    )

    # --------------------------------------------------------
    # CLASSIFICAÇÃO
    # --------------------------------------------------------

    classificacao_ok = (
        andamento_classificacao["concluida"]
    )

    # --------------------------------------------------------
    # COMPLEMENTARES
    # --------------------------------------------------------

    complementares_ok = (
        registro
        .informacoes_complementares_verificadas
        in [
            "Verificado",
            "Não se aplica",
        ]
    )

    etapas = [
        info_ok,
        visual_ok,
        intervencoes_ok,
        anomalias_anteriores_ok,
        novas_ok,
        minimo_fotos_ok,
        abrangencia_fotos_ok,
        classificacao_ok,
        complementares_ok,
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
            "Fotografias",
            f"{fotos}/8",
        )

    with c3:

        st.metric(
            "Classificação",
            (
                "Concluída"
                if classificacao_ok
                else "Pendente"
            ),
        )

    if concluidas == len(etapas):

        st.success(
            "Todas as verificações de preenchimento da "
            "inspeção rotineira foram atendidas."
        )

    else:

        st.warning(
            "Ainda existem etapas pendentes nesta "
            "inspeção rotineira."
        )

    st.divider()

    st.checkbox(
        "Informações gerais e histórico verificados",
        value=info_ok,
        disabled=True,
        key=f"rot_and_info_{inspecao_ativa.id}",
    )

    st.checkbox(
        "Abrangência da inspeção visual verificada",
        value=visual_ok,
        disabled=True,
        key=f"rot_and_visual_{inspecao_ativa.id}",
    )

    st.checkbox(
        "Intervenções executadas ou em andamento verificadas",
        value=intervencoes_ok,
        disabled=True,
        key=f"rot_and_intervencoes_{inspecao_ativa.id}",
    )

    st.checkbox(
        "Evolução das anomalias anteriores verificada",
        value=anomalias_anteriores_ok,
        disabled=True,
        key=f"rot_and_anomalias_anteriores_{inspecao_ativa.id}",
    )

    if total_anteriores > 0:

        st.caption(
            f"Anomalias anteriores observadas nesta campanha: "
            f"{verificadas_anteriores}/{total_anteriores}"
        )

    else:

        st.caption(
            "Não existem anomalias anteriores ativas "
            "em acompanhamento."
        )

    st.checkbox(
        "Novas ocorrências verificadas",
        value=novas_ok,
        disabled=True,
        key=f"rot_and_novas_{inspecao_ativa.id}",
    )

    st.caption(
        f"Novas anomalias registradas nesta campanha: "
        f"{quantidade_novas}"
    )

    st.checkbox(
        "Mínimo de oito registros fotográficos atingido",
        value=minimo_fotos_ok,
        disabled=True,
        key=f"rot_and_minimo_fotos_{inspecao_ativa.id}",
    )

    st.checkbox(
        "Abrangência do levantamento fotográfico verificada",
        value=abrangencia_fotos_ok,
        disabled=True,
        key=f"rot_and_abrangencia_fotos_{inspecao_ativa.id}",
    )

    st.checkbox(
        "Classificação dos componentes concluída",
        value=classificacao_ok,
        disabled=True,
        key=f"rot_and_classificacao_{inspecao_ativa.id}",
    )

    st.checkbox(
        "Alterações, informações complementares e "
        "recomendações verificadas",
        value=complementares_ok,
        disabled=True,
        key=f"rot_and_complementares_{inspecao_ativa.id}",
    )

    st.info(
        "Este painel acompanha o preenchimento do sistema. "
        "A conclusão das etapas não substitui a avaliação, "
        "validação e responsabilidade técnica do profissional."
    )


# ============================================================
# PREENCHIMENTO DA ROTINEIRA
# ============================================================

def mostrar_preenchimento_rotineira(
    oae_ativa,
    inspecao_ativa,
):

    if inspecao_ativa is None:

        st.info(
            "Selecione uma inspeção rotineira."
        )

        return

    if (
        inspecao_ativa.tipo_inspecao
        != "Rotineira"
    ):

        st.warning(
            "A inspeção selecionada não é "
            "do tipo Rotineira."
        )

        return

    registro = garantir_registro_rotineira(
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

    if (
        inspecao_ativa.registro_profissional
    ):

        st.write(
            "**Registro profissional:** "
            f"{inspecao_ativa.registro_profissional}"
        )

    anterior = buscar_inspecao_anterior(
        oae_ativa.id,
        inspecao_ativa,
    )

    if anterior is not None:

        dias = calcular_intervalo_dias(
            anterior.data_inspecao,
            inspecao_ativa.data_inspecao,
        )

        st.caption(
            "Intervalo em relação à inspeção anterior: "
            f"{dias} dia(s)."
        )

    st.divider()

    st.caption(
        "Os campos de conteúdo são preenchidos diretamente. Os seletores de "
        "conferência indicam apenas se a etapa foi verificada/concluída e não "
        "bloqueiam a digitação dos demais campos."
    )

    abas = st.tabs(
        [
            "📍 Informações gerais",
            "👁️ Inspeção visual",
            "🛠️ Intervenções",
            "🔁 Anomalias anteriores",
            "🆕 Novas ocorrências",
            "📷 Fotografias",
            "⭐ Classificação",
            "📝 Alterações e terapia",
            "✅ Andamento",
        ]
    )

    with abas[0]:

        mostrar_identificacao_historico(
            oae_ativa,
            inspecao_ativa,
            registro,
        )

    with abas[1]:

        mostrar_inspecao_visual(
            registro,
        )

    with abas[2]:

        mostrar_intervencoes(
            registro,
        )

    with abas[3]:

        mostrar_anomalias_anteriores(
            oae_ativa,
            inspecao_ativa,
            registro,
        )

    with abas[4]:

        mostrar_novas_ocorrencias(
            oae_ativa,
            inspecao_ativa,
            registro,
        )

    with abas[5]:

        mostrar_fotografias_rotineira(
            oae_ativa,
            inspecao_ativa,
            registro,
        )

    with abas[6]:

        mostrar_classificacao_rotineira(
            oae_ativa,
            inspecao_ativa,
        )

    with abas[7]:

        mostrar_alteracoes_recomendacoes(
            inspecao_ativa,
            registro,
        )

    with abas[8]:

        mostrar_andamento_rotineira(
            oae_ativa,
            inspecao_ativa,
            registro,
        )


# ============================================================
# MÓDULO PRINCIPAL
# ============================================================

def mostrar_modulo_rotineira(
    oae_ativa,
    inspecao_ativa=None,
):

    st.header(
        "🟩 Inspeção Rotineira"
    )

    st.caption(
        "Módulo específico para acompanhamento periódico "
        "da OAE conforme a inspeção rotineira."
    )

    if oae_ativa is None:

        st.warning(
            "Selecione ou cadastre uma OAE."
        )

        return

    tab_nova, tab_preencher = st.tabs(
        [
            "➕ Nova inspeção rotineira",
            "📝 Preencher inspeção rotineira",
        ]
    )

    with tab_nova:

        mostrar_nova_inspecao_rotineira(
            oae_ativa
        )

    with tab_preencher:

        rotineiras = (
            buscar_inspecoes_rotineiras(
                oae_ativa.id
            )
        )

        if len(rotineiras) == 0:

            st.info(
                "Nenhuma inspeção rotineira "
                "cadastrada para esta OAE."
            )

            return

        ids = [
            item.id
            for item in rotineiras
        ]

        ordenadas = sorted(
            rotineiras,
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
            and
            inspecao_ativa.id
            in ids
        ):

            id_padrao = (
                inspecao_ativa.id
            )

        selecionada_id = st.selectbox(
            "Inspeção rotineira",
            options=ids,
            format_func=lambda x: mapa[x],
            index=ids.index(
                id_padrao
            ),
            key="rotineira_selecionada",
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

        mostrar_preenchimento_rotineira(
            oae_ativa,
            selecionada,
        )