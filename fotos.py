import streamlit as st

from pathlib import Path
from uuid import uuid4

from database import SessionLocal
import models


# ============================================================
# PASTA DE ARMAZENAMENTO
# ============================================================

PASTA_FOTOS = Path(
    "uploads/fotos"
)

PASTA_FOTOS.mkdir(
    parents=True,
    exist_ok=True
)


# ============================================================
# FUNÇÕES AUXILIARES
# ============================================================

def buscar_observacoes_anomalias(
    oae_id,
    inspecao_id,
    componente_id
):

    db = SessionLocal()

    anomalias = (
        db.query(models.AnomaliaPermanente)
        .filter(
            models.AnomaliaPermanente.oae_id
            == oae_id
        )
        .filter(
            models.AnomaliaPermanente.componente_id
            == componente_id
        )
        .order_by(
            models.AnomaliaPermanente.id
        )
        .all()
    )

    resultados = []

    for anomalia in anomalias:

        observacao = (
            db.query(models.ObservacaoAnomalia)
            .filter(
                models.ObservacaoAnomalia.anomalia_id
                == anomalia.id
            )
            .filter(
                models.ObservacaoAnomalia.inspecao_id
                == inspecao_id
            )
            .first()
        )

        if observacao is not None:

            resultados.append(
                {
                    "anomalia": anomalia,
                    "observacao": observacao
                }
            )

    db.close()

    return resultados


def buscar_vinculo_fotografia(
    fotografia_id
):

    db = SessionLocal()

    vinculo = (
        db.query(
            models.VinculoFotografiaAnomalia
        )
        .filter(
            models.VinculoFotografiaAnomalia.fotografia_id
            == fotografia_id
        )
        .first()
    )

    if vinculo is None:

        db.close()

        return None

    anomalia = (
        db.query(
            models.AnomaliaPermanente
        )
        .filter(
            models.AnomaliaPermanente.id
            == vinculo.anomalia_permanente_id
        )
        .first()
    )

    observacao = (
        db.query(
            models.ObservacaoAnomalia
        )
        .filter(
            models.ObservacaoAnomalia.id
            == vinculo.observacao_anomalia_id
        )
        .first()
    )

    db.close()

    return {
        "vinculo": vinculo,
        "anomalia": anomalia,
        "observacao": observacao
    }


def buscar_nome_componente(
    componente_id
):

    if componente_id is None:
        return "Sem componente específico"

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

    if componente is None:
        return f"Componente ID {componente_id}"

    return componente.nome


# ============================================================
# MÓDULO PRINCIPAL
# ============================================================

def mostrar_modulo_fotografias(
    oae_ativa,
    inspecao_ativa,
    componente_ativo
):

    st.header(
        "📷 Registro fotográfico"
    )


    # ========================================================
    # VERIFICAÇÕES
    # ========================================================

    if oae_ativa is None:

        st.warning(
            "Selecione uma OAE antes de registrar fotografias."
        )

        return


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
    # CONTEXTO
    # ========================================================

    st.write(
        f"**OAE:** "
        f"{oae_ativa.id} - {oae_ativa.nome}"
    )

    st.write(
        f"**Inspeção:** "
        f"{inspecao_ativa.id} - "
        f"{inspecao_ativa.tipo_inspecao} - "
        f"{inspecao_ativa.data_inspecao.strftime('%d/%m/%Y')}"
    )

    st.write(
        f"**Componente:** "
        f"{componente_ativo.id} - "
        f"{componente_ativo.nome}"
    )

    st.divider()


    # ========================================================
    # OBSERVAÇÕES DE ANOMALIAS DISPONÍVEIS
    # ========================================================

    observacoes_disponiveis = (
        buscar_observacoes_anomalias(
            oae_id=oae_ativa.id,
            inspecao_id=inspecao_ativa.id,
            componente_id=componente_ativo.id
        )
    )


    # ========================================================
    # NOVA FOTOGRAFIA
    # ========================================================

    st.subheader(
        "➕ Adicionar fotografia"
    )

    tipo_vinculo = st.radio(
        "O que esta fotografia registra?",
        [
            "Registro geral do componente",
            "Anomalia observada nesta inspeção"
        ],
        horizontal=True
    )


    # ========================================================
    # ESCOLHA DA ANOMALIA
    # ========================================================

    item_anomalia_selecionado = None

    if (
        tipo_vinculo
        == "Anomalia observada nesta inspeção"
    ):

        if len(observacoes_disponiveis) == 0:

            st.warning(
                "Não existe nenhuma anomalia com observação "
                "registrada para este componente nesta inspeção."
            )

            st.info(
                "Primeiro vá ao módulo ⚠️ Anomalias e registre "
                "uma nova anomalia ou uma nova observação de "
                "anomalia existente. Depois volte aqui para "
                "vincular a fotografia."
            )

        else:

            mapa_anomalias = {}

            for item in observacoes_disponiveis:

                anomalia = item["anomalia"]
                observacao = item["observacao"]

                texto = (
                    f"ID {anomalia.id} - "
                    f"{anomalia.tipo_anomalia} - "
                    f"{anomalia.localizacao_referencia}"
                )

                mapa_anomalias[
                    texto
                ] = {
                    "anomalia": anomalia,
                    "observacao": observacao
                }

            opcao_anomalia = st.selectbox(
                "Anomalia registrada nesta inspeção",
                options=list(
                    mapa_anomalias.keys()
                )
            )

            item_anomalia_selecionado = (
                mapa_anomalias[
                    opcao_anomalia
                ]
            )

            anomalia_selecionada = (
                item_anomalia_selecionado[
                    "anomalia"
                ]
            )

            observacao_selecionada = (
                item_anomalia_selecionado[
                    "observacao"
                ]
            )

            st.success(
                f"Fotografia será vinculada à "
                f"Anomalia permanente ID "
                f"{anomalia_selecionada.id}."
            )

            col1, col2 = st.columns(2)

            with col1:

                st.write(
                    "**Tipo:**",
                    anomalia_selecionada.tipo_anomalia
                )

                st.write(
                    "**Localização de referência:**",
                    anomalia_selecionada.localizacao_referencia
                )

            with col2:

                st.write(
                    "**Observação desta inspeção:**",
                    f"ID {observacao_selecionada.id}"
                )

                st.write(
                    "**Situação observada:**",
                    (
                        observacao_selecionada.situacao_observada
                        or "Não informada"
                    )
                )


    # ========================================================
    # FORMULÁRIO DA FOTOGRAFIA
    # ========================================================

    pode_salvar = True

    if (
        tipo_vinculo
        == "Anomalia observada nesta inspeção"
        and
        item_anomalia_selecionado is None
    ):

        pode_salvar = False


    with st.form(
        "form_registro_fotografico"
    ):

        arquivo = st.file_uploader(
            "Selecionar fotografia",
            type=[
                "jpg",
                "jpeg",
                "png",
                "webp"
            ]
        )

        data_foto = st.date_input(
            "Data da fotografia",
            value=inspecao_ativa.data_inspecao,
            format="DD/MM/YYYY"
        )

        tipo_registro = st.selectbox(
            "Tipo de registro",
            [
                "Vista geral",
                "Vista superior",
                "Vista lateral",
                "Vista inferior",
                "Elemento estrutural",
                "Anomalia",
                "Outro"
            ],
            index=(
                5
                if (
                    tipo_vinculo
                    == "Anomalia observada nesta inspeção"
                )
                else 4
            )
        )

        identificacao = st.text_input(
            "Identificação da fotografia",
            placeholder=(
                "Ex.: Foto 03 - Fissura na face inferior "
                "da Longarina 1"
            )
        )

        observacoes_foto = st.text_area(
            "Observações da fotografia"
        )

        salvar_foto = st.form_submit_button(
            "Salvar fotografia",
            disabled=not pode_salvar
        )


    # ========================================================
    # SALVAR FOTOGRAFIA
    # ========================================================

    if salvar_foto:

        if arquivo is None:

            st.error(
                "Selecione uma fotografia."
            )

        elif identificacao.strip() == "":

            st.error(
                "Informe a identificação da fotografia."
            )

        else:

            extensao_original = (
                Path(
                    arquivo.name
                ).suffix.lower()
            )

            if extensao_original == "":

                extensao_original = ".jpg"

            nome_salvo = (
                f"{uuid4().hex}"
                f"{extensao_original}"
            )

            caminho_salvo = (
                PASTA_FOTOS
                / nome_salvo
            )


            # ------------------------------------------------
            # SALVAR ARQUIVO FÍSICO
            # ------------------------------------------------

            with open(
                caminho_salvo,
                "wb"
            ) as arquivo_destino:

                arquivo_destino.write(
                    arquivo.getbuffer()
                )


            # ------------------------------------------------
            # SALVAR REGISTRO NO BANCO
            # ------------------------------------------------

            db = SessionLocal()

            nova_foto = models.Fotografia(
                oae_id=oae_ativa.id,
                inspecao_id=inspecao_ativa.id,
                componente_id=componente_ativo.id,

                # O modelo antigo não será mais utilizado
                # para novas fotografias.
                anomalia_id=None,

                data_foto=data_foto,
                tipo_registro=tipo_registro,
                identificacao=identificacao,
                nome_arquivo=arquivo.name,
                caminho_arquivo=str(
                    caminho_salvo
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


            # ------------------------------------------------
            # VÍNCULO COM NOVO MODELO DE ANOMALIAS
            # ------------------------------------------------

            if (
                tipo_vinculo
                == "Anomalia observada nesta inspeção"
                and
                item_anomalia_selecionado
                is not None
            ):

                anomalia = (
                    item_anomalia_selecionado[
                        "anomalia"
                    ]
                )

                observacao = (
                    item_anomalia_selecionado[
                        "observacao"
                    ]
                )

                novo_vinculo = (
                    models.VinculoFotografiaAnomalia(
                        fotografia_id=
                            nova_foto.id,

                        anomalia_permanente_id=
                            anomalia.id,

                        observacao_anomalia_id=
                            observacao.id
                    )
                )

                db.add(
                    novo_vinculo
                )

                db.commit()


            foto_id = (
                nova_foto.id
            )

            db.close()


            st.success(
                f"Fotografia registrada com sucesso. "
                f"ID: {foto_id}"
            )

            if (
                tipo_vinculo
                == "Anomalia observada nesta inspeção"
            ):

                st.success(
                    "A fotografia também foi vinculada "
                    "à anomalia permanente e à observação "
                    "desta inspeção."
                )

            st.rerun()


    # ========================================================
    # LISTAGEM DAS FOTOGRAFIAS DA INSPEÇÃO
    # ========================================================

    st.divider()

    st.subheader(
        "📚 Fotografias da inspeção ativa"
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


    total_fotos = len(
        fotografias
    )

    st.metric(
        "Total de fotografias nesta inspeção",
        total_fotos
    )


    # ========================================================
    # VERIFICAÇÃO DE REGISTRO FOTOGRÁFICO
    # ========================================================

    if (
        inspecao_ativa.tipo_inspecao
        in [
            "Cadastral",
            "Rotineira"
        ]
    ):

        if total_fotos < 8:

            st.warning(
                f"Esta inspeção possui {total_fotos} "
                f"fotografia(s) registrada(s). "
                f"O roteiro correspondente prevê um "
                f"registro fotográfico mínimo, portanto "
                f"o conjunto ainda deve ser complementado."
            )

        else:

            st.success(
                "O registro fotográfico desta inspeção "
                "já possui pelo menos 8 fotografias."
            )

    else:

        st.info(
            "Para este tipo de inspeção, o sistema não "
            "aplicará automaticamente a regra numérica "
            "de 8 fotografias. A documentação deve ser "
            "compatível com o roteiro específico da campanha."
        )


    # ========================================================
    # SEM FOTOGRAFIAS
    # ========================================================

    if total_fotos == 0:

        st.info(
            "Nenhuma fotografia registrada "
            "nesta inspeção."
        )

        return


    # ========================================================
    # EXIBIR FOTOGRAFIAS
    # ========================================================

    for foto in fotografias:

        componente_nome = (
            buscar_nome_componente(
                foto.componente_id
            )
        )

        titulo = (
            f"Foto ID {foto.id} - "
            f"{foto.identificacao}"
        )

        with st.expander(
            titulo
        ):

            caminho = Path(
                foto.caminho_arquivo
            )

            if caminho.exists():

                try:

                    st.image(
                        str(caminho),
                        caption=foto.identificacao
                    )

                except Exception:

                    st.warning(
                        "Não foi possível exibir "
                        "esta imagem."
                    )

            else:

                st.warning(
                    "O arquivo desta fotografia "
                    "não foi encontrado na pasta local."
                )


            # ------------------------------------------------
            # INFORMAÇÕES BÁSICAS
            # ------------------------------------------------

            col1, col2 = st.columns(2)

            with col1:

                st.write(
                    "**ID da fotografia:**",
                    foto.id
                )

                st.write(
                    "**Data:**",
                    foto.data_foto.strftime(
                        "%d/%m/%Y"
                    )
                )

                st.write(
                    "**Tipo de registro:**",
                    foto.tipo_registro
                )

            with col2:

                st.write(
                    "**Componente:**",
                    componente_nome
                )

                st.write(
                    "**Arquivo original:**",
                    foto.nome_arquivo
                )


            # ------------------------------------------------
            # VÍNCULO COM ANOMALIA
            # ------------------------------------------------

            vinculo = (
                buscar_vinculo_fotografia(
                    foto.id
                )
            )

            if vinculo is None:

                if foto.anomalia_id is not None:

                    st.warning(
                        "Esta fotografia pertence ao modelo "
                        "antigo de anomalias. Ela será mantida "
                        "no histórico, mas ainda não possui "
                        "vínculo com uma anomalia permanente."
                    )

                else:

                    st.info(
                        "Registro geral, sem vínculo com "
                        "anomalia permanente."
                    )

            else:

                anomalia = (
                    vinculo[
                        "anomalia"
                    ]
                )

                observacao = (
                    vinculo[
                        "observacao"
                    ]
                )

                st.success(
                    "Fotografia vinculada ao "
                    "acompanhamento temporal de anomalia."
                )

                if anomalia is not None:

                    st.write(
                        "**Anomalia permanente:**",
                        (
                            f"ID {anomalia.id} - "
                            f"{anomalia.tipo_anomalia}"
                        )
                    )

                    st.write(
                        "**Localização de referência:**",
                        anomalia.localizacao_referencia
                    )

                if observacao is not None:

                    st.write(
                        "**Observação da inspeção:**",
                        f"ID {observacao.id}"
                    )

                    st.write(
                        "**Situação observada:**",
                        (
                            observacao.situacao_observada
                            or "Não informada"
                        )
                    )

                    if (
                        observacao.abertura_fissura_mm
                        is not None
                    ):

                        st.write(
                            "**Abertura registrada:**",
                            (
                                f"{observacao.abertura_fissura_mm:.2f} mm"
                            )
                        )

                    if (
                        observacao.extensao_anomalia_cm
                        is not None
                    ):

                        st.write(
                            "**Extensão registrada:**",
                            (
                                f"{observacao.extensao_anomalia_cm:.1f} cm"
                            )
                        )


            # ------------------------------------------------
            # OBSERVAÇÕES
            # ------------------------------------------------

            if foto.observacoes:

                st.write(
                    "**Observações:**"
                )

                st.write(
                    foto.observacoes
                )