import streamlit as st

from database import SessionLocal
import models

from classificacao import (
    calcular_classificacao_consolidada,
    nota_texto
)


# ============================================================
# CONSULTAS
# ============================================================

def buscar_componente(componente_id):

    if componente_id is None:
        return None

    db = SessionLocal()

    componente = (
        db.query(models.Componente)
        .filter(
            models.Componente.id == componente_id
        )
        .first()
    )

    db.close()

    return componente


def buscar_anomalia(anomalia_id):

    if anomalia_id is None:
        return None

    db = SessionLocal()

    anomalia = (
        db.query(models.AnomaliaPermanente)
        .filter(
            models.AnomaliaPermanente.id
            == anomalia_id
        )
        .first()
    )

    db.close()

    return anomalia


# ============================================================
# FOTOGRAFIAS
# ============================================================

def contar_fotos_observacao(observacao_id):

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


def buscar_fotos_observacao(observacao_id):

    db = SessionLocal()

    vinculos = (
        db.query(
            models.VinculoFotografiaAnomalia
        )
        .filter(
            models.VinculoFotografiaAnomalia.observacao_anomalia_id
            == observacao_id
        )
        .all()
    )

    fotos = []

    for vinculo in vinculos:

        fotografia = (
            db.query(models.Fotografia)
            .filter(
                models.Fotografia.id
                == vinculo.fotografia_id
            )
            .first()
        )

        if fotografia is not None:
            fotos.append(fotografia)

    db.close()

    return fotos


def contar_fotografias_inspecao(
    oae_id,
    inspecao_id
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
#
# IMPORTANTE:
# Não calculamos min() diretamente aqui.
#
# Toda a consolidação vem do classificacao.py,
# que já exclui valores NA do cálculo.
# ============================================================

def calcular_notas_inspecao(
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


def contar_componentes_avaliados(
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

    ids = {
        item.componente_id
        for item in classificacoes
    }

    return len(ids)


# ============================================================
# OBSERVAÇÕES DAS ANOMALIAS
# ============================================================

def buscar_observacoes_inspecao(
    inspecao_id
):

    db = SessionLocal()

    observacoes = (
        db.query(
            models.ObservacaoAnomalia
        )
        .filter(
            models.ObservacaoAnomalia.inspecao_id
            == inspecao_id
        )
        .order_by(
            models.ObservacaoAnomalia.id
        )
        .all()
    )

    db.close()

    return observacoes


# ============================================================
# HISTÓRICO DA OAE
# ============================================================

def mostrar_historico_oae(oae_ativa):

    st.header(
        "📜 Histórico das inspeções"
    )

    st.caption(
        f"Histórico da OAE: "
        f"{oae_ativa.id} - {oae_ativa.nome}"
    )

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
    # CADA INSPEÇÃO
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

            # =================================================
            # DADOS DA INSPEÇÃO
            # =================================================

            st.write(
                "**Responsável:**",
                (
                    inspecao.responsavel
                    or "Não informado"
                )
            )

            st.write(
                "**Registro profissional:**",
                (
                    inspecao.registro_profissional
                    or "Não informado"
                )
            )

            if inspecao.observacoes:

                st.write(
                    "**Observações gerais:**"
                )

                st.write(
                    inspecao.observacoes
                )


            # =================================================
            # CONTADORES
            # =================================================

            observacoes = (
                buscar_observacoes_inspecao(
                    inspecao.id
                )
            )

            componentes_avaliados = (
                contar_componentes_avaliados(
                    oae_ativa.id,
                    inspecao.id
                )
            )

            fotos_inspecao = (
                contar_fotografias_inspecao(
                    oae_ativa.id,
                    inspecao.id
                )
            )

            st.divider()

            c1, c2, c3 = st.columns(3)

            with c1:

                st.metric(
                    "Componentes avaliados",
                    componentes_avaliados
                )

            with c2:

                st.metric(
                    "Anomalias observadas",
                    len(observacoes)
                )

            with c3:

                st.metric(
                    "Fotografias",
                    fotos_inspecao
                )


            # =================================================
            # NOTAS FINAIS DA INSPEÇÃO
            # =================================================

            st.divider()

            st.subheader(
                "⭐ Notas finais da inspeção"
            )

            notas = calcular_notas_inspecao(
                oae_ativa.id,
                inspecao.id
            )

            if notas is None:

                st.info(
                    "Nenhuma classificação registrada "
                    "nesta inspeção."
                )

            else:

                c1, c2, c3 = st.columns(3)

                # =============================================
                # ESTRUTURAL
                # =============================================

                with c1:

                    nota = notas[
                        "estrutural"
                    ]

                    if nota is None:

                        st.metric(
                            "Estrutural",
                            "—"
                        )

                    else:

                        st.metric(
                            "Estrutural",
                            nota
                        )

                        st.caption(
                            nota_texto(nota)
                        )


                # =============================================
                # FUNCIONAL
                # =============================================

                with c2:

                    nota = notas[
                        "funcional"
                    ]

                    if nota is None:

                        st.metric(
                            "Funcional",
                            "NA"
                        )

                        st.caption(
                            "Sem nota funcional aplicável"
                        )

                    else:

                        st.metric(
                            "Funcional",
                            nota
                        )

                        st.caption(
                            nota_texto(nota)
                        )


                # =============================================
                # DURABILIDADE
                # =============================================

                with c3:

                    nota = notas[
                        "durabilidade"
                    ]

                    if nota is None:

                        st.metric(
                            "Durabilidade",
                            "—"
                        )

                    else:

                        st.metric(
                            "Durabilidade",
                            nota
                        )

                        st.caption(
                            nota_texto(nota)
                        )


            # =================================================
            # ANOMALIAS
            # =================================================

            st.divider()

            st.subheader(
                "⚠️ Anomalias observadas"
            )

            if len(observacoes) == 0:

                st.info(
                    "Nenhuma observação de anomalia "
                    "registrada nesta inspeção."
                )

            else:

                for observacao in observacoes:

                    anomalia = buscar_anomalia(
                        observacao.anomalia_id
                    )

                    if anomalia is None:
                        continue

                    componente = buscar_componente(
                        anomalia.componente_id
                    )

                    if componente is None:

                        nome_componente = (
                            f"Componente ID "
                            f"{anomalia.componente_id}"
                        )

                    else:

                        nome_componente = (
                            componente.nome
                        )


                    # =========================================
                    # IDENTIFICAÇÃO
                    # =========================================

                    st.markdown(
                        f"#### {anomalia.tipo_anomalia}"
                    )

                    st.write(
                        "**Anomalia permanente ID:**",
                        anomalia.id
                    )

                    st.write(
                        "**Componente:**",
                        nome_componente
                    )

                    st.write(
                        "**Localização de referência:**",
                        (
                            anomalia.localizacao_referencia
                            or "Não informada"
                        )
                    )


                    # =========================================
                    # OBSERVAÇÃO DA CAMPANHA
                    # =========================================

                    st.write(
                        "**Descrição da observação:**",
                        (
                            observacao.descricao
                            or "Não informada"
                        )
                    )

                    if (
                        observacao.localizacao_detalhada
                    ):

                        st.write(
                            "**Localização detalhada:**",
                            observacao.localizacao_detalhada
                        )


                    # =========================================
                    # MEDIÇÕES
                    # =========================================

                    c1, c2 = st.columns(2)

                    with c1:

                        if (
                            observacao.abertura_fissura_mm
                            is not None
                        ):

                            st.metric(
                                "Abertura registrada",
                                (
                                    f"{observacao.abertura_fissura_mm:.2f} mm"
                                )
                            )

                        else:

                            st.write(
                                "**Abertura:** "
                                "Não registrada"
                            )


                    with c2:

                        if (
                            observacao.extensao_anomalia_cm
                            is not None
                        ):

                            st.metric(
                                "Extensão registrada",
                                (
                                    f"{observacao.extensao_anomalia_cm:.1f} cm"
                                )
                            )

                        else:

                            st.write(
                                "**Extensão:** "
                                "Não registrada"
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
                            "**Observações complementares:**"
                        )

                        st.write(
                            observacao.observacoes
                        )


                    # =========================================
                    # FOTOS DA OBSERVAÇÃO
                    # =========================================

                    quantidade_fotos = (
                        contar_fotos_observacao(
                            observacao.id
                        )
                    )

                    st.write(
                        "**Fotografias vinculadas:**",
                        quantidade_fotos
                    )

                    fotos = buscar_fotos_observacao(
                        observacao.id
                    )

                    if len(fotos) > 0:

                        itens_fotos = []

                        for foto in fotos:

                            identificacao = (
                                foto.identificacao
                                or
                                f"Foto ID {foto.id}"
                            )

                            itens_fotos.append(
                                f"{identificacao} "
                                f"(ID {foto.id})"
                            )

                        st.caption(
                            " | ".join(
                                itens_fotos
                            )
                        )

                    st.divider()