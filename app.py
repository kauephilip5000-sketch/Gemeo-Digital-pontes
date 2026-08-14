import streamlit as st
import pandas as pd
import altair as alt

from database import engine, Base, SessionLocal
import models

from anomalias import mostrar_modulo_anomalias
from fotos import mostrar_modulo_fotografias
from historico import mostrar_historico_oae
from evolucao import mostrar_evolucao_oae

from classificacao import (
    mostrar_modulo_classificacao,
    calcular_classificacao_consolidada,
    componentes_classificados,
    nota_texto
)


# ============================================================
# CONFIGURAÇÃO DA PÁGINA
# ============================================================

st.set_page_config(
    page_title="Gêmeo Digital - Pontes",
    page_icon="🌉",
    layout="wide"
)


# ============================================================
# BANCO DE DADOS
# ============================================================

Base.metadata.create_all(bind=engine)


# ============================================================
# FUNÇÕES DE CONSULTA
# ============================================================

def buscar_oaes():

    db = SessionLocal()

    dados = (
        db.query(models.OAE)
        .order_by(models.OAE.id)
        .all()
    )

    db.close()

    return dados


def buscar_oae_por_id(oae_id):

    if oae_id is None:
        return None

    db = SessionLocal()

    dado = (
        db.query(models.OAE)
        .filter(
            models.OAE.id == oae_id
        )
        .first()
    )

    db.close()

    return dado


def buscar_componentes(oae_id):

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


def buscar_componente_por_id(
    componente_id
):

    if componente_id is None:
        return None

    db = SessionLocal()

    dado = (
        db.query(models.Componente)
        .filter(
            models.Componente.id
            == componente_id
        )
        .first()
    )

    db.close()

    return dado


def buscar_inspecoes(oae_id):

    db = SessionLocal()

    dados = (
        db.query(models.Inspecao)
        .filter(
            models.Inspecao.oae_id
            == oae_id
        )
        .order_by(
            models.Inspecao.data_inspecao.desc(),
            models.Inspecao.id.desc()
        )
        .all()
    )

    db.close()

    return dados


def buscar_inspecoes_cronologicas(
    oae_id
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
            models.Inspecao.id.asc()
        )
        .all()
    )

    db.close()

    return dados


def buscar_inspecao_por_id(
    inspecao_id
):

    if inspecao_id is None:
        return None

    db = SessionLocal()

    dado = (
        db.query(models.Inspecao)
        .filter(
            models.Inspecao.id
            == inspecao_id
        )
        .first()
    )

    db.close()

    return dado


def buscar_detalhe_inspecao(
    inspecao_id
):

    if inspecao_id is None:
        return None

    db = SessionLocal()

    detalhe = (
        db.query(models.DetalheInspecao)
        .filter(
            models.DetalheInspecao.inspecao_id
            == inspecao_id
        )
        .first()
    )

    db.close()

    return detalhe


# ============================================================
# CLASSIFICAÇÃO CONSOLIDADA
#
# Agora a regra vem do classificacao.py.
# ============================================================

def calcular_notas_finais(
    oae_id,
    inspecao_id
):

    resultado = (
        calcular_classificacao_consolidada(
            oae_id,
            inspecao_id
        )
    )

    if (
        resultado["estrutural"] is None
        and
        resultado["funcional"] is None
        and
        resultado["durabilidade"] is None
    ):

        return None

    return {
        "estrutural":
            resultado["estrutural"],

        "funcional":
            resultado["funcional"],

        "durabilidade":
            resultado["durabilidade"]
    }


# ============================================================
# CONTADORES
# ============================================================

def contar_dados_gerais():

    db = SessionLocal()

    dados = {
        "oaes":
            db.query(models.OAE).count(),

        "inspecoes":
            db.query(models.Inspecao).count(),

        "anomalias":
            (
                db.query(
                    models.AnomaliaPermanente
                )
                .filter(
                    models.AnomaliaPermanente.ativa
                    == 1
                )
                .count()
            ),

        "fotografias":
            db.query(
                models.Fotografia
            ).count()
    }

    db.close()

    return dados


def contar_dados_inspecao(
    oae_id,
    inspecao_id
):

    db = SessionLocal()

    anomalias = (
        db.query(
            models.ObservacaoAnomalia
        )
        .filter(
            models.ObservacaoAnomalia.inspecao_id
            == inspecao_id
        )
        .count()
    )

    fotografias = (
        db.query(
            models.Fotografia
        )
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

    return {
        "anomalias_observadas":
            anomalias,

        "fotografias":
            fotografias,

        "componentes_classificados":
            componentes_classificados(
                oae_id,
                inspecao_id
            )
    }


# ============================================================
# DADOS PARA GRÁFICOS
# ============================================================

def dados_evolucao_classificacoes(
    oae_id
):

    inspecoes = (
        buscar_inspecoes_cronologicas(
            oae_id
        )
    )

    dados = []

    for inspecao in inspecoes:

        notas = calcular_notas_finais(
            oae_id,
            inspecao.id
        )

        if notas is not None:

            dados.append(
                {
                    "Data":
                        inspecao.data_inspecao,

                    "Estrutural":
                        notas["estrutural"],

                    "Funcional":
                        notas["funcional"],

                    "Durabilidade":
                        notas["durabilidade"]
                }
            )

    return dados


def dados_anomalias_por_componente(
    oae_id
):

    componentes = buscar_componentes(
        oae_id
    )

    dados = []

    db = SessionLocal()

    for componente in componentes:

        quantidade = (
            db.query(
                models.AnomaliaPermanente
            )
            .filter(
                models.AnomaliaPermanente.oae_id
                == oae_id
            )
            .filter(
                models.AnomaliaPermanente.componente_id
                == componente.id
            )
            .filter(
                models.AnomaliaPermanente.ativa
                == 1
            )
            .count()
        )

        if quantidade > 0:

            dados.append(
                {
                    "Componente":
                        componente.nome,

                    "Anomalias":
                        quantidade
                }
            )

    db.close()

    return dados


# ============================================================
# GRÁFICO DE EVOLUÇÃO
#
# Sem interactive(), portanto o scroll não altera o gráfico.
# Também ignora valores NA.
# ============================================================

def mostrar_grafico_evolucao_dashboard(
    dados_evolucao
):

    if len(dados_evolucao) < 2:

        st.info(
            "São necessárias pelo menos duas inspeções "
            "com classificações para exibir o gráfico "
            "de evolução."
        )

        return

    linhas = []

    for item in dados_evolucao:

        data = item["Data"]

        if item["Estrutural"] is not None:

            linhas.append(
                {
                    "Data":
                        data,

                    "Parâmetro":
                        "Estrutural",

                    "Nota":
                        item["Estrutural"]
                }
            )

        if item["Funcional"] is not None:

            linhas.append(
                {
                    "Data":
                        data,

                    "Parâmetro":
                        "Funcional",

                    "Nota":
                        item["Funcional"]
                }
            )

        if item["Durabilidade"] is not None:

            linhas.append(
                {
                    "Data":
                        data,

                    "Parâmetro":
                        "Durabilidade",

                    "Nota":
                        item["Durabilidade"]
                }
            )

    if len(linhas) == 0:

        st.info(
            "Ainda não existem classificações "
            "aplicáveis suficientes para o gráfico."
        )

        return

    df = pd.DataFrame(
        linhas
    )

    df = df.sort_values(
        "Data"
    )

    grafico = (
        alt.Chart(
            df
        )
        .mark_line(
            point=True
        )
        .encode(

            x=alt.X(
                "Data:T",
                title="Data da inspeção",
                sort="ascending",
                axis=alt.Axis(
                    format="%d/%m/%Y",
                    labelAngle=0
                )
            ),

            y=alt.Y(
                "Nota:Q",
                title="Nota",
                scale=alt.Scale(
                    domain=[
                        0,
                        5
                    ]
                ),
                axis=alt.Axis(
                    tickMinStep=1
                )
            ),

            color=alt.Color(
                "Parâmetro:N",
                title="Parâmetro"
            ),

            tooltip=[
                alt.Tooltip(
                    "Data:T",
                    title="Data",
                    format="%d/%m/%Y"
                ),

                alt.Tooltip(
                    "Parâmetro:N",
                    title="Parâmetro"
                ),

                alt.Tooltip(
                    "Nota:Q",
                    title="Nota"
                )
            ]
        )
        .properties(
            height=350
        )
    )

    st.altair_chart(
        grafico,
        width="stretch"
    )


# ============================================================
# GRÁFICO DE ANOMALIAS
# ============================================================

def mostrar_grafico_anomalias_dashboard(
    dados_anomalias
):

    if len(dados_anomalias) == 0:

        st.info(
            "Nenhuma anomalia permanente "
            "cadastrada para esta OAE."
        )

        return

    df = pd.DataFrame(
        dados_anomalias
    )

    grafico = (
        alt.Chart(
            df
        )
        .mark_bar()
        .encode(

            x=alt.X(
                "Anomalias:Q",
                title="Quantidade de anomalias",
                axis=alt.Axis(
                    tickMinStep=1
                )
            ),

            y=alt.Y(
                "Componente:N",
                title="Componente",
                sort="-x"
            ),

            tooltip=[
                alt.Tooltip(
                    "Componente:N",
                    title="Componente"
                ),

                alt.Tooltip(
                    "Anomalias:Q",
                    title="Quantidade"
                )
            ]
        )
        .properties(
            height=300
        )
    )

    st.altair_chart(
        grafico,
        width="stretch"
    )


# ============================================================
# ANOMALIAS ANTERIORES
# ============================================================

def contar_anomalias_anteriores(
    oae_id,
    inspecao_atual
):

    db = SessionLocal()

    anomalias = (
        db.query(
            models.AnomaliaPermanente
        )
        .filter(
            models.AnomaliaPermanente.oae_id
            == oae_id
        )
        .filter(
            models.AnomaliaPermanente.ativa
            == 1
        )
        .all()
    )

    quantidade = 0

    for anomalia in anomalias:

        inspecao_origem = (
            db.query(
                models.Inspecao
            )
            .filter(
                models.Inspecao.id
                == anomalia.inspecao_origem_id
            )
            .first()
        )

        if (
            inspecao_origem is not None
            and
            inspecao_origem.data_inspecao
            < inspecao_atual.data_inspecao
        ):

            quantidade += 1

    db.close()

    return quantidade


def contar_anomalias_anteriores_observadas(
    oae_id,
    inspecao_atual
):

    db = SessionLocal()

    anomalias = (
        db.query(
            models.AnomaliaPermanente
        )
        .filter(
            models.AnomaliaPermanente.oae_id
            == oae_id
        )
        .filter(
            models.AnomaliaPermanente.ativa
            == 1
        )
        .all()
    )

    quantidade = 0

    for anomalia in anomalias:

        inspecao_origem = (
            db.query(
                models.Inspecao
            )
            .filter(
                models.Inspecao.id
                == anomalia.inspecao_origem_id
            )
            .first()
        )

        if (
            inspecao_origem is not None
            and
            inspecao_origem.data_inspecao
            < inspecao_atual.data_inspecao
        ):

            observacao = (
                db.query(
                    models.ObservacaoAnomalia
                )
                .filter(
                    models.ObservacaoAnomalia.anomalia_id
                    == anomalia.id
                )
                .filter(
                    models.ObservacaoAnomalia.inspecao_id
                    == inspecao_atual.id
                )
                .first()
            )

            if observacao is not None:

                quantidade += 1

    db.close()

    return quantidade


# ============================================================
# NAVEGAÇÃO
# ============================================================

PAGINAS = [
    "🏠 Visão geral",
    "🌉 Dados da OAE",
    "🧱 Componentes",
    "📋 Inspeções",
    "⚠️ Anomalias",
    "⭐ Classificação",
    "📷 Fotografias",
    "📈 Histórico e evolução",
    "📄 Relatórios"
]


def ir_para_pagina(nome):

    st.session_state.pagina_destino = (
        nome
    )

    st.rerun()


# ============================================================
# SESSION STATE
# ============================================================

if "oae_ativa_id" not in st.session_state:

    st.session_state.oae_ativa_id = None


if "inspecao_ativa_id" not in st.session_state:

    st.session_state.inspecao_ativa_id = None


if "componente_ativo_id" not in st.session_state:

    st.session_state.componente_ativo_id = None


if "pagina_menu" not in st.session_state:

    st.session_state.pagina_menu = (
        "🏠 Visão geral"
    )


# Corrige também a navegação dos botões rápidos.
if "pagina_destino" in st.session_state:

    destino = (
        st.session_state.pagina_destino
    )

    if destino in PAGINAS:

        st.session_state.pagina_menu = (
            destino
        )

    del st.session_state.pagina_destino


# ============================================================
# CONTEXTO
# ============================================================

oaes = buscar_oaes()

oae_ativa = None
inspecao_ativa = None
componente_ativo = None


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    st.title(
        "🌉 Gêmeo Digital"
    )

    st.caption(
        "Inspeção e acompanhamento de OAEs"
    )

    st.divider()

    st.subheader(
        "Contexto de trabalho"
    )

    # ========================================================
    # OAE
    # ========================================================

    if len(oaes) == 0:

        st.warning(
            "Nenhuma OAE cadastrada."
        )

    else:

        ids_oaes = [
            oae.id
            for oae in oaes
        ]

        if (
            st.session_state.oae_ativa_id
            not in ids_oaes
        ):

            st.session_state.oae_ativa_id = (
                ids_oaes[0]
            )

        mapa_oaes = {
            oae.id:
                f"{oae.id} - {oae.nome}"
            for oae in oaes
        }

        oae_id = st.selectbox(
            "OAE ativa",
            options=ids_oaes,
            format_func=lambda x:
                mapa_oaes[x],
            index=ids_oaes.index(
                st.session_state.oae_ativa_id
            )
        )

        if (
            oae_id
            != st.session_state.oae_ativa_id
        ):

            st.session_state.oae_ativa_id = (
                oae_id
            )

            st.session_state.inspecao_ativa_id = None
            st.session_state.componente_ativo_id = None

            st.rerun()

        oae_ativa = buscar_oae_por_id(
            st.session_state.oae_ativa_id
        )

        # ====================================================
        # INSPEÇÃO ATIVA
        # ====================================================

        inspecoes_sidebar = buscar_inspecoes(
            oae_ativa.id
        )

        if len(inspecoes_sidebar) == 0:

            st.info(
                "Esta OAE ainda não possui inspeções."
            )

            st.session_state.inspecao_ativa_id = None

        else:

            ids_inspecoes = [
                item.id
                for item in inspecoes_sidebar
            ]

            if (
                st.session_state.inspecao_ativa_id
                not in ids_inspecoes
            ):

                st.session_state.inspecao_ativa_id = (
                    ids_inspecoes[0]
                )

            mapa_inspecoes = {
                item.id:
                    (
                        f"{item.id} - "
                        f"{item.tipo_inspecao} - "
                        f"{item.data_inspecao.strftime('%d/%m/%Y')}"
                    )
                for item in inspecoes_sidebar
            }

            inspecao_id = st.selectbox(
                "Inspeção ativa",
                options=ids_inspecoes,
                format_func=lambda x:
                    mapa_inspecoes[x],
                index=ids_inspecoes.index(
                    st.session_state.inspecao_ativa_id
                )
            )

            st.session_state.inspecao_ativa_id = (
                inspecao_id
            )

            inspecao_ativa = buscar_inspecao_por_id(
                inspecao_id
            )

        # ====================================================
        # COMPONENTE ATIVO
        # ====================================================

        componentes_sidebar = buscar_componentes(
            oae_ativa.id
        )

        if len(componentes_sidebar) == 0:

            st.info(
                "Esta OAE ainda não possui componentes."
            )

            st.session_state.componente_ativo_id = None

        else:

            ids_componentes = [
                item.id
                for item in componentes_sidebar
            ]

            if (
                st.session_state.componente_ativo_id
                not in ids_componentes
            ):

                st.session_state.componente_ativo_id = (
                    ids_componentes[0]
                )

            mapa_componentes = {
                item.id:
                    f"{item.id} - {item.nome}"
                for item in componentes_sidebar
            }

            componente_id = st.selectbox(
                "Componente ativo",
                options=ids_componentes,
                format_func=lambda x:
                    mapa_componentes[x],
                index=ids_componentes.index(
                    st.session_state.componente_ativo_id
                )
            )

            st.session_state.componente_ativo_id = (
                componente_id
            )

            componente_ativo = (
                buscar_componente_por_id(
                    componente_id
                )
            )

    # ========================================================
    # MENU
    # ========================================================

    st.divider()

    st.subheader(
        "Menu"
    )

    pagina = st.radio(
        "Navegação",
        PAGINAS,
        key="pagina_menu",
        label_visibility="collapsed"
    )

    st.divider()

    st.caption(
        "TCC 2 • Gêmeo Digital para Pontes"
    )


# ============================================================
# CABEÇALHO
# ============================================================

st.title(
    "🌉 Gêmeo Digital para Inspeção de Pontes"
)

st.caption(
    "Sistema de apoio à inspeção, diagnóstico "
    "e acompanhamento temporal de OAEs"
)


# ============================================================
# CONTEXTO SUPERIOR
# ============================================================

if oae_ativa is not None:

    coluna1, coluna2, coluna3 = (
        st.columns(3)
    )

    with coluna1:

        st.metric(
            "🌉 OAE ativa",
            oae_ativa.nome
        )

    with coluna2:

        if inspecao_ativa is None:

            st.metric(
                "📋 Inspeção ativa",
                "Não cadastrada"
            )

        else:

            st.metric(
                "📋 Inspeção ativa",
                inspecao_ativa.data_inspecao.strftime(
                    "%d/%m/%Y"
                )
            )

            st.caption(
                inspecao_ativa.tipo_inspecao
            )

    with coluna3:

        if componente_ativo is None:

            st.metric(
                "🧱 Componente ativo",
                "Não cadastrado"
            )

        else:

            st.metric(
                "🧱 Componente ativo",
                componente_ativo.nome
            )

            st.caption(
                componente_ativo.categoria
            )

    st.divider()


# ============================================================
# VISÃO GERAL
# ============================================================

if pagina == "🏠 Visão geral":

    st.header(
        "Painel geral"
    )

    st.caption(
        "Resumo dos dados cadastrados e da condição "
        "da OAE atualmente selecionada."
    )

    totais = contar_dados_gerais()

    c1, c2, c3, c4 = (
        st.columns(4)
    )

    with c1:

        st.metric(
            "🌉 OAEs cadastradas",
            totais["oaes"]
        )

    with c2:

        st.metric(
            "📋 Inspeções",
            totais["inspecoes"]
        )

    with c3:

        st.metric(
            "⚠️ Anomalias acompanhadas",
            totais["anomalias"]
        )

    with c4:

        st.metric(
            "📷 Fotografias",
            totais["fotografias"]
        )

    st.divider()

    if oae_ativa is None:

        st.warning(
            "Nenhuma OAE cadastrada."
        )

    else:

        # ====================================================
        # RESUMO DA OAE
        # ====================================================

        st.subheader(
            f"🌉 {oae_ativa.nome}"
        )

        c1, c2, c3, c4 = (
            st.columns(4)
        )

        with c1:

            st.write(
                "**Código**"
            )

            st.write(
                oae_ativa.codigo
                or
                "Não informado"
            )

        with c2:

            st.write(
                "**Localização**"
            )

            localizacao = (
                f"{oae_ativa.municipio or ''}"
            )

            if oae_ativa.uf:

                if localizacao:

                    localizacao += " - "

                localizacao += (
                    oae_ativa.uf
                )

            st.write(
                localizacao
                or
                "Não informada"
            )

        with c3:

            st.write(
                "**Rodovia**"
            )

            st.write(
                oae_ativa.rodovia
                or
                "Não informada"
            )

        with c4:

            st.write(
                "**Tipo estrutural**"
            )

            st.write(
                oae_ativa.tipo_estrutura
                or
                "Não informado"
            )

        st.divider()

        # ====================================================
        # CONDIÇÃO DA INSPEÇÃO ATIVA
        # ====================================================

        st.subheader(
            "⭐ Condição da inspeção ativa"
        )

        if inspecao_ativa is None:

            st.info(
                "Esta OAE ainda não possui inspeções."
            )

        else:

            componentes_oae = buscar_componentes(
                oae_ativa.id
            )

            total_componentes = len(
                componentes_oae
            )

            total_classificados = (
                componentes_classificados(
                    oae_ativa.id,
                    inspecao_ativa.id
                )
            )

            notas = calcular_notas_finais(
                oae_ativa.id,
                inspecao_ativa.id
            )

            if notas is None:

                st.info(
                    "Nenhum componente foi classificado "
                    "nesta inspeção."
                )

            else:

                c1, c2, c3 = (
                    st.columns(3)
                )

                with c1:

                    nota = (
                        notas["estrutural"]
                    )

                    st.metric(
                        "Estrutural",
                        (
                            nota
                            if nota is not None
                            else "—"
                        )
                    )

                    if nota is not None:

                        st.caption(
                            nota_texto(
                                nota
                            )
                        )

                with c2:

                    nota = (
                        notas["funcional"]
                    )

                    st.metric(
                        "Funcional",
                        (
                            nota
                            if nota is not None
                            else "NA"
                        )
                    )

                    if nota is not None:

                        st.caption(
                            nota_texto(
                                nota
                            )
                        )

                    else:

                        st.caption(
                            "Não aplicável"
                        )

                with c3:

                    nota = (
                        notas["durabilidade"]
                    )

                    st.metric(
                        "Durabilidade",
                        (
                            nota
                            if nota is not None
                            else "—"
                        )
                    )

                    if nota is not None:

                        st.caption(
                            nota_texto(
                                nota
                            )
                        )

                if (
                    total_componentes > 0
                    and
                    total_classificados
                    == total_componentes
                ):

                    st.success(
                        "Todos os componentes cadastrados "
                        "foram classificados nesta inspeção."
                    )

                else:

                    st.warning(
                        "A consolidação é provisória. "
                        "Existem componentes pendentes."
                    )

        # ====================================================
        # ANDAMENTO
        # ====================================================

        st.subheader(
            "📊 Andamento da inspeção"
        )

        if inspecao_ativa is None:

            st.info(
                "Nenhuma inspeção ativa."
            )

        else:

            total_componentes = len(
                buscar_componentes(
                    oae_ativa.id
                )
            )

            classificados = (
                componentes_classificados(
                    oae_ativa.id,
                    inspecao_ativa.id
                )
            )

            pendentes = max(
                total_componentes
                - classificados,
                0
            )

            percentual = (
                classificados
                / total_componentes
                if total_componentes > 0
                else 0
            )

            c1, c2, c3 = (
                st.columns(3)
            )

            with c1:

                st.metric(
                    "Componentes cadastrados",
                    total_componentes
                )

            with c2:

                st.metric(
                    "Classificados",
                    classificados
                )

            with c3:

                st.metric(
                    "Pendentes",
                    pendentes
                )

            st.progress(
                percentual
            )

            st.caption(
                f"{percentual * 100:.0f}% dos componentes "
                f"possuem classificação nesta inspeção."
            )

        st.divider()

        # ====================================================
        # EVOLUÇÃO
        # ====================================================

        st.subheader(
            "📈 Evolução da condição da OAE"
        )

        dados_evolucao = (
            dados_evolucao_classificacoes(
                oae_ativa.id
            )
        )

        mostrar_grafico_evolucao_dashboard(
            dados_evolucao
        )

        st.caption(
            "As linhas representam a evolução das notas "
            "consolidadas das inspeções registradas."
        )

        st.divider()

        esquerda, direita = (
            st.columns(2)
        )

        # ====================================================
        # ANOMALIAS
        # ====================================================

        with esquerda:

            st.subheader(
                "⚠️ Anomalias por componente"
            )

            dados_anomalias = (
                dados_anomalias_por_componente(
                    oae_ativa.id
                )
            )

            mostrar_grafico_anomalias_dashboard(
                dados_anomalias
            )

        # ====================================================
        # RESUMO INSPEÇÃO
        # ====================================================

        with direita:

            st.subheader(
                "📋 Resumo da inspeção ativa"
            )

            if inspecao_ativa is None:

                st.info(
                    "Nenhuma inspeção ativa."
                )

            else:

                resumo = contar_dados_inspecao(
                    oae_ativa.id,
                    inspecao_ativa.id
                )

                st.metric(
                    "⭐ Componentes classificados",
                    resumo[
                        "componentes_classificados"
                    ]
                )

                st.metric(
                    "⚠️ Anomalias observadas",
                    resumo[
                        "anomalias_observadas"
                    ]
                )

                st.metric(
                    "📷 Fotografias",
                    resumo[
                        "fotografias"
                    ]
                )

        st.divider()

        # ====================================================
        # ÚLTIMAS INSPEÇÕES
        # ====================================================

        st.subheader(
            "🕒 Últimas inspeções"
        )

        inspecoes_recentes = buscar_inspecoes(
            oae_ativa.id
        )

        if len(inspecoes_recentes) == 0:

            st.info(
                "Nenhuma inspeção cadastrada."
            )

        else:

            dados_tabela = []

            for inspecao in inspecoes_recentes[:5]:

                notas = calcular_notas_finais(
                    oae_ativa.id,
                    inspecao.id
                )

                if notas is None:

                    estrutural = "-"
                    funcional = "-"
                    durabilidade = "-"

                else:

                    estrutural = (
                        notas["estrutural"]
                        if notas["estrutural"]
                        is not None
                        else "—"
                    )

                    funcional = (
                        notas["funcional"]
                        if notas["funcional"]
                        is not None
                        else "NA"
                    )

                    durabilidade = (
                        notas["durabilidade"]
                        if notas["durabilidade"]
                        is not None
                        else "—"
                    )

                dados_tabela.append(
                    {
                        "Data":
                            inspecao.data_inspecao.strftime(
                                "%d/%m/%Y"
                            ),

                        "Tipo":
                            inspecao.tipo_inspecao,

                        "Estrutural":
                            estrutural,

                        "Funcional":
                            funcional,

                        "Durabilidade":
                            durabilidade
                    }
                )

            st.dataframe(
                dados_tabela,
                width="stretch",
                hide_index=True
            )

        st.divider()

        # ====================================================
        # AÇÕES RÁPIDAS
        # ====================================================

        st.subheader(
            "⚡ Ações rápidas"
        )

        c1, c2, c3, c4 = (
            st.columns(4)
        )

        with c1:

            if st.button(
                "➕ Nova inspeção",
                width="stretch"
            ):

                ir_para_pagina(
                    "📋 Inspeções"
                )

        with c2:

            if st.button(
                "⚠️ Registrar anomalia",
                width="stretch"
            ):

                ir_para_pagina(
                    "⚠️ Anomalias"
                )

        with c3:

            if st.button(
                "⭐ Classificar componente",
                width="stretch"
            ):

                ir_para_pagina(
                    "⭐ Classificação"
                )

        with c4:

            if st.button(
                "📷 Adicionar fotografia",
                width="stretch"
            ):

                ir_para_pagina(
                    "📷 Fotografias"
                )


# ============================================================
# DADOS DA OAE
# ============================================================

elif pagina == "🌉 Dados da OAE":

    st.header(
        "Dados da OAE"
    )

    tab1, tab2 = st.tabs(
        [
            "📋 OAE selecionada",
            "➕ Cadastrar nova OAE"
        ]
    )

    with tab1:

        if oae_ativa is None:

            st.info(
                "Nenhuma OAE cadastrada."
            )

        else:

            st.subheader(
                oae_ativa.nome
            )

            c1, c2 = (
                st.columns(2)
            )

            with c1:

                st.write(
                    "**ID:**",
                    oae_ativa.id
                )

                st.write(
                    "**Código:**",
                    oae_ativa.codigo
                )

                st.write(
                    "**Rodovia:**",
                    oae_ativa.rodovia
                )

                st.write(
                    "**Município:**",
                    oae_ativa.municipio
                )

                st.write(
                    "**UF:**",
                    oae_ativa.uf
                )

            with c2:

                st.write(
                    "**Ano de construção:**",
                    oae_ativa.ano_construcao
                )

                st.write(
                    "**Tipo estrutural:**",
                    oae_ativa.tipo_estrutura
                )

                st.write(
                    "**Número de vãos:**",
                    oae_ativa.numero_vaos
                )

                st.write(
                    "**Comprimento:**",
                    oae_ativa.comprimento_total,
                    "m"
                )

                st.write(
                    "**Largura:**",
                    oae_ativa.largura,
                    "m"
                )

                st.write(
                    "**Protensão:**",
                    oae_ativa.tipo_protensao
                )

            st.write(
                "**Observações:**"
            )

            st.write(
                oae_ativa.observacoes
                or
                "Nenhuma observação."
            )

    # ========================================================
    # NOVA OAE
    # ========================================================

    with tab2:

        st.subheader(
            "➕ Cadastrar nova OAE"
        )

        with st.form(
            "form_oae"
        ):

            c1, c2 = (
                st.columns(2)
            )

            with c1:

                nome = st.text_input(
                    "Nome da OAE"
                )

                codigo = st.text_input(
                    "Código"
                )

                rodovia = st.text_input(
                    "Rodovia"
                )

                municipio = st.text_input(
                    "Município"
                )

                uf = st.selectbox(
                    "UF",
                    [
                        "AC", "AL", "AP", "AM",
                        "BA", "CE", "DF", "ES",
                        "GO", "MA", "MT", "MS",
                        "MG", "PA", "PB", "PR",
                        "PE", "PI", "RJ", "RN",
                        "RS", "RO", "RR", "SC",
                        "SP", "SE", "TO"
                    ]
                )

                ano = st.number_input(
                    "Ano de construção",
                    min_value=1800,
                    max_value=2100,
                    step=1
                )

            with c2:

                estrutura = st.selectbox(
                    "Tipo estrutural",
                    [
                        "Concreto protendido",
                        "Concreto armado",
                        "Estrutura mista",
                        "Outro"
                    ]
                )

                vaos = st.number_input(
                    "Número de vãos",
                    min_value=1,
                    step=1
                )

                comprimento = st.number_input(
                    "Comprimento total (m)",
                    min_value=0.0,
                    step=0.1
                )

                largura = st.number_input(
                    "Largura (m)",
                    min_value=0.0,
                    step=0.1
                )

                protensao = st.selectbox(
                    "Tipo de protensão",
                    [
                        "Pré-tração",
                        "Pós-tração",
                        "Não informado",
                        "Não se aplica"
                    ]
                )

            observacoes = st.text_area(
                "Observações"
            )

            salvar = st.form_submit_button(
                "Salvar OAE"
            )

        if salvar:

            if nome.strip() == "":

                st.error(
                    "Informe o nome da OAE."
                )

            else:

                db = SessionLocal()

                nova = models.OAE(
                    nome=nome,
                    codigo=codigo,
                    rodovia=rodovia,
                    municipio=municipio,
                    uf=uf,
                    ano_construcao=ano,
                    tipo_estrutura=estrutura,
                    numero_vaos=vaos,
                    comprimento_total=comprimento,
                    largura=largura,
                    tipo_protensao=protensao,
                    observacoes=observacoes
                )

                db.add(
                    nova
                )

                db.commit()

                db.refresh(
                    nova
                )

                st.session_state.oae_ativa_id = (
                    nova.id
                )

                st.session_state.inspecao_ativa_id = None

                st.session_state.componente_ativo_id = None

                db.close()

                st.rerun()


# ============================================================
# COMPONENTES
# ============================================================

elif pagina == "🧱 Componentes":

    st.header(
        "Componentes"
    )

    if oae_ativa is None:

        st.warning(
            "Cadastre uma OAE primeiro."
        )

    else:

        st.write(
            f"**OAE:** "
            f"{oae_ativa.id} - "
            f"{oae_ativa.nome}"
        )

        tab1, tab2 = st.tabs(
            [
                "📋 Componentes cadastrados",
                "➕ Cadastrar componente"
            ]
        )

        with tab1:

            componentes = buscar_componentes(
                oae_ativa.id
            )

            if len(componentes) == 0:

                st.info(
                    "Nenhum componente cadastrado."
                )

            else:

                dados = []

                for item in componentes:

                    dados.append(
                        {
                            "ID":
                                item.id,

                            "Categoria":
                                item.categoria,

                            "Elemento":
                                item.nome,

                            "Relevância":
                                item.classificacao_elemento,

                            "Observações":
                                item.observacoes
                        }
                    )

                st.dataframe(
                    dados,
                    width="stretch",
                    hide_index=True
                )

        with tab2:

            st.subheader(
                "➕ Cadastrar componente"
            )

            st.caption(
                "A relevância principal, secundário ou "
                "complementar deve ser atribuída considerando "
                "a concepção estrutural da OAE."
            )

            with st.form(
                "form_componente"
            ):

                categoria = st.selectbox(
                    "Categoria",
                    [
                        "Superestrutura",
                        "Mesoestrutura",
                        "Infraestrutura",
                        "Encontros",
                        "Elementos complementares",
                        "Pista / via permanente"
                    ]
                )

                nome = st.text_input(
                    "Nome ou identificação"
                )

                classificacao = st.selectbox(
                    "Relevância do elemento",
                    [
                        "Principal",
                        "Secundário",
                        "Complementar",
                        "Não informado"
                    ]
                )

                observacoes = st.text_area(
                    "Observações"
                )

                salvar = st.form_submit_button(
                    "Salvar componente"
                )

            if salvar:

                if nome.strip() == "":

                    st.error(
                        "Informe o nome do componente."
                    )

                else:

                    db = SessionLocal()

                    novo = models.Componente(
                        oae_id=oae_ativa.id,
                        categoria=categoria,
                        nome=nome,
                        classificacao_elemento=
                            classificacao,
                        observacoes=observacoes
                    )

                    db.add(
                        novo
                    )

                    db.commit()

                    db.refresh(
                        novo
                    )

                    st.session_state.componente_ativo_id = (
                        novo.id
                    )

                    db.close()

                    st.rerun()


# ============================================================
# INSPEÇÕES
# ============================================================

elif pagina == "📋 Inspeções":

    st.header(
        "📋 Inspeções"
    )

    if oae_ativa is None:

        st.warning(
            "Cadastre ou selecione uma OAE."
        )

    else:

        st.write(
            f"**OAE:** "
            f"{oae_ativa.id} - "
            f"{oae_ativa.nome}"
        )

        tab1, tab2, tab3 = st.tabs(
            [
                "📋 Inspeções cadastradas",
                "➕ Nova inspeção",
                "✅ Andamento da inspeção ativa"
            ]
        )

        # ====================================================
        # INSPEÇÕES CADASTRADAS
        # ====================================================

        with tab1:

            inspecoes = buscar_inspecoes(
                oae_ativa.id
            )

            if len(inspecoes) == 0:

                st.info(
                    "Nenhuma inspeção cadastrada."
                )

            else:

                dados = []

                for inspecao in inspecoes:

                    notas = calcular_notas_finais(
                        oae_ativa.id,
                        inspecao.id
                    )

                    if notas is None:

                        estrutural = "-"
                        funcional = "-"
                        durabilidade = "-"

                    else:

                        estrutural = (
                            notas["estrutural"]
                            if notas["estrutural"]
                            is not None
                            else "—"
                        )

                        funcional = (
                            notas["funcional"]
                            if notas["funcional"]
                            is not None
                            else "NA"
                        )

                        durabilidade = (
                            notas["durabilidade"]
                            if notas["durabilidade"]
                            is not None
                            else "—"
                        )

                    dados.append(
                        {
                            "ID":
                                inspecao.id,

                            "Data":
                                inspecao.data_inspecao.strftime(
                                    "%d/%m/%Y"
                                ),

                            "Tipo":
                                inspecao.tipo_inspecao,

                            "Responsável":
                                inspecao.responsavel,

                            "Estrutural":
                                estrutural,

                            "Funcional":
                                funcional,

                            "Durabilidade":
                                durabilidade
                        }
                    )

                st.dataframe(
                    dados,
                    width="stretch",
                    hide_index=True
                )

        # ====================================================
        # NOVA INSPEÇÃO
        # ====================================================

        with tab2:

            st.subheader(
                "➕ Iniciar nova inspeção"
            )

            tipo = st.selectbox(
                "Tipo de inspeção",
                [
                    "Cadastral",
                    "Rotineira",
                    "Especial",
                    "Extraordinária"
                ],
                key="tipo_nova_inspecao"
            )

            if tipo == "Cadastral":

                st.info(
                    "Inspeção destinada ao cadastramento inicial "
                    "da OAE ou à atualização cadastral decorrente "
                    "de alterações relevantes na configuração "
                    "da obra."
                )

            elif tipo == "Rotineira":

                st.info(
                    "Inspeção de acompanhamento. Devem ser "
                    "verificadas as anomalias anteriormente "
                    "observadas e registradas novas ocorrências."
                )

                inspecoes_existentes = buscar_inspecoes(
                    oae_ativa.id
                )

                if len(inspecoes_existentes) > 0:

                    ultima = (
                        inspecoes_existentes[0]
                    )

                    st.write(
                        "**Última inspeção cadastrada:**"
                    )

                    st.write(
                        f"{ultima.tipo_inspecao} - "
                        f"{ultima.data_inspecao.strftime('%d/%m/%Y')}"
                    )

                    db = SessionLocal()

                    anomalias_ativas = (
                        db.query(
                            models.AnomaliaPermanente
                        )
                        .filter(
                            models.AnomaliaPermanente.oae_id
                            == oae_ativa.id
                        )
                        .filter(
                            models.AnomaliaPermanente.ativa
                            == 1
                        )
                        .count()
                    )

                    db.close()

                    st.metric(
                        "Anomalias atualmente em acompanhamento",
                        anomalias_ativas
                    )

            elif tipo == "Especial":

                st.warning(
                    "A inspeção especial possui caráter "
                    "pormenorizado e demanda maior detalhamento "
                    "da vistoria, anomalias, ensaios e diagnóstico."
                )

            elif tipo == "Extraordinária":

                st.warning(
                    "A inspeção extraordinária decorre de uma "
                    "demanda não programada, como impacto, "
                    "incêndio, evento natural ou necessidade "
                    "de avaliação mais criteriosa."
                )

            with st.form(
                "form_nova_inspecao"
            ):

                data = st.date_input(
                    "Data da inspeção",
                    format="DD/MM/YYYY"
                )

                responsavel = st.text_input(
                    "Responsável pela inspeção"
                )

                registro = st.text_input(
                    "Registro profissional"
                )

                observacoes_gerais = st.text_area(
                    "Observações gerais"
                )

                motivo_cadastral = None
                descricao_alteracao = None

                comentarios_alteracoes = None

                procedimento = None
                ensaios = None
                diagnostico = None
                recomendacoes = None

                motivo_extraordinaria = None
                data_evento = None
                descricao_evento = None
                componente_afetado_id = None
                terapia = None

                # =============================================
                # CADASTRAL
                # =============================================

                if tipo == "Cadastral":

                    st.markdown(
                        "### Dados específicos da inspeção cadastral"
                    )

                    motivo_cadastral = st.selectbox(
                        "Motivo da inspeção cadastral",
                        [
                            "Primeira inspeção da OAE",
                            "Alteração na configuração da obra"
                        ]
                    )

                    if (
                        motivo_cadastral
                        == "Alteração na configuração da obra"
                    ):

                        descricao_alteracao = (
                            st.text_area(
                                "Descreva a alteração realizada",
                                placeholder=(
                                    "Ex.: reforço estrutural, "
                                    "alargamento, alteração das dimensões "
                                    "ou mudança do sistema estrutural."
                                )
                            )
                        )

                # =============================================
                # ROTINEIRA
                # =============================================

                elif tipo == "Rotineira":

                    st.markdown(
                        "### Dados específicos da inspeção rotineira"
                    )

                    comentarios_alteracoes = (
                        st.text_area(
                            "Alterações observadas em relação "
                            "à inspeção anterior",
                            placeholder=(
                                "Descreva alterações do estado geral "
                                "da OAE, quando identificadas."
                            )
                        )
                    )

                # =============================================
                # ESPECIAL
                # =============================================

                elif tipo == "Especial":

                    st.markdown(
                        "### Dados específicos da inspeção especial"
                    )

                    procedimento = st.text_area(
                        "Procedimento utilizado na inspeção",
                        placeholder=(
                            "Descreva os procedimentos, recursos "
                            "de acesso e metodologia da vistoria."
                        )
                    )

                    ensaios = st.text_area(
                        "Ensaios previstos ou realizados",
                        placeholder=(
                            "Registre os ensaios não destrutivos "
                            "ou outras investigações aplicáveis."
                        )
                    )

                    diagnostico = st.text_area(
                        "Diagnóstico das anomalias",
                        placeholder=(
                            "Pode ser preenchido ou complementado "
                            "ao longo da inspeção."
                        )
                    )

                    recomendacoes = st.text_area(
                        "Recomendações e avaliações adicionais",
                        placeholder=(
                            "Registre avaliações complementares "
                            "ou recomendações técnicas."
                        )
                    )

                # =============================================
                # EXTRAORDINÁRIA
                # =============================================

                elif tipo == "Extraordinária":

                    st.markdown(
                        "### Dados específicos da inspeção extraordinária"
                    )

                    motivo_extraordinaria = (
                        st.selectbox(
                            "Motivo da inspeção",
                            [
                                "Avaliação mais criteriosa de elemento",
                                "Impacto de veículo",
                                "Impacto de trem",
                                "Impacto de embarcação",
                                "Incêndio",
                                "Inundação",
                                "Vendaval",
                                "Sismo",
                                "Outro evento"
                            ]
                        )
                    )

                    data_evento = st.date_input(
                        "Data do evento",
                        format="DD/MM/YYYY"
                    )

                    descricao_evento = st.text_area(
                        "Descrição do evento ou ocorrência"
                    )

                    componentes = buscar_componentes(
                        oae_ativa.id
                    )

                    if len(componentes) > 0:

                        mapa_componentes_form = {
                            item.id:
                                (
                                    f"{item.id} - "
                                    f"{item.nome}"
                                )
                            for item in componentes
                        }

                        componente_afetado_id = (
                            st.selectbox(
                                "Elemento inicialmente afetado",
                                options=[
                                    None
                                ] + [
                                    item.id
                                    for item in componentes
                                ],
                                format_func=lambda x:
                                    (
                                        "Não definido"
                                        if x is None
                                        else
                                        mapa_componentes_form[x]
                                    )
                            )
                        )

                    terapia = st.text_area(
                        "Terapia ou providência recomendada",
                        placeholder=(
                            "Pode ser complementada após "
                            "avaliação técnica."
                        )
                    )

                salvar_inspecao = (
                    st.form_submit_button(
                        "Iniciar inspeção"
                    )
                )

            if salvar_inspecao:

                db = SessionLocal()

                nova = models.Inspecao(
                    oae_id=oae_ativa.id,
                    tipo_inspecao=tipo,
                    data_inspecao=data,
                    responsavel=responsavel,
                    registro_profissional=registro,
                    observacoes=observacoes_gerais
                )

                db.add(
                    nova
                )

                db.commit()

                db.refresh(
                    nova
                )

                detalhe = models.DetalheInspecao(
                    inspecao_id=nova.id,

                    motivo_cadastral=
                        motivo_cadastral,

                    descricao_alteracao=
                        descricao_alteracao,

                    comentarios_alteracoes=
                        comentarios_alteracoes,

                    procedimento_utilizado=
                        procedimento,

                    ensaios_previstos=
                        ensaios,

                    diagnostico=
                        diagnostico,

                    recomendacoes=
                        recomendacoes,

                    motivo_extraordinaria=
                        motivo_extraordinaria,

                    data_evento=
                        data_evento,

                    descricao_evento=
                        descricao_evento,

                    componente_afetado_id=
                        componente_afetado_id,

                    terapia_recomendada=
                        terapia
                )

                db.add(
                    detalhe
                )

                db.commit()

                novo_id = (
                    nova.id
                )

                db.close()

                st.session_state.inspecao_ativa_id = (
                    novo_id
                )

                st.success(
                    f"Inspeção {tipo} iniciada com sucesso."
                )

                st.rerun()

        # ====================================================
        # ANDAMENTO DA INSPEÇÃO
        # ====================================================

        with tab3:

            if inspecao_ativa is None:

                st.info(
                    "Nenhuma inspeção ativa."
                )

            else:

                st.subheader(
                    f"{inspecao_ativa.tipo_inspecao} - "
                    f"{inspecao_ativa.data_inspecao.strftime('%d/%m/%Y')}"
                )

                detalhe = buscar_detalhe_inspecao(
                    inspecao_ativa.id
                )

                resumo = contar_dados_inspecao(
                    oae_ativa.id,
                    inspecao_ativa.id
                )

                classificados = (
                    resumo[
                        "componentes_classificados"
                    ]
                )

                fotos = (
                    resumo[
                        "fotografias"
                    ]
                )

                observacoes_anomalias = (
                    resumo[
                        "anomalias_observadas"
                    ]
                )

                # =============================================
                # CADASTRAL
                # =============================================

                if (
                    inspecao_ativa.tipo_inspecao
                    == "Cadastral"
                ):

                    st.markdown(
                        "### Checklist da inspeção cadastral"
                    )

                    st.checkbox(
                        "OAE cadastrada no sistema",
                        value=True,
                        disabled=True
                    )

                    st.checkbox(
                        "Registro fotográfico iniciado",
                        value=fotos > 0,
                        disabled=True
                    )

                    st.checkbox(
                        "Classificação dos componentes iniciada",
                        value=classificados > 0,
                        disabled=True
                    )

                    if detalhe is not None:

                        st.write(
                            "**Motivo:**",
                            detalhe.motivo_cadastral
                            or
                            "Não registrado"
                        )

                    st.info(
                        "A etapa de documentos e croquis da "
                        "inspeção cadastral será implementada "
                        "em módulo próprio."
                    )

                # =============================================
                # ROTINEIRA
                # =============================================

                elif (
                    inspecao_ativa.tipo_inspecao
                    == "Rotineira"
                ):

                    st.markdown(
                        "### Checklist da inspeção rotineira"
                    )

                    anteriores = (
                        contar_anomalias_anteriores(
                            oae_ativa.id,
                            inspecao_ativa
                        )
                    )

                    verificadas = (
                        contar_anomalias_anteriores_observadas(
                            oae_ativa.id,
                            inspecao_ativa
                        )
                    )

                    st.write(
                        f"**Anomalias anteriores:** "
                        f"{anteriores}"
                    )

                    st.write(
                        f"**Anomalias anteriores verificadas "
                        f"nesta campanha:** "
                        f"{verificadas}"
                    )

                    st.checkbox(
                        "Anomalias anteriores verificadas",
                        value=(
                            anteriores == 0
                            or
                            verificadas == anteriores
                        ),
                        disabled=True
                    )

                    st.checkbox(
                        "Registro fotográfico realizado",
                        value=fotos > 0,
                        disabled=True
                    )

                    st.checkbox(
                        "Classificação iniciada",
                        value=classificados > 0,
                        disabled=True
                    )

                    if detalhe is not None:

                        if detalhe.comentarios_alteracoes:

                            st.write(
                                "**Alterações em relação "
                                "à inspeção anterior:**"
                            )

                            st.write(
                                detalhe.comentarios_alteracoes
                            )

                # =============================================
                # ESPECIAL
                # =============================================

                elif (
                    inspecao_ativa.tipo_inspecao
                    == "Especial"
                ):

                    st.markdown(
                        "### Checklist da inspeção especial"
                    )

                    st.checkbox(
                        "Procedimento de inspeção registrado",
                        value=(
                            detalhe is not None
                            and
                            bool(
                                detalhe.procedimento_utilizado
                            )
                        ),
                        disabled=True
                    )

                    st.checkbox(
                        "Ensaios registrados",
                        value=(
                            detalhe is not None
                            and
                            bool(
                                detalhe.ensaios_previstos
                            )
                        ),
                        disabled=True
                    )

                    st.checkbox(
                        "Anomalias registradas",
                        value=(
                            observacoes_anomalias > 0
                        ),
                        disabled=True
                    )

                    st.checkbox(
                        "Registro fotográfico realizado",
                        value=fotos > 0,
                        disabled=True
                    )

                    st.checkbox(
                        "Classificação iniciada",
                        value=classificados > 0,
                        disabled=True
                    )

                    st.checkbox(
                        "Diagnóstico registrado",
                        value=(
                            detalhe is not None
                            and
                            bool(
                                detalhe.diagnostico
                            )
                        ),
                        disabled=True
                    )

                # =============================================
                # EXTRAORDINÁRIA
                # =============================================

                elif (
                    inspecao_ativa.tipo_inspecao
                    == "Extraordinária"
                ):

                    st.markdown(
                        "### Checklist da inspeção extraordinária"
                    )

                    st.checkbox(
                        "Motivo da inspeção registrado",
                        value=(
                            detalhe is not None
                            and
                            bool(
                                detalhe.motivo_extraordinaria
                            )
                        ),
                        disabled=True
                    )

                    st.checkbox(
                        "Evento descrito",
                        value=(
                            detalhe is not None
                            and
                            bool(
                                detalhe.descricao_evento
                            )
                        ),
                        disabled=True
                    )

                    st.checkbox(
                        "Anomalias registradas",
                        value=(
                            observacoes_anomalias > 0
                        ),
                        disabled=True
                    )

                    st.checkbox(
                        "Documentação fotográfica registrada",
                        value=fotos > 0,
                        disabled=True
                    )

                    st.checkbox(
                        "Terapia ou providência registrada",
                        value=(
                            detalhe is not None
                            and
                            bool(
                                detalhe.terapia_recomendada
                            )
                        ),
                        disabled=True
                    )

                st.divider()

                st.subheader(
                    "Resumo da campanha"
                )

                c1, c2, c3 = (
                    st.columns(3)
                )

                with c1:

                    st.metric(
                        "Componentes classificados",
                        classificados
                    )

                with c2:

                    st.metric(
                        "Anomalias observadas",
                        observacoes_anomalias
                    )

                with c3:

                    st.metric(
                        "Fotografias",
                        fotos
                    )


# ============================================================
# ANOMALIAS
# ============================================================

elif pagina == "⚠️ Anomalias":

    if (
        oae_ativa is None
        or
        inspecao_ativa is None
        or
        componente_ativo is None
    ):

        st.warning(
            "Selecione OAE, inspeção e componente."
        )

    else:

        mostrar_modulo_anomalias(
            oae_ativa=oae_ativa,
            inspecao_ativa=inspecao_ativa,
            componente_ativo=componente_ativo
        )


# ============================================================
# CLASSIFICAÇÃO
# ============================================================

elif pagina == "⭐ Classificação":

    mostrar_modulo_classificacao(
        oae_ativa=oae_ativa,
        inspecao_ativa=inspecao_ativa,
        componente_ativo=componente_ativo
    )


# ============================================================
# FOTOGRAFIAS
# ============================================================

elif pagina == "📷 Fotografias":

    if (
        oae_ativa is None
        or
        inspecao_ativa is None
        or
        componente_ativo is None
    ):

        st.warning(
            "Selecione OAE, inspeção e componente."
        )

    else:

        mostrar_modulo_fotografias(
            oae_ativa=oae_ativa,
            inspecao_ativa=inspecao_ativa,
            componente_ativo=componente_ativo
        )


# ============================================================
# HISTÓRICO E EVOLUÇÃO
# ============================================================

elif pagina == "📈 Histórico e evolução":

    if oae_ativa is None:

        st.warning(
            "Selecione uma OAE."
        )

    else:

        mostrar_historico_oae(
            oae_ativa=oae_ativa
        )

        mostrar_evolucao_oae(
            oae_ativa=oae_ativa
        )


# ============================================================
# RELATÓRIOS
# ============================================================

elif pagina == "📄 Relatórios":

    st.header(
        "📄 Relatórios"
    )

    st.info(
        "O módulo de relatórios será implementado "
        "após a consolidação dos módulos de inspeção, "
        "anomalias, fotografias, classificação "
        "e histórico."
    )

    if oae_ativa is not None:

        st.write(
            f"**OAE:** "
            f"{oae_ativa.nome}"
        )

    if inspecao_ativa is not None:

        st.write(
            f"**Inspeção:** "
            f"{inspecao_ativa.tipo_inspecao} - "
            f"{inspecao_ativa.data_inspecao.strftime('%d/%m/%Y')}"
        )