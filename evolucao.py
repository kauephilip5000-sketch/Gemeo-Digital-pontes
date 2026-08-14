import streamlit as st
import pandas as pd
import altair as alt

from database import SessionLocal
import models


# ============================================================
# FUNÇÕES AUXILIARES
# ============================================================

def buscar_inspecoes_oae(oae_id):

    db = SessionLocal()

    inspecoes = (
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

    return inspecoes


def buscar_componente(componente_id):

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

    return componente


def calcular_notas_finais(
    oae_id,
    inspecao_id
):

    db = SessionLocal()

    classificacoes = (
        db.query(models.Classificacao)
        .filter(
            models.Classificacao.oae_id
            == oae_id
        )
        .filter(
            models.Classificacao.inspecao_id
            == inspecao_id
        )
        .all()
    )

    db.close()

    if len(classificacoes) == 0:

        return None


    return {
        "estrutural": min(
            item.nota_estrutural
            for item in classificacoes
        ),

        "funcional": min(
            item.nota_funcional
            for item in classificacoes
        ),

        "durabilidade": min(
            item.nota_durabilidade
            for item in classificacoes
        )
    }


def interpretar_variacao_notas(
    nota_anterior,
    nota_atual
):

    variacao = (
        nota_atual
        - nota_anterior
    )

    if variacao > 0:

        situacao = "Melhora"

    elif variacao < 0:

        situacao = "Piora"

    else:

        situacao = "Estável"


    return variacao, situacao


def buscar_anomalias_oae(oae_id):

    db = SessionLocal()

    anomalias = (
        db.query(models.AnomaliaPermanente)
        .filter(
            models.AnomaliaPermanente.oae_id
            == oae_id
        )
        .order_by(
            models.AnomaliaPermanente.id
        )
        .all()
    )

    db.close()

    return anomalias


def buscar_observacoes_anomalia(
    anomalia_id
):

    db = SessionLocal()

    observacoes = (
        db.query(models.ObservacaoAnomalia)
        .filter(
            models.ObservacaoAnomalia.anomalia_id
            == anomalia_id
        )
        .all()
    )


    dados = []

    for observacao in observacoes:

        inspecao = (
            db.query(models.Inspecao)
            .filter(
                models.Inspecao.id
                == observacao.inspecao_id
            )
            .first()
        )


        if inspecao is not None:

            dados.append(
                {
                    "observacao":
                        observacao,

                    "inspecao":
                        inspecao
                }
            )


    db.close()


    # ORDEM CRONOLÓGICA REAL
    dados.sort(
        key=lambda item: (
            item["inspecao"].data_inspecao,
            item["inspecao"].id
        )
    )


    return dados


def contar_fotos_observacao(
    observacao_id
):

    db = SessionLocal()

    quantidade = (
        db.query(
            models.VinculoFotografiaAnomalia
        )
        .filter(
            models.VinculoFotografiaAnomalia.observacao_anomalia_id
            == observacao_id
        )
        .count()
    )

    db.close()

    return quantidade


# ============================================================
# GRÁFICO ESTÁTICO
#
# Não utiliza interactive().
# Portanto o scroll do mouse não altera zoom ou escala.
# ============================================================

def criar_grafico_temporal(
    dataframe,
    campo_valor,
    titulo_eixo_y
):

    grafico = (
        alt.Chart(
            dataframe
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
                f"{campo_valor}:Q",
                title=titulo_eixo_y,
                scale=alt.Scale(
                    zero=False
                )
            ),

            tooltip=[
                alt.Tooltip(
                    "Data:T",
                    title="Data",
                    format="%d/%m/%Y"
                ),

                alt.Tooltip(
                    f"{campo_valor}:Q",
                    title=titulo_eixo_y
                )
            ]
        )
        .properties(
            height=320
        )
    )

    return grafico


# ============================================================
# EVOLUÇÃO DAS CLASSIFICAÇÕES
# ============================================================

def mostrar_evolucao_classificacoes(
    oae_ativa
):

    st.subheader(
        "⭐ Evolução das classificações"
    )


    inspecoes = buscar_inspecoes_oae(
        oae_ativa.id
    )


    dados = []


    for inspecao in inspecoes:

        notas = calcular_notas_finais(
            oae_ativa.id,
            inspecao.id
        )


        if notas is not None:

            dados.append(
                {
                    "inspecao":
                        inspecao,

                    "notas":
                        notas
                }
            )


    if len(dados) < 2:

        st.info(
            "São necessárias pelo menos duas inspeções "
            "com classificações registradas para realizar "
            "a comparação."
        )

        return


    # ========================================================
    # SELEÇÃO DAS INSPEÇÕES
    # ========================================================

    opcoes = {}


    for item in dados:

        inspecao = item["inspecao"]

        texto = (
            f"{inspecao.data_inspecao.strftime('%d/%m/%Y')} "
            f"- {inspecao.tipo_inspecao}"
        )

        opcoes[
            texto
        ] = item


    textos = list(
        opcoes.keys()
    )


    col1, col2 = (
        st.columns(2)
    )


    with col1:

        anterior_texto = st.selectbox(
            "Inspeção anterior",
            textos,
            index=0,
            key="evolucao_inspecao_anterior"
        )


    with col2:

        atual_texto = st.selectbox(
            "Inspeção atual",
            textos,
            index=len(textos) - 1,
            key="evolucao_inspecao_atual"
        )


    anterior = (
        opcoes[
            anterior_texto
        ]
    )


    atual = (
        opcoes[
            atual_texto
        ]
    )


    data_anterior = (
        anterior[
            "inspecao"
        ].data_inspecao
    )


    data_atual = (
        atual[
            "inspecao"
        ].data_inspecao
    )


    if (
        data_atual
        <= data_anterior
    ):

        st.warning(
            "Selecione uma inspeção atual posterior "
            "à inspeção anterior."
        )

        return


    # ========================================================
    # COMPARAÇÃO
    # ========================================================

    comparacao = []


    parametros = [
        (
            "Estrutural",
            "estrutural"
        ),

        (
            "Funcional",
            "funcional"
        ),

        (
            "Durabilidade",
            "durabilidade"
        )
    ]


    for nome, chave in parametros:

        nota_anterior = (
            anterior[
                "notas"
            ][
                chave
            ]
        )


        nota_atual = (
            atual[
                "notas"
            ][
                chave
            ]
        )


        variacao, situacao = (
            interpretar_variacao_notas(
                nota_anterior,
                nota_atual
            )
        )


        comparacao.append(
            {
                "Parâmetro":
                    nome,

                "Nota anterior":
                    nota_anterior,

                "Nota atual":
                    nota_atual,

                "Variação":
                    variacao,

                "Evolução":
                    situacao
            }
        )


    st.dataframe(
        comparacao,
        width="stretch",
        hide_index=True
    )


    col1, col2, col3 = (
        st.columns(3)
    )


    for coluna, item in zip(
        [
            col1,
            col2,
            col3
        ],
        comparacao
    ):

        with coluna:

            st.metric(
                item["Parâmetro"],
                item["Nota atual"],
                delta=item["Variação"]
            )

            st.write(
                f"Situação: "
                f"**{item['Evolução']}**"
            )


    st.caption(
        "Os termos melhora, piora e estável são uma "
        "interpretação descritiva da variação numérica "
        "entre as classificações registradas. "
        "Não substituem a avaliação técnica do inspetor."
    )


# ============================================================
# EVOLUÇÃO DAS ANOMALIAS
# ============================================================

def mostrar_evolucao_anomalias(
    oae_ativa
):

    st.divider()

    st.subheader(
        "⚠️ Evolução das anomalias acompanhadas"
    )


    anomalias = buscar_anomalias_oae(
        oae_ativa.id
    )


    if len(anomalias) == 0:

        st.info(
            "Nenhuma anomalia permanente cadastrada "
            "para esta OAE."
        )

        return


    for anomalia in anomalias:

        componente = buscar_componente(
            anomalia.componente_id
        )


        nome_componente = (
            componente.nome
            if componente is not None
            else
            f"Componente ID {anomalia.componente_id}"
        )


        observacoes = (
            buscar_observacoes_anomalia(
                anomalia.id
            )
        )


        titulo = (
            f"Anomalia ID {anomalia.id} - "
            f"{anomalia.tipo_anomalia} - "
            f"{nome_componente}"
        )


        with st.expander(
            titulo,
            expanded=False
        ):

            st.write(
                "**Localização de referência:**",
                anomalia.localizacao_referencia
            )


            st.write(
                "**Descrição inicial:**",
                (
                    anomalia.descricao_inicial
                    or
                    "Não informada"
                )
            )


            # =================================================
            # SEM OBSERVAÇÕES
            # =================================================

            if len(observacoes) == 0:

                st.info(
                    "Nenhuma observação registrada "
                    "para esta anomalia."
                )

                continue


            # =================================================
            # TABELA HISTÓRICA
            # =================================================

            dados_tabela = []


            for item in observacoes:

                observacao = (
                    item[
                        "observacao"
                    ]
                )


                inspecao = (
                    item[
                        "inspecao"
                    ]
                )


                dados_tabela.append(
                    {
                        "Data":
                            inspecao.data_inspecao.strftime(
                                "%d/%m/%Y"
                            ),

                        "Inspeção":
                            inspecao.tipo_inspecao,

                        "Abertura (mm)":
                            observacao.abertura_fissura_mm,

                        "Extensão (cm)":
                            observacao.extensao_anomalia_cm,

                        "Situação":
                            observacao.situacao_observada,

                        "Fotos":
                            contar_fotos_observacao(
                                observacao.id
                            )
                    }
                )


            st.dataframe(
                dados_tabela,
                width="stretch",
                hide_index=True
            )


            # =================================================
            # EVOLUÇÃO DA ABERTURA
            # =================================================

            dados_abertura = []


            for item in observacoes:

                observacao = (
                    item[
                        "observacao"
                    ]
                )


                inspecao = (
                    item[
                        "inspecao"
                    ]
                )


                if (
                    observacao.abertura_fissura_mm
                    is not None
                ):

                    dados_abertura.append(
                        {
                            "Data":
                                inspecao.data_inspecao,

                            "Abertura":
                                observacao.abertura_fissura_mm
                        }
                    )


            if len(dados_abertura) >= 2:

                st.markdown(
                    "#### Evolução da abertura registrada"
                )


                df_abertura = (
                    pd.DataFrame(
                        dados_abertura
                    )
                )


                df_abertura = (
                    df_abertura.sort_values(
                        "Data"
                    )
                )


                grafico_abertura = (
                    criar_grafico_temporal(
                        dataframe=df_abertura,
                        campo_valor="Abertura",
                        titulo_eixo_y="Abertura (mm)"
                    )
                )


                st.altair_chart(
                    grafico_abertura,
                    width="stretch"
                )


            # =================================================
            # EVOLUÇÃO DA EXTENSÃO
            # =================================================

            dados_extensao = []


            for item in observacoes:

                observacao = (
                    item[
                        "observacao"
                    ]
                )


                inspecao = (
                    item[
                        "inspecao"
                    ]
                )


                if (
                    observacao.extensao_anomalia_cm
                    is not None
                ):

                    dados_extensao.append(
                        {
                            "Data":
                                inspecao.data_inspecao,

                            "Extensão":
                                observacao.extensao_anomalia_cm
                        }
                    )


            if len(dados_extensao) >= 2:

                st.markdown(
                    "#### Evolução da extensão registrada"
                )


                df_extensao = (
                    pd.DataFrame(
                        dados_extensao
                    )
                )


                df_extensao = (
                    df_extensao.sort_values(
                        "Data"
                    )
                )


                grafico_extensao = (
                    criar_grafico_temporal(
                        dataframe=df_extensao,
                        campo_valor="Extensão",
                        titulo_eixo_y="Extensão (cm)"
                    )
                )


                st.altair_chart(
                    grafico_extensao,
                    width="stretch"
                )


            # =================================================
            # COMPARAÇÃO PRIMEIRA X ÚLTIMA
            # =================================================

            if len(observacoes) >= 2:

                primeira = (
                    observacoes[
                        0
                    ][
                        "observacao"
                    ]
                )


                ultima = (
                    observacoes[
                        -1
                    ][
                        "observacao"
                    ]
                )


                primeira_inspecao = (
                    observacoes[
                        0
                    ][
                        "inspecao"
                    ]
                )


                ultima_inspecao = (
                    observacoes[
                        -1
                    ][
                        "inspecao"
                    ]
                )


                st.markdown(
                    "### Comparação entre a primeira "
                    "e a última observação"
                )


                st.write(
                    f"**Primeira observação:** "
                    f"{primeira_inspecao.data_inspecao.strftime('%d/%m/%Y')}"
                )


                st.write(
                    f"**Última observação:** "
                    f"{ultima_inspecao.data_inspecao.strftime('%d/%m/%Y')}"
                )


                col1, col2 = (
                    st.columns(2)
                )


                # =============================================
                # ABERTURA
                # =============================================

                with col1:

                    if (
                        primeira.abertura_fissura_mm
                        is not None
                        and
                        ultima.abertura_fissura_mm
                        is not None
                    ):

                        variacao_abertura = (
                            ultima.abertura_fissura_mm
                            -
                            primeira.abertura_fissura_mm
                        )


                        st.metric(
                            "Abertura atual",
                            (
                                f"{ultima.abertura_fissura_mm:.2f} mm"
                            ),
                            delta=(
                                f"{variacao_abertura:+.2f} mm"
                            )
                        )


                        st.caption(
                            f"Anterior: "
                            f"{primeira.abertura_fissura_mm:.2f} mm"
                        )


                    else:

                        st.metric(
                            "Abertura atual",
                            "Dados insuficientes"
                        )


                # =============================================
                # EXTENSÃO
                # =============================================

                with col2:

                    if (
                        primeira.extensao_anomalia_cm
                        is not None
                        and
                        ultima.extensao_anomalia_cm
                        is not None
                    ):

                        variacao_extensao = (
                            ultima.extensao_anomalia_cm
                            -
                            primeira.extensao_anomalia_cm
                        )


                        st.metric(
                            "Extensão atual",
                            (
                                f"{ultima.extensao_anomalia_cm:.1f} cm"
                            ),
                            delta=(
                                f"{variacao_extensao:+.1f} cm"
                            )
                        )


                        st.caption(
                            f"Anterior: "
                            f"{primeira.extensao_anomalia_cm:.1f} cm"
                        )


                    else:

                        st.metric(
                            "Extensão atual",
                            "Dados insuficientes"
                        )


                st.caption(
                    "Os valores apresentados correspondem "
                    "às diferenças numéricas entre os registros "
                    "das inspeções. A interpretação da gravidade "
                    "e do significado estrutural permanece sob "
                    "responsabilidade do profissional responsável."
                )


# ============================================================
# MÓDULO PRINCIPAL
# ============================================================

def mostrar_evolucao_oae(
    oae_ativa
):

    st.divider()

    st.header(
        "📈 Evolução da condição da OAE"
    )


    if oae_ativa is None:

        st.warning(
            "Selecione uma OAE para visualizar "
            "a evolução temporal."
        )

        return


    st.caption(
        f"Análise temporal da OAE: "
        f"{oae_ativa.id} - "
        f"{oae_ativa.nome}"
    )


    mostrar_evolucao_classificacoes(
        oae_ativa
    )


    mostrar_evolucao_anomalias(
        oae_ativa
    )