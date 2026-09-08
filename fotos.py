import streamlit as st

from pathlib import Path
from uuid import uuid4

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


def vincular_fotografia_existente_a_anomalia(
    fotografia_id,
    componente_id,
    anomalia_id,
    observacao_id,
):
    """
    Vincula uma fotografia já cadastrada a uma anomalia permanente
    e à observação temporal correspondente.

    Também sincroniza o componente e o tipo do registro fotográfico
    para evitar informações contraditórias na interface.
    """

    db = SessionLocal()

    try:

        fotografia = (
            db.query(models.Fotografia)
            .filter(
                models.Fotografia.id
                == fotografia_id
            )
            .first()
        )

        if fotografia is None:

            db.close()
            return (
                False,
                "Fotografia não localizada."
            )

        vinculo_existente = (
            db.query(
                models.VinculoFotografiaAnomalia
            )
            .filter(
                models.VinculoFotografiaAnomalia.fotografia_id
                == fotografia_id
            )
            .first()
        )

        if vinculo_existente is not None:

            db.close()
            return (
                False,
                "Esta fotografia já possui vínculo com uma anomalia."
            )

        anomalia = (
            db.query(models.AnomaliaPermanente)
            .filter(
                models.AnomaliaPermanente.id
                == anomalia_id
            )
            .first()
        )

        observacao = (
            db.query(models.ObservacaoAnomalia)
            .filter(
                models.ObservacaoAnomalia.id
                == observacao_id
            )
            .first()
        )

        if (
            anomalia is None
            or
            observacao is None
        ):

            db.close()
            return (
                False,
                "A anomalia ou a observação selecionada não foi localizada."
            )

        if observacao.anomalia_id != anomalia.id:

            db.close()
            return (
                False,
                "A observação selecionada não pertence à anomalia informada."
            )

        if fotografia.inspecao_id != observacao.inspecao_id:

            db.close()
            return (
                False,
                "A fotografia e a observação pertencem a inspeções diferentes."
            )

        if anomalia.componente_id != componente_id:

            db.close()
            return (
                False,
                "O componente selecionado não corresponde à anomalia."
            )

        novo_vinculo = (
            models.VinculoFotografiaAnomalia(
                fotografia_id=
                    fotografia.id,
                anomalia_permanente_id=
                    anomalia.id,
                observacao_anomalia_id=
                    observacao.id
            )
        )

        fotografia.componente_id = (
            componente_id
        )

        fotografia.tipo_registro = (
            "Anomalia"
        )

        db.add(
            novo_vinculo
        )

        db.commit()

        db.close()

        return (
            True,
            "Fotografia vinculada à anomalia com sucesso."
        )

    except Exception as erro:

        db.rollback()
        db.close()

        return (
            False,
            f"Não foi possível criar o vínculo. Detalhe: {erro}"
        )


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
    componente_ativo=None
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




    # ========================================================
    # CONTEXTO
    # ========================================================

    numero_inspecao = numero_visual_inspecao(
        oae_ativa.id,
        inspecao_ativa.id,
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

    st.caption(
        "Defina abaixo o que a fotografia registra. "
        "O componente será solicitado somente quando necessário."
    )

    st.divider()


    # ========================================================
    # NOVA FOTOGRAFIA
    # ========================================================

    st.subheader(
        "➕ Adicionar fotografia"
    )

    escopo_fotografia = st.radio(
        "O que esta fotografia registra?",
        [
            "Vista geral da OAE",
            "Componente específico",
            "Anomalia observada nesta inspeção"
        ],
        horizontal=True,
        key=f"escopo_fotografia_{inspecao_ativa.id}"
    )

    componente_selecionado = None
    observacoes_disponiveis = []

    if escopo_fotografia == "Vista geral da OAE":

        st.info(
            "Esta fotografia será vinculada à OAE e à inspeção, "
            "sem componente específico."
        )

    else:

        componentes = _buscar_componentes_ordenados(
            oae_ativa.id
        )

        if len(componentes) == 0:

            st.warning(
                "Esta OAE ainda não possui componentes cadastrados."
            )

        else:

            mapa_componentes = {
                item.id: item
                for item in componentes
            }

            mapa_rotulos = {
                item.id: (
                    f"{numero:02d} • "
                    f"{item.nome} • "
                    f"{item.categoria or 'Categoria não informada'}"
                )
                for numero, item in enumerate(
                    componentes,
                    start=1
                )
            }

            sufixo_chave = (
                "componente"
                if escopo_fotografia == "Componente específico"
                else "anomalia"
            )

            componente_id = st.selectbox(
                (
                    "Componente fotografado"
                    if escopo_fotografia == "Componente específico"
                    else "Componente da anomalia"
                ),
                options=list(mapa_componentes.keys()),
                index=None,
                placeholder="Selecione um componente...",
                format_func=lambda valor: mapa_rotulos[valor],
                key=(
                    f"foto_componente_{inspecao_ativa.id}_"
                    f"{sufixo_chave}"
                ),
            )

            if componente_id is not None:

                componente_selecionado = (
                    mapa_componentes[componente_id]
                )

                if escopo_fotografia == "Componente específico":

                    st.info(
                        "Esta fotografia será vinculada ao componente "
                        f"{componente_selecionado.nome}."
                    )

                else:

                    observacoes_disponiveis = (
                        buscar_observacoes_anomalias(
                            oae_id=oae_ativa.id,
                            inspecao_id=inspecao_ativa.id,
                            componente_id=componente_selecionado.id
                        )
                    )

            elif escopo_fotografia == "Componente específico":

                st.caption(
                    "Selecione o componente que aparece na fotografia."
                )

            else:

                st.caption(
                    "Selecione primeiro o componente onde a anomalia "
                    "foi observada."
                )


    # ========================================================
    # ESCOLHA DA ANOMALIA
    # ========================================================

    item_anomalia_selecionado = None

    if (
        escopo_fotografia
        == "Anomalia observada nesta inspeção"
    ):

        if componente_selecionado is None:

            pass

        elif len(observacoes_disponiveis) == 0:

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
                    f"{codigo_visual_anomalia(oae_ativa.id, anomalia.id)} - "
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
                f"{codigo_visual_anomalia(oae_ativa.id, anomalia_selecionada.id)}."
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
                    "Registro vinculado à campanha atual"
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
        escopo_fotografia
        == "Componente específico"
        and
        componente_selecionado is None
    ):

        pode_salvar = False

    if (
        escopo_fotografia
        == "Anomalia observada nesta inspeção"
        and
        (
            componente_selecionado is None
            or
            item_anomalia_selecionado is None
        )
    ):

        pode_salvar = False


    with st.form(
        f"form_registro_fotografico_{inspecao_ativa.id}"
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

        opcoes_tipo_registro = [
            "Vista geral",
            "Vista superior",
            "Vista lateral",
            "Vista inferior",
            "Elemento estrutural",
            "Anomalia",
            "Outro"
        ]

        if escopo_fotografia == "Vista geral da OAE":

            indice_tipo_registro = 0

        elif escopo_fotografia == "Anomalia observada nesta inspeção":

            indice_tipo_registro = 5

        else:

            indice_tipo_registro = 4

        tipo_registro = st.selectbox(
            "Tipo de registro",
            opcoes_tipo_registro,
            index=indice_tipo_registro,
            disabled=(
                escopo_fotografia
                == "Anomalia observada nesta inspeção"
            ),
            help=(
                "Quando a fotografia é vinculada a uma anomalia, "
                "o tipo de registro é definido automaticamente como 'Anomalia'."
                if (
                    escopo_fotografia
                    == "Anomalia observada nesta inspeção"
                )
                else None
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
                componente_id=(
                    None
                    if escopo_fotografia == "Vista geral da OAE"
                    else componente_selecionado.id
                ),

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
                escopo_fotografia
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


            numero_foto = numero_visual_fotografia(
                oae_ativa.id,
                inspecao_ativa.id,
                foto_id,
            )

            st.success(
                (
                    f"Fotografia registrada com sucesso: "
                    f"Foto {numero_foto:02d}."
                )
                if isinstance(numero_foto, int)
                else "Fotografia registrada com sucesso."
            )

            if (
                escopo_fotografia
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

        numero_foto = numero_visual_fotografia(
            oae_ativa.id,
            inspecao_ativa.id,
            foto.id,
        )

        titulo = (
            (
                f"Foto {numero_foto:02d} - "
                f"{foto.identificacao}"
            )
            if isinstance(numero_foto, int)
            else f"Foto - {foto.identificacao}"
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
                    "**Número da fotografia:**",
                    (
                        f"Foto {numero_foto:02d}"
                        if isinstance(numero_foto, int)
                        else "—"
                    )
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
                    (
                        componente_nome
                        if foto.componente_id is not None
                        else "Sem componente específico — vista geral da OAE"
                    )
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

                    st.markdown(
                        "#### 🔗 Vincular esta fotografia a uma anomalia"
                    )

                    st.caption(
                        "Use esta opção quando a fotografia já foi cadastrada, "
                        "mas deveria estar associada a uma anomalia observada "
                        "nesta mesma inspeção."
                    )

                    componentes_vinculo = (
                        _buscar_componentes_ordenados(
                            oae_ativa.id
                        )
                    )

                    mapa_componentes_vinculo = {
                        item.id: item
                        for item in componentes_vinculo
                    }

                    mapa_rotulos_componentes_vinculo = {
                        item.id: (
                            f"{numero:02d} • "
                            f"{item.nome} • "
                            f"{item.categoria or 'Categoria não informada'}"
                        )
                        for numero, item in enumerate(
                            componentes_vinculo,
                            start=1
                        )
                    }

                    componente_padrao_id = (
                        foto.componente_id
                        if (
                            foto.componente_id
                            in mapa_componentes_vinculo
                        )
                        else None
                    )

                    opcoes_componentes_vinculo = list(
                        mapa_componentes_vinculo.keys()
                    )

                    indice_componente_vinculo = None

                    if (
                        componente_padrao_id is not None
                        and
                        componente_padrao_id
                        in opcoes_componentes_vinculo
                    ):

                        indice_componente_vinculo = (
                            opcoes_componentes_vinculo.index(
                                componente_padrao_id
                            )
                        )

                    componente_vinculo_id = st.selectbox(
                        "Componente da anomalia",
                        options=opcoes_componentes_vinculo,
                        index=indice_componente_vinculo,
                        placeholder="Selecione um componente...",
                        format_func=lambda valor: (
                            mapa_rotulos_componentes_vinculo[
                                valor
                            ]
                        ),
                        key=f"vincular_foto_componente_{foto.id}"
                    )

                    if componente_vinculo_id is not None:

                        observacoes_para_vinculo = (
                            buscar_observacoes_anomalias(
                                oae_id=oae_ativa.id,
                                inspecao_id=inspecao_ativa.id,
                                componente_id=
                                    componente_vinculo_id
                            )
                        )

                    else:

                        observacoes_para_vinculo = []

                    if len(observacoes_para_vinculo) == 0:

                        st.caption(
                            "Nenhuma anomalia com observação registrada "
                            "nesta inspeção foi encontrada para o componente "
                            "selecionado."
                        )

                    else:

                        mapa_anomalias_vinculo = {}

                        for item_vinculo in observacoes_para_vinculo:

                            anomalia_vinculo = (
                                item_vinculo[
                                    "anomalia"
                                ]
                            )

                            observacao_vinculo = (
                                item_vinculo[
                                    "observacao"
                                ]
                            )

                            rotulo_anomalia_vinculo = (
                                f"{codigo_visual_anomalia(oae_ativa.id, anomalia_vinculo.id)} - "
                                f"{anomalia_vinculo.tipo_anomalia} - "
                                f"{anomalia_vinculo.localizacao_referencia}"
                            )

                            mapa_anomalias_vinculo[
                                rotulo_anomalia_vinculo
                            ] = {
                                "anomalia":
                                    anomalia_vinculo,
                                "observacao":
                                    observacao_vinculo
                            }

                        anomalia_vinculo_texto = (
                            st.selectbox(
                                "Anomalia observada nesta inspeção",
                                options=list(
                                    mapa_anomalias_vinculo.keys()
                                ),
                                key=f"vincular_foto_anomalia_{foto.id}"
                            )
                        )

                        item_vinculo_selecionado = (
                            mapa_anomalias_vinculo[
                                anomalia_vinculo_texto
                            ]
                        )

                        anomalia_vinculo_selecionada = (
                            item_vinculo_selecionado[
                                "anomalia"
                            ]
                        )

                        observacao_vinculo_selecionada = (
                            item_vinculo_selecionado[
                                "observacao"
                            ]
                        )

                        st.write(
                            "**Vínculo que será criado:**",
                            (
                                f"{codigo_visual_anomalia(oae_ativa.id, anomalia_vinculo_selecionada.id)} "
                                f"— {anomalia_vinculo_selecionada.tipo_anomalia}"
                            )
                        )

                        confirmar_vinculo = st.checkbox(
                            "Confirmo o vínculo desta fotografia com a anomalia selecionada",
                            key=f"confirmar_vinculo_foto_{foto.id}"
                        )

                        if st.button(
                            "🔗 Vincular fotografia à anomalia",
                            key=f"vincular_foto_{foto.id}",
                            type="primary",
                            disabled=not confirmar_vinculo
                        ):

                            sucesso_vinculo, mensagem_vinculo = (
                                vincular_fotografia_existente_a_anomalia(
                                    fotografia_id=
                                        foto.id,
                                    componente_id=
                                        componente_vinculo_id,
                                    anomalia_id=
                                        anomalia_vinculo_selecionada.id,
                                    observacao_id=
                                        observacao_vinculo_selecionada.id,
                                )
                            )

                            if sucesso_vinculo:

                                st.success(
                                    mensagem_vinculo
                                )

                                st.rerun()

                            else:

                                st.error(
                                    mensagem_vinculo
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
                            f"{codigo_visual_anomalia(oae_ativa.id, anomalia.id)} - "
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
                        "Registro vinculado à campanha"
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
            # EXCLUSÃO SEGURA
            # ------------------------------------------------

            st.divider()

            st.markdown(
                "#### 🗑️ Excluir fotografia"
            )

            st.caption(
                "Use esta opção quando a fotografia tiver sido "
                "cadastrada por engano. O registro, o vínculo com "
                "anomalia e o arquivo local serão removidos."
            )

            confirmar_exclusao_foto = st.checkbox(
                "Confirmo que desejo excluir esta fotografia",
                key=f"confirmar_exclusao_foto_{foto.id}"
            )

            if st.button(
                "🗑️ Excluir definitivamente esta fotografia",
                key=f"excluir_foto_{foto.id}",
                disabled=not confirmar_exclusao_foto,
            ):

                caminho_para_excluir = Path(
                    foto.caminho_arquivo
                )

                db_exclusao = SessionLocal()

                try:

                    db_exclusao.query(
                        models.VinculoFotografiaAnomalia
                    ).filter(
                        models.VinculoFotografiaAnomalia.fotografia_id
                        == foto.id
                    ).delete(
                        synchronize_session=False
                    )

                    db_exclusao.query(
                        models.Fotografia
                    ).filter(
                        models.Fotografia.id
                        == foto.id
                    ).delete(
                        synchronize_session=False
                    )

                    db_exclusao.commit()

                except Exception as erro:

                    db_exclusao.rollback()
                    db_exclusao.close()

                    st.error(
                        "Não foi possível excluir a fotografia. "
                        f"Detalhe: {erro}"
                    )

                    st.stop()

                db_exclusao.close()

                try:

                    if caminho_para_excluir.exists():
                        caminho_para_excluir.unlink()

                except Exception:

                    pass

                st.success(
                    "Fotografia excluída com sucesso."
                )

                st.rerun()


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