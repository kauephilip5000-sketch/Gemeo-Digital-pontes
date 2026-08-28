import unicodedata

import streamlit as st
from sqlalchemy import text

from database import SessionLocal, engine
import models
from feedback import definir_feedback_salvamento


ESCALA_CLASSIFICACAO = {
    5: "Excelente",
    4: "Boa",
    3: "Regular",
    2: "Ruim",
    1: "Crítica",
    0: "Emergencial",
}

OPCOES_NOTAS = [
    "5 - Excelente",
    "4 - Boa",
    "3 - Regular",
    "2 - Ruim",
    "1 - Crítica",
    "0 - Emergencial",
]


def nota_texto(nota):
    if nota is None:
        return "Não classificada"
    return ESCALA_CLASSIFICACAO.get(int(nota), "Não classificada")


def converter_opcao_nota(opcao):
    if opcao is None:
        return None
    return int(opcao.split(" - ")[0])


def indice_nota(nota):
    if nota is None:
        return 0
    nota = max(0, min(5, int(nota)))
    return 5 - nota


def normalizar_texto(valor):
    if valor is None:
        return ""

    valor = str(valor).strip().lower()

    valor = unicodedata.normalize(
        "NFKD",
        valor,
    )

    return "".join(
        caractere
        for caractere in valor
        if not unicodedata.combining(caractere)
    )


def eh_inspecao_especial(inspecao):
    if inspecao is None:
        return False

    return (
        "especial"
        in normalizar_texto(
            inspecao.tipo_inspecao
        )
    )


# ============================================================
# TABELA DE CLASSIFICAÇÃO GERAL DA OAE
# ============================================================


def garantir_tabela_classificacao_oae():

    comando = """
    CREATE TABLE IF NOT EXISTS classificacoes_oae (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        oae_id INTEGER NOT NULL,
        inspecao_id INTEGER NOT NULL UNIQUE,
        nota_estrutural INTEGER NOT NULL,
        justificativa_estrutural TEXT,
        nota_funcional INTEGER NOT NULL,
        justificativa_funcional TEXT,
        nota_durabilidade INTEGER NOT NULL,
        justificativa_durabilidade TEXT,
        observacoes TEXT,
        FOREIGN KEY(oae_id) REFERENCES oae(id),
        FOREIGN KEY(inspecao_id) REFERENCES inspecoes(id)
    )
    """

    with engine.begin() as conexao:
        conexao.execute(
            text(comando)
        )


garantir_tabela_classificacao_oae()


# ============================================================
# CONSULTAS
# ============================================================


def buscar_inspecao(
    inspecao_id
):

    db = SessionLocal()

    inspecao = (
        db.query(
            models.Inspecao
        )
        .filter(
            models.Inspecao.id
            == inspecao_id
        )
        .first()
    )

    db.close()

    return inspecao


def buscar_componentes(
    oae_id
):

    db = SessionLocal()

    dados = (
        db.query(
            models.Componente
        )
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

    return dados


def buscar_componente(
    componente_id
):

    db = SessionLocal()

    dado = (
        db.query(
            models.Componente
        )
        .filter(
            models.Componente.id
            == componente_id
        )
        .first()
    )

    db.close()

    return dado


# ============================================================
# CLASSIFICAÇÃO GERAL DA OAE
# ============================================================


def buscar_classificacao_oae(
    oae_id,
    inspecao_id
):

    garantir_tabela_classificacao_oae()

    comando = text(
        """
        SELECT *
        FROM classificacoes_oae
        WHERE
            oae_id = :oae_id
            AND inspecao_id = :inspecao_id
        LIMIT 1
        """
    )

    with engine.begin() as conexao:

        registro = (
            conexao.execute(
                comando,
                {
                    "oae_id":
                        oae_id,

                    "inspecao_id":
                        inspecao_id,
                },
            )
            .mappings()
            .first()
        )

    if registro is None:
        return None

    return dict(
        registro
    )


def salvar_classificacao_oae(
    oae_id,
    inspecao_id,
    nota_estrutural,
    justificativa_estrutural,
    nota_funcional,
    justificativa_funcional,
    nota_durabilidade,
    justificativa_durabilidade,
    observacoes,
):

    existente = buscar_classificacao_oae(
        oae_id,
        inspecao_id,
    )

    parametros = {
        "oae_id":
            oae_id,

        "inspecao_id":
            inspecao_id,

        "nota_estrutural":
            nota_estrutural,

        "justificativa_estrutural":
            justificativa_estrutural,

        "nota_funcional":
            nota_funcional,

        "justificativa_funcional":
            justificativa_funcional,

        "nota_durabilidade":
            nota_durabilidade,

        "justificativa_durabilidade":
            justificativa_durabilidade,

        "observacoes":
            observacoes,
    }

    if existente is None:

        comando = text(
            """
            INSERT INTO classificacoes_oae (
                oae_id,
                inspecao_id,
                nota_estrutural,
                justificativa_estrutural,
                nota_funcional,
                justificativa_funcional,
                nota_durabilidade,
                justificativa_durabilidade,
                observacoes
            )
            VALUES (
                :oae_id,
                :inspecao_id,
                :nota_estrutural,
                :justificativa_estrutural,
                :nota_funcional,
                :justificativa_funcional,
                :nota_durabilidade,
                :justificativa_durabilidade,
                :observacoes
            )
            """
        )

    else:

        comando = text(
            """
            UPDATE classificacoes_oae
            SET
                nota_estrutural =
                    :nota_estrutural,

                justificativa_estrutural =
                    :justificativa_estrutural,

                nota_funcional =
                    :nota_funcional,

                justificativa_funcional =
                    :justificativa_funcional,

                nota_durabilidade =
                    :nota_durabilidade,

                justificativa_durabilidade =
                    :justificativa_durabilidade,

                observacoes =
                    :observacoes
            WHERE
                oae_id = :oae_id
                AND inspecao_id = :inspecao_id
            """
        )

    with engine.begin() as conexao:

        conexao.execute(
            comando,
            parametros,
        )


# ============================================================
# CLASSIFICAÇÕES POR COMPONENTE
# USADAS NA INSPEÇÃO ESPECIAL
# ============================================================


def buscar_classificacoes_componentes(
    oae_id,
    inspecao_id
):

    db = SessionLocal()

    dados = (
        db.query(
            models.Classificacao
        )
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

    return dados


# ============================================================
# FUNÇÃO USADA PELO APP.PY
# ============================================================


def componentes_classificados(
    oae_id,
    inspecao_id
):

    inspecao = buscar_inspecao(
        inspecao_id
    )

    if inspecao is None:
        return 0

    # --------------------------------------------------------
    # CADASTRAL / ROTINEIRA / EXTRAORDINÁRIA
    # --------------------------------------------------------

    if not eh_inspecao_especial(
        inspecao
    ):

        registro = buscar_classificacao_oae(
            oae_id,
            inspecao_id,
        )

        if registro is None:
            return 0

        # Compatibilidade com o painel antigo do app.py.
        # Se a OAE possui classificação geral, o conjunto
        # da inspeção é considerado classificado.
        return len(
            buscar_componentes(
                oae_id
            )
        )

    # --------------------------------------------------------
    # ESPECIAL
    # --------------------------------------------------------

    classificacoes = (
        buscar_classificacoes_componentes(
            oae_id,
            inspecao_id,
        )
    )

    ids = {
        item.componente_id
        for item in classificacoes
    }

    return len(
        ids
    )


# ============================================================
# ANDAMENTO DA CLASSIFICAÇÃO
# ============================================================


def verificar_andamento_classificacao(
    oae_id,
    inspecao_id
):

    inspecao = buscar_inspecao(
        inspecao_id
    )

    if inspecao is None:

        return {
            "total":
                0,

            "avaliados":
                0,

            "pendentes":
                0,

            "concluida":
                False,
        }

    # --------------------------------------------------------
    # CADASTRAL / ROTINEIRA / EXTRAORDINÁRIA
    #
    # Aqui a unidade classificada é a OAE inteira.
    # Portanto o andamento é 0/1 ou 1/1.
    # --------------------------------------------------------

    if not eh_inspecao_especial(
        inspecao
    ):

        registro = buscar_classificacao_oae(
            oae_id,
            inspecao_id,
        )

        avaliado = (
            1
            if registro is not None
            else 0
        )

        return {
            "total":
                1,

            "avaliados":
                avaliado,

            "pendentes":
                1 - avaliado,

            "concluida":
                (
                    avaliado
                    == 1
                ),
        }

    # --------------------------------------------------------
    # ESPECIAL
    # --------------------------------------------------------

    componentes = buscar_componentes(
        oae_id
    )

    classificacoes = (
        buscar_classificacoes_componentes(
            oae_id,
            inspecao_id,
        )
    )

    ids_avaliados = {
        item.componente_id
        for item in classificacoes
    }

    total = len(
        componentes
    )

    avaliados = len(
        ids_avaliados
    )

    pendentes = max(
        total - avaliados,
        0,
    )

    return {
        "total":
            total,

        "avaliados":
            avaliados,

        "pendentes":
            pendentes,

        "concluida":
            (
                total > 0
                and
                avaliados == total
            ),
    }


# ============================================================
# CLASSIFICAÇÃO CONSOLIDADA
# ============================================================


def calcular_classificacao_consolidada(
    oae_id,
    inspecao_id
):

    vazio = {
        "estrutural":
            None,

        "funcional":
            None,

        "durabilidade":
            None,

        "criticos_estrutural":
            [],

        "criticos_funcional":
            [],

        "criticos_durabilidade":
            [],

        "valores_estrutural":
            [],

        "valores_funcional":
            [],

        "valores_durabilidade":
            [],

        "na_funcional":
            [],
    }

    inspecao = buscar_inspecao(
        inspecao_id
    )

    if inspecao is None:
        return vazio

    # --------------------------------------------------------
    # CADASTRAL / ROTINEIRA / EXTRAORDINÁRIA
    # --------------------------------------------------------

    if not eh_inspecao_especial(
        inspecao
    ):

        registro = buscar_classificacao_oae(
            oae_id,
            inspecao_id,
        )

        if registro is None:
            return vazio

        return {
            **vazio,

            "estrutural":
                registro[
                    "nota_estrutural"
                ],

            "funcional":
                registro[
                    "nota_funcional"
                ],

            "durabilidade":
                registro[
                    "nota_durabilidade"
                ],
        }

    # --------------------------------------------------------
    # ESPECIAL
    # --------------------------------------------------------

    classificacoes = (
        buscar_classificacoes_componentes(
            oae_id,
            inspecao_id,
        )
    )

    if len(classificacoes) == 0:
        return vazio

    valores_estrutural = []
    valores_funcional = []
    valores_durabilidade = []

    for classificacao in classificacoes:

        componente = buscar_componente(
            classificacao.componente_id
        )

        if componente is None:
            continue

        if (
            classificacao.nota_estrutural
            is not None
        ):

            valores_estrutural.append(
                {
                    "nota":
                        classificacao.nota_estrutural,

                    "componente":
                        componente,
                }
            )

        if (
            classificacao.nota_funcional
            is not None
        ):

            valores_funcional.append(
                {
                    "nota":
                        classificacao.nota_funcional,

                    "componente":
                        componente,
                }
            )

        if (
            classificacao.nota_durabilidade
            is not None
        ):

            valores_durabilidade.append(
                {
                    "nota":
                        classificacao.nota_durabilidade,

                    "componente":
                        componente,
                }
            )

    def consolidar(
        valores
    ):

        if len(valores) == 0:
            return None, []

        menor = min(
            item["nota"]
            for item in valores
        )

        criticos = [
            item["componente"]
            for item in valores
            if (
                item["nota"]
                == menor
            )
        ]

        return (
            menor,
            criticos,
        )

    (
        nota_estrutural,
        criticos_estrutural,
    ) = consolidar(
        valores_estrutural
    )

    (
        nota_funcional,
        criticos_funcional,
    ) = consolidar(
        valores_funcional
    )

    (
        nota_durabilidade,
        criticos_durabilidade,
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
            [],
    }


# ============================================================
# TELA DE CLASSIFICAÇÃO GERAL
# CADASTRAL / ROTINEIRA / EXTRAORDINÁRIA
# ============================================================


def mostrar_classificacao_geral(
    oae_ativa,
    inspecao_ativa
):

    registro = buscar_classificacao_oae(
        oae_ativa.id,
        inspecao_ativa.id,
    )

    if registro is None:

        nota_estrutural_atual = 5
        nota_funcional_atual = 5
        nota_durabilidade_atual = 5

        justificativa_estrutural = ""
        justificativa_funcional = ""
        justificativa_durabilidade = ""

        observacoes = ""

    else:

        nota_estrutural_atual = (
            registro[
                "nota_estrutural"
            ]
        )

        nota_funcional_atual = (
            registro[
                "nota_funcional"
            ]
        )

        nota_durabilidade_atual = (
            registro[
                "nota_durabilidade"
            ]
        )

        justificativa_estrutural = (
            registro[
                "justificativa_estrutural"
            ]
            or ""
        )

        justificativa_funcional = (
            registro[
                "justificativa_funcional"
            ]
            or ""
        )

        justificativa_durabilidade = (
            registro[
                "justificativa_durabilidade"
            ]
            or ""
        )

        observacoes = (
            registro[
                "observacoes"
            ]
            or ""
        )

    st.subheader(
        "⭐ Classificação geral da OAE"
    )

    st.caption(
        "As notas abaixo representam a condição da OAE "
        "na inspeção selecionada. Não é necessário classificar "
        "cada componente individualmente nesta etapa."
    )

    st.info(
        "O sistema registra a classificação informada pelo "
        "profissional responsável. A atribuição, confirmação "
        "e validação das notas não são realizadas automaticamente."
    )

    with st.form(
        f"form_classificacao_oae_"
        f"{inspecao_ativa.id}"
    ):

        c1, c2, c3 = (
            st.columns(3)
        )

        with c1:

            opcao_estrutural = (
                st.selectbox(
                    "Nota estrutural",
                    OPCOES_NOTAS,
                    index=indice_nota(
                        nota_estrutural_atual
                    ),
                )
            )

        with c2:

            opcao_funcional = (
                st.selectbox(
                    "Nota funcional",
                    OPCOES_NOTAS,
                    index=indice_nota(
                        nota_funcional_atual
                    ),
                )
            )

        with c3:

            opcao_durabilidade = (
                st.selectbox(
                    "Nota de durabilidade",
                    OPCOES_NOTAS,
                    index=indice_nota(
                        nota_durabilidade_atual
                    ),
                )
            )

        nova_justificativa_estrutural = (
            st.text_area(
                "Justificativa estrutural",
                value=
                    justificativa_estrutural,
                placeholder=(
                    "Resuma a condição estrutural "
                    "que fundamenta a nota."
                ),
            )
        )

        nova_justificativa_funcional = (
            st.text_area(
                "Justificativa funcional",
                value=
                    justificativa_funcional,
                placeholder=(
                    "Resuma os aspectos funcionais "
                    "que fundamentam a nota."
                ),
            )
        )

        nova_justificativa_durabilidade = (
            st.text_area(
                "Justificativa de durabilidade",
                value=
                    justificativa_durabilidade,
                placeholder=(
                    "Resuma as condições relacionadas "
                    "à durabilidade que fundamentam a nota."
                ),
            )
        )

        novas_observacoes = (
            st.text_area(
                "Observações complementares",
                value=observacoes,
            )
        )

        salvar = (
            st.form_submit_button(
                (
                    "Salvar classificação da OAE"
                    if registro is None
                    else
                    "Atualizar classificação da OAE"
                )
            )
        )

    if salvar:

        nota_estrutural = (
            converter_opcao_nota(
                opcao_estrutural
            )
        )

        nota_funcional = (
            converter_opcao_nota(
                opcao_funcional
            )
        )

        nota_durabilidade = (
            converter_opcao_nota(
                opcao_durabilidade
            )
        )

        try:

            salvar_classificacao_oae(
                oae_id=
                    oae_ativa.id,

                inspecao_id=
                    inspecao_ativa.id,

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
                    nova_justificativa_durabilidade,

                observacoes=
                    novas_observacoes,
            )

        except Exception as erro:

            st.error(
                "Não foi possível salvar a classificação."
            )

            st.code(
                str(erro)
            )

            return

        definir_feedback_salvamento(
            "Classificação da OAE salva com sucesso."
        )

        st.rerun()

    registro = buscar_classificacao_oae(
        oae_ativa.id,
        inspecao_ativa.id,
    )

    if registro is None:

        st.info(
            "Esta inspeção ainda não possui "
            "classificação geral registrada."
        )

        return

    st.divider()

    st.subheader(
        "📌 Classificação registrada"
    )

    c1, c2, c3 = (
        st.columns(3)
    )

    with c1:

        st.metric(
            "Estrutural",
            registro[
                "nota_estrutural"
            ],
        )

        st.caption(
            nota_texto(
                registro[
                    "nota_estrutural"
                ]
            )
        )

    with c2:

        st.metric(
            "Funcional",
            registro[
                "nota_funcional"
            ],
        )

        st.caption(
            nota_texto(
                registro[
                    "nota_funcional"
                ]
            )
        )

    with c3:

        st.metric(
            "Durabilidade",
            registro[
                "nota_durabilidade"
            ],
        )

        st.caption(
            nota_texto(
                registro[
                    "nota_durabilidade"
                ]
            )
        )


# ============================================================
# TELA DA INSPEÇÃO ESPECIAL
# ============================================================


def mostrar_classificacao_especial(
    oae_ativa,
    inspecao_ativa,
    componente_ativo
):

    st.subheader(
        "🧱 Avaliação detalhada por componente"
    )

    st.caption(
        "Na inspeção especial, o módulo permite "
        "avaliação individual dos componentes."
    )

    if componente_ativo is None:

        st.warning(
            "Selecione um componente."
        )

        return

    db = SessionLocal()

    existente = (
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
        .first()
    )

    db.close()

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

    st.write(
        f"**Componente:** "
        f"{componente_ativo.nome}"
    )

    with st.form(
        f"form_classificacao_especial_"
        f"{inspecao_ativa.id}_"
        f"{componente_ativo.id}"
    ):

        opcao_estrutural = (
            st.selectbox(
                "Nota estrutural",
                OPCOES_NOTAS,
                index=indice_nota(
                    nota_estrutural_atual
                ),
            )
        )

        nova_justificativa_estrutural = (
            st.text_area(
                "Justificativa estrutural",
                value=
                    justificativa_estrutural,
            )
        )

        opcao_funcional = (
            st.selectbox(
                "Nota funcional",
                OPCOES_NOTAS,
                index=indice_nota(
                    nota_funcional_atual
                ),
            )
        )

        nova_justificativa_funcional = (
            st.text_area(
                "Justificativa funcional",
                value=
                    justificativa_funcional,
            )
        )

        opcao_durabilidade = (
            st.selectbox(
                "Nota de durabilidade",
                OPCOES_NOTAS,
                index=indice_nota(
                    nota_durabilidade_atual
                ),
            )
        )

        nova_justificativa_durabilidade = (
            st.text_area(
                "Justificativa de durabilidade",
                value=
                    justificativa_durabilidade,
            )
        )

        salvar = (
            st.form_submit_button(
                (
                    "Salvar avaliação do componente"
                    if existente is None
                    else
                    "Atualizar avaliação do componente"
                )
            )
        )

    if salvar:

        db = SessionLocal()

        classificacao = (
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
            .first()
        )

        if classificacao is None:

            classificacao = (
                models.Classificacao(
                    oae_id=
                        oae_ativa.id,

                    inspecao_id=
                        inspecao_ativa.id,

                    componente_id=
                        componente_ativo.id,

                    nota_estrutural=
                        converter_opcao_nota(
                            opcao_estrutural
                        ),

                    justificativa_estrutural=
                        nova_justificativa_estrutural,

                    nota_funcional=
                        converter_opcao_nota(
                            opcao_funcional
                        ),

                    justificativa_funcional=
                        nova_justificativa_funcional,

                    nota_durabilidade=
                        converter_opcao_nota(
                            opcao_durabilidade
                        ),

                    justificativa_durabilidade=
                        nova_justificativa_durabilidade,
                )
            )

            db.add(
                classificacao
            )

        else:

            classificacao.nota_estrutural = (
                converter_opcao_nota(
                    opcao_estrutural
                )
            )

            classificacao.justificativa_estrutural = (
                nova_justificativa_estrutural
            )

            classificacao.nota_funcional = (
                converter_opcao_nota(
                    opcao_funcional
                )
            )

            classificacao.justificativa_funcional = (
                nova_justificativa_funcional
            )

            classificacao.nota_durabilidade = (
                converter_opcao_nota(
                    opcao_durabilidade
                )
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
                "Não foi possível salvar a avaliação."
            )

            st.code(
                str(erro)
            )

            return

        db.close()

        st.success(
            "Avaliação do componente salva com sucesso."
        )

        st.rerun()

    resultado = (
        calcular_classificacao_consolidada(
            oae_ativa.id,
            inspecao_ativa.id,
        )
    )

    andamento = (
        verificar_andamento_classificacao(
            oae_ativa.id,
            inspecao_ativa.id,
        )
    )

    st.divider()

    st.subheader(
        "⭐ Consolidação da inspeção especial"
    )

    c1, c2, c3 = (
        st.columns(3)
    )

    with c1:

        st.metric(
            "Estrutural",
            (
                resultado[
                    "estrutural"
                ]
                if resultado[
                    "estrutural"
                ] is not None
                else "—"
            ),
        )

    with c2:

        st.metric(
            "Funcional",
            (
                resultado[
                    "funcional"
                ]
                if resultado[
                    "funcional"
                ] is not None
                else "—"
            ),
        )

    with c3:

        st.metric(
            "Durabilidade",
            (
                resultado[
                    "durabilidade"
                ]
                if resultado[
                    "durabilidade"
                ] is not None
                else "—"
            ),
        )

    st.caption(
        f"Componentes avaliados: "
        f"{andamento['avaliados']}/"
        f"{andamento['total']}. "
        f"A confirmação técnica das notas cabe "
        f"ao profissional responsável."
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

    st.write(
        f"**OAE:** "
        f"{oae_ativa.nome}"
    )

    st.write(
        f"**Inspeção:** "
        f"{inspecao_ativa.tipo_inspecao} - "
        f"{inspecao_ativa.data_inspecao.strftime('%d/%m/%Y')}"
    )

    st.divider()

    if eh_inspecao_especial(
        inspecao_ativa
    ):

        mostrar_classificacao_especial(
            oae_ativa,
            inspecao_ativa,
            componente_ativo,
        )

    else:

        mostrar_classificacao_geral(
            oae_ativa,
            inspecao_ativa,
        )