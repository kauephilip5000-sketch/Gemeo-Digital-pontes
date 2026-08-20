import streamlit as st
import pandas as pd
import altair as alt
import re

from database import engine, Base, SessionLocal
import models

from anomalias import mostrar_modulo_anomalias
from fotos import mostrar_modulo_fotografias
from historico import mostrar_historico_oae
from evolucao import mostrar_evolucao_oae
from cadastral import mostrar_modulo_cadastral
from rotineira import mostrar_modulo_rotineira
from especial import mostrar_modulo_especial
from extraordinaria import mostrar_modulo_extraordinaria
from relatorios import mostrar_modulo_relatorios

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
# MENSAGENS DE CONFIRMAÇÃO
# ============================================================

def definir_mensagem_sucesso(mensagem):

    st.session_state["_mensagem_sucesso"] = mensagem


def mostrar_mensagem_sucesso():

    mensagem = st.session_state.pop(
        "_mensagem_sucesso",
        None
    )

    if mensagem:

        st.success(
            mensagem,
            icon="✅"
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


# ============================================================
# ORDEM LÓGICA DOS COMPONENTES
#
# A numeração visual e os seletores não seguem mais a ordem
# em que os registros foram cadastrados no banco.
#
# Exemplo:
# se o Pilar P2 for cadastrado depois da Sinalização,
# ele continuará aparecendo junto da Mesoestrutura.
# ============================================================

ORDEM_CATEGORIAS_COMPONENTES = {
    "Superestrutura": 1,
    "Mesoestrutura": 2,
    "Infraestrutura": 3,
    "Encontros": 4,
    "Elementos complementares": 5,
    "Pista / via permanente": 6,
}


def chave_ordenacao_natural(valor):

    valor = (
        str(valor or "")
        .strip()
        .lower()
    )

    partes = re.split(
        r"(\d+)",
        valor
    )

    chave = []

    for parte in partes:

        if parte.isdigit():

            chave.append(
                (
                    0,
                    int(parte)
                )
            )

        else:

            chave.append(
                (
                    1,
                    parte
                )
            )

    return tuple(chave)


def chave_ordenacao_componente(componente):

    ordem_categoria = (
        ORDEM_CATEGORIAS_COMPONENTES.get(
            componente.categoria,
            99
        )
    )

    return (
        ordem_categoria,
        chave_ordenacao_natural(
            componente.nome
        ),
        componente.id
    )


def buscar_componentes(oae_id):

    db = SessionLocal()

    dados = (
        db.query(models.Componente)
        .filter(
            models.Componente.oae_id
            == oae_id
        )
        .all()
    )

    db.close()

    dados = sorted(
        dados,
        key=chave_ordenacao_componente
    )

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
                    f"{indice} - {item.nome}"
                for indice, item in enumerate(
                    componentes_sidebar,
                    start=1
                )
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
                        str(notas["estrutural"])
                        if notas["estrutural"]
                        is not None
                        else "—"
                    )

                    funcional = (
                        str(notas["funcional"])
                        if notas["funcional"]
                        is not None
                        else "NA"
                    )

                    durabilidade = (
                        str(notas["durabilidade"])
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

    mostrar_mensagem_sucesso()

    tab1, tab2, tab3 = st.tabs(
        [
            "📋 OAE selecionada",
            "➕ Cadastrar nova OAE",
            "✏️ Editar OAE"
        ]
    )

    # ========================================================
    # OAE SELECIONADA
    # ========================================================

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
                    "**ID interno:**",
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
    # CADASTRAR NOVA OAE
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

                try:

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

                    definir_mensagem_sucesso(
                        "OAE cadastrada com sucesso."
                    )

                except Exception as erro:

                    db.rollback()

                    st.error(
                        "Não foi possível salvar a OAE. "
                        f"Detalhe: {erro}"
                    )

                    db.close()

                    st.stop()

                db.close()

                st.rerun()

    # ========================================================
    # EDITAR OAE
    # ========================================================

    with tab3:

        st.subheader(
            "✏️ Editar OAE"
        )

        if oae_ativa is None:

            st.info(
                "Selecione uma OAE para editar."
            )

        else:

            st.caption(
                "Altere somente os campos necessários e "
                "clique em Atualizar OAE."
            )

            lista_ufs = [
                "AC", "AL", "AP", "AM",
                "BA", "CE", "DF", "ES",
                "GO", "MA", "MT", "MS",
                "MG", "PA", "PB", "PR",
                "PE", "PI", "RJ", "RN",
                "RS", "RO", "RR", "SC",
                "SP", "SE", "TO"
            ]

            lista_estruturas = [
                "Concreto protendido",
                "Concreto armado",
                "Estrutura mista",
                "Outro"
            ]

            lista_protensao = [
                "Pré-tração",
                "Pós-tração",
                "Não informado",
                "Não se aplica"
            ]

            indice_uf = (
                lista_ufs.index(
                    oae_ativa.uf
                )
                if oae_ativa.uf
                in lista_ufs
                else 0
            )

            indice_estrutura = (
                lista_estruturas.index(
                    oae_ativa.tipo_estrutura
                )
                if oae_ativa.tipo_estrutura
                in lista_estruturas
                else 0
            )

            indice_protensao = (
                lista_protensao.index(
                    oae_ativa.tipo_protensao
                )
                if oae_ativa.tipo_protensao
                in lista_protensao
                else 0
            )

            with st.form(
                "form_editar_oae"
            ):

                c1, c2 = st.columns(
                    2
                )

                with c1:

                    editar_nome = st.text_input(
                        "Nome da OAE",
                        value=oae_ativa.nome
                        or ""
                    )

                    editar_codigo = st.text_input(
                        "Código",
                        value=oae_ativa.codigo
                        or ""
                    )

                    editar_rodovia = st.text_input(
                        "Rodovia",
                        value=oae_ativa.rodovia
                        or ""
                    )

                    editar_municipio = st.text_input(
                        "Município",
                        value=oae_ativa.municipio
                        or ""
                    )

                    editar_uf = st.selectbox(
                        "UF",
                        lista_ufs,
                        index=indice_uf,
                        key="editar_oae_uf"
                    )

                    editar_ano = st.number_input(
                        "Ano de construção",
                        min_value=1800,
                        max_value=2100,
                        step=1,
                        value=int(
                            oae_ativa.ano_construcao
                            or 2000
                        )
                    )

                with c2:

                    editar_estrutura = st.selectbox(
                        "Tipo estrutural",
                        lista_estruturas,
                        index=indice_estrutura,
                        key="editar_oae_estrutura"
                    )

                    editar_vaos = st.number_input(
                        "Número de vãos",
                        min_value=1,
                        step=1,
                        value=int(
                            oae_ativa.numero_vaos
                            or 1
                        )
                    )

                    editar_comprimento = st.number_input(
                        "Comprimento total (m)",
                        min_value=0.0,
                        step=0.1,
                        value=float(
                            oae_ativa.comprimento_total
                            or 0.0
                        )
                    )

                    editar_largura = st.number_input(
                        "Largura (m)",
                        min_value=0.0,
                        step=0.1,
                        value=float(
                            oae_ativa.largura
                            or 0.0
                        )
                    )

                    editar_protensao = st.selectbox(
                        "Tipo de protensão",
                        lista_protensao,
                        index=indice_protensao,
                        key="editar_oae_protensao"
                    )

                editar_observacoes = st.text_area(
                    "Observações",
                    value=oae_ativa.observacoes
                    or ""
                )

                atualizar_oae = (
                    st.form_submit_button(
                        "Atualizar OAE"
                    )
                )

            if atualizar_oae:

                if editar_nome.strip() == "":

                    st.error(
                        "O nome da OAE não pode ficar vazio."
                    )

                else:

                    db = SessionLocal()

                    try:

                        registro = (
                            db.query(models.OAE)
                            .filter(
                                models.OAE.id
                                == oae_ativa.id
                            )
                            .first()
                        )

                        if registro is None:

                            st.error(
                                "A OAE não foi encontrada."
                            )

                        else:

                            registro.nome = (
                                editar_nome
                            )

                            registro.codigo = (
                                editar_codigo
                            )

                            registro.rodovia = (
                                editar_rodovia
                            )

                            registro.municipio = (
                                editar_municipio
                            )

                            registro.uf = (
                                editar_uf
                            )

                            registro.ano_construcao = (
                                editar_ano
                            )

                            registro.tipo_estrutura = (
                                editar_estrutura
                            )

                            registro.numero_vaos = (
                                editar_vaos
                            )

                            registro.comprimento_total = (
                                editar_comprimento
                            )

                            registro.largura = (
                                editar_largura
                            )

                            registro.tipo_protensao = (
                                editar_protensao
                            )

                            registro.observacoes = (
                                editar_observacoes
                            )

                            db.commit()

                            definir_mensagem_sucesso(
                                "OAE atualizada com sucesso."
                            )

                    except Exception as erro:

                        db.rollback()

                        st.error(
                            "Não foi possível atualizar a OAE. "
                            f"Detalhe: {erro}"
                        )

                        db.close()

                        st.stop()

                    db.close()

                    st.rerun()


# ============================================================
# COMPONENTES
# ============================================================

elif pagina == "🧱 Componentes":

    st.header(
        "Componentes"
    )

    mostrar_mensagem_sucesso()

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

        tab1, tab2, tab3 = st.tabs(
            [
                "📋 Componentes cadastrados",
                "➕ Cadastrar componente",
                "✏️ Editar componente"
            ]
        )

        # ====================================================
        # COMPONENTES CADASTRADOS
        # ====================================================

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

                for numero, item in enumerate(
                    componentes,
                    start=1
                ):

                    dados.append(
                        {
                            "Nº":
                                numero,

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

                st.caption(
                    "Os componentes são organizados automaticamente "
                    "pela estrutura da OAE: Superestrutura → "
                    "Mesoestrutura → Infraestrutura → Encontros → "
                    "Elementos complementares → Pista/via permanente. "
                    "Dentro de cada grupo, os nomes são ordenados de "
                    "forma natural (por exemplo: L1, L2, L3, L10). "
                    "A numeração exibida é visual e própria desta OAE; "
                    "o ID interno do banco permanece inalterado."
                )

        # ====================================================
        # CADASTRAR COMPONENTE
        # ====================================================

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

                    try:

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

                        definir_mensagem_sucesso(
                            f'Componente "{novo.nome}" '
                            "salvo com sucesso."
                        )

                    except Exception as erro:

                        db.rollback()

                        st.error(
                            "Não foi possível salvar o componente. "
                            f"Detalhe: {erro}"
                        )

                        db.close()

                        st.stop()

                    db.close()

                    st.rerun()

        # ====================================================
        # EDITAR COMPONENTE
        # ====================================================

        with tab3:

            st.subheader(
                "✏️ Editar componente"
            )

            componentes_edicao = (
                buscar_componentes(
                    oae_ativa.id
                )
            )

            if len(
                componentes_edicao
            ) == 0:

                st.info(
                    "Nenhum componente cadastrado "
                    "para edição."
                )

            else:

                ids_edicao = [
                    item.id
                    for item in componentes_edicao
                ]

                mapa_edicao = {
                    item.id:
                        f"{numero} - {item.nome}"
                    for numero, item in enumerate(
                        componentes_edicao,
                        start=1
                    )
                }

                componente_editar_id = (
                    st.selectbox(
                        "Selecione o componente",
                        options=ids_edicao,
                        format_func=lambda valor:
                            mapa_edicao[valor],
                        key="componente_editar_id"
                    )
                )

                componente_editar = next(
                    item
                    for item in componentes_edicao
                    if item.id
                    == componente_editar_id
                )

                categorias = [
                    "Superestrutura",
                    "Mesoestrutura",
                    "Infraestrutura",
                    "Encontros",
                    "Elementos complementares",
                    "Pista / via permanente"
                ]

                relevancias = [
                    "Principal",
                    "Secundário",
                    "Complementar",
                    "Não informado"
                ]

                indice_categoria = (
                    categorias.index(
                        componente_editar.categoria
                    )
                    if componente_editar.categoria
                    in categorias
                    else 0
                )

                indice_relevancia = (
                    relevancias.index(
                        componente_editar.classificacao_elemento
                    )
                    if componente_editar.classificacao_elemento
                    in relevancias
                    else 0
                )

                with st.form(
                    "form_editar_componente"
                ):

                    editar_categoria = (
                        st.selectbox(
                            "Categoria",
                            categorias,
                            index=indice_categoria,
                            key=(
                                "editar_componente_categoria_"
                                f"{componente_editar.id}"
                            )
                        )
                    )

                    editar_nome = st.text_input(
                        "Nome ou identificação",
                        value=(
                            componente_editar.nome
                            or ""
                        ),
                        key=(
                            "editar_componente_nome_"
                            f"{componente_editar.id}"
                        )
                    )

                    editar_relevancia = (
                        st.selectbox(
                            "Relevância do elemento",
                            relevancias,
                            index=indice_relevancia,
                            key=(
                                "editar_componente_relevancia_"
                                f"{componente_editar.id}"
                            )
                        )
                    )

                    editar_observacoes = (
                        st.text_area(
                            "Observações",
                            value=(
                                componente_editar.observacoes
                                or ""
                            ),
                            key=(
                                "editar_componente_observacoes_"
                                f"{componente_editar.id}"
                            )
                        )
                    )

                    atualizar_componente = (
                        st.form_submit_button(
                            "Atualizar componente"
                        )
                    )

                if atualizar_componente:

                    if editar_nome.strip() == "":

                        st.error(
                            "O nome do componente "
                            "não pode ficar vazio."
                        )

                    else:

                        db = SessionLocal()

                        try:

                            registro = (
                                db.query(
                                    models.Componente
                                )
                                .filter(
                                    models.Componente.id
                                    == componente_editar.id
                                )
                                .first()
                            )

                            if registro is None:

                                st.error(
                                    "O componente não foi "
                                    "encontrado."
                                )

                            else:

                                registro.categoria = (
                                    editar_categoria
                                )

                                registro.nome = (
                                    editar_nome
                                )

                                registro.classificacao_elemento = (
                                    editar_relevancia
                                )

                                registro.observacoes = (
                                    editar_observacoes
                                )

                                db.commit()

                                st.session_state.componente_ativo_id = (
                                    registro.id
                                )

                                definir_mensagem_sucesso(
                                    f'Componente "{registro.nome}" '
                                    "atualizado com sucesso."
                                )

                        except Exception as erro:

                            db.rollback()

                            st.error(
                                "Não foi possível atualizar "
                                "o componente. "
                                f"Detalhe: {erro}"
                            )

                            db.close()

                            st.stop()

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

        tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(
            [
                "📋 Inspeções cadastradas",
                "🟦 Cadastral",
                "🟩 Rotineira",
                "🟨 Especial",
                "🟥 Extraordinária",
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
                            str(notas["estrutural"])
                            if notas["estrutural"]
                            is not None
                            else "—"
                        )

                        funcional = (
                            str(notas["funcional"])
                            if notas["funcional"]
                            is not None
                            else "NA"
                        )

                        durabilidade = (
                            str(notas["durabilidade"])
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
        # CADASTRAL
        # ====================================================

        with tab2:

            mostrar_modulo_cadastral(
                oae_ativa=oae_ativa,
                inspecao_ativa=inspecao_ativa
            )

        # ====================================================
        # ROTINEIRA
        # ====================================================

        with tab3:

            mostrar_modulo_rotineira(
                oae_ativa=oae_ativa,
                inspecao_ativa=inspecao_ativa
            )

        # ====================================================
        # ESPECIAL
        # ====================================================

        with tab4:

            mostrar_modulo_especial(
                oae_ativa=oae_ativa,
                inspecao_ativa=inspecao_ativa
            )

        # ====================================================
        # EXTRAORDINÁRIA
        # ====================================================

        with tab5:

            mostrar_modulo_extraordinaria(
                oae_ativa=oae_ativa,
                inspecao_ativa=inspecao_ativa
            )

        # ====================================================
        # ANDAMENTO DA INSPEÇÃO
        # ====================================================

        with tab6:

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

                if (
                    inspecao_ativa.tipo_inspecao
                    == "Cadastral"
                ):

                    st.info(
                        "O acompanhamento completo desta campanha "
                        "está disponível na aba 🟦 Cadastral."
                    )

                elif (
                    inspecao_ativa.tipo_inspecao
                    == "Rotineira"
                ):

                    st.info(
                        "O acompanhamento completo desta campanha "
                        "está disponível na aba 🟩 Rotineira."
                    )

                elif (
                    inspecao_ativa.tipo_inspecao
                    == "Especial"
                ):

                    st.info(
                        "O acompanhamento completo desta campanha "
                        "está disponível na aba 🟨 Especial."
                    )

                elif (
                    inspecao_ativa.tipo_inspecao
                    == "Extraordinária"
                ):

                    st.info(
                        "O acompanhamento completo desta campanha "
                        "está disponível na aba 🟥 Extraordinária."
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
                        disabled=True,
                        key="and_extra_terapia"
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

    mostrar_modulo_relatorios(
        oae_ativa=oae_ativa,
        inspecao_ativa=inspecao_ativa,
    )
