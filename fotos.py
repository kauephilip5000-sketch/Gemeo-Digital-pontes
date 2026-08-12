import streamlit as st

from pathlib import Path
from uuid import uuid4

from database import SessionLocal
import models


def mostrar_modulo_fotografias(
    oae_ativa,
    inspecao_ativa,
    componente_ativo
):

    st.divider()

    st.header("Registro fotográfico")

    if inspecao_ativa is None:

        st.warning(
            "Selecione uma inspeção antes de registrar fotografias."
        )

        return

    if componente_ativo is None:

        st.warning(
            "Selecione um componente antes de registrar fotografias."
        )

        return


    # ========================================================
    # BUSCAR ANOMALIAS DO COMPONENTE NA INSPEÇÃO
    # ========================================================

    db = SessionLocal()

    anomalias = (
        db.query(models.Anomalia)
        .filter(
            models.Anomalia.oae_id
            == oae_ativa.id
        )
        .filter(
            models.Anomalia.inspecao_id
            == inspecao_ativa.id
        )
        .filter(
            models.Anomalia.componente_id
            == componente_ativo.id
        )
        .order_by(
            models.Anomalia.id
        )
        .all()
    )

    db.close()


    # ========================================================
    # INFORMAÇÕES DO VÍNCULO
    # ========================================================

    st.write(
        f"**OAE:** {oae_ativa.nome}"
    )

    st.write(
        f"**Inspeção:** "
        f"{inspecao_ativa.tipo_inspecao} - "
        f"{inspecao_ativa.data_inspecao.strftime('%d/%m/%Y')}"
    )

    st.write(
        f"**Componente:** {componente_ativo.nome}"
    )


    # ========================================================
    # OPÇÕES DE ANOMALIA
    # ========================================================

    opcoes_anomalias = {
        "Sem anomalia associada": None
    }

    for anomalia in anomalias:

        texto = (
            f"{anomalia.id} - "
            f"{anomalia.tipo_anomalia}"
        )

        opcoes_anomalias[texto] = anomalia


    # ========================================================
    # FORMULÁRIO DE REGISTRO FOTOGRÁFICO
    # ========================================================

    with st.form(
        "form_registro_fotografico",
        clear_on_submit=True
    ):

        arquivo_foto = st.file_uploader(
            "Selecione a fotografia",
            type=[
                "jpg",
                "jpeg",
                "png",
                "webp"
            ]
        )

        data_foto = st.date_input(
            "Data da fotografia",
            format="DD/MM/YYYY"
        )

        tipo_registro = st.selectbox(
            "Tipo de registro fotográfico",
            [
                "Vista geral",
                "Vista superior",
                "Vista lateral",
                "Vista inferior",
                "Elemento estrutural",
                "Anomalia",
                "Outro"
            ]
        )

        identificacao = st.text_input(
            "Identificação da fotografia",
            placeholder="Ex.: Foto 01 - Longarina L1"
        )

        anomalia_selecionada_texto = st.selectbox(
            "Anomalia relacionada",
            options=list(
                opcoes_anomalias.keys()
            )
        )

        observacoes_foto = st.text_area(
            "Observações da fotografia"
        )

        salvar_foto = st.form_submit_button(
            "Salvar fotografia"
        )


    # ========================================================
    # SALVAR FOTOGRAFIA
    # ========================================================

    if salvar_foto:

        if arquivo_foto is None:

            st.error(
                "Selecione uma fotografia."
            )

        elif identificacao == "":

            st.error(
                "Informe a identificação da fotografia."
            )

        else:

            pasta_fotos = Path(
                "uploads/fotos"
            )

            pasta_fotos.mkdir(
                parents=True,
                exist_ok=True
            )

            extensao = Path(
                arquivo_foto.name
            ).suffix.lower()

            nome_unico = (
                f"{uuid4().hex}{extensao}"
            )

            caminho_arquivo = (
                pasta_fotos / nome_unico
            )

            caminho_arquivo.write_bytes(
                arquivo_foto.getbuffer()
            )

            anomalia_selecionada = (
                opcoes_anomalias[
                    anomalia_selecionada_texto
                ]
            )

            if anomalia_selecionada is None:

                anomalia_id = None

            else:

                anomalia_id = (
                    anomalia_selecionada.id
                )


            db = SessionLocal()

            nova_foto = models.Fotografia(
                oae_id=oae_ativa.id,
                inspecao_id=inspecao_ativa.id,
                componente_id=componente_ativo.id,
                anomalia_id=anomalia_id,
                data_foto=data_foto,
                tipo_registro=tipo_registro,
                identificacao=identificacao,
                nome_arquivo=arquivo_foto.name,
                caminho_arquivo=str(
                    caminho_arquivo
                ),
                observacoes=observacoes_foto
            )

            db.add(
                nova_foto
            )

            db.commit()

            db.refresh(
                nova_foto
            )

            foto_id = nova_foto.id

            db.close()

            st.success(
                f"Fotografia cadastrada com sucesso. "
                f"ID gerado: {foto_id}"
            )


    # ========================================================
    # FOTOGRAFIAS CADASTRADAS
    # ========================================================

    st.subheader(
        "Fotografias da inspeção"
    )

    db = SessionLocal()

    fotografias = (
        db.query(models.Fotografia)
        .filter(
            models.Fotografia.oae_id
            == oae_ativa.id
        )
        .filter(
            models.Fotografia.inspecao_id
            == inspecao_ativa.id
        )
        .order_by(
            models.Fotografia.id
        )
        .all()
    )

    db.close()


    quantidade_fotos = len(
        fotografias
    )

    st.metric(
        "Total de fotografias nesta inspeção",
        quantidade_fotos
    )


    # ========================================================
    # CONTROLE DO QUANTITATIVO MÍNIMO
    # ========================================================

    if inspecao_ativa.tipo_inspecao in [
        "Cadastral",
        "Rotineira"
    ]:

        minimo_fotos = 8

        if quantidade_fotos < minimo_fotos:

            faltam = (
                minimo_fotos - quantidade_fotos
            )

            st.warning(
                f"Foram cadastrados {quantidade_fotos} "
                f"de {minimo_fotos} registros fotográficos. "
                f"Faltam pelo menos {faltam} registro(s) "
                f"para atingir o mínimo indicado na ficha "
                f"da ABNT NBR 9452:2023."
            )

        else:

            st.success(
                f"Quantitativo mínimo atendido: "
                f"{quantidade_fotos} registros fotográficos."
            )

    else:

        st.info(
            "Para este tipo de inspeção, o sistema não aplica "
            "automaticamente a regra de mínimo de oito registros."
        )


    # ========================================================
    # EXIBIÇÃO DAS FOTOGRAFIAS
    # ========================================================

    if quantidade_fotos == 0:

        st.info(
            "Nenhuma fotografia cadastrada "
            "para esta inspeção."
        )

    else:

        for fotografia in fotografias:

            st.write(
                f"### Foto {fotografia.id} - "
                f"{fotografia.identificacao}"
            )

            st.write(
                f"**Data:** "
                f"{fotografia.data_foto.strftime('%d/%m/%Y')}"
            )

            st.write(
                f"**Tipo:** "
                f"{fotografia.tipo_registro}"
            )

            if fotografia.anomalia_id is not None:

                st.write(
                    f"**Anomalia relacionada:** "
                    f"ID {fotografia.anomalia_id}"
                )

            else:

                st.write(
                    "**Anomalia relacionada:** "
                    "Nenhuma"
                )

            caminho = Path(
                fotografia.caminho_arquivo
            )

            if caminho.exists():

                st.image(
                    str(caminho),
                    caption=fotografia.identificacao,
                    width=600
                )

            else:

                st.warning(
                    "Arquivo da fotografia não encontrado."
                )

            if fotografia.observacoes:

                st.write(
                    f"**Observações:** "
                    f"{fotografia.observacoes}"
                )

            st.divider()