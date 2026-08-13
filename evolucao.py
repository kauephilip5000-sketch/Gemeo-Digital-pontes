import streamlit as st

from database import SessionLocal
import models


def obter_notas_finais(inspecao_id, oae_id):

    db = SessionLocal()

    classificacoes = (
        db.query(models.Classificacao)
        .filter(
            models.Classificacao.oae_id == oae_id
        )
        .filter(
            models.Classificacao.inspecao_id == inspecao_id
        )
        .all()
    )

    db.close()

    if len(classificacoes) == 0:

        return None

    notas_estruturais = [
        classificacao.nota_estrutural
        for classificacao in classificacoes
    ]

    notas_funcionais = [
        classificacao.nota_funcional
        for classificacao in classificacoes
    ]

    notas_durabilidade = [
        classificacao.nota_durabilidade
        for classificacao in classificacoes
    ]

    return {
        "estrutural": min(notas_estruturais),
        "funcional": min(notas_funcionais),
        "durabilidade": min(notas_durabilidade)
    }


def interpretar_evolucao(nota_anterior, nota_atual):

    diferenca = nota_atual - nota_anterior

    if diferenca > 0:

        return "Melhora", diferenca

    elif diferenca < 0:

        return "Piora", diferenca

    else:

        return "Estável", diferenca


def mostrar_evolucao_oae(oae_ativa):

    st.divider()

    st.header(
        "Evolução da condição da OAE"
    )

    st.write(
        f"Análise temporal da OAE: "
        f"**{oae_ativa.id} - {oae_ativa.nome}**"
    )


    # ========================================================
    # BUSCAR INSPEÇÕES
    # ========================================================

    db = SessionLocal()

    inspecoes = (
        db.query(models.Inspecao)
        .filter(
            models.Inspecao.oae_id == oae_ativa.id
        )
        .order_by(
            models.Inspecao.data_inspecao.asc(),
            models.Inspecao.id.asc()
        )
        .all()
    )

    db.close()


    # ========================================================
    # VERIFICAR QUANTIDADE DE INSPEÇÕES
    # ========================================================

    if len(inspecoes) < 2:

        st.info(
            "É necessário possuir pelo menos duas inspeções "
            "cadastradas para analisar a evolução temporal."
        )

        return


    # ========================================================
    # MONTAR INSPEÇÕES QUE POSSUEM CLASSIFICAÇÃO
    # ========================================================

    inspecoes_com_notas = []

    for inspecao in inspecoes:

        notas = obter_notas_finais(
            inspecao_id=inspecao.id,
            oae_id=oae_ativa.id
        )

        if notas is not None:

            inspecoes_com_notas.append(
                {
                    "inspecao": inspecao,
                    "notas": notas
                }
            )


    if len(inspecoes_com_notas) < 2:

        st.info(
            "Existem inspeções cadastradas, mas são necessárias "
            "pelo menos duas inspeções com classificações "
            "registradas para realizar a comparação."
        )

        return


    # ========================================================
    # OPÇÕES PARA COMPARAÇÃO
    # ========================================================

    opcoes_inspecoes = {}

    for item in inspecoes_com_notas:

        inspecao = item["inspecao"]

        texto = (
            f"{inspecao.id} - "
            f"{inspecao.tipo_inspecao} - "
            f"{inspecao.data_inspecao.strftime('%d/%m/%Y')}"
        )

        opcoes_inspecoes[texto] = item


    st.subheader(
        "Comparar duas inspeções"
    )


    col1, col2 = st.columns(2)


    with col1:

        inspecao_anterior_texto = st.selectbox(
            "Inspeção anterior",
            options=list(
                opcoes_inspecoes.keys()
            ),
            index=0
        )


    with col2:

        inspecao_atual_texto = st.selectbox(
            "Inspeção mais recente",
            options=list(
                opcoes_inspecoes.keys()
            ),
            index=len(opcoes_inspecoes) - 1
        )


    item_anterior = (
        opcoes_inspecoes[
            inspecao_anterior_texto
        ]
    )

    item_atual = (
        opcoes_inspecoes[
            inspecao_atual_texto
        ]
    )


    inspecao_anterior = (
        item_anterior["inspecao"]
    )

    inspecao_atual = (
        item_atual["inspecao"]
    )


    notas_anterior = (
        item_anterior["notas"]
    )

    notas_atual = (
        item_atual["notas"]
    )


    # ========================================================
    # VERIFICAR ORDEM CRONOLÓGICA
    # ========================================================

    if (
        inspecao_atual.data_inspecao
        < inspecao_anterior.data_inspecao
    ):

        st.warning(
            "A inspeção escolhida como mais recente possui "
            "data anterior à inspeção selecionada como anterior."
        )


    if inspecao_anterior.id == inspecao_atual.id:

        st.warning(
            "Selecione duas inspeções diferentes "
            "para realizar a comparação."
        )

        return


    # ========================================================
    # RESUMO DAS INSPEÇÕES
    # ========================================================

    st.write(
        "### Inspeções selecionadas"
    )

    col1, col2 = st.columns(2)


    with col1:

        st.write(
            "**Inspeção anterior**"
        )

        st.write(
            f"Data: "
            f"{inspecao_anterior.data_inspecao.strftime('%d/%m/%Y')}"
        )

        st.write(
            f"Tipo: "
            f"{inspecao_anterior.tipo_inspecao}"
        )


    with col2:

        st.write(
            "**Inspeção mais recente**"
        )

        st.write(
            f"Data: "
            f"{inspecao_atual.data_inspecao.strftime('%d/%m/%Y')}"
        )

        st.write(
            f"Tipo: "
            f"{inspecao_atual.tipo_inspecao}"
        )


    st.divider()


    # ========================================================
    # COMPARAÇÃO DAS NOTAS
    # ========================================================

    st.subheader(
        "Comparação das classificações"
    )


    evolucao_estrutural, diferenca_estrutural = (
        interpretar_evolucao(
            notas_anterior["estrutural"],
            notas_atual["estrutural"]
        )
    )

    evolucao_funcional, diferenca_funcional = (
        interpretar_evolucao(
            notas_anterior["funcional"],
            notas_atual["funcional"]
        )
    )

    evolucao_durabilidade, diferenca_durabilidade = (
        interpretar_evolucao(
            notas_anterior["durabilidade"],
            notas_atual["durabilidade"]
        )
    )


    dados_comparacao = [
        {
            "Parâmetro": "Estrutural",
            "Nota anterior":
                notas_anterior["estrutural"],
            "Nota atual":
                notas_atual["estrutural"],
            "Variação":
                diferenca_estrutural,
            "Evolução":
                evolucao_estrutural
        },
        {
            "Parâmetro": "Funcional",
            "Nota anterior":
                notas_anterior["funcional"],
            "Nota atual":
                notas_atual["funcional"],
            "Variação":
                diferenca_funcional,
            "Evolução":
                evolucao_funcional
        },
        {
            "Parâmetro": "Durabilidade",
            "Nota anterior":
                notas_anterior["durabilidade"],
            "Nota atual":
                notas_atual["durabilidade"],
            "Variação":
                diferenca_durabilidade,
            "Evolução":
                evolucao_durabilidade
        }
    ]


    st.dataframe(
        dados_comparacao,
        width="stretch"
    )


    # ========================================================
    # INDICADORES
    # ========================================================

    col1, col2, col3 = st.columns(3)


    with col1:

        st.metric(
            "Estrutural",
            notas_atual["estrutural"],
            delta=diferenca_estrutural
        )

        st.write(
            f"Situação: **{evolucao_estrutural}**"
        )


    with col2:

        st.metric(
            "Funcional",
            notas_atual["funcional"],
            delta=diferenca_funcional
        )

        st.write(
            f"Situação: **{evolucao_funcional}**"
        )


    with col3:

        st.metric(
            "Durabilidade",
            notas_atual["durabilidade"],
            delta=diferenca_durabilidade
        )

        st.write(
            f"Situação: **{evolucao_durabilidade}**"
        )


    # ========================================================
    # ANOMALIAS DAS DUAS INSPEÇÕES
    # ========================================================

    st.divider()

    st.subheader(
        "Comparação das anomalias registradas"
    )


    db = SessionLocal()

    anomalias_anteriores = (
        db.query(models.Anomalia)
        .filter(
            models.Anomalia.oae_id
            == oae_ativa.id
        )
        .filter(
            models.Anomalia.inspecao_id
            == inspecao_anterior.id
        )
        .all()
    )


    anomalias_atuais = (
        db.query(models.Anomalia)
        .filter(
            models.Anomalia.oae_id
            == oae_ativa.id
        )
        .filter(
            models.Anomalia.inspecao_id
            == inspecao_atual.id
        )
        .all()
    )

    db.close()


    quantidade_anterior = len(
        anomalias_anteriores
    )

    quantidade_atual = len(
        anomalias_atuais
    )


    col1, col2 = st.columns(2)


    with col1:

        st.metric(
            "Anomalias na inspeção anterior",
            quantidade_anterior
        )


    with col2:

        st.metric(
            "Anomalias na inspeção atual",
            quantidade_atual,
            delta=(
                quantidade_atual
                - quantidade_anterior
            )
        )


    st.caption(
        "A quantidade de anomalias é apenas um indicador "
        "descritivo. Um número maior ou menor de registros, "
        "isoladamente, não determina melhora ou piora da "
        "condição da OAE."
    )