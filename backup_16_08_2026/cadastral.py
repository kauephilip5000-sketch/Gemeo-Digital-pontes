import streamlit as st
from pathlib import Path
from uuid import uuid4

from sqlalchemy import Column, Integer, String, ForeignKey, UniqueConstraint

from database import Base, SessionLocal
import models
from classificacao import calcular_classificacao_consolidada, verificar_andamento_classificacao


# ============================================================
# INSPEÇÃO CADASTRAL - ABNT NBR 9452:2023 - ANEXO A
# ============================================================

class CampoCadastralStatus(Base):
    __tablename__ = "campos_cadastrais_status"
    __table_args__ = (
        UniqueConstraint(
            "inspecao_cadastral_id",
            "campo",
            name="uq_status_campo_cadastral",
        ),
    )

    id = Column(Integer, primary_key=True, index=True)
    inspecao_cadastral_id = Column(
        Integer,
        ForeignKey("inspecoes_cadastrais.id"),
        nullable=False,
    )
    campo = Column(String, nullable=False)
    situacao = Column(String, nullable=False)


SITUACOES_CAMPO = ["Informado", "Não informado", "Não se aplica", "Não verificado"]

TIPOS_DOCUMENTOS = [
    "Dados de projeto, desenhos, memoriais e especificações",
    "Registros de execução da OAE",
    "Termo de recebimento da OAE",
    "Registros de inspeções anteriores",
    "Registros de monitoramento da estrutura",
    "Registros de alargamentos, reforços, reparos, recuperações ou modificações",
]

SITUACOES_DOCUMENTO = ["Disponível", "Não localizado", "Não se aplica", "Não verificado"]

TIPOS_CROQUIS = [
    "Planta do tabuleiro",
    "Corte longitudinal",
    "Corte transversal",
    "Detalhes adicionais",
]

PASTA_DOCUMENTOS = Path("uploads/cadastral/documentos")
PASTA_CROQUIS = Path("uploads/cadastral/croquis")
PASTA_DOCUMENTOS.mkdir(parents=True, exist_ok=True)
PASTA_CROQUIS.mkdir(parents=True, exist_ok=True)


CAMPOS_ESTRUTURA = [
    ("📐 Dimensões principais", [
        ("largura_total", "Largura total (m)", "numero", "Ex.: 12,80 m"),
        ("largura_util", "Largura útil (m)", "numero", "Ex.: 10,80 m"),
    ]),
    ("🏗️ Tipologia estrutural", [
        ("sistema_construtivo", "Sistema construtivo", "texto", "Ex.: vigas pré-moldadas protendidas"),
        ("natureza_transposicao", "Natureza da transposição", "texto", "Ex.: curso d'água, rodovia, ferrovia"),
        ("material", "Material", "texto", "Ex.: concreto protendido"),
        ("secao_tipo", "Seção-tipo", "texto", "Ex.: vigas I com laje superior"),
        ("tipologia_longitudinal_superestrutura", "Tipologia longitudinal da superestrutura", "texto", "Ex.: vigas simplesmente apoiadas"),
        ("tipologia_transversal_superestrutura", "Tipologia transversal da superestrutura", "texto", "Ex.: quatro longarinas e laje"),
        ("tipologia_mesoestrutura", "Tipologia da mesoestrutura", "texto", "Ex.: pilares de concreto armado com travessa"),
        ("tipologia_infraestrutura", "Tipologia da infraestrutura", "texto", "Ex.: blocos sobre estacas"),
    ]),
    ("🔢 Geometria e apoios", [
        ("numero_apoios", "Número de apoios", "inteiro", ""),
        ("numero_pilares_por_apoio", "Número de pilares por apoio", "inteiro", ""),
        ("comprimento_vao_tipico", "Comprimento do vão típico (m)", "numero", ""),
        ("comprimento_vao_maior", "Comprimento do maior vão (m)", "numero", ""),
        ("altura_pilares", "Altura dos pilares (m)", "numero", ""),
    ]),
    ("🧩 Elementos complementares", [
        ("aparelhos_apoio", "Aparelhos de apoio - quantidade e tipo", "area", "Ex.: 8 aparelhos de apoio elastoméricos"),
        ("juntas_dilatacao", "Juntas de dilatação - quantidade e tipo", "area", "Ex.: 2 juntas elastoméricas"),
        ("encontros", "Encontros", "area", "Ex.: encontros em concreto armado"),
        ("taludes", "Taludes", "area", "Ex.: taludes gramados, sem erosão aparente"),
        ("outras_peculiaridades", "Outras peculiaridades", "area", "Ex.: dente Gerber, acesso à seção celular etc."),
    ]),
]

CAMPOS_FUNCIONAIS = [
    ("🛣️ Características da pista", [
        ("caracteristicas_planialtimetricas", "Características plani-altimétricas", "area", "Ex.: região ondulada, traçado em curva, rampa de 2,5%"),
        ("numero_faixas", "Número de faixas / vias", "inteiro", ""),
        ("largura_faixa", "Largura da faixa / via (m)", "numero", ""),
        ("acostamento_situacao", "Acostamento", "texto", "Ex.: existe em ambos os lados"),
        ("largura_acostamento", "Largura do acostamento (m)", "numero", ""),
        ("refugio_situacao", "Refúgio", "texto", "Ex.: refúgio lateral"),
        ("largura_refugio", "Largura do refúgio (m)", "numero", ""),
        ("passeio_passarela_situacao", "Passeio / passarela", "texto", "Ex.: passeio lateral para pedestres"),
        ("largura_passeio_passarela", "Largura do passeio / passarela (m)", "numero", ""),
    ]),
    ("🧱 Elementos funcionais", [
        ("barreira_rigida_situacao", "Barreira rígida", "texto", "Ex.: barreira New Jersey"),
        ("guarda_corpos_situacao", "Guarda-corpos", "texto", "Ex.: guarda-corpo metálico"),
        ("pavimento_via_permanente", "Pavimento / via permanente", "area", "Ex.: revestimento asfáltico"),
        ("drenos_situacao", "Drenos", "texto", "Ex.: buzinotes distribuídos no tabuleiro"),
        ("pingadeiras_situacao", "Pingadeiras", "texto", "Ex.: existentes"),
    ]),
    ("📏 Gabaritos", [
        ("gabarito_vertical_sob_oae", "Gabarito vertical sob a OAE (m)", "numero", ""),
        ("gabarito_vertical_sobre_oae", "Gabarito vertical sobre a OAE (m)", "numero", ""),
        ("gabarito_navegavel_situacao", "Gabarito navegável", "texto", "Ex.: canal navegável sinalizado"),
        ("gabarito_navegavel_altura", "Altura do gabarito navegável (m)", "numero", ""),
        ("gabarito_navegavel_largura", "Largura do gabarito navegável (m)", "numero", ""),
    ]),
    ("🚛 Tráfego", [
        ("frequencia_carga_especial", "Frequência de passagem de carga especial", "texto", "Ex.: eventual / mensal"),
        ("pbt_maximo", "PBT máximo", "numero", ""),
        ("carga_maxima_eixo", "Carga máxima por eixo", "numero", ""),
        ("volume_medio_diario", "Volume médio diário - VMD", "numero", ""),
        ("ano_referencia_vmd", "Ano de referência do VMD", "inteiro", ""),
    ]),
]


# ============================================================
# CONSULTAS
# ============================================================

def buscar_inspecoes_cadastrais(oae_id):
    db = SessionLocal()
    dados = (
        db.query(models.Inspecao)
        .filter(models.Inspecao.oae_id == oae_id)
        .filter(models.Inspecao.tipo_inspecao == "Cadastral")
        .order_by(models.Inspecao.data_inspecao.desc(), models.Inspecao.id.desc())
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
        .filter(models.InspecaoCadastral.inspecao_id == inspecao_id)
        .first()
    )
    db.close()
    return dado


def buscar_detalhe_inspecao(inspecao_id):
    db = SessionLocal()
    dado = (
        db.query(models.DetalheInspecao)
        .filter(models.DetalheInspecao.inspecao_id == inspecao_id)
        .first()
    )
    db.close()
    return dado


def buscar_documentos_cadastrais(cadastro_id):
    db = SessionLocal()
    dados = (
        db.query(models.DocumentoCadastral)
        .filter(models.DocumentoCadastral.inspecao_cadastral_id == cadastro_id)
        .order_by(models.DocumentoCadastral.id)
        .all()
    )
    db.close()
    return dados


def buscar_croquis_cadastrais(cadastro_id):
    db = SessionLocal()
    dados = (
        db.query(models.CroquiCadastral)
        .filter(models.CroquiCadastral.inspecao_cadastral_id == cadastro_id)
        .order_by(models.CroquiCadastral.id)
        .all()
    )
    db.close()
    return dados


def buscar_mapa_status(cadastro_id):
    db = SessionLocal()
    dados = (
        db.query(CampoCadastralStatus)
        .filter(CampoCadastralStatus.inspecao_cadastral_id == cadastro_id)
        .all()
    )
    db.close()
    return {item.campo: item.situacao for item in dados}


def contar_fotos_inspecao(oae_id, inspecao_id):
    db = SessionLocal()
    quantidade = (
        db.query(models.Fotografia)
        .filter(models.Fotografia.oae_id == oae_id)
        .filter(models.Fotografia.inspecao_id == inspecao_id)
        .count()
    )
    db.close()
    return quantidade


def contar_observacoes_anomalias(inspecao_id):
    db = SessionLocal()
    quantidade = (
        db.query(models.ObservacaoAnomalia)
        .filter(models.ObservacaoAnomalia.inspecao_id == inspecao_id)
        .count()
    )
    db.close()
    return quantidade


# ============================================================
# STATUS E CAMPOS CONDICIONAIS
# ============================================================

def inferir_situacao(mapa_status, campo, valor_atual):
    if campo in mapa_status and mapa_status[campo] in SITUACOES_CAMPO:
        return mapa_status[campo]
    if valor_atual not in [None, ""]:
        return "Informado"
    return "Não informado"


def salvar_status(db, cadastro_id, campo, situacao):
    registro = (
        db.query(CampoCadastralStatus)
        .filter(CampoCadastralStatus.inspecao_cadastral_id == cadastro_id)
        .filter(CampoCadastralStatus.campo == campo)
        .first()
    )
    if registro is None:
        db.add(
            CampoCadastralStatus(
                inspecao_cadastral_id=cadastro_id,
                campo=campo,
                situacao=situacao,
            )
        )
    else:
        registro.situacao = situacao


def campo_condicional(cadastro, mapa_status, config, prefixo):
    campo, label, tipo, placeholder = config
    valor_atual = getattr(cadastro, campo)
    situacao_atual = inferir_situacao(mapa_status, campo, valor_atual)

    situacao = st.selectbox(
        f"{label} — situação do dado",
        SITUACOES_CAMPO,
        index=SITUACOES_CAMPO.index(situacao_atual),
        key=f"{prefixo}_{campo}_status",
    )

    if situacao != "Informado":
        st.caption(f"{label}: {situacao}.")
        return situacao, None

    if tipo == "inteiro":
        valor = st.number_input(
            label,
            min_value=0,
            value=int(valor_atual if valor_atual is not None else 0),
            step=1,
            key=f"{prefixo}_{campo}_valor",
        )
    elif tipo == "numero":
        valor = st.number_input(
            label,
            min_value=0.0,
            value=float(valor_atual if valor_atual is not None else 0.0),
            step=1.0 if campo == "volume_medio_diario" else 0.1,
            key=f"{prefixo}_{campo}_valor",
        )
    elif tipo == "area":
        valor = st.text_area(
            label,
            value=valor_atual or "",
            placeholder=placeholder,
            key=f"{prefixo}_{campo}_valor",
        )
    else:
        valor = st.text_input(
            label,
            value=valor_atual or "",
            placeholder=placeholder,
            key=f"{prefixo}_{campo}_valor",
        )

    return situacao, valor


def salvar_grupo_campos(cadastro_id, valores):
    db = SessionLocal()
    registro = db.query(models.InspecaoCadastral).filter(models.InspecaoCadastral.id == cadastro_id).first()

    if registro is None:
        db.close()
        return False

    for campo, (situacao, valor) in valores.items():
        salvar_status(db, cadastro_id, campo, situacao)
        setattr(registro, campo, valor if situacao == "Informado" else None)

    db.commit()
    db.close()
    return True


def salvar_arquivo(arquivo, pasta):
    if arquivo is None:
        return None, None

    extensao = Path(arquivo.name).suffix
    nome_interno = f"{uuid4().hex}{extensao}"
    caminho = pasta / nome_interno

    with open(caminho, "wb") as destino:
        destino.write(arquivo.getbuffer())

    return arquivo.name, str(caminho)


# ============================================================
# NOVA INSPEÇÃO CADASTRAL
# ============================================================

def mostrar_nova_inspecao_cadastral(oae_ativa):
    st.subheader("🟦 Nova inspeção cadastral")
    st.info(
        "A inspeção cadastral corresponde à primeira inspeção da OAE "
        "e também deve ser realizada quando houver alteração na configuração da obra."
    )
    st.write(f"**OAE:** {oae_ativa.id} - {oae_ativa.nome}")

    cadastrais = buscar_inspecoes_cadastrais(oae_ativa.id)
    ja_possui_cadastral = len(cadastrais) > 0

    if ja_possui_cadastral:
        ultima = cadastrais[0]
        st.warning(
            "Esta OAE já possui inspeção cadastral registrada em "
            f"{ultima.data_inspecao.strftime('%d/%m/%Y')}. "
            "Uma nova inspeção cadastral deve estar associada a uma alteração da configuração da obra."
        )

    data_inspecao = st.date_input("Data da inspeção", format="DD/MM/YYYY", key="cad_nova_data")
    responsavel = st.text_input("Inspetor responsável", placeholder="Ex.: João da Silva", key="cad_nova_responsavel")
    registro_profissional = st.text_input(
        "Registro profissional",
        placeholder="Ex.: CREA-GO 123456/D",
        help="Registro profissional do responsável pela inspeção.",
        key="cad_nova_registro",
    )

    if ja_possui_cadastral:
        motivo = "Alteração na configuração da obra"
        st.text_input("Motivo da inspeção cadastral", value=motivo, disabled=True, key="cad_nova_motivo_bloqueado")
    else:
        motivo = st.selectbox(
            "Motivo da inspeção cadastral",
            ["Primeira inspeção da OAE", "Alteração na configuração da obra"],
            key="cad_nova_motivo",
        )

    descricao_alteracao = ""
    if motivo == "Alteração na configuração da obra":
        descricao_alteracao = st.text_area(
            "Descrição da alteração",
            placeholder="Ex.: alargamento do tabuleiro, reforço estrutural, alteração de dimensões ou mudança do sistema estrutural.",
            key="cad_nova_alteracao",
        )

    observacoes = st.text_area(
        "Observações gerais da inspeção",
        placeholder="Ex.: acesso parcial à face inferior do tabuleiro.",
        key="cad_nova_observacoes",
    )

    if not st.button("Criar inspeção cadastral", type="primary", key="cad_criar_inspecao"):
        return

    if responsavel.strip() == "":
        st.error("Informe o inspetor responsável.")
        return

    if motivo == "Alteração na configuração da obra" and descricao_alteracao.strip() == "":
        st.error("Descreva a alteração que motivou a nova inspeção cadastral.")
        return

    db = SessionLocal()

    nova_inspecao = models.Inspecao(
        oae_id=oae_ativa.id,
        tipo_inspecao="Cadastral",
        data_inspecao=data_inspecao,
        responsavel=responsavel,
        registro_profissional=registro_profissional,
        observacoes=observacoes,
    )
    db.add(nova_inspecao)
    db.flush()

    db.add(
        models.DetalheInspecao(
            inspecao_id=nova_inspecao.id,
            motivo_cadastral=motivo,
            descricao_alteracao=descricao_alteracao,
        )
    )
    db.add(models.InspecaoCadastral(inspecao_id=nova_inspecao.id))

    db.commit()
    db.refresh(nova_inspecao)
    novo_id = nova_inspecao.id
    db.close()

    st.session_state.inspecao_ativa_id = novo_id
    st.success("Inspeção cadastral criada com sucesso.")
    st.rerun()


# ============================================================
# IDENTIFICAÇÃO
# ============================================================

def mostrar_identificacao_localizacao(oae_ativa, inspecao_ativa, cadastro):
    st.subheader("1️⃣ Identificação e localização")
    st.caption("Alguns dados são reaproveitados do cadastro principal da OAE.")

    c1, c2, c3 = st.columns(3)
    with c1:
        st.write("**OAE:**", oae_ativa.nome)
        st.write("**Código:**", oae_ativa.codigo or "Não informado")
    with c2:
        st.write("**Rodovia/Ferrovia:**", oae_ativa.rodovia or "Não informado")
        st.write("**Município/UF:**", f"{oae_ativa.municipio or ''} - {oae_ativa.uf or ''}")
    with c3:
        st.write("**Ano da construção:**", oae_ativa.ano_construcao or "Não informado")
        st.write("**Inspetor responsável:**", inspecao_ativa.responsavel or "Não informado")

    mapa_status = buscar_mapa_status(cadastro.id)
    situacao_atual = mapa_status.get("etapa_identificacao", "Em preenchimento")

    with st.form("form_cadastral_identificacao"):
        c1, c2 = st.columns(2)

        with c1:
            jurisdicao = st.text_input("Jurisdição", value=cadastro.jurisdicao or "", placeholder="Ex.: DNIT, DER-GO, concessionária")
            administracao = st.text_input("Administração", value=cadastro.administracao or "", placeholder="Ex.: DNIT - Superintendência Regional de Goiás")
            sentido = st.text_input("Sentido", value=cadastro.sentido or "", placeholder="Ex.: crescente / decrescente ou Catalão → Goiânia")
            localizacao = st.text_input("Localização - quilômetro ou endereço", value=cadastro.localizacao_quilometro_endereco or "", placeholder="Ex.: BR-050, km 278+500")
            projetista = st.text_input("Projetista", value=cadastro.projetista or "", placeholder="Ex.: XYZ Engenharia Ltda.")
            construtor = st.text_input("Construtor", value=cadastro.construtor or "", placeholder="Ex.: Construtora ABC Ltda.")

        with c2:
            latitude = st.text_input("Coordenada - latitude", value=cadastro.coordenada_latitude or "", placeholder="Ex.: -18.165432")
            longitude = st.text_input("Coordenada - longitude", value=cadastro.coordenada_longitude or "", placeholder="Ex.: -47.944210")
            trem_tipo = st.text_input("Trem-tipo provável", value=cadastro.trem_tipo_provavel or "", placeholder="Ex.: TB-45")
            importancia = st.text_input(
                "Importância",
                value=cadastro.importancia or "",
                placeholder="Ex.: ligação regional, corredor logístico",
                help="Descreva a importância da OAE. O software não impõe uma escala própria.",
            )
            finalidade = st.text_input("Finalidade / passagem sobre obstáculo", value=cadastro.finalidade or "", placeholder="Ex.: ponte sobre rio, viaduto rodoviário")
            desvio = st.text_area("Desvio ou rota alternativa", value=cadastro.desvio_rota_alternativa or "", placeholder="Ex.: desvio pela GO-330, acréscimo aproximado de 18 km.")

        situacao_identificacao = st.selectbox(
            "Situação desta etapa",
            ["Em preenchimento", "Verificada pelo inspetor"],
            index=1 if situacao_atual == "Verificada pelo inspetor" else 0,
            help="Marque como verificada somente após conferir os dados desta etapa.",
        )
        salvar = st.form_submit_button("Salvar identificação e localização")

    if not salvar:
        return

    db = SessionLocal()
    registro = db.query(models.InspecaoCadastral).filter(models.InspecaoCadastral.id == cadastro.id).first()

    registro.jurisdicao = jurisdicao
    registro.administracao = administracao
    registro.sentido = sentido
    registro.localizacao_quilometro_endereco = localizacao
    registro.projetista = projetista
    registro.construtor = construtor
    registro.coordenada_latitude = latitude
    registro.coordenada_longitude = longitude
    registro.trem_tipo_provavel = trem_tipo
    registro.importancia = importancia if importancia.strip() else None
    registro.finalidade = finalidade
    registro.desvio_rota_alternativa = desvio

    salvar_status(db, cadastro.id, "etapa_identificacao", situacao_identificacao)
    db.commit()
    db.close()

    st.success("Identificação e localização salvas.")
    st.rerun()


# ============================================================
# ESTRUTURA E FUNCIONAL
# ============================================================

def mostrar_grupo_campos(cadastro, grupos, prefixo):
    mapa_status = buscar_mapa_status(cadastro.id)
    valores = {}

    for indice, (nome_grupo, campos) in enumerate(grupos):
        with st.expander(nome_grupo, expanded=(indice == 0)):
            if nome_grupo == "🚛 Tráfego":
                st.caption(
                    "A ficha cadastral inclui informações de tráfego. "
                    "Quando o dado não estiver disponível, registre 'Não informado' ou 'Não verificado'."
                )

            colunas = st.columns(2)
            for i, config in enumerate(campos):
                with colunas[i % 2]:
                    valores[config[0]] = campo_condicional(cadastro, mapa_status, config, prefixo)

    return valores


def mostrar_caracteristicas_estruturais(oae_ativa, cadastro):
    st.subheader("2️⃣ Características da estrutura")
    st.info(
        "Quando o dado estiver disponível, selecione 'Informado' e preencha o valor. "
        "Não use 0 para representar informação desconhecida."
    )

    st.markdown("##### Dados já disponíveis no cadastro da OAE")
    c1, c2, c3 = st.columns(3)

    with c1:
        st.metric(
            "Comprimento total",
            f"{oae_ativa.comprimento_total:.2f} m" if oae_ativa.comprimento_total is not None else "Não informado",
        )
    with c2:
        st.metric(
            "Largura cadastrada",
            f"{oae_ativa.largura:.2f} m" if oae_ativa.largura is not None else "Não informada",
        )
    with c3:
        st.metric("Número de vãos", oae_ativa.numero_vaos if oae_ativa.numero_vaos is not None else "Não informado")

    st.caption("Esses dados são reaproveitados da OAE.")
    valores = mostrar_grupo_campos(cadastro, CAMPOS_ESTRUTURA, "estrutura")

    if st.button("💾 Salvar características estruturais", type="primary", key="salvar_cadastral_estrutura"):
        if salvar_grupo_campos(cadastro.id, valores):
            st.success("Características estruturais salvas.")
            st.rerun()
        st.error("Não foi possível salvar os dados.")


def mostrar_caracteristicas_funcionais(cadastro):
    st.subheader("3️⃣ Características funcionais")
    st.info(
        "Os dados funcionais são preenchidos conforme a aplicabilidade. "
        "Quando possuir a informação, selecione 'Informado' para liberar o campo de valor."
    )

    valores = mostrar_grupo_campos(cadastro, CAMPOS_FUNCIONAIS, "funcional")

    if st.button("💾 Salvar características funcionais", type="primary", key="salvar_cadastral_funcional"):
        if salvar_grupo_campos(cadastro.id, valores):
            st.success("Características funcionais salvas.")
            st.rerun()
        st.error("Não foi possível salvar os dados.")


# ============================================================
# AMBIENTAL
# ============================================================

def mostrar_caracteristicas_ambientais(cadastro):
    st.subheader("4️⃣ Características ambientais")
    st.info(
        "Registre apenas as informações aplicáveis e disponíveis. "
        "A caracterização ambiental é separada das informações complementares e recomendações."
    )

    mapa_status = buscar_mapa_status(cadastro.id)

    with st.expander("🌱 Características ambientais", expanded=True):
        opcoes_agressividade = ["Não informada", "Fraca", "Moderada", "Forte", "Muito forte"]
        agressividade_atual = cadastro.grau_agressividade_ambiental or "Não informada"
        if agressividade_atual not in opcoes_agressividade:
            agressividade_atual = "Não informada"

        agressividade = st.selectbox(
            "Grau de agressividade ambiental",
            opcoes_agressividade,
            index=opcoes_agressividade.index(agressividade_atual),
            help="A ficha cadastral remete à ABNT NBR 6118 para esta caracterização.",
            key="cad_ambiental_agressividade",
        )

        opcoes_curso = ["Não verificado", "Sim", "Não", "Não se aplica"]
        curso_atual = cadastro.curso_agua_aplicavel or "Não verificado"
        if curso_atual not in opcoes_curso:
            curso_atual = "Não verificado"

        curso_agua = st.selectbox(
            "Curso d'água aplicável",
            opcoes_curso,
            index=opcoes_curso.index(curso_atual),
            key="cad_ambiental_curso",
        )

        nome_curso = None
        inundacao = None

        if curso_agua == "Sim":
            nome_curso = st.text_input(
                "Nome do curso d'água",
                value=cadastro.nome_curso_agua or "",
                placeholder="Ex.: Rio São Marcos",
                key="cad_ambiental_nome_curso",
            )
            inundacao = st.text_area(
                "Histórico de inundação no local da OAE",
                value=cadastro.historico_inundacao or "",
                placeholder="Ex.: sem registros conhecidos ou descrever eventos conhecidos.",
                key="cad_ambiental_inundacao",
            )
        elif curso_agua == "Não verificado":
            st.caption("Curso d'água ainda não verificado.")
        else:
            st.caption(f"Curso d'água: {curso_agua}.")

    with st.expander("📝 Informações complementares e recomendações", expanded=False):
        informacoes = st.text_area(
            "Informações complementares",
            value=cadastro.informacoes_complementares or "",
            placeholder="Registre outras informações relevantes para a caracterização cadastral.",
            key="cad_ambiental_complementares",
        )
        recomendacoes = st.text_area(
            "Recomendações terapêuticas",
            value=cadastro.recomendacoes_terapeuticas or "",
            placeholder="Ex.: limpeza de drenos, recuperação localizada ou outra recomendação definida pelo responsável.",
            key="cad_ambiental_recomendacoes",
        )
        observacoes = st.text_area(
            "Observações do cadastro",
            value=cadastro.observacoes_cadastro or "",
            placeholder="Observações adicionais sobre o preenchimento.",
            key="cad_ambiental_observacoes",
        )

    situacao_atual = mapa_status.get("etapa_ambiental", "Em preenchimento")
    situacao_ambiental = st.selectbox(
        "Situação da etapa ambiental",
        ["Em preenchimento", "Verificada pelo inspetor"],
        index=1 if situacao_atual == "Verificada pelo inspetor" else 0,
        key="cad_ambiental_etapa",
    )

    if not st.button("💾 Salvar dados ambientais e complementares", type="primary", key="salvar_cadastral_ambiental"):
        return

    db = SessionLocal()
    registro = db.query(models.InspecaoCadastral).filter(models.InspecaoCadastral.id == cadastro.id).first()

    registro.grau_agressividade_ambiental = agressividade if agressividade != "Não informada" else None
    registro.curso_agua_aplicavel = curso_agua

    if curso_agua == "Sim":
        registro.nome_curso_agua = nome_curso
        registro.historico_inundacao = inundacao
    else:
        registro.nome_curso_agua = None
        registro.historico_inundacao = None

    registro.informacoes_complementares = informacoes
    registro.recomendacoes_terapeuticas = recomendacoes
    registro.observacoes_cadastro = observacoes

    salvar_status(db, cadastro.id, "etapa_ambiental", situacao_ambiental)
    db.commit()
    db.close()

    st.success("Dados ambientais e complementares salvos.")
    st.rerun()


# ============================================================
# DOCUMENTOS
# ============================================================

def mostrar_documentos(cadastro):
    st.subheader("5️⃣ Documentos iniciais")
    st.caption(
        "Registre a situação de cada documento. A ausência de um documento não impede "
        "o registro da inspeção; ela deve ficar documentada."
    )

    ajudas = {
        TIPOS_DOCUMENTOS[0]: "Ex.: projeto estrutural, desenhos de forma, memorial e especificações disponíveis.",
        TIPOS_DOCUMENTOS[1]: "Ex.: alterações durante a construção, ensaios de materiais e proteções aplicadas.",
        TIPOS_DOCUMENTOS[2]: "Registre se o termo está disponível, não foi localizado ou não se aplica.",
        TIPOS_DOCUMENTOS[3]: "Quando houver, registre relatórios ou fichas de inspeções anteriores.",
        TIPOS_DOCUMENTOS[4]: "Quando houver, registre dados de instrumentação ou monitoramento anterior.",
        TIPOS_DOCUMENTOS[5]: "Registre intervenções ou modificações anteriores da OAE, quando existirem.",
    }

    existentes = buscar_documentos_cadastrais(cadastro.id)
    mapa = {item.tipo_documento: item for item in existentes}

    for indice, tipo in enumerate(TIPOS_DOCUMENTOS, start=1):
        existente = mapa.get(tipo)

        with st.expander(f"{indice}. {tipo}", expanded=False):
            st.caption(ajudas.get(tipo, ""))

            situacao_atual = existente.situacao if existente is not None else "Não verificado"
            if situacao_atual not in SITUACOES_DOCUMENTO:
                situacao_atual = "Não verificado"

            descricao_atual = existente.descricao if existente is not None and existente.descricao else ""

            with st.form(f"form_documento_{indice}"):
                situacao = st.selectbox(
                    "Situação",
                    SITUACOES_DOCUMENTO,
                    index=SITUACOES_DOCUMENTO.index(situacao_atual),
                )
                descricao = st.text_area(
                    "Descrição / observações",
                    value=descricao_atual,
                    placeholder="Ex.: documento disponível em PDF; não localizado no acervo; não se aplica.",
                )
                arquivo = st.file_uploader("Anexar documento", key=f"arquivo_documento_{indice}")
                salvar = st.form_submit_button("Salvar documento")

            if salvar:
                nome_arquivo = None
                caminho_arquivo = None

                if arquivo is not None:
                    nome_arquivo, caminho_arquivo = salvar_arquivo(arquivo, PASTA_DOCUMENTOS)

                db = SessionLocal()
                registro = (
                    db.query(models.DocumentoCadastral)
                    .filter(models.DocumentoCadastral.inspecao_cadastral_id == cadastro.id)
                    .filter(models.DocumentoCadastral.tipo_documento == tipo)
                    .first()
                )

                if registro is None:
                    db.add(
                        models.DocumentoCadastral(
                            inspecao_cadastral_id=cadastro.id,
                            tipo_documento=tipo,
                            situacao=situacao,
                            descricao=descricao,
                            nome_arquivo=nome_arquivo,
                            caminho_arquivo=caminho_arquivo,
                        )
                    )
                else:
                    registro.situacao = situacao
                    registro.descricao = descricao
                    if nome_arquivo is not None:
                        registro.nome_arquivo = nome_arquivo
                        registro.caminho_arquivo = caminho_arquivo

                db.commit()
                db.close()
                st.success("Documento atualizado.")
                st.rerun()

            if existente is not None:
                st.write("**Situação atual:**", existente.situacao)
                if existente.nome_arquivo:
                    st.write("**Arquivo anexado:**", existente.nome_arquivo)


# ============================================================
# CROQUIS
# ============================================================

def mostrar_croquis(cadastro):
    st.subheader("6️⃣ Croquis")
    st.caption(
        "Registre os croquis previstos para a inspeção cadastral. "
        "Detalhes adicionais são utilizados quando pertinentes."
    )

    ajudas = {
        "Planta do tabuleiro": "Ex.: largura, faixas, identificação dos vãos e elementos principais.",
        "Corte longitudinal": "Ex.: vãos, apoios, encontros e cotas principais.",
        "Corte transversal": "Ex.: largura total, faixas, passeios, barreiras e disposição dos elementos principais.",
        "Detalhes adicionais": "Ex.: dente Gerber, aparelhos de apoio, seção celular ou outro detalhe relevante.",
    }

    existentes = buscar_croquis_cadastrais(cadastro.id)
    mapa = {item.tipo_croqui: item for item in existentes}

    for indice, tipo in enumerate(TIPOS_CROQUIS, start=1):
        existente = mapa.get(tipo)

        with st.expander(tipo, expanded=False):
            st.caption(ajudas.get(tipo, ""))

            opcoes = ["Anexado", "Pendente", "Não se aplica"] if tipo == "Detalhes adicionais" else ["Anexado", "Pendente"]
            situacao_atual = existente.situacao if existente is not None else "Pendente"
            if situacao_atual not in opcoes:
                situacao_atual = "Pendente"

            descricao_atual = existente.descricao if existente is not None and existente.descricao else ""

            with st.form(f"form_croqui_{indice}"):
                situacao = st.selectbox("Situação", opcoes, index=opcoes.index(situacao_atual))
                descricao = st.text_area(
                    "Descrição",
                    value=descricao_atual,
                    placeholder="Ex.: croqui esquemático com dimensões principais.",
                )
                arquivo = st.file_uploader(
                    "Anexar croqui",
                    type=["pdf", "png", "jpg", "jpeg"],
                    key=f"arquivo_croqui_{indice}",
                )
                salvar = st.form_submit_button("Salvar croqui")

            if salvar:
                nome_arquivo = None
                caminho_arquivo = None

                if arquivo is not None:
                    nome_arquivo, caminho_arquivo = salvar_arquivo(arquivo, PASTA_CROQUIS)

                db = SessionLocal()
                registro = (
                    db.query(models.CroquiCadastral)
                    .filter(models.CroquiCadastral.inspecao_cadastral_id == cadastro.id)
                    .filter(models.CroquiCadastral.tipo_croqui == tipo)
                    .first()
                )

                if registro is None:
                    db.add(
                        models.CroquiCadastral(
                            inspecao_cadastral_id=cadastro.id,
                            tipo_croqui=tipo,
                            situacao=situacao,
                            descricao=descricao,
                            nome_arquivo=nome_arquivo,
                            caminho_arquivo=caminho_arquivo,
                        )
                    )
                else:
                    registro.situacao = situacao
                    registro.descricao = descricao
                    if nome_arquivo is not None:
                        registro.nome_arquivo = nome_arquivo
                        registro.caminho_arquivo = caminho_arquivo

                db.commit()
                db.close()
                st.success("Croqui atualizado.")
                st.rerun()

            if existente is not None:
                st.write("**Situação atual:**", existente.situacao)
                if existente.nome_arquivo:
                    st.write("**Arquivo anexado:**", existente.nome_arquivo)


# ============================================================
# REGISTROS VINCULADOS
# ============================================================

def mostrar_integracoes(oae_ativa, inspecao_ativa):
    st.subheader("7️⃣ Anomalias, classificação e fotografias")
    st.caption(
        "Esses registros permanecem nos módulos específicos do sistema "
        "e são vinculados à campanha de inspeção."
    )

    anomalias = contar_observacoes_anomalias(inspecao_ativa.id)
    fotos = contar_fotos_inspecao(oae_ativa.id, inspecao_ativa.id)
    andamento = verificar_andamento_classificacao(oae_ativa.id, inspecao_ativa.id)
    classificacao = calcular_classificacao_consolidada(oae_ativa.id, inspecao_ativa.id)

    cadastro = buscar_inspecao_cadastral(inspecao_ativa.id)
    mapa_status = buscar_mapa_status(cadastro.id) if cadastro is not None else {}

    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric("Anomalias registradas nesta inspeção", anomalias)
        if anomalias == 0:
            st.caption(
                "Nenhuma anomalia foi registrada nesta campanha. "
                "Isso não significa, por si só, que a verificação já foi realizada."
            )
    with c2:
        st.metric("Componentes classificados", f"{andamento['avaliados']}/{andamento['total']}")
    with c3:
        st.metric("Fotografias", f"{fotos}/8")
        if fotos >= 8:
            st.caption("Quantidade mínima de oito registros atingida.")
        else:
            st.caption(f"Faltam {8 - fotos} fotografia(s) para atingir oito registros.")

    st.divider()
    st.markdown("#### ⚠️ Verificação de anomalias")

    opcoes_anomalias = [
        "Não verificada",
        "Verificada - sem anomalias identificadas",
        "Verificada - anomalias registradas",
    ]
    atual_anomalias = mapa_status.get("verificacao_anomalias", "Não verificada")
    if atual_anomalias not in opcoes_anomalias:
        atual_anomalias = "Não verificada"

    verificacao_anomalias = st.selectbox(
        "Situação da verificação de anomalias",
        opcoes_anomalias,
        index=opcoes_anomalias.index(atual_anomalias),
        help="Este campo diferencia 'nenhuma anomalia encontrada' de 'ainda não verificado'.",
        key="cad_verificacao_anomalias",
    )

    if anomalias > 0 and verificacao_anomalias == "Verificada - sem anomalias identificadas":
        st.warning("Existem anomalias registradas nesta inspeção. Essa opção é incompatível com os registros.")
    if anomalias == 0 and verificacao_anomalias == "Verificada - anomalias registradas":
        st.warning("Nenhuma anomalia está registrada nesta inspeção.")

    st.markdown("#### 📷 Verificação do levantamento fotográfico")
    if fotos >= 8:
        st.success("A quantidade mínima de oito registros foi atingida.")
    else:
        st.warning("A quantidade mínima de oito registros ainda não foi atingida.")

    opcoes_fotos = ["Não verificada", "Verificada pelo inspetor"]
    atual_fotos = mapa_status.get("abrangencia_fotografica", "Não verificada")
    if atual_fotos not in opcoes_fotos:
        atual_fotos = "Não verificada"

    abrangencia_fotografica = st.selectbox(
        "Abrangência do levantamento fotográfico",
        opcoes_fotos,
        index=opcoes_fotos.index(atual_fotos),
        help="A contagem automática não substitui a conferência das vistas e elementos necessários.",
        key="cad_abrangencia_fotografica",
    )

    if st.button("💾 Salvar verificações desta etapa", type="primary", key="salvar_verificacoes_cadastral"):
        if anomalias > 0 and verificacao_anomalias == "Verificada - sem anomalias identificadas":
            st.error("Corrija a situação da verificação de anomalias.")
            return
        if anomalias == 0 and verificacao_anomalias == "Verificada - anomalias registradas":
            st.error("Registre as anomalias antes de confirmar essa situação.")
            return
        if cadastro is None:
            st.error("Não foi possível localizar o cadastro especializado desta inspeção.")
            return

        db = SessionLocal()
        salvar_status(db, cadastro.id, "verificacao_anomalias", verificacao_anomalias)
        salvar_status(db, cadastro.id, "abrangencia_fotografica", abrangencia_fotografica)
        db.commit()
        db.close()
        st.success("Verificações salvas.")
        st.rerun()

    if any([
        classificacao["estrutural"] is not None,
        classificacao["funcional"] is not None,
        classificacao["durabilidade"] is not None,
    ]):
        st.divider()
        st.markdown("#### ⭐ Notas consolidadas atuais")
        c1, c2, c3 = st.columns(3)

        with c1:
            st.metric("Estrutural", classificacao["estrutural"] if classificacao["estrutural"] is not None else "—")
        with c2:
            st.metric("Funcional", classificacao["funcional"] if classificacao["funcional"] is not None else "NA")
        with c3:
            st.metric("Durabilidade", classificacao["durabilidade"] if classificacao["durabilidade"] is not None else "—")

    st.info(
        "Para registrar ou editar esses dados, utilize os módulos "
        "⚠️ Anomalias, ⭐ Classificação e 📷 Fotografias no menu lateral."
    )


# ============================================================
# ANDAMENTO
# ============================================================

def mostrar_status_cadastral(oae_ativa, inspecao_ativa, cadastro):
    st.subheader("8️⃣ Andamento da inspeção cadastral")

    mapa_status = buscar_mapa_status(cadastro.id)
    documentos = buscar_documentos_cadastrais(cadastro.id)
    croquis = buscar_croquis_cadastrais(cadastro.id)
    fotos = contar_fotos_inspecao(oae_ativa.id, inspecao_ativa.id)
    anomalias = contar_observacoes_anomalias(inspecao_ativa.id)
    classificacao = verificar_andamento_classificacao(oae_ativa.id, inspecao_ativa.id)

    identificacao_ok = mapa_status.get("etapa_identificacao") == "Verificada pelo inspetor"

    campos_estrutura = [campo[0] for _, grupo in CAMPOS_ESTRUTURA for campo in grupo]
    campos_funcionais = [campo[0] for _, grupo in CAMPOS_FUNCIONAIS for campo in grupo]

    estrutura_ok = all(
        campo in mapa_status
        and mapa_status[campo] != "Não verificado"
        for campo in campos_estrutura
    )

    funcional_ok = all(
        campo in mapa_status
        and mapa_status[campo] != "Não verificado"
        for campo in campos_funcionais
    )

    ambiental_ok = mapa_status.get("etapa_ambiental") == "Verificada pelo inspetor"

    mapa_documentos = {
        item.tipo_documento: item.situacao
        for item in documentos
    }

    documentos_ok = all(
        tipo in mapa_documentos
        and mapa_documentos[tipo] != "Não verificado"
        for tipo in TIPOS_DOCUMENTOS
    )

    documentos_tratados = sum(
        1
        for tipo in TIPOS_DOCUMENTOS
        if tipo in mapa_documentos
        and mapa_documentos[tipo] != "Não verificado"
    )

    mapa_croquis = {item.tipo_croqui: item.situacao for item in croquis}
    principais_ok = all(
        mapa_croquis.get(tipo) == "Anexado"
        for tipo in ["Planta do tabuleiro", "Corte longitudinal", "Corte transversal"]
    )
    detalhes_ok = mapa_croquis.get("Detalhes adicionais") in ["Anexado", "Não se aplica"]
    croquis_ok = principais_ok and detalhes_ok

    verificacao_anomalias = mapa_status.get("verificacao_anomalias", "Não verificada")
    if anomalias > 0:
        anomalias_ok = verificacao_anomalias == "Verificada - anomalias registradas"
    else:
        anomalias_ok = verificacao_anomalias == "Verificada - sem anomalias identificadas"

    minimo_fotos_ok = fotos >= 8
    abrangencia_fotos_ok = mapa_status.get("abrangencia_fotografica") == "Verificada pelo inspetor"

    etapas = [
        identificacao_ok,
        estrutura_ok,
        funcional_ok,
        ambiental_ok,
        documentos_ok,
        croquis_ok,
        anomalias_ok,
        classificacao["concluida"],
        minimo_fotos_ok,
        abrangencia_fotos_ok,
    ]
    concluidas = sum(1 for item in etapas if item)

    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric("Etapas atendidas", f"{concluidas}/{len(etapas)}")
    with c2:
        st.metric("Fotografias", f"{fotos}/8")
    with c3:
        st.metric("Anomalias registradas", anomalias)

    if concluidas == len(etapas):
        st.success("Todas as verificações de preenchimento desta inspeção cadastral foram atendidas.")
    else:
        st.warning("Ainda existem etapas pendentes nesta inspeção cadastral.")

    st.divider()

    st.checkbox("Identificação e localização verificadas", value=identificacao_ok, disabled=True)
    st.checkbox("Características estruturais verificadas", value=estrutura_ok, disabled=True)
    st.checkbox("Características funcionais verificadas", value=funcional_ok, disabled=True)
    st.checkbox("Características ambientais verificadas", value=ambiental_ok, disabled=True)

    st.checkbox("Documentos iniciais verificados", value=documentos_ok, disabled=True)
    st.caption(
        f"Documentos efetivamente verificados: "
        f"{documentos_tratados}/{len(TIPOS_DOCUMENTOS)}"
    )

    st.checkbox("Croquis verificados", value=croquis_ok, disabled=True)
    st.caption(
        "Planta do tabuleiro, corte longitudinal e corte transversal devem estar anexados. "
        "Detalhes adicionais podem estar anexados ou marcados como não aplicáveis."
    )

    st.checkbox("Verificação de anomalias concluída", value=anomalias_ok, disabled=True)
    st.caption(f"Situação registrada: {verificacao_anomalias}. Anomalias vinculadas: {anomalias}.")

    st.checkbox("Classificação dos componentes concluída", value=classificacao["concluida"], disabled=True)
    st.checkbox("Quantidade mínima de oito registros fotográficos atingida", value=minimo_fotos_ok, disabled=True)
    st.checkbox("Abrangência do levantamento fotográfico verificada", value=abrangencia_fotos_ok, disabled=True)

    st.info(
        "Campos marcados como 'Não informado' ou 'Não se aplica' podem ser considerados "
        "tratados quando essa situação tiver sido confirmada pelo inspetor. "
        "Campos marcados como 'Não verificado' continuam pendentes. "
        "A conclusão técnica permanece sob responsabilidade do profissional responsável."
    )


# ============================================================
# PREENCHIMENTO E MÓDULO PRINCIPAL
# ============================================================

def mostrar_preenchimento_cadastral(oae_ativa, inspecao_ativa):
    if inspecao_ativa is None:
        st.info("Selecione uma inspeção cadastral.")
        return

    if inspecao_ativa.tipo_inspecao != "Cadastral":
        st.warning("A inspeção selecionada não é do tipo Cadastral.")
        return

    cadastro = buscar_inspecao_cadastral(inspecao_ativa.id)

    if cadastro is None:
        db = SessionLocal()
        db.add(models.InspecaoCadastral(inspecao_id=inspecao_ativa.id))
        db.commit()
        db.close()
        cadastro = buscar_inspecao_cadastral(inspecao_ativa.id)

    st.write(f"**Inspeção:** {inspecao_ativa.data_inspecao.strftime('%d/%m/%Y')}")

    detalhe = buscar_detalhe_inspecao(inspecao_ativa.id)
    if detalhe is not None:
        st.write("**Motivo:**", detalhe.motivo_cadastral or "Não informado")
        if detalhe.descricao_alteracao:
            st.write("**Alteração registrada:**", detalhe.descricao_alteracao)

    st.divider()

    abas = st.tabs([
        "📍 Identificação",
        "🏗️ Estrutura",
        "🛣️ Funcional",
        "🌱 Ambiental",
        "📂 Documentos",
        "📐 Croquis",
        "🔗 Registros vinculados",
        "✅ Andamento",
    ])

    with abas[0]:
        mostrar_identificacao_localizacao(oae_ativa, inspecao_ativa, cadastro)
    with abas[1]:
        mostrar_caracteristicas_estruturais(oae_ativa, cadastro)
    with abas[2]:
        mostrar_caracteristicas_funcionais(cadastro)
    with abas[3]:
        mostrar_caracteristicas_ambientais(cadastro)
    with abas[4]:
        mostrar_documentos(cadastro)
    with abas[5]:
        mostrar_croquis(cadastro)
    with abas[6]:
        mostrar_integracoes(oae_ativa, inspecao_ativa)
    with abas[7]:
        mostrar_status_cadastral(oae_ativa, inspecao_ativa, cadastro)


def mostrar_modulo_cadastral(oae_ativa, inspecao_ativa=None):
    st.header("🟦 Inspeção Cadastral")
    st.caption("Módulo específico para registro da inspeção cadastral da OAE.")

    if oae_ativa is None:
        st.warning("Selecione ou cadastre uma OAE.")
        return

    tab_nova, tab_preencher = st.tabs([
        "➕ Nova inspeção cadastral",
        "📝 Preencher inspeção cadastral",
    ])

    with tab_nova:
        mostrar_nova_inspecao_cadastral(oae_ativa)

    with tab_preencher:
        cadastrais = buscar_inspecoes_cadastrais(oae_ativa.id)

        if len(cadastrais) == 0:
            st.info("Nenhuma inspeção cadastral cadastrada para esta OAE.")
            return

        ids = [item.id for item in cadastrais]
        mapa = {
            item.id: f"{item.id} - {item.data_inspecao.strftime('%d/%m/%Y')}"
            for item in cadastrais
        }

        id_padrao = ids[0]
        if inspecao_ativa is not None and inspecao_ativa.id in ids:
            id_padrao = inspecao_ativa.id

        selecionada_id = st.selectbox(
            "Inspeção cadastral",
            options=ids,
            format_func=lambda x: mapa[x],
            index=ids.index(id_padrao),
            key="cadastral_selecionada",
        )

        db = SessionLocal()
        selecionada = db.query(models.Inspecao).filter(models.Inspecao.id == selecionada_id).first()
        db.close()

        mostrar_preenchimento_cadastral(oae_ativa, selecionada)