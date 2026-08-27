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





# ============================================================
# CATÁLOGO DE ANOMALIAS
# ============================================================

TIPOS_ANOMALIA = [
    "Fissura / trinca",
    "Desplacamento / destacamento do concreto",
    "Armadura exposta",
    "Corrosão de armadura",
    "Infiltração / umidade",
    "Eflorescência",
    "Deformação",
    "Deterioração de aparelho de apoio",
    "Deterioração de junta de dilatação",
    "Obstrução / deficiência de drenagem",
    "Desgaste / deterioração do pavimento",
    "Erosão / solapamento",
    "Dano por impacto",
    "Outra anomalia",
]


def normalizar_tipo_anomalia(
    tipo_selecionado,
    outro_tipo,
):

    if tipo_selecionado == "Outra anomalia":

        return (
            outro_tipo.strip()
            if outro_tipo
            and outro_tipo.strip()
            else "Outra anomalia"
        )

    return tipo_selecionado


def tipo_exige_abertura_fissura(
    tipo_selecionado,
):

    return (
        tipo_selecionado
        == "Fissura / trinca"
    )


def tipo_exige_extensao(
    tipo_selecionado,
):

    return tipo_selecionado in [
        "Fissura / trinca",
        "Desplacamento / destacamento do concreto",
        "Armadura exposta",
        "Corrosão de armadura",
        "Infiltração / umidade",
        "Eflorescência",
        "Deformação",
        "Deterioração de aparelho de apoio",
        "Deterioração de junta de dilatação",
        "Obstrução / deficiência de drenagem",
        "Desgaste / deterioração do pavimento",
        "Erosão / solapamento",
        "Dano por impacto",
        "Outra anomalia",
    ]


def rotulo_extensao_anomalia(
    tipo_selecionado,
):

    if tipo_selecionado == "Dano por impacto":
        return "Dimensão principal da área afetada (cm)"

    if tipo_selecionado == "Erosão / solapamento":
        return "Extensão aproximada da região afetada (cm)"

    if tipo_selecionado == "Obstrução / deficiência de drenagem":
        return "Extensão aproximada do trecho afetado (cm)"

    return "Extensão da anomalia (cm)"




def buscar_anomalias_oae(
    oae_id,
):

    db = SessionLocal()

    dados = (
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

    return dados


def buscar_componente_por_id(
    componente_id,
):

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


def buscar_inspecao_por_id(
    inspecao_id,
):

    if inspecao_id is None:
        return None

    db = SessionLocal()

    inspecao = (
        db.query(models.Inspecao)
        .filter(
            models.Inspecao.id
            == inspecao_id
        )
        .first()
    )

    db.close()

    return inspecao


def mostrar_visao_geral_anomalias_oae(
    oae_ativa,
    componente_ativo=None,
):

    st.divider()

    st.subheader(
        "🌉 Visão geral das anomalias da OAE"
    )

    st.caption(
        "Esta visão reúne todas as anomalias cadastradas na ponte, "
        "independentemente do componente ativo."
    )

    anomalias = buscar_anomalias_oae(
        oae_ativa.id
    )

    if len(anomalias) == 0:

        st.info(
            "Nenhuma anomalia foi cadastrada para esta OAE."
        )

        return

    registros = []

    componentes_encontrados = set()
    tipos_encontrados = set()
    situacoes_encontradas = set()

    for anomalia in anomalias:

        componente = buscar_componente_por_id(
            anomalia.componente_id
        )

        inspecao_origem = buscar_inspecao_por_id(
            anomalia.inspecao_origem_id
        )

        componente_nome = (
            componente.nome
            if componente is not None
            else "Componente não localizado"
        )

        numero_componente = numero_visual_componente(
            oae_ativa.id,
            anomalia.componente_id,
        )

        componente_visual = (
            f"{numero_componente} - {componente_nome}"
        )

        codigo = codigo_visual_anomalia(
            oae_ativa.id,
            anomalia.id,
        )

        if inspecao_origem is not None:

            numero_inspecao = numero_visual_inspecao(
                oae_ativa.id,
                inspecao_origem.id,
            )

            origem_visual = (
                f"{numero_inspecao} - "
                f"{inspecao_origem.tipo_inspecao} - "
                f"{inspecao_origem.data_inspecao.strftime('%d/%m/%Y')}"
            )

        else:

            origem_visual = "Não localizada"

        situacao = (
            "Ativa"
            if getattr(
                anomalia,
                "ativa",
                1
            )
            else "Inativa"
        )

        registros.append(
            {
                "_componente_id": anomalia.componente_id,
                "Código": codigo,
                "Componente": componente_visual,
                "Tipo": anomalia.tipo_anomalia or "Não informado",
                "Localização": (
                    anomalia.localizacao_referencia
                    or "Não informada"
                ),
                "Inspeção de origem": origem_visual,
                "Situação": situacao,
            }
        )

        componentes_encontrados.add(
            componente_visual
        )

        tipos_encontrados.add(
            anomalia.tipo_anomalia
            or "Não informado"
        )

        situacoes_encontradas.add(
            situacao
        )

    total = len(
        registros
    )

    total_ativas = sum(
        1
        for item in registros
        if item["Situação"] == "Ativa"
    )

    total_inativas = total - total_ativas

    componentes_afetados = len(
        {
            item["_componente_id"]
            for item in registros
        }
    )

    c1, c2, c3, c4 = st.columns(
        4
    )

    with c1:
        st.metric(
            "Total de anomalias",
            total
        )

    with c2:
        st.metric(
            "Ativas",
            total_ativas
        )

    with c3:
        st.metric(
            "Inativas",
            total_inativas
        )

    with c4:
        st.metric(
            "Componentes afetados",
            componentes_afetados
        )

    st.markdown(
        "#### 🔎 Filtros"
    )

    c1, c2, c3 = st.columns(
        3
    )

    with c1:

        filtro_componente = st.selectbox(
            "Componente",
            [
                "Todos"
            ]
            + sorted(
                componentes_encontrados,
                key=_chave_natural
            ),
            key=(
                f"filtro_anomalias_oae_componente_"
                f"{oae_ativa.id}"
            )
        )

    with c2:

        filtro_tipo = st.selectbox(
            "Tipo de anomalia",
            [
                "Todos"
            ]
            + sorted(
                tipos_encontrados,
                key=_chave_natural
            ),
            key=(
                f"filtro_anomalias_oae_tipo_"
                f"{oae_ativa.id}"
            )
        )

    with c3:

        filtro_situacao = st.selectbox(
            "Situação",
            [
                "Todas"
            ]
            + sorted(
                situacoes_encontradas
            ),
            key=(
                f"filtro_anomalias_oae_situacao_"
                f"{oae_ativa.id}"
            )
        )

    filtrados = []

    for item in registros:

        if (
            filtro_componente != "Todos"
            and
            item["Componente"]
            != filtro_componente
        ):
            continue

        if (
            filtro_tipo != "Todos"
            and
            item["Tipo"]
            != filtro_tipo
        ):
            continue

        if (
            filtro_situacao != "Todas"
            and
            item["Situação"]
            != filtro_situacao
        ):
            continue

        filtrados.append(
            item
        )

    if componente_ativo is not None:

        st.caption(
            "O componente ativo continua sendo usado no cadastro "
            "e na listagem específica acima. Esta tabela mostra a OAE inteira."
        )

    tabela = [
        {
            "Código": item["Código"],
            "Componente": item["Componente"],
            "Tipo": item["Tipo"],
            "Localização": item["Localização"],
            "Inspeção de origem": item["Inspeção de origem"],
            "Situação": item["Situação"],
        }
        for item in filtrados
    ]

    st.dataframe(
        tabela,
        width="stretch",
        hide_index=True
    )

    st.caption(
        f"Exibindo {len(tabela)} de {total} anomalia(s) cadastrada(s) na OAE."
    )



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

        st.caption(
            "Selecione uma categoria padronizada. "
            "Os campos de medição exibidos abaixo mudam "
            "conforme o tipo escolhido."
        )

        tipo_anomalia_selecionado = st.selectbox(
            "Tipo de anomalia",
            TIPOS_ANOMALIA,
            key="nova_anomalia_tipo"
        )

        outro_tipo_anomalia = ""

        if (
            tipo_anomalia_selecionado
            == "Outra anomalia"
        ):

            outro_tipo_anomalia = st.text_input(
                "Especifique o tipo de anomalia",
                placeholder=(
                    "Ex.: falha localizada de revestimento"
                ),
                key="nova_anomalia_outro_tipo"
            )

        localizacao_referencia = st.text_input(
            "Localização de referência",
            placeholder=(
                "Ex.: face inferior da Longarina L2, "
                "região central do vão"
            ),
            key="nova_anomalia_localizacao"
        )

        descricao_inicial = st.text_area(
            "Descrição inicial da anomalia",
            placeholder=(
                "Descreva a manifestação observada, "
                "aspecto, posição e características relevantes."
            ),
            key="nova_anomalia_descricao"
        )

        abertura_fissura_mm = 0.0

        if tipo_exige_abertura_fissura(
            tipo_anomalia_selecionado
        ):

            abertura_fissura_mm = st.number_input(
                "Abertura da fissura (mm)",
                min_value=0.0,
                step=0.01,
                format="%.2f",
                key="nova_anomalia_abertura"
            )

        extensao_anomalia_cm = 0.0

        if tipo_exige_extensao(
            tipo_anomalia_selecionado
        ):

            extensao_anomalia_cm = st.number_input(
                rotulo_extensao_anomalia(
                    tipo_anomalia_selecionado
                ),
                min_value=0.0,
                step=0.1,
                format="%.1f",
                key="nova_anomalia_extensao"
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
            ],
            key="nova_anomalia_situacao"
        )

        observacoes = st.text_area(
            "Observações",
            placeholder=(
                "Registre informações complementares "
                "relevantes para o acompanhamento."
            ),
            key="nova_anomalia_observacoes"
        )

        salvar_nova_anomalia = st.button(
            "💾 Salvar nova anomalia",
            type="primary",
            key="salvar_nova_anomalia"
        )

        if salvar_nova_anomalia:

            tipo_anomalia = normalizar_tipo_anomalia(
                tipo_anomalia_selecionado,
                outro_tipo_anomalia,
            )

            if (
                tipo_anomalia_selecionado
                == "Outra anomalia"
                and
                outro_tipo_anomalia.strip()
                == ""
            ):

                st.error(
                    "Informe qual é a outra anomalia."
                )

            elif localizacao_referencia.strip() == "":

                st.error(
                    "Informe a localização de referência."
                )

            elif descricao_inicial.strip() == "":

                st.error(
                    "Informe a descrição inicial da anomalia."
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
                                if (
                                    tipo_exige_abertura_fissura(
                                        tipo_anomalia_selecionado
                                    )
                                    and
                                    abertura_fissura_mm > 0
                                )
                                else None
                            ),
                        extensao_anomalia_cm=
                            (
                                extensao_anomalia_cm
                                if (
                                    tipo_exige_extensao(
                                        tipo_anomalia_selecionado
                                    )
                                    and
                                    extensao_anomalia_cm > 0
                                )
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

                st.rerun()


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

                tipo_existente = (
                    anomalia_escolhida.tipo_anomalia
                    or ""
                )

                descricao = st.text_area(
                    "Descrição nesta inspeção",
                    placeholder=(
                        "Descreva o estado atual da anomalia "
                        "e eventuais alterações observadas."
                    ),
                    key=f"obs_existente_descricao_{anomalia_escolhida.id}"
                )

                localizacao_detalhada = st.text_input(
                    "Localização detalhada nesta inspeção",
                    value=(
                        anomalia_escolhida
                        .localizacao_referencia
                    ),
                    key=f"obs_existente_localizacao_{anomalia_escolhida.id}"
                )

                abertura_fissura_mm = 0.0

                if (
                    "fissura" in tipo_existente.lower()
                    or
                    "trinca" in tipo_existente.lower()
                ):

                    abertura_fissura_mm = (
                        st.number_input(
                            "Abertura da fissura (mm)",
                            min_value=0.0,
                            step=0.01,
                            format="%.2f",
                            key=f"obs_existente_abertura_{anomalia_escolhida.id}"
                        )
                    )

                extensao_anomalia_cm = st.number_input(
                    "Extensão / dimensão principal da anomalia (cm)",
                    min_value=0.0,
                    step=0.1,
                    format="%.1f",
                    key=f"obs_existente_extensao_{anomalia_escolhida.id}"
                )

                situacao_observada = st.selectbox(
                    "Situação observada",
                    [
                        "Estável",
                        "Evolução observada",
                        "Redução aparente",
                        "Reparada",
                        "Não determinada"
                    ],
                    key=f"obs_existente_situacao_{anomalia_escolhida.id}"
                )

                observacoes = st.text_area(
                    "Observações",
                    key=f"obs_existente_observacoes_{anomalia_escolhida.id}"
                )

                salvar_observacao = st.button(
                    "💾 Salvar observação",
                    type="primary",
                    key=f"salvar_observacao_existente_{anomalia_escolhida.id}"
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

                    st.rerun()


    # ========================================================
    # ANOMALIAS PERMANENTES DO COMPONENTE
    # ========================================================

    st.divider()

    st.subheader(
        "🧩 Anomalias acompanhadas neste componente"
    )

    st.caption(
        "Esta seção mostra somente as anomalias vinculadas "
        "ao componente atualmente selecionado."
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

                st.divider()

                st.markdown(
                    "#### 🗑️ Excluir anomalia"
                )

                st.caption(
                    "Use esta opção somente quando a anomalia foi "
                    "cadastrada por engano. A exclusão remove o registro "
                    "permanente, suas observações de inspeção e os vínculos "
                    "com fotografias. As fotografias permanecem cadastradas."
                )

                confirmar_exclusao = st.checkbox(
                    "Confirmo que esta anomalia foi cadastrada por engano",
                    key=f"confirmar_exclusao_anomalia_{anomalia.id}"
                )

                if st.button(
                    "🗑️ Excluir definitivamente esta anomalia",
                    key=f"excluir_anomalia_{anomalia.id}",
                    disabled=not confirmar_exclusao,
                ):

                    db_exclusao = SessionLocal()

                    try:

                        # Buscar observações vinculadas antes da exclusão.
                        observacoes_para_excluir = (
                            db_exclusao.query(
                                models.ObservacaoAnomalia
                            )
                            .filter(
                                models.ObservacaoAnomalia.anomalia_id
                                == anomalia.id
                            )
                            .all()
                        )

                        ids_observacoes = [
                            item.id
                            for item in observacoes_para_excluir
                        ]

                        # Remover vínculos de fotografias com a anomalia.
                        db_exclusao.query(
                            models.VinculoFotografiaAnomalia
                        ).filter(
                            models.VinculoFotografiaAnomalia
                            .anomalia_permanente_id
                            == anomalia.id
                        ).delete(
                            synchronize_session=False
                        )

                        # Segurança adicional para vínculos por observação.
                        if len(ids_observacoes) > 0:

                            db_exclusao.query(
                                models.VinculoFotografiaAnomalia
                            ).filter(
                                models.VinculoFotografiaAnomalia
                                .observacao_anomalia_id
                                .in_(ids_observacoes)
                            ).delete(
                                synchronize_session=False
                            )

                        # Remover as observações temporais.
                        db_exclusao.query(
                            models.ObservacaoAnomalia
                        ).filter(
                            models.ObservacaoAnomalia.anomalia_id
                            == anomalia.id
                        ).delete(
                            synchronize_session=False
                        )

                        # Remover a anomalia permanente.
                        db_exclusao.query(
                            models.AnomaliaPermanente
                        ).filter(
                            models.AnomaliaPermanente.id
                            == anomalia.id
                        ).delete(
                            synchronize_session=False
                        )

                        db_exclusao.commit()

                    except Exception as erro:

                        db_exclusao.rollback()
                        db_exclusao.close()

                        st.error(
                            "Não foi possível excluir a anomalia. "
                            f"Detalhe: {erro}"
                        )

                        st.stop()

                    db_exclusao.close()

                    st.success(
                        "Anomalia excluída com sucesso."
                    )

                    st.rerun()

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

    mostrar_visao_geral_anomalias_oae(
        oae_ativa=oae_ativa,
        componente_ativo=componente_ativo,
    )

