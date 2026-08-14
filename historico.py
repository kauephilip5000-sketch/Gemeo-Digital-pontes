import streamlit as st

from database import SessionLocal
import models


# ============================================================
# FUNÇÕES AUXILIARES
# ============================================================

def buscar_componente(componente_id):
    db = SessionLocal()

    componente = (
        db.query(models.Componente)
        .filter(models.Componente.id == componente_id)
        .first()
    )

    db.close()

    return componente


def buscar_anomalia(anomalia_id):
    db = SessionLocal()

    anomalia = (
        db.query(models.AnomaliaPermanente)
        .filter(models.AnomaliaPermanente.id == anomalia_id)
        .first()
    )

    db.close()

    return anomalia


def contar_fotos_observacao(observacao_id):
    db = SessionLocal()

    quantidade = (
        db.query(models.VinculoFotografiaAnomalia)
        .filter(
            models.VinculoFotografiaAnomalia.observacao_anomalia_id
            == observacao_id
        )
        .count()
    )

    db.close()

    return quantidade


def buscar_fotos_observacao(observacao_id):
    db = SessionLocal()

    vinculos = (
        db.query(models.VinculoFotografiaAnomalia)
        .filter(
            models.VinculoFotografiaAnomalia.observacao_anomalia_id
            == observacao_id
        )
        .all()
    )

    fotografias = []

    for vinculo in vinculos:

        foto = (
            db.query(models.Fotografia)
            .filter(
                models.Fotografia.id
                == vinculo.fotografia_id
            )
            .first()
        )

        if foto is not None:
            fotografias.append(foto)

    db.close()

    return fotografias


def calcular_notas_inspecao(oae_id, inspecao_id):
    db = SessionLocal()

    classificacoes = (
        db.query(models.Classificacao)
        .filter(models.Classificacao.oae_id == oae_id)
        .filter(models.Classificacao.inspecao_id == inspecao_id)
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


def contar_componentes_avaliados(inspecao_id):
    db = SessionLocal()

    classificacoes = (
        db.query(models.Classificacao)
        .filter(
            models.Classificacao.inspecao_id
            == inspecao_id
        )
        .all()
    )

    db.close()

    ids_componentes = {
        item.componente_id
        for item in classificacoes
    }

    return len(ids_componentes)


def buscar_observacoes_inspecao(inspecao_id):
    db = SessionLocal()

    observacoes = (
        db.query(models.ObservacaoAnomalia)
        .filter(
            models.ObservacaoAnomalia.inspecao_id
            == inspecao_id
        )
        .order_by(models.ObservacaoAnomalia.id)
        .all()
    )

    db.close()

    return observacoes


def contar_fotografias_inspecao(oae_id, inspecao_id):
    db = SessionLocal()

    quantidade = (
        db.query(models.Fotografia)
        .filter(models.Fotografia.oae_id == oae_id)
        .filter(models.Fotografia.inspecao_id == inspecao_id)
        .count()
    )

    db.close()

    return quantidade


# ============================================================
# MÓDULO PRINCIPAL
# ============================================================

def mostrar_historico_oae(oae_ativa):

    st.header(
        "📚 Histórico das inspeções"
    )

    if oae_ativa is None:

        st.warning(
            "Selecione uma OAE para visualizar o histórico."
        )

        return


    st.caption(
        f"Histórico da OAE: "
        f"{oae_ativa.id} - {oae_ativa.nome}"
    )


    # ========================================================
    # BUSCAR INSPEÇÕES
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
            "Nenhuma inspeção cadastrada para esta OAE."
        )

        return


    # ========================================================
    # EXIBIR CADA INSPEÇÃO
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
                f"**ID da inspeção:** {inspecao.id}"
            )

            st.write(
                f"**Tipo:** {inspecao.tipo_inspecao}"
            )

            st.write(
                f"**Data:** "
                f"{inspecao.data_inspecao.strftime('%d/%m/%Y')}"
            )

            st.write(
                f"**Responsável:** "
                f"{inspecao.responsavel or 'Não informado'}"
            )

            st.write(
                f"**Registro profissional:** "
                f"{inspecao.registro_profissional or 'Não informado'}"
            )

            st.write(
                f"**Observações gerais:** "
                f"{inspecao.observacoes or 'Nenhuma'}"
            )


            # =================================================
            # RESUMO
            # =================================================

            componentes_avaliados = (
                contar_componentes_avaliados(
                    inspecao.id
                )
            )

            observacoes_anomalias = (
                buscar_observacoes_inspecao(
                    inspecao.id
                )
            )

            fotografias = (
                contar_fotografias_inspecao(
                    oae_ativa.id,
                    inspecao.id
                )
            )


            col1, col2, col3 = (
                st.columns(3)
            )

            with col1:

                st.metric(
                    "Componentes avaliados",
                    componentes_avaliados
                )

            with col2:

                st.metric(
                    "Anomalias observadas",
                    len(observacoes_anomalias)
                )

            with col3:

                st.metric(
                    "Fotografias",
                    fotografias
                )


            # =================================================
            # CLASSIFICAÇÃO DA INSPEÇÃO
            # =================================================

            st.subheader(
                "⭐ Classificação da inspeção"
            )

            notas = calcular_notas_inspecao(
                oae_ativa.id,
                inspecao.id
            )

            if notas is None:

                st.info(
                    "Nenhuma classificação registrada "
                    "para esta inspeção."
                )

            else:

                col1, col2, col3 = (
                    st.columns(3)
                )

                with col1:

                    st.metric(
                        "Estrutural",
                        notas["estrutural"]
                    )

                with col2:

                    st.metric(
                        "Funcional",
                        notas["funcional"]
                    )

                with col3:

                    st.metric(
                        "Durabilidade",
                        notas["durabilidade"]
                    )


            # =================================================
            # ANOMALIAS OBSERVADAS NA INSPEÇÃO
            # =================================================

            st.subheader(
                "⚠️ Anomalias observadas nesta inspeção"
            )

            if len(observacoes_anomalias) == 0:

                st.info(
                    "Nenhuma observação de anomalia "
                    "registrada nesta inspeção."
                )

            else:

                for observacao in observacoes_anomalias:

                    anomalia = buscar_anomalia(
                        observacao.anomalia_id
                    )

                    if anomalia is None:
                        continue

                    componente = buscar_componente(
                        anomalia.componente_id
                    )

                    nome_componente = (
                        componente.nome
                        if componente is not None
                        else f"Componente ID {anomalia.componente_id}"
                    )

                    titulo_anomalia = (
                        f"Anomalia ID {anomalia.id} - "
                        f"{anomalia.tipo_anomalia} - "
                        f"{nome_componente}"
                    )

                    with st.container(
                        border=True
                    ):

                        st.markdown(
                            f"#### {titulo_anomalia}"
                        )

                        st.write(
                            "**Localização de referência:**",
                            anomalia.localizacao_referencia
                        )

                        if observacao.localizacao_detalhada:

                            st.write(
                                "**Localização nesta inspeção:**",
                                observacao.localizacao_detalhada
                            )

                        if observacao.descricao:

                            st.write(
                                "**Descrição nesta inspeção:**",
                                observacao.descricao
                            )


                        # =====================================
                        # MEDIDAS
                        # =====================================

                        col1, col2, col3 = (
                            st.columns(3)
                        )

                        with col1:

                            if (
                                observacao.abertura_fissura_mm
                                is None
                            ):

                                abertura = "-"

                            else:

                                abertura = (
                                    f"{observacao.abertura_fissura_mm:.2f} mm"
                                )

                            st.metric(
                                "Abertura",
                                abertura
                            )

                        with col2:

                            if (
                                observacao.extensao_anomalia_cm
                                is None
                            ):

                                extensao = "-"

                            else:

                                extensao = (
                                    f"{observacao.extensao_anomalia_cm:.1f} cm"
                                )

                            st.metric(
                                "Extensão",
                                extensao
                            )

                        with col3:

                            st.metric(
                                "Fotografias vinculadas",
                                contar_fotos_observacao(
                                    observacao.id
                                )
                            )


                        st.write(
                            "**Situação observada:**",
                            (
                                observacao.situacao_observada
                                or "Não informada"
                            )
                        )

                        if observacao.observacoes:

                            st.write(
                                "**Observações:**",
                                observacao.observacoes
                            )


                        # =====================================
                        # FOTOS DA OBSERVAÇÃO
                        # =====================================

                        fotos_observacao = (
                            buscar_fotos_observacao(
                                observacao.id
                            )
                        )

                        if len(fotos_observacao) > 0:

                            st.write(
                                "**Registro fotográfico vinculado:**"
                            )

                            for foto in fotos_observacao:

                                st.write(
                                    f"📷 Foto ID {foto.id} - "
                                    f"{foto.identificacao}"
                                )