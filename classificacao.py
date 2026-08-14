import streamlit as st

from database import SessionLocal
import models


# ============================================================
# NBR 9452:2023
# CLASSIFICAÇÃO DA CONDIÇÃO DA OAE
# ============================================================


ESCALA_CLASSIFICACAO = {
    5: "Excelente",
    4: "Boa",
    3: "Regular",
    2: "Ruim",
    1: "Crítica",
    0: "Emergencial"
}


OPCOES_NOTAS = [
    "5 - Excelente",
    "4 - Boa",
    "3 - Regular",
    "2 - Ruim",
    "1 - Crítica",
    "0 - Emergencial"
]


# ============================================================
# FUNÇÕES DE TEXTO
# ============================================================

def nota_texto(nota):

    if nota is None:
        return "NA"

    return ESCALA_CLASSIFICACAO.get(
        nota,
        "Não classificada"
    )


def converter_opcao_nota(opcao):

    if opcao is None:
        return None

    return int(
        opcao.split(" - ")[0]
    )


# ============================================================
# NORMALIZAÇÃO DA CATEGORIA
# ============================================================

def normalizar_categoria(categoria):

    if categoria is None:
        return ""

    texto = (
        categoria
        .strip()
        .lower()
    )

    mapa = {
        "superestrutura":
            "Superestrutura",

        "mesoestrutura":
            "Mesoestrutura",

        "infraestrutura":
            "Infraestrutura",

        "elementos de encontro":
            "Encontros",

        "encontros":
            "Encontros",

        "elementos complementares":
            "Elementos complementares",

        "complementares":
            "Elementos complementares",

        "pista / via permanente":
            "Pista / via permanente",

        "pista/via permanente":
            "Pista / via permanente",

        "pista":
            "Pista / via permanente",

        "via permanente":
            "Pista / via permanente"
    }

    return mapa.get(
        texto,
        categoria
    )


# ============================================================
# APLICABILIDADE DO PARÂMETRO FUNCIONAL
#
# Conforme o modelo da Tabela 2 da NBR 9452:2023:
#
# Mesoestrutura  -> NA
# Infraestrutura -> NA
# ============================================================

def parametro_funcional_aplicavel(
    componente
):

    if componente is None:
        return False

    categoria = normalizar_categoria(
        componente.categoria
    )

    if categoria in [
        "Mesoestrutura",
        "Infraestrutura"
    ]:

        return False

    return True


# ============================================================
# CONSULTAS AO BANCO
# ============================================================

def buscar_componentes(oae_id):

    db = SessionLocal()

    componentes = (
        db.query(models.Componente)
        .filter(
            models.Componente.oae_id
            == oae_id
        )
        .order_by(
            models.Componente.id
        )
        .all()
    )

    db.close()

    return componentes


def buscar_componente_por_id(
    componente_id
):

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


def buscar_classificacao(
    oae_id,
    inspecao_id,
    componente_id
):

    db = SessionLocal()

    classificacao = (
        db.query(models.Classificacao)
        .filter(
            models.Classificacao.oae_id
            == oae_id
        )
        .filter(
            models.Classificacao.inspecao_id
            == inspecao_id
        )
        .filter(
            models.Classificacao.componente_id
            == componente_id
        )
        .order_by(
            models.Classificacao.id.desc()
        )
        .first()
    )

    db.close()

    return classificacao


def buscar_classificacoes_inspecao(
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
        .order_by(
            models.Classificacao.id
        )
        .all()
    )

    db.close()

    return classificacoes


# ============================================================
# COMPONENTES CLASSIFICADOS
# ============================================================

def componentes_classificados(
    oae_id,
    inspecao_id
):

    classificacoes = (
        buscar_classificacoes_inspecao(
            oae_id,
            inspecao_id
        )
    )

    ids = {
        item.componente_id
        for item in classificacoes
    }

    return len(ids)


# ============================================================
# CONSOLIDAÇÃO
#
# Nota final de cada parâmetro =
# menor nota aplicável entre os componentes classificados.
# ============================================================

def calcular_classificacao_consolidada(
    oae_id,
    inspecao_id
):

    classificacoes = (
        buscar_classificacoes_inspecao(
            oae_id,
            inspecao_id
        )
    )

    if len(classificacoes) == 0:

        return {
            "estrutural": None,
            "funcional": None,
            "durabilidade": None,

            "criticos_estrutural": [],
            "criticos_funcional": [],
            "criticos_durabilidade": [],

            "valores_estrutural": [],
            "valores_funcional": [],
            "valores_durabilidade": [],

            "na_funcional": []
        }


    valores_estrutural = []
    valores_funcional = []
    valores_durabilidade = []

    na_funcional = []


    for classificacao in classificacoes:

        componente = buscar_componente_por_id(
            classificacao.componente_id
        )


        if componente is None:
            continue


        # ====================================================
        # ESTRUTURAL
        # ====================================================

        if (
            classificacao.nota_estrutural
            is not None
        ):

            valores_estrutural.append(
                {
                    "nota":
                        classificacao.nota_estrutural,

                    "componente":
                        componente
                }
            )


        # ====================================================
        # FUNCIONAL
        # ====================================================

        if parametro_funcional_aplicavel(
            componente
        ):

            if (
                classificacao.nota_funcional
                is not None
            ):

                valores_funcional.append(
                    {
                        "nota":
                            classificacao.nota_funcional,

                        "componente":
                            componente
                    }
                )

        else:

            na_funcional.append(
                componente
            )


        # ====================================================
        # DURABILIDADE
        # ====================================================

        if (
            classificacao.nota_durabilidade
            is not None
        ):

            valores_durabilidade.append(
                {
                    "nota":
                        classificacao.nota_durabilidade,

                    "componente":
                        componente
                }
            )


    # ========================================================
    # MENOR NOTA
    # ========================================================

    def consolidar(lista):

        if len(lista) == 0:
            return None, []

        menor_nota = min(
            item["nota"]
            for item in lista
        )


        criticos = [
            item["componente"]
            for item in lista
            if item["nota"] == menor_nota
        ]


        return (
            menor_nota,
            criticos
        )


    (
        nota_estrutural,
        criticos_estrutural
    ) = consolidar(
        valores_estrutural
    )


    (
        nota_funcional,
        criticos_funcional
    ) = consolidar(
        valores_funcional
    )


    (
        nota_durabilidade,
        criticos_durabilidade
    ) = consolidar(
        valores_durabilidade
    )


    return {
        "estrutural":
            nota_estrutural,

        "funcional":
            nota_funcional,

        "durabilidade":
            nota_durabilidade,

        "criticos_estrutural":
            criticos_estrutural,

        "criticos_funcional":
            criticos_funcional,

        "criticos_durabilidade":
            criticos_durabilidade,

        "valores_estrutural":
            valores_estrutural,

        "valores_funcional":
            valores_funcional,

        "valores_durabilidade":
            valores_durabilidade,

        "na_funcional":
            na_funcional
    }


# ============================================================
# TEXTO DOS COMPONENTES
# ============================================================

def texto_componentes_criticos(
    componentes
):

    if len(componentes) == 0:

        return "Não determinado"


    nomes = []


    for componente in componentes:

        relevancia = (
            componente.classificacao_elemento
            or
            "Não informada"
        )


        nomes.append(
            f"{componente.nome} "
            f"({relevancia})"
        )


    return ", ".join(
        nomes
    )


# ============================================================
# FÓRMULA VISUAL DA CONSOLIDAÇÃO
# ============================================================

def criar_texto_calculo(
    valores
):

    if len(valores) == 0:

        return "Nenhuma nota aplicável registrada."


    partes = []


    for item in valores:

        componente = (
            item["componente"]
        )

        nota = (
            item["nota"]
        )


        partes.append(
            f"{componente.nome} = {nota}"
        )


    menor = min(
        item["nota"]
        for item in valores
    )


    texto = " | ".join(
        partes
    )


    return (
        f"{texto}  →  menor nota = {menor}"
    )


# ============================================================
# ANDAMENTO
# ============================================================

def verificar_andamento_classificacao(
    oae_id,
    inspecao_id
):

    componentes = buscar_componentes(
        oae_id
    )


    classificacoes = (
        buscar_classificacoes_inspecao(
            oae_id,
            inspecao_id
        )
    )


    componentes_avaliados = {
        item.componente_id
        for item in classificacoes
    }


    total = len(
        componentes
    )


    avaliados = len(
        componentes_avaliados
    )


    pendentes = max(
        total - avaliados,
        0
    )


    concluida = (
        total > 0
        and
        avaliados == total
    )


    return {
        "total":
            total,

        "avaliados":
            avaliados,

        "pendentes":
            pendentes,

        "concluida":
            concluida
    }


# ============================================================
# FORMULÁRIO
# ============================================================

def mostrar_formulario_classificacao(
    oae_ativa,
    inspecao_ativa,
    componente_ativo
):

    st.subheader(
        "🧱 Avaliação do componente ativo"
    )


    categoria = normalizar_categoria(
        componente_ativo.categoria
    )


    relevancia = (
        componente_ativo.classificacao_elemento
        or
        "Não informada"
    )


    c1, c2, c3 = (
        st.columns(3)
    )


    with c1:

        st.write(
            "**Componente**"
        )

        st.write(
            componente_ativo.nome
        )


    with c2:

        st.write(
            "**Categoria**"
        )

        st.write(
            categoria
        )


    with c3:

        st.write(
            "**Relevância estrutural**"
        )

        st.write(
            relevancia
        )


    if relevancia in [
        "",
        "Não informado",
        "Não informada",
        None
    ]:

        st.warning(
            "A relevância deste elemento ainda não foi "
            "definida. O inspetor deve verificar se o "
            "elemento é principal, secundário ou complementar "
            "considerando a concepção estrutural da OAE."
        )


    existente = buscar_classificacao(
        oae_ativa.id,
        inspecao_ativa.id,
        componente_ativo.id
    )


    # ========================================================
    # VALORES ATUAIS
    # ========================================================

    if existente is None:

        nota_estrutural_atual = 5
        nota_funcional_atual = 5
        nota_durabilidade_atual = 5

        justificativa_estrutural = ""
        justificativa_funcional = ""
        justificativa_durabilidade = ""

    else:

        nota_estrutural_atual = (
            existente.nota_estrutural
            if existente.nota_estrutural
            is not None
            else 5
        )


        nota_funcional_atual = (
            existente.nota_funcional
            if existente.nota_funcional
            is not None
            else 5
        )


        nota_durabilidade_atual = (
            existente.nota_durabilidade
            if existente.nota_durabilidade
            is not None
            else 5
        )


        justificativa_estrutural = (
            existente.justificativa_estrutural
            or ""
        )


        justificativa_funcional = (
            existente.justificativa_funcional
            or ""
        )


        justificativa_durabilidade = (
            existente.justificativa_durabilidade
            or ""
        )


    funcional_aplicavel = (
        parametro_funcional_aplicavel(
            componente_ativo
        )
    )


    if not funcional_aplicavel:

        st.info(
            f"O componente ativo pertence à categoria "
            f"**{categoria}**. Para esta categoria, "
            f"o parâmetro funcional é apresentado como "
            f"**NA — não aplicável**."
        )


    with st.form(
        "form_classificacao_normativa"
    ):

        # ====================================================
        # ESTRUTURAL
        # ====================================================

        st.markdown(
            "### Estrutural"
        )


        opcao_estrutural = st.selectbox(
            "Nota estrutural",
            OPCOES_NOTAS,
            index=5 - nota_estrutural_atual,
            key="classificacao_nota_estrutural"
        )


        nova_justificativa_estrutural = (
            st.text_area(
                "Justificativa estrutural",
                value=justificativa_estrutural,
                placeholder=(
                    "Descreva a condição observada e a "
                    "justificativa técnica da nota."
                )
            )
        )


        st.divider()


        # ====================================================
        # FUNCIONAL
        # ====================================================

        st.markdown(
            "### Funcional"
        )


        if funcional_aplicavel:

            opcao_funcional = st.selectbox(
                "Nota funcional",
                OPCOES_NOTAS,
                index=5 - nota_funcional_atual,
                key="classificacao_nota_funcional"
            )


            nova_justificativa_funcional = (
                st.text_area(
                    "Justificativa funcional",
                    value=justificativa_funcional,
                    placeholder=(
                        "Descreva os aspectos funcionais "
                        "considerados na atribuição da nota."
                    )
                )
            )

        else:

            st.text_input(
                "Nota funcional",
                value="NA",
                disabled=True
            )


            st.caption(
                "NA significa não aplicável. "
                "Não é nota zero e não participa "
                "do cálculo da nota funcional final."
            )


            opcao_funcional = None


            nova_justificativa_funcional = (
                "NA - parâmetro funcional não aplicável "
                "à categoria do componente."
            )


        st.divider()


        # ====================================================
        # DURABILIDADE
        # ====================================================

        st.markdown(
            "### Durabilidade"
        )


        opcao_durabilidade = st.selectbox(
            "Nota de durabilidade",
            OPCOES_NOTAS,
            index=5 - nota_durabilidade_atual,
            key="classificacao_nota_durabilidade"
        )


        nova_justificativa_durabilidade = (
            st.text_area(
                "Justificativa de durabilidade",
                value=justificativa_durabilidade,
                placeholder=(
                    "Descreva as condições relacionadas "
                    "à durabilidade e vida útil."
                )
            )
        )


        salvar = st.form_submit_button(
            (
                "Salvar classificação"
                if existente is None
                else
                "Atualizar classificação"
            )
        )


    # ========================================================
    # SALVAR
    # ========================================================

    if salvar:

        nota_estrutural = converter_opcao_nota(
            opcao_estrutural
        )


        if funcional_aplicavel:

            nota_funcional = converter_opcao_nota(
                opcao_funcional
            )

        else:

            nota_funcional = None


        nota_durabilidade = converter_opcao_nota(
            opcao_durabilidade
        )


        db = SessionLocal()


        classificacao = (
            db.query(models.Classificacao)
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


        if classificacao is None:

            classificacao = (
                models.Classificacao(
                    oae_id=oae_ativa.id,
                    inspecao_id=inspecao_ativa.id,
                    componente_id=componente_ativo.id,

                    nota_estrutural=
                        nota_estrutural,

                    justificativa_estrutural=
                        nova_justificativa_estrutural,

                    nota_funcional=
                        nota_funcional,

                    justificativa_funcional=
                        nova_justificativa_funcional,

                    nota_durabilidade=
                        nota_durabilidade,

                    justificativa_durabilidade=
                        nova_justificativa_durabilidade
                )
            )


            db.add(
                classificacao
            )

        else:

            classificacao.nota_estrutural = (
                nota_estrutural
            )

            classificacao.justificativa_estrutural = (
                nova_justificativa_estrutural
            )

            classificacao.nota_funcional = (
                nota_funcional
            )

            classificacao.justificativa_funcional = (
                nova_justificativa_funcional
            )

            classificacao.nota_durabilidade = (
                nota_durabilidade
            )

            classificacao.justificativa_durabilidade = (
                nova_justificativa_durabilidade
            )


        try:

            db.commit()

        except Exception as erro:

            db.rollback()

            db.close()

            st.error(
                "Não foi possível salvar a classificação."
            )

            st.code(
                str(erro)
            )

            return


        db.close()


        st.success(
            "Classificação salva com sucesso."
        )


        st.rerun()


# ============================================================
# NOTAS DO COMPONENTE ATIVO
# ============================================================

def mostrar_classificacao_componente(
    oae_ativa,
    inspecao_ativa,
    componente_ativo
):

    st.divider()

    st.subheader(
        "📌 Notas do componente ativo"
    )


    st.caption(
        "Os valores abaixo pertencem somente ao componente "
        "selecionado e não representam, isoladamente, "
        "as notas finais da OAE."
    )


    classificacao = buscar_classificacao(
        oae_ativa.id,
        inspecao_ativa.id,
        componente_ativo.id
    )


    if classificacao is None:

        st.info(
            "Este componente ainda não possui "
            "classificação nesta inspeção."
        )

        return


    funcional_aplicavel = (
        parametro_funcional_aplicavel(
            componente_ativo
        )
    )


    c1, c2, c3 = (
        st.columns(3)
    )


    with c1:

        st.metric(
            "Estrutural",
            classificacao.nota_estrutural
        )

        st.caption(
            nota_texto(
                classificacao.nota_estrutural
            )
        )


    with c2:

        if funcional_aplicavel:

            st.metric(
                "Funcional",
                classificacao.nota_funcional
            )

            st.caption(
                nota_texto(
                    classificacao.nota_funcional
                )
            )

        else:

            st.metric(
                "Funcional",
                "NA"
            )

            st.caption(
                "Não aplicável a este componente"
            )


    with c3:

        st.metric(
            "Durabilidade",
            classificacao.nota_durabilidade
        )

        st.caption(
            nota_texto(
                classificacao.nota_durabilidade
            )
        )


# ============================================================
# NOTAS FINAIS DA OAE
# ============================================================

def mostrar_classificacao_consolidada(
    oae_ativa,
    inspecao_ativa
):

    st.divider()

    st.subheader(
        "⭐ Notas finais da OAE"
    )


    st.info(
        "Regra de consolidação: para cada parâmetro, "
        "a nota apresentada é a menor nota aplicável "
        "entre os componentes avaliados. "
        "Valores NA não participam do cálculo."
    )


    andamento = (
        verificar_andamento_classificacao(
            oae_ativa.id,
            inspecao_ativa.id
        )
    )


    resultado = (
        calcular_classificacao_consolidada(
            oae_ativa.id,
            inspecao_ativa.id
        )
    )


    # ========================================================
    # ANDAMENTO
    # ========================================================

    c1, c2, c3 = (
        st.columns(3)
    )


    with c1:

        st.metric(
            "Componentes cadastrados",
            andamento["total"]
        )


    with c2:

        st.metric(
            "Componentes avaliados",
            andamento["avaliados"]
        )


    with c3:

        st.metric(
            "Pendentes",
            andamento["pendentes"]
        )


    if andamento["concluida"]:

        st.success(
            "Todos os componentes cadastrados possuem "
            "classificação nesta inspeção."
        )

    else:

        st.warning(
            "As notas finais apresentadas abaixo são "
            "provisórias enquanto existirem "
            "componentes pendentes."
        )


    # ========================================================
    # ESTRUTURAL
    # ========================================================

    st.markdown(
        "### Estrutural"
    )


    nota = resultado[
        "estrutural"
    ]


    c1, c2 = (
        st.columns(
            [
                1,
                2
            ]
        )
    )


    with c1:

        if nota is None:

            st.metric(
                "Nota final estrutural",
                "—"
            )

        else:

            st.metric(
                "Nota final estrutural",
                nota
            )

            st.caption(
                nota_texto(
                    nota
                )
            )


    with c2:

        if nota is not None:

            st.write(
                "**Componente(s) determinante(s):**"
            )


            st.write(
                texto_componentes_criticos(
                    resultado[
                        "criticos_estrutural"
                    ]
                )
            )


            st.caption(
                criar_texto_calculo(
                    resultado[
                        "valores_estrutural"
                    ]
                )
            )


    st.divider()


    # ========================================================
    # FUNCIONAL
    # ========================================================

    st.markdown(
        "### Funcional"
    )


    nota = resultado[
        "funcional"
    ]


    c1, c2 = (
        st.columns(
            [
                1,
                2
            ]
        )
    )


    with c1:

        if nota is None:

            st.metric(
                "Nota final funcional",
                "NA"
            )

        else:

            st.metric(
                "Nota final funcional",
                nota
            )

            st.caption(
                nota_texto(
                    nota
                )
            )


    with c2:

        if nota is not None:

            st.write(
                "**Componente(s) determinante(s):**"
            )


            st.write(
                texto_componentes_criticos(
                    resultado[
                        "criticos_funcional"
                    ]
                )
            )


            st.caption(
                criar_texto_calculo(
                    resultado[
                        "valores_funcional"
                    ]
                )
            )


        # ====================================================
        # COMPONENTES NA
        # ====================================================

        if len(
            resultado[
                "na_funcional"
            ]
        ) > 0:

            nomes_na = [
                componente.nome
                for componente in resultado[
                    "na_funcional"
                ]
            ]


            st.write(
                "**Componentes com funcional = NA:**"
            )


            st.write(
                ", ".join(
                    nomes_na
                )
            )


            st.caption(
                "Esses componentes não entram no "
                "cálculo da nota funcional final."
            )


    st.divider()


    # ========================================================
    # DURABILIDADE
    # ========================================================

    st.markdown(
        "### Durabilidade"
    )


    nota = resultado[
        "durabilidade"
    ]


    c1, c2 = (
        st.columns(
            [
                1,
                2
            ]
        )
    )


    with c1:

        if nota is None:

            st.metric(
                "Nota final de durabilidade",
                "—"
            )

        else:

            st.metric(
                "Nota final de durabilidade",
                nota
            )

            st.caption(
                nota_texto(
                    nota
                )
            )


    with c2:

        if nota is not None:

            st.write(
                "**Componente(s) determinante(s):**"
            )


            st.write(
                texto_componentes_criticos(
                    resultado[
                        "criticos_durabilidade"
                    ]
                )
            )


            st.caption(
                criar_texto_calculo(
                    resultado[
                        "valores_durabilidade"
                    ]
                )
            )


    st.caption(
        "O sistema realiza a consolidação matemática das "
        "notas registradas. A atribuição, confirmação e "
        "validação técnica das classificações permanecem "
        "sob responsabilidade do inspetor."
    )


# ============================================================
# QUADRO RESUMO
# ============================================================

def mostrar_tabela_classificacoes(
    oae_ativa,
    inspecao_ativa
):

    st.divider()

    st.subheader(
        "📋 Quadro de classificações dos componentes"
    )


    componentes = buscar_componentes(
        oae_ativa.id
    )


    if len(componentes) == 0:

        st.info(
            "Nenhum componente cadastrado."
        )

        return


    dados = []


    for componente in componentes:

        classificacao = buscar_classificacao(
            oae_ativa.id,
            inspecao_ativa.id,
            componente.id
        )


        funcional_aplicavel = (
            parametro_funcional_aplicavel(
                componente
            )
        )


        if classificacao is None:

            estrutural = (
                "Pendente"
            )


            funcional = (
                "Pendente"
                if funcional_aplicavel
                else "NA"
            )


            durabilidade = (
                "Pendente"
            )

        else:

            estrutural = (
                classificacao.nota_estrutural
                if classificacao.nota_estrutural
                is not None
                else "Pendente"
            )


            if funcional_aplicavel:

                funcional = (
                    classificacao.nota_funcional
                    if classificacao.nota_funcional
                    is not None
                    else "Pendente"
                )

            else:

                funcional = "NA"


            durabilidade = (
                classificacao.nota_durabilidade
                if classificacao.nota_durabilidade
                is not None
                else "Pendente"
            )


        dados.append(
            {
                "Componente":
                    componente.nome,

                "Categoria":
                    normalizar_categoria(
                        componente.categoria
                    ),

                "Relevância":
                    (
                        componente.classificacao_elemento
                        or
                        "Não informada"
                    ),

                "Estrutural":
                    estrutural,

                "Funcional":
                    funcional,

                "Durabilidade":
                    durabilidade
            }
        )


    st.dataframe(
        dados,
        width="stretch",
        hide_index=True
    )


    st.caption(
        "Pendente = parâmetro ainda não avaliado. "
        "NA = parâmetro não aplicável."
    )


# ============================================================
# MÓDULO PRINCIPAL
# ============================================================

def mostrar_modulo_classificacao(
    oae_ativa,
    inspecao_ativa,
    componente_ativo
):

    st.header(
        "⭐ Classificação da condição"
    )


    if oae_ativa is None:

        st.warning(
            "Selecione uma OAE."
        )

        return


    if inspecao_ativa is None:

        st.warning(
            "Selecione uma inspeção."
        )

        return


    if componente_ativo is None:

        st.warning(
            "Selecione um componente."
        )

        return


    st.caption(
        "Avaliação da condição da OAE segundo os "
        "parâmetros estrutural, funcional e de durabilidade."
    )


    st.write(
        f"**OAE:** "
        f"{oae_ativa.id} - "
        f"{oae_ativa.nome}"
    )


    st.write(
        f"**Inspeção:** "
        f"{inspecao_ativa.tipo_inspecao} - "
        f"{inspecao_ativa.data_inspecao.strftime('%d/%m/%Y')}"
    )


    mostrar_formulario_classificacao(
        oae_ativa,
        inspecao_ativa,
        componente_ativo
    )


    mostrar_classificacao_componente(
        oae_ativa,
        inspecao_ativa,
        componente_ativo
    )


    mostrar_classificacao_consolidada(
        oae_ativa,
        inspecao_ativa
    )


    mostrar_tabela_classificacoes(
        oae_ativa,
        inspecao_ativa
    )