import streamlit as st

from database import engine, Base, SessionLocal
import models

from anomalias import mostrar_modulo_anomalias
from fotos import mostrar_modulo_fotografias
from historico import mostrar_historico_oae
from evolucao import mostrar_evolucao_oae


# ============================================================
# BANCO DE DADOS
# ============================================================

Base.metadata.create_all(bind=engine)


# ============================================================
# CONFIGURAÇÃO DA PÁGINA
# ============================================================

st.set_page_config(
    page_title="Gêmeo Digital - Pontes",
    page_icon="🌉",
    layout="wide"
)


# ============================================================
# CABEÇALHO
# ============================================================

st.title(
    "🌉 Gêmeo Digital para Inspeção de Pontes"
)

st.subheader(
    "Sistema de apoio à inspeção e ao acompanhamento "
    "da integridade estrutural"
)

st.write(
    """
    Este protótipo está sendo desenvolvido em Python
    como parte do Trabalho de Conclusão de Curso 2.
    """
)

st.divider()


# ============================================================
# FUNCIONALIDADES
# ============================================================

st.header(
    "Funcionalidades previstas"
)

st.write(
    "✅ Cadastro da OAE"
)

st.write(
    "✅ Cadastro dos componentes estruturais"
)

st.write(
    "✅ Registro de inspeções"
)

st.write(
    "✅ Registro de anomalias"
)

st.write(
    "✅ Acompanhamento temporal de anomalias"
)

st.write(
    "✅ Classificação estrutural, funcional e de durabilidade"
)

st.write(
    "✅ Armazenamento de fotografias"
)

st.write(
    "✅ Histórico das inspeções"
)

st.write(
    "✅ Evolução temporal das classificações"
)

st.write(
    "⬜ Emissão de relatórios"
)

st.divider()


# ============================================================
# CADASTRO DA OAE
# ============================================================

st.header(
    "Cadastro da OAE"
)

with st.form(
    "form_cadastro_oae"
):

    col1, col2 = st.columns(
        2
    )

    with col1:

        nome_oae = st.text_input(
            "Nome da OAE"
        )

        codigo_oae = st.text_input(
            "Código ou identificação da OAE"
        )

        rodovia = st.text_input(
            "Rodovia"
        )

        municipio = st.text_input(
            "Município"
        )

        uf = st.selectbox(
            "UF",
            [
                "AC",
                "AL",
                "AP",
                "AM",
                "BA",
                "CE",
                "DF",
                "ES",
                "GO",
                "MA",
                "MT",
                "MS",
                "MG",
                "PA",
                "PB",
                "PR",
                "PE",
                "PI",
                "RJ",
                "RN",
                "RS",
                "RO",
                "RR",
                "SC",
                "SP",
                "SE",
                "TO"
            ]
        )

        ano_construcao = st.number_input(
            "Ano de construção",
            min_value=1900,
            max_value=2100,
            step=1
        )

    with col2:

        tipo_estrutura = st.selectbox(
            "Tipo estrutural",
            [
                "Concreto protendido",
                "Concreto armado",
                "Estrutura mista",
                "Outro"
            ]
        )

        numero_vaos = st.number_input(
            "Número de vãos",
            min_value=1,
            step=1
        )

        comprimento_total = st.number_input(
            "Comprimento total da OAE (m)",
            min_value=0.0,
            step=0.1
        )

        largura = st.number_input(
            "Largura da OAE (m)",
            min_value=0.0,
            step=0.1
        )

        tipo_protensao = st.selectbox(
            "Tipo de protensão",
            [
                "Pré-tração",
                "Pós-tração",
                "Não informado",
                "Não se aplica"
            ]
        )

    observacoes = st.text_area(
        "Observações"
    )

    enviar = st.form_submit_button(
        "Salvar cadastro"
    )


# ============================================================
# SALVAR OAE
# ============================================================

if enviar:

    if nome_oae == "":

        st.error(
            "O nome da OAE é obrigatório."
        )

    else:

        db = SessionLocal()

        nova_oae = models.OAE(
            nome=nome_oae,
            codigo=codigo_oae,
            rodovia=rodovia,
            municipio=municipio,
            uf=uf,
            ano_construcao=ano_construcao,
            tipo_estrutura=tipo_estrutura,
            numero_vaos=numero_vaos,
            comprimento_total=comprimento_total,
            largura=largura,
            tipo_protensao=tipo_protensao,
            observacoes=observacoes
        )

        db.add(
            nova_oae
        )

        db.commit()

        db.refresh(
            nova_oae
        )

        id_gerado = (
            nova_oae.id
        )

        db.close()

        st.success(
            f"OAE cadastrada com sucesso. "
            f"ID gerado: {id_gerado}"
        )


st.divider()


# ============================================================
# OAEs CADASTRADAS
# ============================================================

st.header(
    "OAEs cadastradas"
)

db = SessionLocal()

oaes = (
    db.query(
        models.OAE
    )
    .order_by(
        models.OAE.id
    )
    .all()
)

db.close()


if len(oaes) == 0:

    st.info(
        "Nenhuma OAE cadastrada."
    )

else:

    dados_oaes = []

    for oae in oaes:

        dados_oaes.append(
            {
                "ID":
                    oae.id,
                "Nome":
                    oae.nome,
                "Código":
                    oae.codigo,
                "Rodovia":
                    oae.rodovia,
                "Município":
                    oae.municipio,
                "UF":
                    oae.uf,
                "Tipo estrutural":
                    oae.tipo_estrutura
            }
        )

    st.dataframe(
        dados_oaes,
        width="stretch"
    )


    # ========================================================
    # OAE ATIVA
    # ========================================================

    st.subheader(
        "Selecionar OAE ativa"
    )

    opcoes_oae = {
        (
            f"{oae.id} - "
            f"{oae.nome}"
        ): oae
        for oae in oaes
    }

    oae_escolhida = st.selectbox(
        "Escolha uma OAE",
        options=list(
            opcoes_oae.keys()
        )
    )

    oae_ativa = (
        opcoes_oae[
            oae_escolhida
        ]
    )

    st.success(
        f"OAE ativa: "
        f"{oae_ativa.nome}"
    )

    st.write(
        "### Dados da OAE selecionada"
    )

    st.write(
        "ID:",
        oae_ativa.id
    )

    st.write(
        "Nome:",
        oae_ativa.nome
    )

    st.write(
        "Código:",
        oae_ativa.codigo
    )

    st.write(
        "Rodovia:",
        oae_ativa.rodovia
    )

    st.write(
        "Município:",
        oae_ativa.municipio
    )

    st.write(
        "UF:",
        oae_ativa.uf
    )

    st.write(
        "Tipo estrutural:",
        oae_ativa.tipo_estrutura
    )

    st.divider()


    # ========================================================
    # CADASTRO DE COMPONENTE
    # ========================================================

    st.header(
        "Cadastro de componente"
    )

    st.write(
        f"Componente vinculado à OAE: "
        f"{oae_ativa.id} - "
        f"{oae_ativa.nome}"
    )

    with st.form(
        "form_cadastro_componente"
    ):

        categoria_componente = st.selectbox(
            "Categoria do componente",
            [
                "Superestrutura",
                "Mesoestrutura",
                "Infraestrutura",
                "Elementos de encontro"
            ]
        )

        nome_componente = st.text_input(
            "Nome ou identificação do elemento"
        )

        classificacao_elemento = st.selectbox(
            "Classificação do elemento",
            [
                "Principal",
                "Secundário",
                "Complementar",
                "Não informado"
            ]
        )

        observacoes_componente = st.text_area(
            "Observações do componente"
        )

        salvar_componente = (
            st.form_submit_button(
                "Salvar componente"
            )
        )


    if salvar_componente:

        if nome_componente == "":

            st.error(
                "O nome ou identificação "
                "do componente é obrigatório."
            )

        else:

            db = SessionLocal()

            novo_componente = models.Componente(
                oae_id=oae_ativa.id,
                categoria=categoria_componente,
                nome=nome_componente,
                classificacao_elemento=
                    classificacao_elemento,
                observacoes=
                    observacoes_componente
            )

            db.add(
                novo_componente
            )

            db.commit()

            db.refresh(
                novo_componente
            )

            componente_id = (
                novo_componente.id
            )

            db.close()

            st.success(
                f"Componente cadastrado com sucesso. "
                f"ID gerado: {componente_id}"
            )


    st.divider()


    # ========================================================
    # COMPONENTES CADASTRADOS
    # ========================================================

    st.header(
        "Componentes cadastrados da OAE ativa"
    )

    db = SessionLocal()

    componentes = (
        db.query(
            models.Componente
        )
        .filter(
            models.Componente.oae_id
            == oae_ativa.id
        )
        .order_by(
            models.Componente.id
        )
        .all()
    )

    db.close()

    componente_ativo = None


    if len(componentes) == 0:

        st.info(
            "Nenhum componente cadastrado "
            "para esta OAE."
        )

    else:

        dados_componentes = []

        for componente in componentes:

            dados_componentes.append(
                {
                    "ID":
                        componente.id,
                    "Categoria":
                        componente.categoria,
                    "Elemento":
                        componente.nome,
                    "Classificação":
                        componente.classificacao_elemento,
                    "Observações":
                        componente.observacoes
                }
            )

        st.dataframe(
            dados_componentes,
            width="stretch"
        )


        # ====================================================
        # COMPONENTE ATIVO
        # ====================================================

        st.subheader(
            "Selecionar componente ativo"
        )

        opcoes_componentes = {
            (
                f"{componente.id} - "
                f"{componente.nome}"
            ): componente
            for componente in componentes
        }

        componente_escolhido = st.selectbox(
            "Escolha um componente",
            options=list(
                opcoes_componentes.keys()
            )
        )

        componente_ativo = (
            opcoes_componentes[
                componente_escolhido
            ]
        )

        st.success(
            f"Componente ativo: "
            f"{componente_ativo.nome}"
        )

        st.write(
            "### Dados do componente selecionado"
        )

        st.write(
            "ID:",
            componente_ativo.id
        )

        st.write(
            "Categoria:",
            componente_ativo.categoria
        )

        st.write(
            "Elemento:",
            componente_ativo.nome
        )

        st.write(
            "Classificação:",
            componente_ativo.classificacao_elemento
        )

        st.write(
            "Observações:",
            componente_ativo.observacoes
        )


    st.divider()


    # ========================================================
    # CADASTRO DE INSPEÇÃO
    # ========================================================

    st.header(
        "Cadastro de inspeção"
    )

    st.write(
        f"Inspeção vinculada à OAE: "
        f"{oae_ativa.id} - "
        f"{oae_ativa.nome}"
    )

    with st.form(
        "form_cadastro_inspecao"
    ):

        tipo_inspecao = st.selectbox(
            "Tipo de inspeção",
            [
                "Cadastral",
                "Rotineira",
                "Especial",
                "Extraordinária"
            ]
        )

        data_inspecao = st.date_input(
            "Data da inspeção",
            format="DD/MM/YYYY"
        )

        responsavel_inspecao = st.text_input(
            "Responsável pela inspeção"
        )

        registro_profissional = st.text_input(
            "Registro profissional"
        )

        observacoes_inspecao = st.text_area(
            "Observações da inspeção"
        )

        salvar_inspecao = (
            st.form_submit_button(
                "Salvar inspeção"
            )
        )


    if salvar_inspecao:

        db = SessionLocal()

        nova_inspecao = models.Inspecao(
            oae_id=oae_ativa.id,
            tipo_inspecao=
                tipo_inspecao,
            data_inspecao=
                data_inspecao,
            responsavel=
                responsavel_inspecao,
            registro_profissional=
                registro_profissional,
            observacoes=
                observacoes_inspecao
        )

        db.add(
            nova_inspecao
        )

        db.commit()

        db.refresh(
            nova_inspecao
        )

        inspecao_id = (
            nova_inspecao.id
        )

        db.close()

        st.success(
            f"Inspeção cadastrada com sucesso. "
            f"ID gerado: {inspecao_id}"
        )


    st.divider()


    # ========================================================
    # INSPEÇÕES CADASTRADAS
    # ========================================================

    st.header(
        "Inspeções cadastradas da OAE ativa"
    )

    db = SessionLocal()

    inspecoes = (
        db.query(
            models.Inspecao
        )
        .filter(
            models.Inspecao.oae_id
            == oae_ativa.id
        )
        .order_by(
            models.Inspecao.id
        )
        .all()
    )

    db.close()

    inspecao_ativa = None


    if len(inspecoes) == 0:

        st.info(
            "Nenhuma inspeção cadastrada "
            "para esta OAE."
        )

    else:

        dados_inspecoes = []

        for inspecao in inspecoes:

            dados_inspecoes.append(
                {
                    "ID":
                        inspecao.id,
                    "Tipo":
                        inspecao.tipo_inspecao,
                    "Data":
                        inspecao.data_inspecao.strftime(
                            "%d/%m/%Y"
                        ),
                    "Responsável":
                        inspecao.responsavel,
                    "Registro profissional":
                        inspecao.registro_profissional,
                    "Observações":
                        inspecao.observacoes
                }
            )

        st.dataframe(
            dados_inspecoes,
            width="stretch"
        )


        # ====================================================
        # INSPEÇÃO ATIVA
        # ====================================================

        st.subheader(
            "Selecionar inspeção ativa"
        )

        opcoes_inspecoes = {
            (
                f"{inspecao.id} - "
                f"{inspecao.tipo_inspecao} - "
                f"{inspecao.data_inspecao.strftime('%d/%m/%Y')}"
            ): inspecao
            for inspecao in inspecoes
        }

        inspecao_escolhida = st.selectbox(
            "Escolha uma inspeção",
            options=list(
                opcoes_inspecoes.keys()
            )
        )

        inspecao_ativa = (
            opcoes_inspecoes[
                inspecao_escolhida
            ]
        )

        st.success(
            f"Inspeção ativa: "
            f"{inspecao_ativa.tipo_inspecao} - "
            f"{inspecao_ativa.data_inspecao.strftime('%d/%m/%Y')}"
        )

        st.write(
            "### Dados da inspeção selecionada"
        )

        st.write(
            "ID:",
            inspecao_ativa.id
        )

        st.write(
            "Tipo:",
            inspecao_ativa.tipo_inspecao
        )

        st.write(
            "Data:",
            inspecao_ativa.data_inspecao.strftime(
                "%d/%m/%Y"
            )
        )

        st.write(
            "Responsável:",
            inspecao_ativa.responsavel
        )

        st.write(
            "Registro profissional:",
            inspecao_ativa.registro_profissional
        )

        st.write(
            "Observações:",
            inspecao_ativa.observacoes
        )


    st.divider()


    # ========================================================
    # CADASTRO ANTIGO DE ANOMALIA
    #
    # TEMPORÁRIO:
    # manteremos este módulo por enquanto para preservar
    # e visualizar os registros antigos já existentes.
    # ========================================================

    st.header(
        "Cadastro de anomalia - modelo anterior"
    )

    st.caption(
        "Este cadastro será substituído pelo novo módulo "
        "de acompanhamento de anomalias após a validação."
    )

    if componente_ativo is None:

        st.warning(
            "Cadastre e selecione um componente "
            "antes de registrar uma anomalia."
        )

    elif inspecao_ativa is None:

        st.warning(
            "Cadastre e selecione uma inspeção "
            "antes de registrar uma anomalia."
        )

    else:

        st.write(
            f"**OAE:** "
            f"{oae_ativa.id} - "
            f"{oae_ativa.nome}"
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

        with st.form(
            "form_cadastro_anomalia_antigo"
        ):

            tipo_anomalia = st.text_input(
                "Tipo de anomalia"
            )

            localizacao_anomalia = st.text_input(
                "Localização da anomalia no elemento"
            )

            descricao_anomalia = st.text_area(
                "Descrição da anomalia"
            )

            observacoes_anomalia = st.text_area(
                "Observações da anomalia"
            )

            salvar_anomalia = (
                st.form_submit_button(
                    "Salvar anomalia"
                )
            )


        if salvar_anomalia:

            if tipo_anomalia == "":

                st.error(
                    "O tipo de anomalia é obrigatório."
                )

            else:

                db = SessionLocal()

                nova_anomalia = models.Anomalia(
                    oae_id=
                        oae_ativa.id,
                    inspecao_id=
                        inspecao_ativa.id,
                    componente_id=
                        componente_ativo.id,
                    tipo_anomalia=
                        tipo_anomalia,
                    descricao=
                        descricao_anomalia,
                    localizacao=
                        localizacao_anomalia,
                    observacoes=
                        observacoes_anomalia
                )

                db.add(
                    nova_anomalia
                )

                db.commit()

                db.refresh(
                    nova_anomalia
                )

                anomalia_id = (
                    nova_anomalia.id
                )

                db.close()

                st.success(
                    f"Anomalia cadastrada com sucesso. "
                    f"ID gerado: {anomalia_id}"
                )


        # ====================================================
        # ANOMALIAS ANTIGAS
        # ====================================================

        st.subheader(
            "Anomalias do modelo anterior"
        )

        db = SessionLocal()

        anomalias = (
            db.query(
                models.Anomalia
            )
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


        if len(anomalias) == 0:

            st.info(
                "Nenhuma anomalia do modelo anterior "
                "cadastrada para esta inspeção e componente."
            )

        else:

            dados_anomalias = []

            for anomalia in anomalias:

                dados_anomalias.append(
                    {
                        "ID":
                            anomalia.id,
                        "Tipo":
                            anomalia.tipo_anomalia,
                        "Localização":
                            anomalia.localizacao,
                        "Descrição":
                            anomalia.descricao,
                        "Observações":
                            anomalia.observacoes
                    }
                )

            st.dataframe(
                dados_anomalias,
                width="stretch"
            )


    st.divider()


    # ========================================================
    # CLASSIFICAÇÃO NBR 9452
    # ========================================================

    st.header(
        "Classificação da condição"
    )

    if componente_ativo is None:

        st.warning(
            "Selecione um componente para "
            "realizar a classificação."
        )

    elif inspecao_ativa is None:

        st.warning(
            "Selecione uma inspeção para "
            "realizar a classificação."
        )

    else:

        st.info(
            "As notas devem ser atribuídas pelo inspetor "
            "responsável, com base nos critérios da "
            "ABNT NBR 9452:2023."
        )

        st.write(
            f"**OAE avaliada:** "
            f"{oae_ativa.id} - "
            f"{oae_ativa.nome}"
        )

        st.write(
            f"**Componente avaliado:** "
            f"{componente_ativo.id} - "
            f"{componente_ativo.nome}"
        )

        st.write(
            f"**Inspeção:** "
            f"{inspecao_ativa.id} - "
            f"{inspecao_ativa.tipo_inspecao} - "
            f"{inspecao_ativa.data_inspecao.strftime('%d/%m/%Y')}"
        )


        # ====================================================
        # VERIFICAR CLASSIFICAÇÃO EXISTENTE
        # ====================================================

        db = SessionLocal()

        classificacao_existente = (
            db.query(
                models.Classificacao
            )
            .filter(
                models.Classificacao.oae_id
                == oae_ativa.id
            )
            .filter(
                models.Classificacao.inspecao_id
                == inspecao_ativa.id
            )
            .filter(
                models.Classificacao.componente_id
                == componente_ativo.id
            )
            .order_by(
                models.Classificacao.id.desc()
            )
            .first()
        )

        db.close()


        # ====================================================
        # VALORES INICIAIS
        # ====================================================

        if classificacao_existente is None:

            st.warning(
                "Este componente ainda não possui "
                "classificação nesta inspeção."
            )

            valor_estrutural = 5
            valor_funcional = 5
            valor_durabilidade = 5

            justificativa_estrutural_atual = ""
            justificativa_funcional_atual = ""
            justificativa_durabilidade_atual = ""

        else:

            st.success(
                "Este componente já possui uma classificação "
                "nesta inspeção. Ao salvar novamente, os dados "
                "existentes serão atualizados."
            )

            st.write(
                "### Classificação atualmente registrada"
            )

            col1, col2, col3 = st.columns(
                3
            )

            with col1:

                st.metric(
                    "Estrutural",
                    classificacao_existente.nota_estrutural
                )

            with col2:

                st.metric(
                    "Funcional",
                    classificacao_existente.nota_funcional
                )

            with col3:

                st.metric(
                    "Durabilidade",
                    classificacao_existente.nota_durabilidade
                )


            valor_estrutural = (
                classificacao_existente.nota_estrutural
            )

            valor_funcional = (
                classificacao_existente.nota_funcional
            )

            valor_durabilidade = (
                classificacao_existente.nota_durabilidade
            )

            justificativa_estrutural_atual = (
                classificacao_existente.justificativa_estrutural
                or ""
            )

            justificativa_funcional_atual = (
                classificacao_existente.justificativa_funcional
                or ""
            )

            justificativa_durabilidade_atual = (
                classificacao_existente.justificativa_durabilidade
                or ""
            )


        # ====================================================
        # OPÇÕES DE NOTA
        # ====================================================

        opcoes_notas = [
            "5 - Excelente",
            "4 - Boa",
            "3 - Regular",
            "2 - Ruim",
            "1 - Crítica",
            "0 - Emergencial"
        ]

        indice_estrutural = (
            5 - valor_estrutural
        )

        indice_funcional = (
            5 - valor_funcional
        )

        indice_durabilidade = (
            5 - valor_durabilidade
        )


        # ====================================================
        # FORMULÁRIO DE CLASSIFICAÇÃO
        # ====================================================

        with st.form(
            "form_classificacao"
        ):

            nota_estrutural_texto = st.selectbox(
                "Nota estrutural",
                opcoes_notas,
                index=indice_estrutural
            )

            justificativa_estrutural = st.text_area(
                "Justificativa da nota estrutural",
                value=
                    justificativa_estrutural_atual
            )

            nota_funcional_texto = st.selectbox(
                "Nota funcional",
                opcoes_notas,
                index=indice_funcional
            )

            justificativa_funcional = st.text_area(
                "Justificativa da nota funcional",
                value=
                    justificativa_funcional_atual
            )

            nota_durabilidade_texto = st.selectbox(
                "Nota de durabilidade",
                opcoes_notas,
                index=indice_durabilidade
            )

            justificativa_durabilidade = st.text_area(
                "Justificativa da nota de durabilidade",
                value=
                    justificativa_durabilidade_atual
            )


            if classificacao_existente is None:

                texto_botao = (
                    "Salvar classificação"
                )

            else:

                texto_botao = (
                    "Atualizar classificação"
                )


            salvar_classificacao = (
                st.form_submit_button(
                    texto_botao
                )
            )


        # ====================================================
        # SALVAR OU ATUALIZAR CLASSIFICAÇÃO
        # ====================================================

        if salvar_classificacao:

            nota_estrutural = int(
                nota_estrutural_texto[0]
            )

            nota_funcional = int(
                nota_funcional_texto[0]
            )

            nota_durabilidade = int(
                nota_durabilidade_texto[0]
            )


            db = SessionLocal()

            classificacao_banco = (
                db.query(
                    models.Classificacao
                )
                .filter(
                    models.Classificacao.oae_id
                    == oae_ativa.id
                )
                .filter(
                    models.Classificacao.inspecao_id
                    == inspecao_ativa.id
                )
                .filter(
                    models.Classificacao.componente_id
                    == componente_ativo.id
                )
                .order_by(
                    models.Classificacao.id.desc()
                )
                .first()
            )


            if classificacao_banco is None:

                nova_classificacao = (
                    models.Classificacao(
                        oae_id=
                            oae_ativa.id,
                        inspecao_id=
                            inspecao_ativa.id,
                        componente_id=
                            componente_ativo.id,
                        nota_estrutural=
                            nota_estrutural,
                        justificativa_estrutural=
                            justificativa_estrutural,
                        nota_funcional=
                            nota_funcional,
                        justificativa_funcional=
                            justificativa_funcional,
                        nota_durabilidade=
                            nota_durabilidade,
                        justificativa_durabilidade=
                            justificativa_durabilidade
                    )
                )

                db.add(
                    nova_classificacao
                )

                db.commit()

                db.refresh(
                    nova_classificacao
                )

                classificacao_id = (
                    nova_classificacao.id
                )

                db.close()

                st.success(
                    f"Classificação cadastrada com sucesso. "
                    f"ID gerado: {classificacao_id}"
                )

            else:

                classificacao_banco.nota_estrutural = (
                    nota_estrutural
                )

                classificacao_banco.justificativa_estrutural = (
                    justificativa_estrutural
                )

                classificacao_banco.nota_funcional = (
                    nota_funcional
                )

                classificacao_banco.justificativa_funcional = (
                    justificativa_funcional
                )

                classificacao_banco.nota_durabilidade = (
                    nota_durabilidade
                )

                classificacao_banco.justificativa_durabilidade = (
                    justificativa_durabilidade
                )

                classificacao_id = (
                    classificacao_banco.id
                )

                db.commit()

                db.close()

                st.success(
                    f"Classificação ID "
                    f"{classificacao_id} "
                    f"atualizada com sucesso."
                )


        # ====================================================
        # CLASSIFICAÇÃO ATUAL
        # ====================================================

        st.subheader(
            "Classificação registrada para este componente"
        )

        db = SessionLocal()

        classificacao_atual = (
            db.query(
                models.Classificacao
            )
            .filter(
                models.Classificacao.oae_id
                == oae_ativa.id
            )
            .filter(
                models.Classificacao.inspecao_id
                == inspecao_ativa.id
            )
            .filter(
                models.Classificacao.componente_id
                == componente_ativo.id
            )
            .order_by(
                models.Classificacao.id.desc()
            )
            .first()
        )

        db.close()


        if classificacao_atual is None:

            st.info(
                "Nenhuma classificação registrada "
                "para este componente nesta inspeção."
            )

        else:

            dados_classificacao = [
                {
                    "ID":
                        classificacao_atual.id,
                    "OAE":
                        oae_ativa.id,
                    "Inspeção":
                        inspecao_ativa.id,
                    "Componente":
                        componente_ativo.id,
                    "Estrutural":
                        classificacao_atual.nota_estrutural,
                    "Funcional":
                        classificacao_atual.nota_funcional,
                    "Durabilidade":
                        classificacao_atual.nota_durabilidade,
                    "Justificativa estrutural":
                        classificacao_atual.justificativa_estrutural,
                    "Justificativa funcional":
                        classificacao_atual.justificativa_funcional,
                    "Justificativa de durabilidade":
                        classificacao_atual.justificativa_durabilidade
                }
            ]

            st.dataframe(
                dados_classificacao,
                width="stretch"
            )


    # ========================================================
    # NOVO MÓDULO DE ACOMPANHAMENTO DAS ANOMALIAS
    # ========================================================

    mostrar_modulo_anomalias(
        oae_ativa=oae_ativa,
        inspecao_ativa=inspecao_ativa,
        componente_ativo=componente_ativo
    )


    # ========================================================
    # REGISTRO FOTOGRÁFICO
    # ========================================================

    mostrar_modulo_fotografias(
        oae_ativa=oae_ativa,
        inspecao_ativa=inspecao_ativa,
        componente_ativo=componente_ativo
    )


    # ========================================================
    # HISTÓRICO
    # ========================================================

    mostrar_historico_oae(
        oae_ativa=oae_ativa
    )


    # ========================================================
    # EVOLUÇÃO TEMPORAL
    # ========================================================

    mostrar_evolucao_oae(
        oae_ativa=oae_ativa
    )