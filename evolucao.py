import streamlit as st
import pandas as pd
import altair as alt

from database import SessionLocal
import models

from classificacao import (
    calcular_classificacao_consolidada,
    nota_texto
)


# ============================================================
# CONSULTAS
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

    if componente_id is None:
        return None

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


# ============================================================
# CLASSIFICAÇÃO
#
# Toda a regra de consolidação vem agora do classificacao.py.
#
# Isso impede:
# min(5, None)
#
# e mantém o NA fora do cálculo funcional.
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
# INTERPRETAÇÃO DA VARIAÇÃO
# ============================================================

def interpretar_variacao_notas(
    nota_anterior,
    nota_atual
):

    if (
        nota_anterior is None
        or
        nota_atual is None
    ):

        return None, "NA"


    variacao = (
        nota_atual
        -
        nota_anterior
    )


    if variacao > 0:

        situacao = "Melhora"

    elif variacao < 0:

        situacao = "Piora"

    else:

        situacao = "Estável"


    return (
        variacao,
        situacao
    )


# ============================================================
# ANOMALIAS
# ============================================================

def buscar_anomalias_oae(oae_id):

    db = SessionLocal()

    anomalias = (
        db.query(
            models.AnomaliaPermanente
        )
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
        db.query(
            models.ObservacaoAnomalia
        )
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
# GRÁFICOS TEMPORAIS
#
# Sem .interactive()
# Portanto o scroll do mouse não altera o gráfico.
# ============================================================

def criar_grafico_temporal(
    dataframe,
    campo_valor,
    titulo_eixo_y
):
    """
    Gráfico temporal compacto para o módulo de evolução.

    Exibe no eixo X apenas as datas efetivamente registradas nas
    inspeções, evitando datas intermediárias sem observação.
    """

    dataframe = (
        dataframe
        .sort_values("Data")
        .copy()
    )

    # Garante que a coluna Data seja realmente do tipo datetime
    # antes de usar o accessor .dt do pandas.
    dataframe["Data"] = pd.to_datetime(
        dataframe["Data"],
        errors="coerce"
    )

    dataframe = (
        dataframe
        .dropna(subset=["Data"])
        .sort_values("Data")
    )

    grafico = (
        alt.Chart(
            dataframe
        )
        .mark_line(
            point=alt.OverlayMarkDef(
                size=70,
                filled=True
            ),
            strokeWidth=2
        )
        .encode(
            x=alt.X(
                "Data:T",
                title="Data da inspeção",
                sort="ascending",
                axis=alt.Axis(
                    values=(
                        dataframe["Data"]
                        .dt.to_pydatetime()
                        .tolist()
                    ),
                    format="%d/%m/%Y",
                    labelAngle=0,
                    labelPadding=8,
                    grid=False
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
            height=235
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


    st.caption(
        "Comparação entre as notas finais aplicáveis "
        "de duas inspeções da OAE."
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

        inspecao = item[
            "inspecao"
        ]


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


    anterior = opcoes[
        anterior_texto
    ]

    atual = opcoes[
        atual_texto
    ]


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


        if (
            nota_anterior is None
            or
            nota_atual is None
        ):

            comparacao.append(
                {
                    "Parâmetro":
                        nome,

                    "Nota anterior":
                        (
                            nota_anterior
                            if nota_anterior is not None
                            else "NA"
                        ),

                    "Nota atual":
                        (
                            nota_atual
                            if nota_atual is not None
                            else "NA"
                        ),

                    "Variação":
                        "NA",

                    "Evolução":
                        "Não comparável"
                }
            )

        else:

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


    # ========================================================
    # CARTÕES
    # ========================================================

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

            nota_atual = item[
                "Nota atual"
            ]


            variacao = item[
                "Variação"
            ]


            if (
                nota_atual == "NA"
            ):

                st.metric(
                    item["Parâmetro"],
                    "NA"
                )

                st.caption(
                    "Parâmetro não comparável "
                    "entre as inspeções selecionadas."
                )

            else:

                delta = (
                    variacao
                    if variacao != "NA"
                    else None
                )


                st.metric(
                    item["Parâmetro"],
                    nota_atual,
                    delta=delta
                )


                st.caption(
                    nota_texto(
                        nota_atual
                    )
                )


                st.write(
                    f"Situação: "
                    f"**{item['Evolução']}**"
                )


    st.caption(
        "Melhora, piora e estável representam apenas "
        "a diferença numérica entre as notas registradas. "
        "A interpretação técnica permanece sob "
        "responsabilidade do profissional responsável."
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
                (
                    anomalia.localizacao_referencia
                    or
                    "Não informada"
                )
            )


            st.write(
                "**Descrição inicial:**",
                (
                    anomalia.descricao_inicial
                    or
                    "Não informada"
                )
            )


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

                observacao = item[
                    "observacao"
                ]

                inspecao = item[
                    "inspecao"
                ]


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
            # ABERTURA
            # =================================================

            dados_abertura = []


            for item in observacoes:

                observacao = item[
                    "observacao"
                ]

                inspecao = item[
                    "inspecao"
                ]


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


                df_abertura = pd.DataFrame(
                    dados_abertura
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


                margem_esq, coluna_grafico, margem_dir = st.columns(
                    [0.08, 0.84, 0.08]
                )

                with coluna_grafico:
                    st.altair_chart(
                        grafico_abertura,
                        width="stretch"
                    )


            # =================================================
            # EXTENSÃO
            # =================================================

            dados_extensao = []


            for item in observacoes:

                observacao = item[
                    "observacao"
                ]

                inspecao = item[
                    "inspecao"
                ]


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


                df_extensao = pd.DataFrame(
                    dados_extensao
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


                margem_esq, coluna_grafico, margem_dir = st.columns(
                    [0.08, 0.84, 0.08]
                )

                with coluna_grafico:
                    st.altair_chart(
                        grafico_extensao,
                        width="stretch"
                    )


            # =================================================
            # PRIMEIRA X ÚLTIMA OBSERVAÇÃO
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