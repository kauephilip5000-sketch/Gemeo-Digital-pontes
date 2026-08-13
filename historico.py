import streamlit as st

from database import SessionLocal
import models


def mostrar_historico_oae(oae_ativa):

    st.divider()

    st.header("Histórico das inspeções")

    st.write(
        f"Histórico da OAE: "
        f"**{oae_ativa.id} - {oae_ativa.nome}**"
    )


    # ========================================================
    # BUSCAR INSPEÇÕES DA OAE
    # ========================================================

    db = SessionLocal()

    inspecoes = (
        db.query(models.Inspecao)
        .filter(
            models.Inspecao.oae_id
            == oae_ativa.id
        )
        .order_by(
            models.Inspecao.data_inspecao.desc(),
            models.Inspecao.id.desc()
        )
        .all()
    )

    db.close()


    if len(inspecoes) == 0:

        st.info(
            "Nenhuma inspeção cadastrada "
            "para esta OAE."
        )

        return


    # ========================================================
    # RESUMO GERAL
    # ========================================================

    quantidade_inspecoes = len(
        inspecoes
    )

    st.metric(
        "Total de inspeções cadastradas",
        quantidade_inspecoes
    )


    # ========================================================
    # PERCORRER HISTÓRICO
    # ========================================================

    for inspecao in inspecoes:

        titulo = (
            f"{inspecao.data_inspecao.strftime('%d/%m/%Y')} "
            f"- {inspecao.tipo_inspecao}"
        )

        with st.expander(
            titulo,
            expanded=False
        ):

            st.write(
                f"**ID da inspeção:** "
                f"{inspecao.id}"
            )

            st.write(
                f"**Tipo:** "
                f"{inspecao.tipo_inspecao}"
            )

            st.write(
                f"**Data:** "
                f"{inspecao.data_inspecao.strftime('%d/%m/%Y')}"
            )

            if inspecao.responsavel:

                st.write(
                    f"**Responsável:** "
                    f"{inspecao.responsavel}"
                )

            if inspecao.registro_profissional:

                st.write(
                    f"**Registro profissional:** "
                    f"{inspecao.registro_profissional}"
                )

            if inspecao.observacoes:

                st.write(
                    f"**Observações:** "
                    f"{inspecao.observacoes}"
                )


            # =================================================
            # COMPONENTES AVALIADOS
            # =================================================

            db = SessionLocal()

            classificacoes = (
                db.query(models.Classificacao)
                .filter(
                    models.Classificacao.oae_id
                    == oae_ativa.id
                )
                .filter(
                    models.Classificacao.inspecao_id
                    == inspecao.id
                )
                .all()
            )

            db.close()


            componentes_avaliados = set()

            for classificacao in classificacoes:

                componentes_avaliados.add(
                    classificacao.componente_id
                )


            quantidade_componentes = len(
                componentes_avaliados
            )


            # =================================================
            # ANOMALIAS
            # =================================================

            db = SessionLocal()

            anomalias = (
                db.query(models.Anomalia)
                .filter(
                    models.Anomalia.oae_id
                    == oae_ativa.id
                )
                .filter(
                    models.Anomalia.inspecao_id
                    == inspecao.id
                )
                .all()
            )

            db.close()

            quantidade_anomalias = len(
                anomalias
            )


            # =================================================
            # FOTOGRAFIAS
            # =================================================

            db = SessionLocal()

            fotografias = (
                db.query(models.Fotografia)
                .filter(
                    models.Fotografia.oae_id
                    == oae_ativa.id
                )
                .filter(
                    models.Fotografia.inspecao_id
                    == inspecao.id
                )
                .all()
            )

            db.close()

            quantidade_fotos = len(
                fotografias
            )


            # =================================================
            # INDICADORES
            # =================================================

            col1, col2, col3 = st.columns(3)

            with col1:

                st.metric(
                    "Componentes avaliados",
                    quantidade_componentes
                )

            with col2:

                st.metric(
                    "Anomalias",
                    quantidade_anomalias
                )

            with col3:

                st.metric(
                    "Fotografias",
                    quantidade_fotos
                )


            # =================================================
            # CLASSIFICAÇÃO DA INSPEÇÃO
            # =================================================

            if len(classificacoes) == 0:

                st.info(
                    "Nenhuma classificação registrada "
                    "para esta inspeção."
                )

            else:

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


                nota_estrutural_final = min(
                    notas_estruturais
                )

                nota_funcional_final = min(
                    notas_funcionais
                )

                nota_durabilidade_final = min(
                    notas_durabilidade
                )


                st.write(
                    "### Classificação da inspeção"
                )


                col1, col2, col3 = st.columns(3)


                with col1:

                    st.metric(
                        "Estrutural",
                        nota_estrutural_final
                    )


                with col2:

                    st.metric(
                        "Funcional",
                        nota_funcional_final
                    )


                with col3:

                    st.metric(
                        "Durabilidade",
                        nota_durabilidade_final
                    )


            # =================================================
            # LISTA DE ANOMALIAS
            # =================================================

            if quantidade_anomalias > 0:

                st.write(
                    "### Anomalias registradas"
                )

                dados_anomalias = []

                for anomalia in anomalias:

                    db = SessionLocal()

                    componente = (
                        db.query(models.Componente)
                        .filter(
                            models.Componente.id
                            == anomalia.componente_id
                        )
                        .first()
                    )

                    db.close()


                    if componente is None:

                        nome_componente = (
                            "Componente não encontrado"
                        )

                    else:

                        nome_componente = (
                            componente.nome
                        )


                    dados_anomalias.append(
                        {
                            "ID":
                                anomalia.id,
                            "Componente":
                                nome_componente,
                            "Tipo":
                                anomalia.tipo_anomalia,
                            "Localização":
                                anomalia.localizacao,
                            "Descrição":
                                anomalia.descricao
                        }
                    )


                st.dataframe(
                    dados_anomalias,
                    width="stretch"
                )