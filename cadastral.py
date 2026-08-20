import streamlit as st

from pathlib import Path
from uuid import uuid4

from sqlalchemy import (
    Column,
    Integer,
    String,
    ForeignKey,
    UniqueConstraint
)

from database import Base, SessionLocal
import models

from classificacao import (
    calcular_classificacao_consolidada,
    verificar_andamento_classificacao
)


# ============================================================
# INSPEÇÃO CADASTRAL
# ABNT NBR 9452:2023 - ANEXO A
#
# IMPORTANTE
# ----------
# A NBR 9452:2023 determina que os dados do Anexo A sejam
# coletados quando existentes e cabíveis em cada caso.
#
# Para evitar que "0" seja confundido com "não informado",
# este módulo registra separadamente a situação de vários
# campos:
#
# - Informado
# - Não informado
# - Não se aplica
# - Não verificado
#
# Essas quatro situações são uma solução de organização do
# software. Elas NÃO constituem uma classificação normativa.
# ============================================================


# ============================================================
# TABELA AUXILIAR DE STATUS DOS CAMPOS
#
# É uma tabela nova. Como cadastral.py é importado antes do
# Base.metadata.create_all(bind=engine) no app.py, ela será
# criada automaticamente sem alterar as tabelas antigas.
# ============================================================

class CampoCadastralStatus(Base):
    __tablename__ = "campos_cadastrais_status"

    __table_args__ = (
        UniqueConstraint(
            "inspecao_cadastral_id",
            "campo",
            name="uq_status_campo_cadastral"
        ),
    )

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    inspecao_cadastral_id = Column(
        Integer,
        ForeignKey("inspecoes_cadastrais.id"),
        nullable=False
    )

    campo = Column(
        String,
        nullable=False
    )

    situacao = Column(
        String,
        nullable=False
    )


# ============================================================
# CONSTANTES
# ============================================================

PASTA_DOCUMENTOS = Path(
    "uploads/cadastral/documentos"
)

PASTA_CROQUIS = Path(
    "uploads/cadastral/croquis"
)

PASTA_DOCUMENTOS.mkdir(
    parents=True,
    exist_ok=True
)

PASTA_CROQUIS.mkdir(
    parents=True,
    exist_ok=True
)


TIPOS_DOCUMENTOS = [
    "Dados de projeto, desenhos, memoriais e especificações",
    "Registros de execução da OAE",
    "Termo de recebimento da OAE",
    "Registros de inspeções anteriores",
    "Registros de monitoramento da estrutura",
    (
        "Registros de alargamentos, reforços, reparos, "
        "recuperações ou modificações"
    )
]


SITUACOES_DOCUMENTO = [
    "Disponível",
    "Não localizado",
    "Não se aplica",
    "Não verificado"
]


TIPOS_CROQUIS = [
    "Planta do tabuleiro",
    "Corte longitudinal",
    "Corte transversal",
    "Detalhes adicionais"
]


SITUACOES_CROQUI = [
    "Anexado",
    "Pendente",
    "Não se aplica"
]


SITUACOES_CAMPO = [
    "Informado",
    "Não informado",
    "Não se aplica",
    "Não verificado"
]


# ============================================================
# CONSULTAS BÁSICAS
# ============================================================

def buscar_inspecoes_cadastrais(oae_id):

    db = SessionLocal()

    dados = (
        db.query(models.Inspecao)
        .filter(
            models.Inspecao.oae_id == oae_id
        )
        .filter(
            models.Inspecao.tipo_inspecao == "Cadastral"
        )
        .order_by(
            models.Inspecao.data_inspecao.desc(),
            models.Inspecao.id.desc()
        )
        .all()
    )

    db.close()

    return dados


def buscar_inspecao_cadastral(inspecao_id):

    if inspecao_id is None:
        return None

    db = SessionLocal()

    dado = (
        db.query(models.InspecaoCadastral)
        .filter(
            models.InspecaoCadastral.inspecao_id
            == inspecao_id
        )
        .first()
    )

    db.close()

    return dado


def buscar_detalhe_inspecao(inspecao_id):

    db = SessionLocal()

    dado = (
        db.query(models.DetalheInspecao)
        .filter(
            models.DetalheInspecao.inspecao_id
            == inspecao_id
        )
        .first()
    )

    db.close()

    return dado


def buscar_documentos_cadastrais(cadastro_id):

    db = SessionLocal()

    dados = (
        db.query(models.DocumentoCadastral)
        .filter(
            models.DocumentoCadastral.inspecao_cadastral_id
            == cadastro_id
        )
        .order_by(models.DocumentoCadastral.id)
        .all()
    )

    db.close()

    return dados


def buscar_croquis_cadastrais(cadastro_id):

    db = SessionLocal()

    dados = (
        db.query(models.CroquiCadastral)
        .filter(
            models.CroquiCadastral.inspecao_cadastral_id
            == cadastro_id
        )
        .order_by(models.CroquiCadastral.id)
        .all()
    )

    db.close()

    return dados


def buscar_mapa_status(cadastro_id):

    db = SessionLocal()

    dados = (
        db.query(CampoCadastralStatus)
        .filter(
            CampoCadastralStatus.inspecao_cadastral_id
            == cadastro_id
        )
        .all()
    )

    db.close()

    return {
        item.campo: item.situacao
        for item in dados
    }


def contar_fotos_inspecao(oae_id, inspecao_id):

    db = SessionLocal()

    quantidade = (
        db.query(models.Fotografia)
        .filter(
            models.Fotografia.oae_id == oae_id
        )
        .filter(
            models.Fotografia.inspecao_id == inspecao_id
        )
        .count()
    )

    db.close()

    return quantidade


def contar_observacoes_anomalias(inspecao_id):

    db = SessionLocal()

    quantidade = (
        db.query(models.ObservacaoAnomalia)
        .filter(
            models.ObservacaoAnomalia.inspecao_id
            == inspecao_id
        )
        .count()
    )

    db.close()

    return quantidade


# ============================================================
# STATUS DOS CAMPOS
# ============================================================

def inferir_situacao(
    mapa_status,
    campo,
    valor_atual
):

    if campo in mapa_status:

        valor = mapa_status[campo]

        if valor in SITUACOES_CAMPO:
            return valor

    if valor_atual not in [
        None,
        ""
    ]:
        return "Informado"

    return "Não informado"


def salvar_status(
    db,
    cadastro_id,
    campo,
    situacao
):

    registro = (
        db.query(CampoCadastralStatus)
        .filter(
            CampoCadastralStatus.inspecao_cadastral_id
            == cadastro_id
        )
        .filter(
            CampoCadastralStatus.campo
            == campo
        )
        .first()
    )

    if registro is None:

        registro = CampoCadastralStatus(
            inspecao_cadastral_id=
                cadastro_id,
            campo=campo,
            situacao=situacao
        )

        db.add(registro)

    else:

        registro.situacao = situacao


def seletor_situacao(
    label,
    campo,
    mapa_status,
    valor_atual,
    key_prefix,
    help_text=None
):

    situacao_atual = inferir_situacao(
        mapa_status,
        campo,
        valor_atual
    )

    return st.selectbox(
        f"{label} — situação do dado",
        SITUACOES_CAMPO,
        index=SITUACOES_CAMPO.index(
            situacao_atual
        ),
        key=f"{key_prefix}_{campo}_status",
        help=help_text
    )


def campo_numerico_condicional(
    label,
    campo,
    mapa_status,
    valor_atual,
    key_prefix,
    step=0.1,
    inteiro=False,
    help_text=None
):

    situacao = seletor_situacao(
        label=label,
        campo=campo,
        mapa_status=mapa_status,
        valor_atual=valor_atual,
        key_prefix=key_prefix,
        help_text=help_text
    )

    valor = None

    if situacao == "Informado":

        if inteiro:

            valor = st.number_input(
                label,
                min_value=0,
                value=int(
                    valor_atual
                    if valor_atual is not None
                    else 0
                ),
                step=1,
                key=f"{key_prefix}_{campo}_valor"
            )

        else:

            valor = st.number_input(
                label,
                min_value=0.0,
                value=float(
                    valor_atual
                    if valor_atual is not None
                    else 0.0
                ),
                step=step,
                key=f"{key_prefix}_{campo}_valor"
            )

    else:

        st.caption(
            f"{label}: {situacao}."
        )

    return situacao, valor


def campo_texto_condicional(
    label,
    campo,
    mapa_status,
    valor_atual,
    key_prefix,
    placeholder="",
    textarea=False,
    help_text=None
):

    situacao = seletor_situacao(
        label=label,
        campo=campo,
        mapa_status=mapa_status,
        valor_atual=valor_atual,
        key_prefix=key_prefix,
        help_text=help_text
    )

    valor = ""

    if situacao == "Informado":

        if textarea:

            valor = st.text_area(
                label,
                value=valor_atual or "",
                placeholder=placeholder,
                key=f"{key_prefix}_{campo}_valor"
            )

        else:

            valor = st.text_input(
                label,
                value=valor_atual or "",
                placeholder=placeholder,
                key=f"{key_prefix}_{campo}_valor"
            )

    else:

        st.caption(
            f"{label}: {situacao}."
        )

    return situacao, valor



# ============================================================
# CAMPOS SIMPLES DA ABA ESTRUTURA
#
# Nesta interface não há mais o fluxo repetitivo:
# "Situação do dado" -> "Informado" -> outro campo.
#
# Para campos padronizados, o usuário escolhe diretamente
# o valor. As opções "Não informado", "Não se aplica" e
# "Não verificado" continuam disponíveis no mesmo seletor.
#
# Para textos e números, campo vazio significa "Não informado".
# ============================================================

OPCOES_SEM_VALOR = [
    "Não informado",
    "Não se aplica",
    "Não verificado",
]


def campo_lista_simples(
    label,
    campo,
    mapa_status,
    valor_atual,
    opcoes,
    key_prefix,
    descricao=None,
):

    if descricao:

        st.caption(
            descricao
        )

    situacao_atual = inferir_situacao(
        mapa_status,
        campo,
        valor_atual
    )

    lista = (
        OPCOES_SEM_VALOR
        + list(opcoes)
    )

    # Preserva algum valor antigo que tenha sido digitado
    # antes desta melhoria de interface.
    if (
        valor_atual
        and
        valor_atual not in lista
    ):

        lista.append(
            valor_atual
        )

    if (
        situacao_atual != "Informado"
        and
        situacao_atual in OPCOES_SEM_VALOR
    ):

        valor_inicial = situacao_atual

    elif (
        valor_atual
        and
        valor_atual in lista
    ):

        valor_inicial = valor_atual

    else:

        valor_inicial = "Não informado"

    selecionado = st.selectbox(
        label,
        options=lista,
        index=lista.index(
            valor_inicial
        ),
        key=f"{key_prefix}_{campo}_direto"
    )

    if selecionado in OPCOES_SEM_VALOR:

        return (
            selecionado,
            ""
        )

    return (
        "Informado",
        selecionado
    )


def campo_texto_simples(
    label,
    campo,
    mapa_status,
    valor_atual,
    key_prefix,
    placeholder="",
    descricao=None,
    textarea=False,
):

    if descricao:

        st.caption(
            descricao
        )

    situacao_atual = inferir_situacao(
        mapa_status,
        campo,
        valor_atual
    )

    # Se o dado já estava explicitamente marcado como
    # não aplicável/não verificado, a opção continua disponível.
    modo_inicial = (
        situacao_atual
        if situacao_atual
        in ["Não se aplica", "Não verificado"]
        else "Preencher"
    )

    modo = st.selectbox(
        f"{label} — preenchimento",
        [
            "Preencher",
            "Não se aplica",
            "Não verificado",
        ],
        index=[
            "Preencher",
            "Não se aplica",
            "Não verificado",
        ].index(
            modo_inicial
        ),
        key=f"{key_prefix}_{campo}_modo"
    )

    if modo != "Preencher":

        return (
            modo,
            ""
        )

    if textarea:

        valor = st.text_area(
            label,
            value=valor_atual or "",
            placeholder=placeholder,
            key=f"{key_prefix}_{campo}_direto"
        )

    else:

        valor = st.text_input(
            label,
            value=valor_atual or "",
            placeholder=placeholder,
            key=f"{key_prefix}_{campo}_direto"
        )

    if valor.strip() == "":

        return (
            "Não informado",
            ""
        )

    return (
        "Informado",
        valor.strip()
    )


def campo_numero_texto_simples(
    label,
    campo,
    mapa_status,
    valor_atual,
    key_prefix,
    inteiro=False,
    descricao=None,
    placeholder="",
):

    if descricao:

        st.caption(
            descricao
        )

    situacao_atual = inferir_situacao(
        mapa_status,
        campo,
        valor_atual
    )

    modo_inicial = (
        situacao_atual
        if situacao_atual
        in ["Não se aplica", "Não verificado"]
        else "Preencher"
    )

    modo = st.selectbox(
        f"{label} — preenchimento",
        [
            "Preencher",
            "Não se aplica",
            "Não verificado",
        ],
        index=[
            "Preencher",
            "Não se aplica",
            "Não verificado",
        ].index(
            modo_inicial
        ),
        key=f"{key_prefix}_{campo}_modo"
    )

    if modo != "Preencher":

        return (
            modo,
            None
        )

    if valor_atual is None:

        inicial = ""

    elif inteiro:

        inicial = str(
            int(valor_atual)
        )

    else:

        inicial = (
            f"{float(valor_atual):.2f}"
            .replace(".", ",")
        )

    valor_txt = st.text_input(
        label,
        value=inicial,
        placeholder=placeholder,
        key=f"{key_prefix}_{campo}_direto"
    )

    if valor_txt.strip() == "":

        return (
            "Não informado",
            None
        )

    normalizado = (
        valor_txt
        .strip()
        .replace(" ", "")
        .replace(",", ".")
    )

    try:

        if inteiro:

            valor = int(
                float(normalizado)
            )

        else:

            valor = float(
                normalizado
            )

    except ValueError:

        st.error(
            f'O valor informado em "{label}" não é numérico.'
        )

        return (
            "Não informado",
            None
        )

    return (
        "Informado",
        valor
    )




# ============================================================
# ARQUIVOS
# ============================================================

def salvar_arquivo(arquivo, pasta):

    if arquivo is None:
        return None, None

    extensao = Path(
        arquivo.name
    ).suffix

    nome_interno = (
        f"{uuid4().hex}{extensao}"
    )

    caminho = (
        pasta / nome_interno
    )

    with open(
        caminho,
        "wb"
    ) as destino:

        destino.write(
            arquivo.getbuffer()
        )

    return (
        arquivo.name,
        str(caminho)
    )


# ============================================================
# NOVA INSPEÇÃO CADASTRAL
# ============================================================

def mostrar_nova_inspecao_cadastral(
    oae_ativa
):

    st.subheader(
        "🟦 Nova inspeção cadastral"
    )

    st.info(
        "A inspeção cadastral é a primeira inspeção da OAE "
        "e também deve ser realizada quando houver alteração "
        "na configuração da obra."
    )

    st.write(
        f"**OAE:** {oae_ativa.id} - {oae_ativa.nome}"
    )

    inspecoes_existentes = (
        buscar_inspecoes_cadastrais(
            oae_ativa.id
        )
    )

    ja_possui_cadastral = (
        len(inspecoes_existentes) > 0
    )

    if ja_possui_cadastral:

        ultima = inspecoes_existentes[0]

        st.warning(
            "Esta OAE já possui inspeção cadastral registrada "
            f"em {ultima.data_inspecao.strftime('%d/%m/%Y')}. "
            "Uma nova inspeção cadastral deve estar associada "
            "a uma alteração da configuração da obra."
        )

    with st.form(
        "form_nova_inspecao_cadastral"
    ):

        data_inspecao = st.date_input(
            "Data da inspeção",
            format="DD/MM/YYYY"
        )

        responsavel = st.text_input(
            "Inspetor responsável",
            placeholder="Ex.: João da Silva"
        )

        registro_profissional = st.text_input(
            "Registro profissional",
            placeholder="Ex.: CREA-GO 123456/D",
            help=(
                "Registro profissional do responsável "
                "pela inspeção."
            )
        )

        if ja_possui_cadastral:

            st.text_input(
                "Motivo da inspeção cadastral",
                value="Alteração na configuração da obra",
                disabled=True
            )

            motivo = (
                "Alteração na configuração da obra"
            )

        else:

            motivo = st.selectbox(
                "Motivo da inspeção cadastral",
                [
                    "Primeira inspeção da OAE",
                    "Alteração na configuração da obra"
                ]
            )

        descricao_alteracao = ""

        if (
            motivo
            == "Alteração na configuração da obra"
        ):

            descricao_alteracao = (
                st.text_area(
                    "Descrição da alteração",
                    placeholder=(
                        "Ex.: alargamento do tabuleiro, "
                        "reforço estrutural, alteração de dimensões "
                        "ou mudança do sistema estrutural."
                    )
                )
            )

        observacoes = st.text_area(
            "Observações gerais da inspeção",
            placeholder=(
                "Ex.: acesso parcial à face inferior do tabuleiro."
            )
        )

        salvar = st.form_submit_button(
            "Criar inspeção cadastral"
        )

    if salvar:

        if responsavel.strip() == "":

            st.error(
                "Informe o inspetor responsável."
            )

            return

        if (
            motivo
            == "Alteração na configuração da obra"
            and
            descricao_alteracao.strip() == ""
        ):

            st.error(
                "Descreva a alteração que motivou "
                "a nova inspeção cadastral."
            )

            return

        db = SessionLocal()

        nova_inspecao = models.Inspecao(
            oae_id=oae_ativa.id,
            tipo_inspecao="Cadastral",
            data_inspecao=data_inspecao,
            responsavel=responsavel,
            registro_profissional=
                registro_profissional,
            observacoes=observacoes
        )

        db.add(nova_inspecao)
        db.flush()

        detalhe = models.DetalheInspecao(
            inspecao_id=nova_inspecao.id,
            motivo_cadastral=motivo,
            descricao_alteracao=
                descricao_alteracao
        )

        db.add(detalhe)

        cadastro = models.InspecaoCadastral(
            inspecao_id=nova_inspecao.id
        )

        db.add(cadastro)

        db.commit()
        db.refresh(nova_inspecao)

        novo_id = nova_inspecao.id

        db.close()

        st.session_state.inspecao_ativa_id = (
            novo_id
        )

        st.success(
            "Inspeção cadastral criada com sucesso."
        )

        st.rerun()


# ============================================================
# IDENTIFICAÇÃO
# ============================================================

def mostrar_identificacao_localizacao(
    oae_ativa,
    inspecao_ativa,
    cadastro
):

    st.subheader(
        "1️⃣ Identificação e localização"
    )

    st.caption(
        "Alguns dados são reaproveitados do cadastro "
        "principal da OAE."
    )

    c1, c2, c3 = st.columns(3)

    with c1:

        st.write(
            "**OAE:**",
            oae_ativa.nome
        )

        st.write(
            "**Código:**",
            oae_ativa.codigo
            or "Não informado"
        )

    with c2:

        st.write(
            "**Rodovia/Ferrovia:**",
            oae_ativa.rodovia
            or "Não informado"
        )

        st.write(
            "**Município/UF:**",
            (
                f"{oae_ativa.municipio or ''}"
                f" - {oae_ativa.uf or ''}"
            )
        )

    with c3:

        st.write(
            "**Ano da construção:**",
            oae_ativa.ano_construcao
            or "Não informado"
        )

        st.write(
            "**Inspetor responsável:**",
            inspecao_ativa.responsavel
            or "Não informado"
        )

    with st.form(
        "form_cadastral_identificacao"
    ):

        c1, c2 = st.columns(2)

        with c1:

            jurisdicao = st.text_input(
                "Jurisdição",
                value=cadastro.jurisdicao or "",
                placeholder=(
                    "Ex.: DNIT, DER-GO, concessionária"
                )
            )

            administracao = st.text_input(
                "Administração",
                value=cadastro.administracao or "",
                placeholder=(
                    "Ex.: DNIT - Superintendência Regional de Goiás"
                )
            )

            sentido = st.text_input(
                "Sentido",
                value=cadastro.sentido or "",
                placeholder=(
                    "Ex.: crescente / decrescente "
                    "ou Catalão → Goiânia"
                )
            )

            localizacao = st.text_input(
                "Localização - quilômetro ou endereço",
                value=(
                    cadastro.localizacao_quilometro_endereco
                    or ""
                ),
                placeholder="Ex.: BR-050, km 278+500"
            )

            projetista = st.text_input(
                "Projetista",
                value=cadastro.projetista or "",
                placeholder="Ex.: XYZ Engenharia Ltda."
            )

            construtor = st.text_input(
                "Construtor",
                value=cadastro.construtor or "",
                placeholder="Ex.: Construtora ABC Ltda."
            )

        with c2:

            latitude = st.text_input(
                "Coordenada - latitude",
                value=(
                    cadastro.coordenada_latitude
                    or ""
                ),
                placeholder="Ex.: -18.165432"
            )

            longitude = st.text_input(
                "Coordenada - longitude",
                value=(
                    cadastro.coordenada_longitude
                    or ""
                ),
                placeholder="Ex.: -47.944210"
            )

            trem_tipo = st.text_input(
                "Trem-tipo provável",
                value=(
                    cadastro.trem_tipo_provavel
                    or ""
                ),
                placeholder="Ex.: TB-45"
            )

            importancia_opcoes = [
                "Não informado",
                "Alta",
                "Média",
                "Baixa"
            ]

            importancia_atual = (
                cadastro.importancia
                or "Não informado"
            )

            importancia = st.selectbox(
                "Importância",
                importancia_opcoes,
                index=(
                    importancia_opcoes.index(
                        importancia_atual
                    )
                    if importancia_atual
                    in importancia_opcoes
                    else 0
                )
            )

            finalidade = st.text_input(
                "Finalidade / passagem sobre obstáculo",
                value=cadastro.finalidade or "",
                placeholder=(
                    "Ex.: ponte sobre rio, "
                    "viaduto rodoviário"
                )
            )

            desvio = st.text_area(
                "Desvio ou rota alternativa",
                value=(
                    cadastro.desvio_rota_alternativa
                    or ""
                ),
                placeholder=(
                    "Ex.: desvio pela GO-330, "
                    "acréscimo de 18 km."
                )
            )

        salvar = st.form_submit_button(
            "Salvar identificação e localização"
        )

    if salvar:

        db = SessionLocal()

        registro = (
            db.query(models.InspecaoCadastral)
            .filter(
                models.InspecaoCadastral.id
                == cadastro.id
            )
            .first()
        )

        registro.jurisdicao = jurisdicao
        registro.administracao = administracao
        registro.sentido = sentido
        registro.localizacao_quilometro_endereco = (
            localizacao
        )
        registro.projetista = projetista
        registro.construtor = construtor
        registro.coordenada_latitude = latitude
        registro.coordenada_longitude = longitude
        registro.trem_tipo_provavel = trem_tipo
        registro.importancia = (
            importancia
            if importancia != "Não informado"
            else None
        )
        registro.finalidade = finalidade
        registro.desvio_rota_alternativa = desvio

        db.commit()
        db.close()

        st.success(
            "Identificação e localização salvas."
        )

        st.rerun()


# ============================================================
# ESTRUTURA
# ============================================================

def mostrar_caracteristicas_estruturais(
    oae_ativa,
    cadastro
):

    st.subheader(
        "2️⃣ Características da estrutura"
    )

    st.info(
        "Agora o preenchimento é direto. Nos campos padronizados, "
        "selecione a opção que corresponde à OAE. Nos campos de "
        "descrição, escreva apenas quando necessário."
    )

    mapa_status = buscar_mapa_status(
        cadastro.id
    )

    # ========================================================
    # RESUMO
    # ========================================================

    st.markdown(
        "### 📌 Dados gerais já cadastrados"
    )

    c1, c2, c3 = st.columns(
        3
    )

    with c1:

        st.metric(
            "Comprimento total",
            (
                f"{oae_ativa.comprimento_total:.2f} m"
                if oae_ativa.comprimento_total is not None
                else "Não informado"
            )
        )

    with c2:

        st.metric(
            "Largura cadastrada",
            (
                f"{oae_ativa.largura:.2f} m"
                if oae_ativa.largura is not None
                else "Não informado"
            )
        )

    with c3:

        st.metric(
            "Número de vãos",
            (
                oae_ativa.numero_vaos
                if oae_ativa.numero_vaos is not None
                else "Não informado"
            )
        )

    st.divider()

    # ========================================================
    # A. DIMENSÕES
    # ========================================================

    st.markdown(
        "### 📐 A. Dimensões principais"
    )

    st.caption(
        "Se o valor não for conhecido, deixe o campo vazio."
    )

    c1, c2 = st.columns(
        2
    )

    with c1:

        sit_largura_total, largura_total = (
            campo_numero_texto_simples(
                "Largura total (m)",
                "largura_total",
                mapa_status,
                cadastro.largura_total,
                "estrutura",
                descricao=(
                    "Largura completa da seção transversal da OAE."
                ),
                placeholder="Ex.: 12,00"
            )
        )

    with c2:

        sit_largura_util, largura_util = (
            campo_numero_texto_simples(
                "Largura útil (m)",
                "largura_util",
                mapa_status,
                cadastro.largura_util,
                "estrutura",
                descricao=(
                    "Largura efetivamente disponível para circulação."
                ),
                placeholder="Ex.: 10,50"
            )
        )

    st.divider()

    # ========================================================
    # B. SISTEMA ESTRUTURAL
    # ========================================================

    st.markdown(
        "### 🏗️ B. Sistema estrutural"
    )

    st.caption(
        "As opções abaixo seguem a organização da ficha cadastral "
        "da NBR 9452:2023."
    )

    st.markdown(
        "#### B1. Construção, material e transposição"
    )

    c1, c2 = st.columns(
        2
    )

    with c1:

        sit_sistema, sistema_construtivo = (
            campo_lista_simples(
                "Sistema construtivo",
                "sistema_construtivo",
                mapa_status,
                cadastro.sistema_construtivo,
                [
                    "Moldado no local",
                    "Pré-moldado somente armado",
                    "Pré-moldado protendido (pós-tensão)",
                    "Pré-moldado protendido (pré-tensão)",
                    "Balanço sucessivo",
                    "Aduelas pré-moldadas",
                    "Empurrada",
                    "Estaiada",
                    "Pênsil",
                    "Estrutura metálica ou mista",
                    "Não identificado",
                    "Outros"
                ],
                "estrutura",
                descricao=(
                    "Como a estrutura principal foi executada."
                )
            )
        )

        sit_material, material = (
            campo_lista_simples(
                "Material predominante",
                "material",
                mapa_status,
                cadastro.material,
                [
                    "Concreto simples (CS)",
                    "Concreto armado (CA)",
                    "Concreto protendido (CP)",
                    "Aço (A)",
                    "Madeira (MD)",
                    "Pedra argamassada (PA)",
                    "Mista (MI)",
                    "Alvenaria (AL)",
                    "Não identificado",
                    "Outros"
                ],
                "estrutura",
                descricao=(
                    "Material predominante da estrutura."
                )
            )
        )

    with c2:

        sit_natureza, natureza_transposicao = (
            campo_lista_simples(
                "Natureza da transposição",
                "natureza_transposicao",
                mapa_status,
                cadastro.natureza_transposicao,
                [
                    "Superfície aquífera",
                    "Rodovia",
                    "Ferrovia",
                    "Vale",
                    "Grota",
                    "Contorno de encosta",
                    "Via urbana",
                    "Via de pedestre",
                    "Outras"
                ],
                "estrutura",
                descricao=(
                    "O que existe sob a OAE."
                )
            )
        )

        sit_secao, secao_tipo = (
            campo_texto_simples(
                "Seção-tipo",
                "secao_tipo",
                mapa_status,
                cadastro.secao_tipo,
                "estrutura",
                placeholder=(
                    "Ex.: cinco vigas I protendidas com laje superior."
                ),
                descricao=(
                    "Descreva resumidamente a seção transversal."
                )
            )
        )

    st.markdown(
        "#### B2. Superestrutura"
    )

    c1, c2 = st.columns(
        2
    )

    with c1:

        sit_long, longitudinal = (
            campo_lista_simples(
                "Comportamento longitudinal",
                "tipologia_longitudinal_superestrutura",
                mapa_status,
                cadastro.tipologia_longitudinal_superestrutura,
                [
                    "Biapoiada ou isostática",
                    "Contínua",
                    "Vão apoiado em consolo ou dente Gerber",
                    "Arco superior",
                    "Arco intermediário",
                    "Arco inferior",
                    "Pórtico",
                    "Estaiada",
                    "Pênsil",
                    "Treliça",
                    "Outras"
                ],
                "estrutura",
                descricao=(
                    "Forma resistente ao longo do eixo da ponte."
                )
            )
        )

    with c2:

        sit_transv, transversal = (
            campo_lista_simples(
                "Configuração transversal",
                "tipologia_transversal_superestrutura",
                mapa_status,
                cadastro.tipologia_transversal_superestrutura,
                [
                    "Laje",
                    "Duas vigas",
                    "Grelha",
                    "Seção celular",
                    "Treliça",
                    "Outras"
                ],
                "estrutura",
                descricao=(
                    "Organização da superestrutura vista em corte transversal."
                )
            )
        )

    st.markdown(
        "#### B3. Mesoestrutura e fundações"
    )

    c1, c2 = st.columns(
        2
    )

    with c1:

        sit_meso, mesoestrutura = (
            campo_lista_simples(
                "Mesoestrutura",
                "tipologia_mesoestrutura",
                mapa_status,
                cadastro.tipologia_mesoestrutura,
                [
                    "Pilares isolados",
                    "Pilares com travessa",
                    "Pilares contraventados",
                    "Pilares parede",
                    "Pilones",
                    "Outras"
                ],
                "estrutura",
                descricao=(
                    "Configuração dos pilares/apoios intermediários."
                )
            )
        )

    with c2:

        sit_infra, infraestrutura = (
            campo_lista_simples(
                "Fundação / infraestrutura",
                "tipologia_infraestrutura",
                mapa_status,
                cadastro.tipologia_infraestrutura,
                [
                    "Fundação superficial",
                    "Tubulões",
                    "Estaca escavada",
                    "Estaca pré-moldada",
                    "Estaca metálica",
                    "Estaca de madeira",
                    "Não identificado",
                    "Outras"
                ],
                "estrutura",
                descricao=(
                    "Sistema de fundação da OAE."
                )
            )
        )

    st.divider()

    # ========================================================
    # C. GEOMETRIA
    # ========================================================

    st.markdown(
        "### 🔢 C. Geometria e apoios"
    )

    c1, c2 = st.columns(
        2
    )

    with c1:

        sit_apoios, numero_apoios = (
            campo_numero_texto_simples(
                "Número de apoios",
                "numero_apoios",
                mapa_status,
                cadastro.numero_apoios,
                "estrutura",
                inteiro=True,
                descricao=(
                    "Quantidade total de linhas de apoio da OAE."
                ),
                placeholder="Ex.: 5"
            )
        )

        sit_pilares, pilares_apoio = (
            campo_numero_texto_simples(
                "Pilares por apoio",
                "numero_pilares_por_apoio",
                mapa_status,
                cadastro.numero_pilares_por_apoio,
                "estrutura",
                inteiro=True,
                descricao=(
                    "Quantidade típica de pilares em cada apoio intermediário."
                ),
                placeholder="Ex.: 2"
            )
        )

        sit_vao_tip, vao_tipico = (
            campo_numero_texto_simples(
                "Vão típico (m)",
                "comprimento_vao_tipico",
                mapa_status,
                cadastro.comprimento_vao_tipico,
                "estrutura",
                descricao=(
                    "Comprimento predominante dos vãos."
                ),
                placeholder="Ex.: 30,00"
            )
        )

    with c2:

        sit_vao_maior, vao_maior = (
            campo_numero_texto_simples(
                "Maior vão (m)",
                "comprimento_vao_maior",
                mapa_status,
                cadastro.comprimento_vao_maior,
                "estrutura",
                descricao=(
                    "Maior distância entre dois apoios consecutivos."
                ),
                placeholder="Ex.: 30,00"
            )
        )

        sit_altura, altura_pilares = (
            campo_numero_texto_simples(
                "Altura típica dos pilares (m)",
                "altura_pilares",
                mapa_status,
                cadastro.altura_pilares,
                "estrutura",
                descricao=(
                    "Altura aproximada dos pilares intermediários."
                ),
                placeholder="Ex.: 8,00"
            )
        )

    st.divider()

    # ========================================================
    # D. APOIOS E ELEMENTOS ASSOCIADOS
    # ========================================================

    st.markdown(
        "### 🧩 D. Apoios, encontros e elementos associados"
    )

    st.caption(
        "Descreva somente o necessário. Os exemplos servem como guia."
    )

    c1, c2 = st.columns(
        2
    )

    with c1:

        sit_aparelhos, aparelhos = (
            campo_texto_simples(
                "Aparelhos de apoio",
                "aparelhos_apoio",
                mapa_status,
                cadastro.aparelhos_apoio,
                "estrutura",
                placeholder=(
                    "Ex.: aparelhos elastoméricos distribuídos nos apoios."
                ),
                descricao=(
                    "Informe tipo, quantidade ou organização quando conhecida."
                ),
                textarea=True
            )
        )

        sit_encontros, encontros = (
            campo_texto_simples(
                "Encontros",
                "encontros",
                mapa_status,
                cadastro.encontros,
                "estrutura",
                placeholder=(
                    "Ex.: E1 e E2 em concreto armado com muros de ala."
                ),
                descricao=(
                    "Descreva os encontros das extremidades da OAE."
                ),
                textarea=True
            )
        )

        sit_taludes, taludes = (
            campo_texto_simples(
                "Taludes",
                "taludes",
                mapa_status,
                cadastro.taludes,
                "estrutura",
                placeholder=(
                    "Ex.: taludes gramados, sem erosão aparente."
                ),
                descricao=(
                    "Condição/configuração dos taludes junto aos encontros."
                ),
                textarea=True
            )
        )

    with c2:

        sit_juntas, juntas = (
            campo_texto_simples(
                "Juntas de dilatação",
                "juntas_dilatacao",
                mapa_status,
                cadastro.juntas_dilatacao,
                "estrutura",
                placeholder=(
                    "Ex.: 2 juntas elastoméricas, junto a E1 e E2."
                ),
                descricao=(
                    "Informe tipo, quantidade e localização quando conhecida."
                ),
                textarea=True
            )
        )

        sit_pec, peculiaridades = (
            campo_texto_simples(
                "Outras particularidades",
                "outras_peculiaridades",
                mapa_status,
                cadastro.outras_peculiaridades,
                "estrutura",
                placeholder=(
                    "Ex.: dente Gerber, acesso à seção celular ou outro detalhe."
                ),
                descricao=(
                    "Use apenas para algo relevante não registrado acima."
                ),
                textarea=True
            )
        )

    st.divider()

    if st.button(
        "💾 Salvar características estruturais",
        type="primary",
        key=f"salvar_estrutura_{cadastro.id}"
    ):

        db = SessionLocal()

        try:

            registro = (
                db.query(models.InspecaoCadastral)
                .filter(
                    models.InspecaoCadastral.id
                    == cadastro.id
                )
                .first()
            )

            valores = {
                "largura_total":
                    (sit_largura_total, largura_total),

                "largura_util":
                    (sit_largura_util, largura_util),

                "sistema_construtivo":
                    (sit_sistema, sistema_construtivo),

                "natureza_transposicao":
                    (sit_natureza, natureza_transposicao),

                "material":
                    (sit_material, material),

                "secao_tipo":
                    (sit_secao, secao_tipo),

                "tipologia_longitudinal_superestrutura":
                    (sit_long, longitudinal),

                "tipologia_transversal_superestrutura":
                    (sit_transv, transversal),

                "tipologia_mesoestrutura":
                    (sit_meso, mesoestrutura),

                "tipologia_infraestrutura":
                    (sit_infra, infraestrutura),

                "numero_apoios":
                    (sit_apoios, numero_apoios),

                "numero_pilares_por_apoio":
                    (sit_pilares, pilares_apoio),

                "comprimento_vao_tipico":
                    (sit_vao_tip, vao_tipico),

                "comprimento_vao_maior":
                    (sit_vao_maior, vao_maior),

                "altura_pilares":
                    (sit_altura, altura_pilares),

                "aparelhos_apoio":
                    (sit_aparelhos, aparelhos),

                "juntas_dilatacao":
                    (sit_juntas, juntas),

                "encontros":
                    (sit_encontros, encontros),

                "taludes":
                    (sit_taludes, taludes),

                "outras_peculiaridades":
                    (sit_pec, peculiaridades)
            }

            for campo, dados in valores.items():

                situacao, valor = dados

                salvar_status(
                    db,
                    cadastro.id,
                    campo,
                    situacao
                )

                if situacao == "Informado":

                    setattr(
                        registro,
                        campo,
                        valor
                    )

                else:

                    setattr(
                        registro,
                        campo,
                        None
                    )

            db.commit()

            st.session_state[
                "_mensagem_cadastral"
            ] = (
                "Características estruturais salvas com sucesso."
            )

        except Exception as erro:

            db.rollback()

            st.error(
                "Não foi possível salvar as características "
                f"estruturais. Detalhe: {erro}"
            )

            db.close()

            st.stop()

        db.close()

        st.rerun()


# ============================================================
# FUNCIONAL
# ============================================================

def mostrar_caracteristicas_funcionais(
    cadastro
):

    st.subheader(
        "3️⃣ Características funcionais"
    )

    st.info(
        "Os dados funcionais também são preenchidos conforme "
        "a aplicabilidade. Não use 0 para representar ausência "
        "de informação."
    )

    mapa_status = buscar_mapa_status(
        cadastro.id
    )

    with st.form(
        "form_cadastral_funcional"
    ):

        # ----------------------------------------------------
        # PISTA
        # ----------------------------------------------------

        with st.expander(
            "🛣️ Características da pista",
            expanded=True
        ):

            sit_plani, planialtimetricas = (
                campo_texto_condicional(
                    "Características plani-altimétricas",
                    "caracteristicas_planialtimetricas",
                    mapa_status,
                    cadastro.caracteristicas_planialtimetricas,
                    "funcional",
                    placeholder=(
                        "Ex.: região ondulada, traçado em curva, "
                        "rampa longitudinal de 2,5%."
                    ),
                    textarea=True
                )
            )

            c1, c2 = st.columns(2)

            with c1:

                sit_faixas, numero_faixas = (
                    campo_numerico_condicional(
                        "Número de faixas / vias",
                        "numero_faixas",
                        mapa_status,
                        cadastro.numero_faixas,
                        "funcional",
                        inteiro=True
                    )
                )

            with c2:

                sit_larg_faixa, largura_faixa = (
                    campo_numerico_condicional(
                        "Largura da faixa / via (m)",
                        "largura_faixa",
                        mapa_status,
                        cadastro.largura_faixa,
                        "funcional"
                    )
                )

            c1, c2 = st.columns(2)

            with c1:

                sit_acost, acostamento = (
                    campo_texto_condicional(
                        "Acostamento",
                        "acostamento_situacao",
                        mapa_status,
                        cadastro.acostamento_situacao,
                        "funcional",
                        placeholder=(
                            "Ex.: existe em ambos os lados"
                        )
                    )
                )

                sit_larg_acost, largura_acostamento = (
                    campo_numerico_condicional(
                        "Largura do acostamento (m)",
                        "largura_acostamento",
                        mapa_status,
                        cadastro.largura_acostamento,
                        "funcional"
                    )
                )

                sit_ref, refugio = (
                    campo_texto_condicional(
                        "Refúgio",
                        "refugio_situacao",
                        mapa_status,
                        cadastro.refugio_situacao,
                        "funcional",
                        placeholder="Ex.: inexistente"
                    )
                )

                sit_larg_ref, largura_refugio = (
                    campo_numerico_condicional(
                        "Largura do refúgio (m)",
                        "largura_refugio",
                        mapa_status,
                        cadastro.largura_refugio,
                        "funcional"
                    )
                )

            with c2:

                sit_passeio, passeio = (
                    campo_texto_condicional(
                        "Passeio / passarela",
                        "passeio_passarela_situacao",
                        mapa_status,
                        cadastro.passeio_passarela_situacao,
                        "funcional",
                        placeholder=(
                            "Ex.: passeio lateral para pedestres"
                        )
                    )
                )

                sit_larg_passeio, largura_passeio = (
                    campo_numerico_condicional(
                        "Largura do passeio / passarela (m)",
                        "largura_passeio_passarela",
                        mapa_status,
                        cadastro.largura_passeio_passarela,
                        "funcional"
                    )
                )

        # ----------------------------------------------------
        # ELEMENTOS FUNCIONAIS
        # ----------------------------------------------------

        with st.expander(
            "🧱 Elementos funcionais",
            expanded=False
        ):

            sit_barreira, barreira = (
                campo_texto_condicional(
                    "Barreira rígida",
                    "barreira_rigida_situacao",
                    mapa_status,
                    cadastro.barreira_rigida_situacao,
                    "funcional",
                    placeholder=(
                        "Ex.: barreira New Jersey"
                    )
                )
            )

            sit_guarda, guarda_corpos = (
                campo_texto_condicional(
                    "Guarda-corpos",
                    "guarda_corpos_situacao",
                    mapa_status,
                    cadastro.guarda_corpos_situacao,
                    "funcional",
                    placeholder=(
                        "Ex.: guarda-corpo metálico"
                    )
                )
            )

            sit_pav, pavimento = (
                campo_texto_condicional(
                    "Pavimento / via permanente",
                    "pavimento_via_permanente",
                    mapa_status,
                    cadastro.pavimento_via_permanente,
                    "funcional",
                    placeholder=(
                        "Ex.: revestimento asfáltico"
                    ),
                    textarea=True
                )
            )

            sit_drenos, drenos = (
                campo_texto_condicional(
                    "Drenos",
                    "drenos_situacao",
                    mapa_status,
                    cadastro.drenos_situacao,
                    "funcional",
                    placeholder=(
                        "Ex.: buzinotes distribuídos no tabuleiro"
                    )
                )
            )

            sit_ping, pingadeiras = (
                campo_texto_condicional(
                    "Pingadeiras",
                    "pingadeiras_situacao",
                    mapa_status,
                    cadastro.pingadeiras_situacao,
                    "funcional",
                    placeholder="Ex.: existentes"
                )
            )

        # ----------------------------------------------------
        # GABARITOS
        # ----------------------------------------------------

        with st.expander(
            "📏 Gabaritos",
            expanded=False
        ):

            c1, c2 = st.columns(2)

            with c1:

                sit_gab_sob, gabarito_sob = (
                    campo_numerico_condicional(
                        "Gabarito vertical sob a OAE (m)",
                        "gabarito_vertical_sob_oae",
                        mapa_status,
                        cadastro.gabarito_vertical_sob_oae,
                        "funcional"
                    )
                )

                sit_gab_sobre, gabarito_sobre = (
                    campo_numerico_condicional(
                        "Gabarito vertical sobre a OAE (m)",
                        "gabarito_vertical_sobre_oae",
                        mapa_status,
                        cadastro.gabarito_vertical_sobre_oae,
                        "funcional"
                    )
                )

            with c2:

                sit_gab_nav, gabarito_navegavel = (
                    campo_texto_condicional(
                        "Gabarito navegável",
                        "gabarito_navegavel_situacao",
                        mapa_status,
                        cadastro.gabarito_navegavel_situacao,
                        "funcional",
                        placeholder=(
                            "Ex.: canal navegável sinalizado"
                        )
                    )
                )

                sit_gab_alt, navegavel_altura = (
                    campo_numerico_condicional(
                        "Altura do gabarito navegável (m)",
                        "gabarito_navegavel_altura",
                        mapa_status,
                        cadastro.gabarito_navegavel_altura,
                        "funcional"
                    )
                )

                sit_gab_larg, navegavel_largura = (
                    campo_numerico_condicional(
                        "Largura do gabarito navegável (m)",
                        "gabarito_navegavel_largura",
                        mapa_status,
                        cadastro.gabarito_navegavel_largura,
                        "funcional"
                    )
                )

        # ----------------------------------------------------
        # TRÁFEGO
        # ----------------------------------------------------

        with st.expander(
            "🚛 Tráfego",
            expanded=False
        ):

            st.caption(
                "A ficha cadastral da NBR 9452 inclui dados "
                "de tráfego. Quando o dado não estiver disponível, "
                "marque 'Não informado' ou 'Não verificado'."
            )

            c1, c2 = st.columns(2)

            with c1:

                sit_freq, frequencia = (
                    campo_texto_condicional(
                        "Frequência de passagem de carga especial",
                        "frequencia_carga_especial",
                        mapa_status,
                        cadastro.frequencia_carga_especial,
                        "funcional",
                        placeholder=(
                            "Ex.: eventual / mensal"
                        )
                    )
                )

                sit_pbt, pbt = (
                    campo_numerico_condicional(
                        "PBT máximo",
                        "pbt_maximo",
                        mapa_status,
                        cadastro.pbt_maximo,
                        "funcional"
                    )
                )

                sit_eixo, carga_eixo = (
                    campo_numerico_condicional(
                        "Carga máxima por eixo",
                        "carga_maxima_eixo",
                        mapa_status,
                        cadastro.carga_maxima_eixo,
                        "funcional"
                    )
                )

            with c2:

                sit_vmd, vmd = (
                    campo_numerico_condicional(
                        "Volume médio diário - VMD",
                        "volume_medio_diario",
                        mapa_status,
                        cadastro.volume_medio_diario,
                        "funcional",
                        step=1.0
                    )
                )

                sit_ano_vmd, ano_vmd = (
                    campo_numerico_condicional(
                        "Ano de referência do VMD",
                        "ano_referencia_vmd",
                        mapa_status,
                        cadastro.ano_referencia_vmd,
                        "funcional",
                        inteiro=True
                    )
                )

        salvar = st.form_submit_button(
            "Salvar características funcionais"
        )

    if salvar:

        db = SessionLocal()

        registro = (
            db.query(models.InspecaoCadastral)
            .filter(
                models.InspecaoCadastral.id
                == cadastro.id
            )
            .first()
        )

        valores = {
            "caracteristicas_planialtimetricas":
                (sit_plani, planialtimetricas),

            "numero_faixas":
                (sit_faixas, numero_faixas),

            "largura_faixa":
                (sit_larg_faixa, largura_faixa),

            "acostamento_situacao":
                (sit_acost, acostamento),

            "largura_acostamento":
                (sit_larg_acost, largura_acostamento),

            "refugio_situacao":
                (sit_ref, refugio),

            "largura_refugio":
                (sit_larg_ref, largura_refugio),

            "passeio_passarela_situacao":
                (sit_passeio, passeio),

            "largura_passeio_passarela":
                (sit_larg_passeio, largura_passeio),

            "barreira_rigida_situacao":
                (sit_barreira, barreira),

            "guarda_corpos_situacao":
                (sit_guarda, guarda_corpos),

            "pavimento_via_permanente":
                (sit_pav, pavimento),

            "drenos_situacao":
                (sit_drenos, drenos),

            "pingadeiras_situacao":
                (sit_ping, pingadeiras),

            "gabarito_vertical_sob_oae":
                (sit_gab_sob, gabarito_sob),

            "gabarito_vertical_sobre_oae":
                (sit_gab_sobre, gabarito_sobre),

            "gabarito_navegavel_situacao":
                (sit_gab_nav, gabarito_navegavel),

            "gabarito_navegavel_altura":
                (sit_gab_alt, navegavel_altura),

            "gabarito_navegavel_largura":
                (sit_gab_larg, navegavel_largura),

            "frequencia_carga_especial":
                (sit_freq, frequencia),

            "pbt_maximo":
                (sit_pbt, pbt),

            "carga_maxima_eixo":
                (sit_eixo, carga_eixo),

            "volume_medio_diario":
                (sit_vmd, vmd),

            "ano_referencia_vmd":
                (sit_ano_vmd, ano_vmd)
        }

        for campo, (
            situacao,
            valor
        ) in valores.items():

            salvar_status(
                db,
                cadastro.id,
                campo,
                situacao
            )

            setattr(
                registro,
                campo,
                (
                    valor
                    if situacao == "Informado"
                    else None
                )
            )

        db.commit()
        db.close()

        st.success(
            "Características funcionais salvas."
        )

        st.rerun()


# ============================================================
# AMBIENTAL
# ============================================================

def mostrar_caracteristicas_ambientais(
    cadastro
):

    st.subheader(
        "4️⃣ Características ambientais"
    )

    st.caption(
        "A classificação do grau de agressividade deve seguir "
        "a referência indicada pela ficha cadastral."
    )

    with st.form(
        "form_cadastral_ambiental"
    ):

        agressividade_opcoes = [
            "Não informada",
            "Fraca",
            "Moderada",
            "Forte",
            "Muito forte"
        ]

        agressividade_atual = (
            cadastro.grau_agressividade_ambiental
            or "Não informada"
        )

        agressividade = st.selectbox(
            "Grau de agressividade ambiental",
            agressividade_opcoes,
            index=(
                agressividade_opcoes.index(
                    agressividade_atual
                )
                if agressividade_atual
                in agressividade_opcoes
                else 0
            )
        )

        curso_opcoes = [
            "Não verificado",
            "Sim",
            "Não"
        ]

        curso_atual = (
            cadastro.curso_agua_aplicavel
            or "Não verificado"
        )

        curso_agua = st.selectbox(
            "Caracterização de curso d'água aplicável",
            curso_opcoes,
            index=(
                curso_opcoes.index(
                    curso_atual
                )
                if curso_atual
                in curso_opcoes
                else 0
            )
        )

        nome_curso = st.text_input(
            "Nome do curso d'água",
            value=(
                cadastro.nome_curso_agua
                or ""
            ),
            placeholder="Ex.: Rio São Marcos"
        )

        inundacao = st.text_area(
            "Histórico de inundação no local",
            value=(
                cadastro.historico_inundacao
                or ""
            ),
            placeholder=(
                "Ex.: sem registros conhecidos, "
                "ou descrever eventos conhecidos."
            )
        )

        informacoes = st.text_area(
            "Informações complementares",
            value=(
                cadastro.informacoes_complementares
                or ""
            )
        )

        recomendacoes = st.text_area(
            "Recomendações terapêuticas",
            value=(
                cadastro.recomendacoes_terapeuticas
                or ""
            )
        )

        observacoes = st.text_area(
            "Observações do cadastro",
            value=(
                cadastro.observacoes_cadastro
                or ""
            )
        )

        salvar = st.form_submit_button(
            "Salvar dados ambientais e complementares"
        )

    if salvar:

        db = SessionLocal()

        registro = (
            db.query(models.InspecaoCadastral)
            .filter(
                models.InspecaoCadastral.id
                == cadastro.id
            )
            .first()
        )

        registro.grau_agressividade_ambiental = (
            agressividade
            if agressividade != "Não informada"
            else None
        )

        registro.curso_agua_aplicavel = curso_agua
        registro.nome_curso_agua = nome_curso
        registro.historico_inundacao = inundacao
        registro.informacoes_complementares = (
            informacoes
        )
        registro.recomendacoes_terapeuticas = (
            recomendacoes
        )
        registro.observacoes_cadastro = (
            observacoes
        )

        db.commit()
        db.close()

        st.success(
            "Dados ambientais e complementares salvos."
        )

        st.rerun()


# ============================================================
# DOCUMENTOS
# ============================================================

def mostrar_documentos(cadastro):

    st.subheader(
        "5️⃣ Documentos iniciais"
    )

    st.caption(
        "Registre a situação de cada documento. "
        "A ausência do documento não deve impedir o cadastro; "
        "ela deve ficar registrada."
    )

    existentes = (
        buscar_documentos_cadastrais(
            cadastro.id
        )
    )

    mapa = {
        item.tipo_documento: item
        for item in existentes
    }

    for indice, tipo in enumerate(
        TIPOS_DOCUMENTOS,
        start=1
    ):

        existente = mapa.get(tipo)

        with st.expander(
            f"{indice}. {tipo}",
            expanded=False
        ):

            situacao_atual = (
                existente.situacao
                if existente is not None
                else "Não verificado"
            )

            descricao_atual = (
                existente.descricao
                if existente is not None
                and existente.descricao
                else ""
            )

            with st.form(
                f"form_documento_{indice}"
            ):

                situacao = st.selectbox(
                    "Situação",
                    SITUACOES_DOCUMENTO,
                    index=(
                        SITUACOES_DOCUMENTO.index(
                            situacao_atual
                        )
                        if situacao_atual
                        in SITUACOES_DOCUMENTO
                        else 3
                    )
                )

                descricao = st.text_area(
                    "Descrição / observações",
                    value=descricao_atual
                )

                arquivo = st.file_uploader(
                    "Anexar documento",
                    key=f"documento_{indice}"
                )

                salvar = st.form_submit_button(
                    "Salvar documento"
                )

            if salvar:

                nome_arquivo = None
                caminho_arquivo = None

                if arquivo is not None:

                    (
                        nome_arquivo,
                        caminho_arquivo
                    ) = salvar_arquivo(
                        arquivo,
                        PASTA_DOCUMENTOS
                    )

                db = SessionLocal()

                registro = (
                    db.query(
                        models.DocumentoCadastral
                    )
                    .filter(
                        models.DocumentoCadastral.inspecao_cadastral_id
                        == cadastro.id
                    )
                    .filter(
                        models.DocumentoCadastral.tipo_documento
                        == tipo
                    )
                    .first()
                )

                if registro is None:

                    registro = models.DocumentoCadastral(
                        inspecao_cadastral_id=
                            cadastro.id,
                        tipo_documento=tipo,
                        situacao=situacao,
                        descricao=descricao,
                        nome_arquivo=
                            nome_arquivo,
                        caminho_arquivo=
                            caminho_arquivo
                    )

                    db.add(registro)

                else:

                    registro.situacao = situacao
                    registro.descricao = descricao

                    if nome_arquivo is not None:

                        registro.nome_arquivo = (
                            nome_arquivo
                        )

                        registro.caminho_arquivo = (
                            caminho_arquivo
                        )

                db.commit()
                db.close()

                st.success(
                    "Documento atualizado."
                )

                st.rerun()

            if existente is not None:

                st.write(
                    "**Situação atual:**",
                    existente.situacao
                )

                if existente.nome_arquivo:

                    st.write(
                        "**Arquivo anexado:**",
                        existente.nome_arquivo
                    )


# ============================================================
# CROQUIS
# ============================================================

def mostrar_croquis(cadastro):

    st.subheader(
        "6️⃣ Croquis"
    )

    st.caption(
        "A ficha cadastral prevê planta do tabuleiro, "
        "corte longitudinal, corte transversal e detalhes "
        "adicionais quando relevantes."
    )

    existentes = (
        buscar_croquis_cadastrais(
            cadastro.id
        )
    )

    mapa = {
        item.tipo_croqui: item
        for item in existentes
    }

    for indice, tipo in enumerate(
        TIPOS_CROQUIS,
        start=1
    ):

        existente = mapa.get(tipo)

        with st.expander(
            tipo,
            expanded=False
        ):

            situacao_atual = (
                existente.situacao
                if existente is not None
                else "Pendente"
            )

            descricao_atual = (
                existente.descricao
                if existente is not None
                and existente.descricao
                else ""
            )

            with st.form(
                f"form_croqui_{indice}"
            ):

                situacao = st.selectbox(
                    "Situação",
                    SITUACOES_CROQUI,
                    index=(
                        SITUACOES_CROQUI.index(
                            situacao_atual
                        )
                        if situacao_atual
                        in SITUACOES_CROQUI
                        else 1
                    )
                )

                descricao = st.text_area(
                    "Descrição",
                    value=descricao_atual
                )

                arquivo = st.file_uploader(
                    "Anexar croqui",
                    key=f"croqui_{indice}",
                    type=[
                        "pdf",
                        "png",
                        "jpg",
                        "jpeg"
                    ]
                )

                salvar = st.form_submit_button(
                    "Salvar croqui"
                )

            if salvar:

                nome_arquivo = None
                caminho_arquivo = None

                if arquivo is not None:

                    (
                        nome_arquivo,
                        caminho_arquivo
                    ) = salvar_arquivo(
                        arquivo,
                        PASTA_CROQUIS
                    )

                db = SessionLocal()

                registro = (
                    db.query(
                        models.CroquiCadastral
                    )
                    .filter(
                        models.CroquiCadastral.inspecao_cadastral_id
                        == cadastro.id
                    )
                    .filter(
                        models.CroquiCadastral.tipo_croqui
                        == tipo
                    )
                    .first()
                )

                if registro is None:

                    registro = models.CroquiCadastral(
                        inspecao_cadastral_id=
                            cadastro.id,
                        tipo_croqui=tipo,
                        situacao=situacao,
                        descricao=descricao,
                        nome_arquivo=
                            nome_arquivo,
                        caminho_arquivo=
                            caminho_arquivo
                    )

                    db.add(registro)

                else:

                    registro.situacao = situacao
                    registro.descricao = descricao

                    if nome_arquivo is not None:

                        registro.nome_arquivo = (
                            nome_arquivo
                        )

                        registro.caminho_arquivo = (
                            caminho_arquivo
                        )

                db.commit()
                db.close()

                st.success(
                    "Croqui atualizado."
                )

                st.rerun()


# ============================================================
# REGISTROS VINCULADOS
# ============================================================

def mostrar_integracoes(
    oae_ativa,
    inspecao_ativa
):

    st.subheader(
        "7️⃣ Anomalias, classificação e fotografias"
    )

    anomalias = (
        contar_observacoes_anomalias(
            inspecao_ativa.id
        )
    )

    fotos = contar_fotos_inspecao(
        oae_ativa.id,
        inspecao_ativa.id
    )

    andamento_classificacao = (
        verificar_andamento_classificacao(
            oae_ativa.id,
            inspecao_ativa.id
        )
    )

    classificacao = (
        calcular_classificacao_consolidada(
            oae_ativa.id,
            inspecao_ativa.id
        )
    )

    c1, c2, c3 = st.columns(3)

    with c1:

        st.metric(
            "Anomalias observadas",
            anomalias
        )

    with c2:

        st.metric(
            "Componentes classificados",
            (
                f"{andamento_classificacao['avaliados']}"
                f"/"
                f"{andamento_classificacao['total']}"
            )
        )

    with c3:

        st.metric(
            "Fotografias",
            fotos
        )

        if fotos >= 8:

            st.caption(
                "Quantidade mínima da ficha cadastral "
                "atingida."
            )

        else:

            st.caption(
                f"Faltam {8 - fotos} fotografia(s) "
                "para atingir oito registros."
            )

    if (
        classificacao["estrutural"] is not None
        or
        classificacao["funcional"] is not None
        or
        classificacao["durabilidade"] is not None
    ):

        st.markdown(
            "#### Notas consolidadas atuais"
        )

        c1, c2, c3 = st.columns(3)

        with c1:

            st.metric(
                "Estrutural",
                (
                    classificacao["estrutural"]
                    if classificacao["estrutural"]
                    is not None
                    else "—"
                )
            )

        with c2:

            st.metric(
                "Funcional",
                (
                    classificacao["funcional"]
                    if classificacao["funcional"]
                    is not None
                    else "NA"
                )
            )

        with c3:

            st.metric(
                "Durabilidade",
                (
                    classificacao["durabilidade"]
                    if classificacao["durabilidade"]
                    is not None
                    else "—"
                )
            )

    st.warning(
        "A quantidade de fotografias, isoladamente, "
        "não comprova que o levantamento fotográfico "
        "está completo."
    )


# ============================================================
# ANDAMENTO
# ============================================================

def mostrar_status_cadastral(
    oae_ativa,
    inspecao_ativa,
    cadastro
):

    st.subheader(
        "8️⃣ Andamento da inspeção cadastral"
    )

    documentos = (
        buscar_documentos_cadastrais(
            cadastro.id
        )
    )

    croquis = (
        buscar_croquis_cadastrais(
            cadastro.id
        )
    )

    fotos = contar_fotos_inspecao(
        oae_ativa.id,
        inspecao_ativa.id
    )

    classificacao = (
        verificar_andamento_classificacao(
            oae_ativa.id,
            inspecao_ativa.id
        )
    )

    mapa_status = buscar_mapa_status(
        cadastro.id
    )

    documentos_registrados = len(
        documentos
    )

    croquis_resolvidos = sum(
        1
        for croqui in croquis
        if croqui.situacao in [
            "Anexado",
            "Não se aplica"
        ]
    )

    # Um bloco é considerado "verificado" quando há registros
    # de situação para os seus campos principais, mesmo que o
    # resultado seja "não informado" ou "não se aplica".
    campos_estrutura = [
        "largura_total",
        "largura_util",
        "sistema_construtivo",
        "natureza_transposicao",
        "material",
        "secao_tipo",
        "tipologia_longitudinal_superestrutura",
        "tipologia_transversal_superestrutura",
        "tipologia_mesoestrutura",
        "tipologia_infraestrutura",
        "numero_apoios",
        "numero_pilares_por_apoio",
        "comprimento_vao_tipico",
        "comprimento_vao_maior",
        "altura_pilares",
        "aparelhos_apoio",
        "juntas_dilatacao",
        "encontros",
        "taludes",
        "outras_peculiaridades"
    ]

    campos_funcionais = [
        "caracteristicas_planialtimetricas",
        "numero_faixas",
        "largura_faixa",
        "acostamento_situacao",
        "largura_acostamento",
        "refugio_situacao",
        "largura_refugio",
        "passeio_passarela_situacao",
        "largura_passeio_passarela",
        "barreira_rigida_situacao",
        "guarda_corpos_situacao",
        "pavimento_via_permanente",
        "drenos_situacao",
        "pingadeiras_situacao",
        "gabarito_vertical_sob_oae",
        "gabarito_vertical_sobre_oae",
        "gabarito_navegavel_situacao",
        "gabarito_navegavel_altura",
        "gabarito_navegavel_largura",
        "frequencia_carga_especial",
        "pbt_maximo",
        "carga_maxima_eixo",
        "volume_medio_diario",
        "ano_referencia_vmd"
    ]

    estrutura_verificada = all(
        campo in mapa_status
        for campo in campos_estrutura
    )

    funcional_verificada = all(
        campo in mapa_status
        for campo in campos_funcionais
    )

    identificacao_iniciada = any(
        [
            cadastro.jurisdicao,
            cadastro.administracao,
            cadastro.sentido,
            cadastro.localizacao_quilometro_endereco
        ]
    )

    st.checkbox(
        "Identificação e localização iniciadas",
        value=identificacao_iniciada,
        disabled=True
    )

    st.checkbox(
        "Características estruturais verificadas",
        value=estrutura_verificada,
        disabled=True
    )

    st.checkbox(
        "Características funcionais verificadas",
        value=funcional_verificada,
        disabled=True
    )

    st.checkbox(
        "Documentos iniciais verificados",
        value=(
            documentos_registrados
            == len(TIPOS_DOCUMENTOS)
        ),
        disabled=True
    )

    st.caption(
        f"Documentos com situação registrada: "
        f"{documentos_registrados}/"
        f"{len(TIPOS_DOCUMENTOS)}"
    )

    st.checkbox(
        "Croquis verificados",
        value=(
            croquis_resolvidos
            == len(TIPOS_CROQUIS)
        ),
        disabled=True
    )

    st.caption(
        f"Croquis resolvidos: "
        f"{croquis_resolvidos}/"
        f"{len(TIPOS_CROQUIS)}"
    )

    st.checkbox(
        "Classificação dos componentes concluída",
        value=classificacao[
            "concluida"
        ],
        disabled=True
    )

    st.checkbox(
        "Mínimo de oito registros fotográficos atingido",
        value=fotos >= 8,
        disabled=True
    )

    st.info(
        "Um campo marcado como 'Não informado', "
        "'Não verificado' ou 'Não se aplica' é considerado "
        "tratado pelo formulário, mas não como dado informado. "
        "A conclusão técnica permanece sob responsabilidade "
        "do inspetor."
    )


# ============================================================
# PREENCHIMENTO
# ============================================================

def mostrar_preenchimento_cadastral(
    oae_ativa,
    inspecao_ativa
):

    if inspecao_ativa is None:

        st.info(
            "Selecione uma inspeção cadastral."
        )

        return

    if (
        inspecao_ativa.tipo_inspecao
        != "Cadastral"
    ):

        st.warning(
            "A inspeção ativa não é do tipo Cadastral."
        )

        return

    cadastro = buscar_inspecao_cadastral(
        inspecao_ativa.id
    )

    if cadastro is None:

        db = SessionLocal()

        cadastro = models.InspecaoCadastral(
            inspecao_id=inspecao_ativa.id
        )

        db.add(cadastro)
        db.commit()
        db.close()

        cadastro = buscar_inspecao_cadastral(
            inspecao_ativa.id
        )

    st.write(
        f"**Inspeção:** "
        f"{inspecao_ativa.data_inspecao.strftime('%d/%m/%Y')}"
    )

    mensagem_cadastral = st.session_state.pop(
        "_mensagem_cadastral",
        None
    )

    if mensagem_cadastral:

        st.success(
            mensagem_cadastral,
            icon="✅"
        )


    detalhe = buscar_detalhe_inspecao(
        inspecao_ativa.id
    )

    if detalhe is not None:

        st.write(
            "**Motivo:**",
            (
                detalhe.motivo_cadastral
                or "Não informado"
            )
        )

        if detalhe.descricao_alteracao:

            st.write(
                "**Alteração registrada:**",
                detalhe.descricao_alteracao
            )

    st.divider()

    abas = st.tabs(
        [
            "📍 Identificação",
            "🏗️ Estrutura",
            "🛣️ Funcional",
            "🌱 Ambiental",
            "📂 Documentos",
            "📐 Croquis",
            "🔗 Registros vinculados",
            "✅ Andamento"
        ]
    )

    with abas[0]:

        mostrar_identificacao_localizacao(
            oae_ativa,
            inspecao_ativa,
            cadastro
        )

    with abas[1]:

        mostrar_caracteristicas_estruturais(
            oae_ativa,
            cadastro
        )

    with abas[2]:

        mostrar_caracteristicas_funcionais(
            cadastro
        )

    with abas[3]:

        mostrar_caracteristicas_ambientais(
            cadastro
        )

    with abas[4]:

        mostrar_documentos(
            cadastro
        )

    with abas[5]:

        mostrar_croquis(
            cadastro
        )

    with abas[6]:

        mostrar_integracoes(
            oae_ativa,
            inspecao_ativa
        )

    with abas[7]:

        mostrar_status_cadastral(
            oae_ativa,
            inspecao_ativa,
            cadastro
        )


# ============================================================
# MÓDULO PRINCIPAL
# ============================================================

def mostrar_modulo_cadastral(
    oae_ativa,
    inspecao_ativa=None
):

    st.header(
        "🟦 Inspeção Cadastral"
    )

    st.caption(
        "Módulo específico para registro da inspeção "
        "cadastral da OAE."
    )

    if oae_ativa is None:

        st.warning(
            "Selecione ou cadastre uma OAE."
        )

        return

    tab1, tab2 = st.tabs(
        [
            "➕ Nova inspeção cadastral",
            "📝 Preencher inspeção cadastral"
        ]
    )

    with tab1:

        mostrar_nova_inspecao_cadastral(
            oae_ativa
        )

    with tab2:

        cadastrais = (
            buscar_inspecoes_cadastrais(
                oae_ativa.id
            )
        )

        if len(cadastrais) == 0:

            st.info(
                "Nenhuma inspeção cadastral cadastrada "
                "para esta OAE."
            )

        else:

            ids = [
                item.id
                for item in cadastrais
            ]

            mapa = {
                item.id:
                    (
                        f"{numero} - "
                        f"{item.data_inspecao.strftime('%d/%m/%Y')}"
                    )
                for numero, item in enumerate(
                    sorted(
                        cadastrais,
                        key=lambda item: (
                            item.data_inspecao,
                            item.id
                        )
                    ),
                    start=1
                )
            }

            id_padrao = ids[0]

            if (
                inspecao_ativa is not None
                and
                inspecao_ativa.id in ids
            ):

                id_padrao = (
                    inspecao_ativa.id
                )

            selecionada_id = st.selectbox(
                "Inspeção cadastral",
                options=ids,
                format_func=lambda x:
                    mapa[x],
                index=ids.index(
                    id_padrao
                ),
                key="cadastral_selecionada"
            )

            db = SessionLocal()

            selecionada = (
                db.query(models.Inspecao)
                .filter(
                    models.Inspecao.id
                    == selecionada_id
                )
                .first()
            )

            db.close()

            mostrar_preenchimento_cadastral(
                oae_ativa,
                selecionada
            )