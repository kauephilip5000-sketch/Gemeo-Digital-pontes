import streamlit as st

from database import SessionLocal
import models


# ============================================================
# NUMERAÇÃO VISUAL
# ============================================================

ORDEM_CATEGORIAS_COMPONENTES = {
    "Superestrutura": 1,
    "Mesoestrutura": 2,
    "Infraestrutura": 3,
    "Encontros": 4,
    "Elementos complementares": 5,
    "Pista / via permanente": 6,
}


def _chave_natural(texto):

    import re

    partes = re.split(
        r"(\d+)",
        (texto or "").lower()
    )

    return [
        int(parte)
        if parte.isdigit()
        else parte
        for parte in partes
    ]


def _buscar_componentes_ordenados(oae_id):

    db = SessionLocal()

    componentes = (
        db.query(models.Componente)
        .filter(
            models.Componente.oae_id
            == oae_id
        )
        .all()
    )

    db.close()

    return sorted(
        componentes,
        key=lambda item: (
            ORDEM_CATEGORIAS_COMPONENTES.get(
                getattr(
                    item,
                    "categoria",
                    None
                ),
                999
            ),
            _chave_natural(
                getattr(
                    item,
                    "nome",
                    ""
                )
            ),
            item.id,
        )
    )


def numero_visual_componente(
    oae_id,
    componente_id,
):

    componentes = _buscar_componentes_ordenados(
        oae_id
    )

    for numero, componente in enumerate(
        componentes,
        start=1
    ):

        if componente.id == componente_id:
            return numero

    return "—"


def numero_visual_inspecao(
    oae_id,
    inspecao_id,
):

    db = SessionLocal()

    inspecoes = (
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

    for numero, inspecao in enumerate(
        inspecoes,
        start=1
    ):

        if inspecao.id == inspecao_id:
            return numero

    return "—"


def numero_visual_anomalia(
    oae_id,
    anomalia_id,
):

    db = SessionLocal()

    anomalias = (
        db.query(models.AnomaliaPermanente)
        .filter(
            models.AnomaliaPermanente.oae_id
            == oae_id
        )
        .order_by(
            models.AnomaliaPermanente.id.asc()
        )
        .all()
    )

    db.close()

    for numero, item in enumerate(
        anomalias,
        start=1
    ):

        if item.id == anomalia_id:
            return numero

    return "—"


def codigo_visual_anomalia(
    oae_id,
    anomalia_id,
):

    numero = numero_visual_anomalia(
        oae_id,
        anomalia_id,
    )

    if isinstance(numero, int):
        return f"A{numero:02d}"

    return "A—"


def numero_visual_fotografia(
    oae_id,
    inspecao_id,
    fotografia_id,
):

    db = SessionLocal()

    fotografias = (
        db.query(models.Fotografia)
        .filter(
            models.Fotografia.oae_id
            == oae_id
        )
        .filter(
            models.Fotografia.inspecao_id
            == inspecao_id
        )
        .order_by(
            models.Fotografia.data_foto.asc(),
            models.Fotografia.id.asc(),
        )
        .all()
    )

    db.close()

    for numero, item in enumerate(
        fotografias,
        start=1
    ):

        if item.id == fotografia_id:
            return numero

    return "—"




def mostrar_modulo_anomalias(
    oae_ativa,
    inspecao_ativa,
    componente_ativo
):

    st.divider()

    st.header(
        "Registro de anomalias"
    )

    if inspecao_ativa is None:

        st.warning(
            "Selecione uma inspeção antes de registrar anomalias."
        )

        return

    if componente_ativo is None:

        st.warning(
            "Selecione um componente antes de registrar anomalias."
        )

        return


    # ========================================================
    # CONTEXTO ATUAL
    # ========================================================

    numero_inspecao = numero_visual_inspecao(
        oae_ativa.id,
        inspecao_ativa.id,
    )

    numero_componente = numero_visual_componente(
        oae_ativa.id,
        componente_ativo.id,
    )

    st.write(
        f"**OAE:** {oae_ativa.nome}"
    )

    st.write(
        f"**Inspeção:** "
        f"{numero_inspecao} - "
        f"{inspecao_ativa.tipo_inspecao} - "
        f"{inspecao_ativa.data_inspecao.strftime('%d/%m/%Y')}"
    )

    st.write(
        f"**Componente:** "
        f"{numero_componente} - "
        f"{componente_ativo.nome}"
    )


    # ========================================================
    # BUSCAR ANOMALIAS PERMANENTES DO COMPONENTE
    # ========================================================

    db = SessionLocal()

    anomalias_existentes = (
        db.query(models.AnomaliaPermanente)
        .filter(
            models.AnomaliaPermanente.oae_id
            == oae_ativa.id
        )
        .filter(
            models.AnomaliaPermanente.componente_id
            == componente_ativo.id
        )
        .filter(
            models.AnomaliaPermanente.ativa
            == 1
        )
        .order_by(
            models.AnomaliaPermanente.id
        )
        .all()
    )

    db.close()


    # ========================================================
    # ESCOLHER NOVA OU EXISTENTE
    # ========================================================

    tipo_registro = st.radio(
        "A ocorrência observada é:",
        [
            "Nova anomalia",
            "Anomalia já cadastrada"
        ]
    )


    # ========================================================
    # NOVA ANOMALIA
    # ========================================================

    if tipo_registro == "Nova anomalia":

        st.subheader(
            "Cadastrar nova anomalia"
        )

        with st.form(
            "form_nova_anomalia"
        ):

            tipo_anomalia = st.text_input(
                "Tipo de anomalia"
            )

            localizacao_referencia = st.text_input(
                "Localização de referência",
                placeholder=(
                    "Ex.: face inferior da Longarina 1, "
                    "região central do vão"
                )
            )

            descricao_inicial = st.text_area(
                "Descrição inicial da anomalia"
            )

            abertura_fissura_mm = st.number_input(
                "Abertura da fissura (mm)",
                min_value=0.0,
                step=0.01,
                format="%.2f"
            )

            extensao_anomalia_cm = st.number_input(
                "Extensão da anomalia (cm)",
                min_value=0.0,
                step=0.1,
                format="%.1f"
            )

            situacao_observada = st.selectbox(
                "Situação observada",
                [
                    "Identificada nesta inspeção",
                    "Estável",
                    "Evolução observada",
                    "Redução aparente",
                    "Reparada",
                    "Não determinada"
                ]
            )

            observacoes = st.text_area(
                "Observações"
            )

            salvar_nova_anomalia = (
                st.form_submit_button(
                    "Salvar nova anomalia"
                )
            )


        if salvar_nova_anomalia:

            if tipo_anomalia == "":

                st.error(
                    "Informe o tipo da anomalia."
                )

            elif localizacao_referencia == "":

                st.error(
                    "Informe a localização de referência."
                )

            else:

                db = SessionLocal()

                nova_anomalia = (
                    models.AnomaliaPermanente(
                        oae_id=oae_ativa.id,
                        componente_id=
                            componente_ativo.id,
                        inspecao_origem_id=
                            inspecao_ativa.id,
                        tipo_anomalia=
                            tipo_anomalia,
                        localizacao_referencia=
                            localizacao_referencia,
                        descricao_inicial=
                            descricao_inicial,
                        ativa=1
                    )
                )

                db.add(
                    nova_anomalia
                )

                db.commit()

                db.refresh(
                    nova_anomalia
                )


                nova_observacao = (
                    models.ObservacaoAnomalia(
                        anomalia_id=
                            nova_anomalia.id,
                        inspecao_id=
                            inspecao_ativa.id,
                        descricao=
                            descricao_inicial,
                        localizacao_detalhada=
                            localizacao_referencia,
                        abertura_fissura_mm=
                            (
                                abertura_fissura_mm
                                if abertura_fissura_mm > 0
                                else None
                            ),
                        extensao_anomalia_cm=
                            (
                                extensao_anomalia_cm
                                if extensao_anomalia_cm > 0
                                else None
                            ),
                        situacao_observada=
                            situacao_observada,
                        observacoes=
                            observacoes
                    )
                )

                db.add(
                    nova_observacao
                )

                db.commit()

                anomalia_id = (
                    nova_anomalia.id
                )

                db.close()

                codigo_anomalia = codigo_visual_anomalia(
                    oae_ativa.id,
                    anomalia_id,
                )

                st.success(
                    f"Nova anomalia cadastrada com sucesso: "
                    f"{codigo_anomalia}."
                )


    # ========================================================
    # ANOMALIA JÁ EXISTENTE
    # ========================================================

    else:

        st.subheader(
            "Registrar nova observação de anomalia existente"
        )

        if len(anomalias_existentes) == 0:

            st.info(
                "Não existem anomalias permanentes cadastradas "
                "para este componente."
            )

        else:

            opcoes_anomalias = {}

            for anomalia in anomalias_existentes:

                texto = (
                    f"{codigo_visual_anomalia(oae_ativa.id, anomalia.id)} - "
                    f"{anomalia.tipo_anomalia} - "
                    f"{anomalia.localizacao_referencia}"
                )

                opcoes_anomalias[
                    texto
                ] = anomalia


            anomalia_escolhida_texto = st.selectbox(
                "Selecione a anomalia observada novamente",
                options=list(
                    opcoes_anomalias.keys()
                )
            )

            anomalia_escolhida = (
                opcoes_anomalias[
                    anomalia_escolhida_texto
                ]
            )


            st.write(
                f"**Tipo:** "
                f"{anomalia_escolhida.tipo_anomalia}"
            )

            st.write(
                f"**Localização de referência:** "
                f"{anomalia_escolhida.localizacao_referencia}"
            )

            numero_origem = numero_visual_inspecao(
                oae_ativa.id,
                anomalia_escolhida.inspecao_origem_id,
            )

            st.write(
                f"**Inspeção de origem:** "
                f"{numero_origem}"
            )


            # =================================================
            # VERIFICAR OBSERVAÇÃO NESTA INSPEÇÃO
            # =================================================

            db = SessionLocal()

            observacao_existente = (
                db.query(models.ObservacaoAnomalia)
                .filter(
                    models.ObservacaoAnomalia.anomalia_id
                    == anomalia_escolhida.id
                )
                .filter(
                    models.ObservacaoAnomalia.inspecao_id
                    == inspecao_ativa.id
                )
                .first()
            )

            db.close()


            if observacao_existente is not None:

                st.warning(
                    "Esta anomalia já possui uma observação "
                    "registrada nesta inspeção."
                )

            else:

                with st.form(
                    "form_observacao_anomalia_existente"
                ):

                    descricao = st.text_area(
                        "Descrição nesta inspeção"
                    )

                    localizacao_detalhada = st.text_input(
                        "Localização detalhada nesta inspeção",
                        value=(
                            anomalia_escolhida
                            .localizacao_referencia
                        )
                    )

                    abertura_fissura_mm = st.number_input(
                        "Abertura da fissura (mm)",
                        min_value=0.0,
                        step=0.01,
                        format="%.2f"
                    )

                    extensao_anomalia_cm = st.number_input(
                        "Extensão da anomalia (cm)",
                        min_value=0.0,
                        step=0.1,
                        format="%.1f"
                    )

                    situacao_observada = st.selectbox(
                        "Situação observada",
                        [
                            "Estável",
                            "Evolução observada",
                            "Redução aparente",
                            "Reparada",
                            "Não determinada"
                        ]
                    )

                    observacoes = st.text_area(
                        "Observações"
                    )

                    salvar_observacao = (
                        st.form_submit_button(
                            "Salvar observação"
                        )
                    )


                if salvar_observacao:

                    db = SessionLocal()

                    nova_observacao = (
                        models.ObservacaoAnomalia(
                            anomalia_id=
                                anomalia_escolhida.id,
                            inspecao_id=
                                inspecao_ativa.id,
                            descricao=
                                descricao,
                            localizacao_detalhada=
                                localizacao_detalhada,
                            abertura_fissura_mm=
                                (
                                    abertura_fissura_mm
                                    if abertura_fissura_mm > 0
                                    else None
                                ),
                            extensao_anomalia_cm=
                                (
                                    extensao_anomalia_cm
                                    if extensao_anomalia_cm > 0
                                    else None
                                ),
                            situacao_observada=
                                situacao_observada,
                            observacoes=
                                observacoes
                        )
                    )

                    db.add(
                        nova_observacao
                    )

                    db.commit()

                    db.close()

                    st.success(
                        "Nova observação registrada "
                        "para a anomalia existente."
                    )


    # ========================================================
    # ANOMALIAS PERMANENTES DO COMPONENTE
    # ========================================================

    st.divider()

    st.subheader(
        "Anomalias acompanhadas neste componente"
    )

    db = SessionLocal()

    anomalias_listagem = (
        db.query(models.AnomaliaPermanente)
        .filter(
            models.AnomaliaPermanente.oae_id
            == oae_ativa.id
        )
        .filter(
            models.AnomaliaPermanente.componente_id
            == componente_ativo.id
        )
        .order_by(
            models.AnomaliaPermanente.id
        )
        .all()
    )

    db.close()


    if len(anomalias_listagem) == 0:

        st.info(
            "Nenhuma anomalia permanente cadastrada "
            "para este componente."
        )

    else:

        for anomalia in anomalias_listagem:

            titulo = (
                f"{codigo_visual_anomalia(oae_ativa.id, anomalia.id)} - "
                f"{anomalia.tipo_anomalia} - "
                f"{anomalia.localizacao_referencia}"
            )

            with st.expander(
                titulo
            ):

                numero_origem = numero_visual_inspecao(
                    oae_ativa.id,
                    anomalia.inspecao_origem_id,
                )

                st.write(
                    f"**Inspeção de origem:** "
                    f"{numero_origem}"
                )

                st.write(
                    f"**Descrição inicial:** "
                    f"{anomalia.descricao_inicial}"
                )

                db = SessionLocal()

                observacoes_anomalia = (
                    db.query(models.ObservacaoAnomalia)
                    .filter(
                        models.ObservacaoAnomalia.anomalia_id
                        == anomalia.id
                    )
                    .order_by(
                        models.ObservacaoAnomalia.inspecao_id
                    )
                    .all()
                )

                db.close()


                dados_observacoes = []

                for observacao in observacoes_anomalia:

                    db = SessionLocal()

                    inspecao = (
                        db.query(models.Inspecao)
                        .filter(
                            models.Inspecao.id
                            == observacao.inspecao_id
                        )
                        .first()
                    )

                    db.close()


                    if inspecao is None:

                        data_inspecao = (
                            "Inspeção não encontrada"
                        )

                    else:

                        data_inspecao = (
                            inspecao.data_inspecao.strftime(
                                "%d/%m/%Y"
                            )
                        )


                    dados_observacoes.append(
                        {
                            "Inspeção":
                                numero_visual_inspecao(
                                    oae_ativa.id,
                                    observacao.inspecao_id,
                                ),
                            "Data":
                                data_inspecao,
                            "Abertura (mm)":
                                observacao.abertura_fissura_mm,
                            "Extensão (cm)":
                                observacao.extensao_anomalia_cm,
                            "Situação":
                                observacao.situacao_observada,
                            "Descrição":
                                observacao.descricao
                        }
                    )


                if len(dados_observacoes) == 0:

                    st.info(
                        "Nenhuma observação cadastrada."
                    )

                else:

                    st.dataframe(
                        dados_observacoes,
                        width="stretch"
                    )