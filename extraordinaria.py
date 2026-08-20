import streamlit as st

from datetime import date

from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    Date,
    ForeignKey,
    UniqueConstraint,
)

from database import Base, SessionLocal
import models

from classificacao import (
    calcular_classificacao_consolidada,
    verificar_andamento_classificacao,
)


# ============================================================
# INSPEÇÃO EXTRAORDINÁRIA
# ABNT NBR 9452:2023 - ITEM 4.4
# ============================================================


class RegistroExtraordinaria(Base):
    __tablename__ = "registros_extraordinaria"

    __table_args__ = (
        UniqueConstraint(
            "inspecao_id",
            name="uq_registro_extraordinaria_inspecao",
        ),
    )

    id = Column(Integer, primary_key=True, index=True)
    inspecao_id = Column(
        Integer,
        ForeignKey("inspecoes.id"),
        nullable=False,
    )

    # Motivo / evento
    motivo = Column(String, nullable=True)
    data_evento = Column(Date, nullable=True)
    descricao_evento = Column(Text, nullable=True)
    origem_demanda = Column(Text, nullable=True)

    # Escopo
    componente_afetado_id = Column(
        Integer,
        ForeignKey("componentes.id"),
        nullable=True,
    )
    outros_elementos_afetados = Column(Text, nullable=True)
    escopo_verificado = Column(String, nullable=True)

    # Descrição da obra / acesso
    descricao_obra = Column(Text, nullable=True)
    condicoes_acesso = Column(Text, nullable=True)
    equipamentos_acesso = Column(Text, nullable=True)
    limitacoes_inspecao = Column(Text, nullable=True)
    descricao_verificada = Column(String, nullable=True)

    # Anomalias / mapeamento
    sintese_anomalias = Column(Text, nullable=True)
    referencia_mapeamento = Column(Text, nullable=True)
    abrangencia_mapeamento = Column(String, nullable=True)
    anomalias_verificadas = Column(String, nullable=True)

    # Fotografias
    abrangencia_fotografica = Column(String, nullable=True)
    referencia_fotografica = Column(Text, nullable=True)
    fotografias_verificadas = Column(String, nullable=True)

    # Subaquática, quando aplicável
    inspecao_subaquatica = Column(String, nullable=True)
    observacoes_subaquaticas = Column(Text, nullable=True)

    # Terapia / providências
    terapia_recomendada = Column(Text, nullable=True)
    medidas_emergenciais = Column(Text, nullable=True)
    necessidade_interdicao = Column(String, nullable=True)
    necessidade_monitoramento = Column(String, nullable=True)
    necessidade_especial = Column(String, nullable=True)
    recomendacoes_complementares = Column(Text, nullable=True)
    terapia_verificada = Column(String, nullable=True)

    # Conclusão
    conclusao = Column(Text, nullable=True)
    conclusao_preenchimento = Column(String, nullable=True)


STATUS_VERIFICACAO = [
    "Não verificado",
    "Verificado",
    "Não se aplica",
]

STATUS_SIM_NAO = [
    "Não verificado",
    "Sim",
    "Não",
]

STATUS_SUBAQUATICA = [
    "Não verificado",
    "Realizada",
    "Não se aplica",
]

MOTIVOS_EXTRAORDINARIA = [
    "Avaliação mais criteriosa de elemento ou parte da OAE",
    "Impacto de veículo",
    "Impacto de trem",
    "Impacto de embarcação",
    "Incêndio",
    "Inundação",
    "Vendaval",
    "Sismo",
    "Outro evento da natureza",
    "Outra demanda não programada",
]


# ============================================================
# CONSULTAS
# ============================================================


def buscar_inspecoes_extraordinarias(oae_id):
    db = SessionLocal()
    dados = (
        db.query(models.Inspecao)
        .filter(models.Inspecao.oae_id == oae_id)
        .filter(models.Inspecao.tipo_inspecao == "Extraordinária")
        .order_by(
            models.Inspecao.data_inspecao.desc(),
            models.Inspecao.id.desc(),
        )
        .all()
    )
    db.close()
    return dados


def buscar_registro_extraordinaria(inspecao_id):
    if inspecao_id is None:
        return None

    db = SessionLocal()
    registro = (
        db.query(RegistroExtraordinaria)
        .filter(RegistroExtraordinaria.inspecao_id == inspecao_id)
        .first()
    )
    db.close()
    return registro


def garantir_registro_extraordinaria(inspecao_id):
    registro = buscar_registro_extraordinaria(inspecao_id)
    if registro is not None:
        return registro

    db = SessionLocal()
    novo = RegistroExtraordinaria(inspecao_id=inspecao_id)
    db.add(novo)
    db.commit()
    db.close()
    return buscar_registro_extraordinaria(inspecao_id)


def buscar_componentes(oae_id):
    db = SessionLocal()
    dados = (
        db.query(models.Componente)
        .filter(models.Componente.oae_id == oae_id)
        .order_by(models.Componente.id)
        .all()
    )
    db.close()
    return dados


def buscar_anomalias_ativas(oae_id, inspecao_ativa):
    db = SessionLocal()
    dados = (
        db.query(models.AnomaliaPermanente)
        .join(
            models.Inspecao,
            models.Inspecao.id
            == models.AnomaliaPermanente.inspecao_origem_id,
        )
        .filter(models.AnomaliaPermanente.oae_id == oae_id)
        .filter(models.AnomaliaPermanente.ativa == 1)
        .filter(
            (
                models.Inspecao.data_inspecao
                < inspecao_ativa.data_inspecao
            )
            |
            (
                (models.Inspecao.data_inspecao == inspecao_ativa.data_inspecao)
                & (models.Inspecao.id <= inspecao_ativa.id)
            )
        )
        .order_by(models.AnomaliaPermanente.id)
        .all()
    )
    db.close()
    return dados


def buscar_observacao(anomalia_id, inspecao_id):
    db = SessionLocal()
    dado = (
        db.query(models.ObservacaoAnomalia)
        .filter(models.ObservacaoAnomalia.anomalia_id == anomalia_id)
        .filter(models.ObservacaoAnomalia.inspecao_id == inspecao_id)
        .first()
    )
    db.close()
    return dado


def contar_fotografias(oae_id, inspecao_id):
    db = SessionLocal()
    quantidade = (
        db.query(models.Fotografia)
        .filter(models.Fotografia.oae_id == oae_id)
        .filter(models.Fotografia.inspecao_id == inspecao_id)
        .count()
    )
    db.close()
    return quantidade


# ============================================================
# NOVA INSPEÇÃO EXTRAORDINÁRIA
# ============================================================


def mostrar_nova_extraordinaria(oae_ativa):
    st.subheader("🟥 Nova inspeção extraordinária")

    st.warning(
        "Use este módulo para demandas não programadas que exijam "
        "avaliação específica de um elemento, parte da OAE ou de "
        "consequências de impacto, incêndio ou evento da natureza."
    )

    componentes = buscar_componentes(oae_ativa.id)
    mapa_componentes = {
        item.id: f"{item.id} - {item.nome}"
        for item in componentes
    }

    data_inspecao = st.date_input(
        "Data da inspeção",
        value=date.today(),
        format="DD/MM/YYYY",
        key="extra_nova_data",
    )

    motivo = st.selectbox(
        "Motivo da inspeção",
        MOTIVOS_EXTRAORDINARIA,
        key="extra_nova_motivo",
    )

    data_evento = st.date_input(
        "Data do evento ou demanda",
        value=date.today(),
        format="DD/MM/YYYY",
        key="extra_nova_data_evento",
    )

    descricao_evento = st.text_area(
        "Descrição do evento ou ocorrência",
        key="extra_nova_evento",
    )

    origem_demanda = st.text_area(
        "Origem da demanda / informação complementar",
        key="extra_nova_origem",
    )

    componente_afetado_id = st.selectbox(
        "Elemento inicialmente afetado",
        options=[None] + [item.id for item in componentes],
        format_func=lambda x: (
            "Não definido" if x is None else mapa_componentes[x]
        ),
        key="extra_nova_componente",
    )

    responsavel = st.text_input(
        "Responsável pela inspeção",
        key="extra_nova_responsavel",
    )

    registro_profissional = st.text_input(
        "Registro profissional",
        key="extra_nova_registro",
    )

    observacoes = st.text_area(
        "Observações iniciais",
        key="extra_nova_observacoes",
    )

    salvar = st.button(
        "Criar inspeção extraordinária",
        type="primary",
        key="extra_nova_salvar",
    )

    if not salvar:
        return

    if responsavel.strip() == "":
        st.error("Informe o responsável pela inspeção.")
        return

    if descricao_evento.strip() == "":
        st.error("Descreva o evento, ocorrência ou demanda.")
        return

    db = SessionLocal()

    nova = models.Inspecao(
        oae_id=oae_ativa.id,
        tipo_inspecao="Extraordinária",
        data_inspecao=data_inspecao,
        responsavel=responsavel,
        registro_profissional=registro_profissional,
        observacoes=observacoes,
    )

    db.add(nova)
    db.flush()

    detalhe = models.DetalheInspecao(
        inspecao_id=nova.id,
        motivo_extraordinaria=motivo,
        data_evento=data_evento,
        descricao_evento=descricao_evento,
        componente_afetado_id=componente_afetado_id,
        terapia_recomendada="",
    )
    db.add(detalhe)

    registro = RegistroExtraordinaria(
        inspecao_id=nova.id,
        motivo=motivo,
        data_evento=data_evento,
        descricao_evento=descricao_evento,
        origem_demanda=origem_demanda,
        componente_afetado_id=componente_afetado_id,
    )
    db.add(registro)

    db.commit()
    db.refresh(nova)
    novo_id = nova.id
    db.close()

    st.session_state.inspecao_ativa_id = novo_id
    st.success("Inspeção extraordinária criada com sucesso.")
    st.rerun()


# ============================================================
# 1 - EVENTO E ESCOPO
# ============================================================


def mostrar_evento_escopo(oae_ativa, inspecao_ativa, registro):
    st.subheader("1️⃣ Evento e escopo da inspeção")

    componentes = buscar_componentes(oae_ativa.id)
    mapa_componentes = {
        item.id: f"{item.id} - {item.nome}"
        for item in componentes
    }

    motivo_atual = registro.motivo or MOTIVOS_EXTRAORDINARIA[0]
    if motivo_atual not in MOTIVOS_EXTRAORDINARIA:
        motivo_atual = MOTIVOS_EXTRAORDINARIA[0]

    motivo = st.selectbox(
        "Motivo da inspeção",
        MOTIVOS_EXTRAORDINARIA,
        index=MOTIVOS_EXTRAORDINARIA.index(motivo_atual),
        key="extra_evento_motivo",
    )

    data_evento = st.date_input(
        "Data do evento ou demanda",
        value=(registro.data_evento or inspecao_ativa.data_inspecao),
        format="DD/MM/YYYY",
        key="extra_evento_data",
    )

    descricao_evento = st.text_area(
        "Descrição do evento ou ocorrência",
        value=registro.descricao_evento or "",
        key="extra_evento_descricao",
    )

    origem_demanda = st.text_area(
        "Origem da demanda / informação complementar",
        value=registro.origem_demanda or "",
        key="extra_evento_origem",
    )

    componente_atual = registro.componente_afetado_id
    if componente_atual not in mapa_componentes:
        componente_atual = None

    componente_afetado_id = st.selectbox(
        "Elemento inicialmente afetado",
        options=[None] + [item.id for item in componentes],
        index=([None] + [item.id for item in componentes]).index(
            componente_atual
        ),
        format_func=lambda x: (
            "Não definido" if x is None else mapa_componentes[x]
        ),
        key="extra_evento_componente",
    )

    outros = st.text_area(
        "Outros elementos ou regiões afetados",
        value=registro.outros_elementos_afetados or "",
        key="extra_evento_outros",
    )

    atual = registro.escopo_verificado or "Não verificado"
    if atual not in STATUS_VERIFICACAO:
        atual = "Não verificado"

    status = st.selectbox(
        "Situação da definição do escopo",
        STATUS_VERIFICACAO,
        index=STATUS_VERIFICACAO.index(atual),
        key="extra_evento_status",
    )

    salvar = st.button(
        "💾 Salvar evento e escopo",
        type="primary",
        key="extra_evento_salvar",
    )

    if salvar:
        if status == "Verificado" and descricao_evento.strip() == "":
            st.error("Descreva o evento ou demanda antes de concluir.")
            return

        db = SessionLocal()
        dado = (
            db.query(RegistroExtraordinaria)
            .filter(RegistroExtraordinaria.id == registro.id)
            .first()
        )
        dado.motivo = motivo
        dado.data_evento = data_evento
        dado.descricao_evento = descricao_evento
        dado.origem_demanda = origem_demanda
        dado.componente_afetado_id = componente_afetado_id
        dado.outros_elementos_afetados = outros
        dado.escopo_verificado = status

        detalhe = (
            db.query(models.DetalheInspecao)
            .filter(models.DetalheInspecao.inspecao_id == inspecao_ativa.id)
            .first()
        )
        if detalhe is not None:
            detalhe.motivo_extraordinaria = motivo
            detalhe.data_evento = data_evento
            detalhe.descricao_evento = descricao_evento
            detalhe.componente_afetado_id = componente_afetado_id

        db.commit()
        db.close()
        st.success("Evento e escopo atualizados.")
        st.rerun()


# ============================================================
# 2 - DESCRIÇÃO DA OBRA / ACESSO
# ============================================================


def mostrar_descricao_acesso(registro):
    st.subheader("2️⃣ Descrição da obra e condições de acesso")

    descricao = st.text_area(
        "Descrição da obra ou da parte avaliada",
        value=registro.descricao_obra or "",
        key="extra_desc_obra",
    )

    equipamentos = st.text_area(
        "Equipamentos ou recursos de acesso utilizados",
        value=registro.equipamentos_acesso or "",
        key="extra_desc_equipamentos",
    )

    condicoes = st.text_area(
        "Condições de acesso",
        value=registro.condicoes_acesso or "",
        key="extra_desc_acesso",
    )

    limitacoes = st.text_area(
        "Limitações da inspeção",
        value=registro.limitacoes_inspecao or "",
        key="extra_desc_limitacoes",
    )

    sub_atual = registro.inspecao_subaquatica or "Não verificado"
    if sub_atual not in STATUS_SUBAQUATICA:
        sub_atual = "Não verificado"

    subaquatica = st.selectbox(
        "Inspeção subaquática",
        STATUS_SUBAQUATICA,
        index=STATUS_SUBAQUATICA.index(sub_atual),
        key="extra_desc_subaquatica",
    )

    obs_sub = st.text_area(
        "Observações sobre inspeção subaquática",
        value=registro.observacoes_subaquaticas or "",
        key="extra_desc_obs_sub",
    )

    atual = registro.descricao_verificada or "Não verificado"
    if atual not in STATUS_VERIFICACAO:
        atual = "Não verificado"

    status = st.selectbox(
        "Situação desta etapa",
        STATUS_VERIFICACAO,
        index=STATUS_VERIFICACAO.index(atual),
        key="extra_desc_status",
    )

    salvar = st.button(
        "💾 Salvar descrição e acesso",
        type="primary",
        key="extra_desc_salvar",
    )

    if salvar:
        if status == "Verificado" and descricao.strip() == "":
            st.error("Descreva a obra ou parte avaliada antes de concluir.")
            return

        db = SessionLocal()
        dado = (
            db.query(RegistroExtraordinaria)
            .filter(RegistroExtraordinaria.id == registro.id)
            .first()
        )
        dado.descricao_obra = descricao
        dado.equipamentos_acesso = equipamentos
        dado.condicoes_acesso = condicoes
        dado.limitacoes_inspecao = limitacoes
        dado.inspecao_subaquatica = subaquatica
        dado.observacoes_subaquaticas = obs_sub
        dado.descricao_verificada = status
        db.commit()
        db.close()
        st.success("Descrição e condições de acesso atualizadas.")
        st.rerun()


# ============================================================
# 3 - ANOMALIAS E MAPEAMENTO
# ============================================================


def mostrar_anomalias_mapeamento(oae_ativa, inspecao_ativa, registro):
    st.subheader("3️⃣ Anomalias e mapeamento")

    anomalias = buscar_anomalias_ativas(oae_ativa.id, inspecao_ativa)
    observadas = 0
    dados = []

    for anomalia in anomalias:
        obs = buscar_observacao(anomalia.id, inspecao_ativa.id)
        if obs is not None:
            observadas += 1

        componente = next(
            (
                item
                for item in buscar_componentes(oae_ativa.id)
                if item.id == anomalia.componente_id
            ),
            None,
        )

        dados.append(
            {
                "ID": anomalia.id,
                "Componente": (
                    componente.nome if componente is not None else "—"
                ),
                "Anomalia": anomalia.tipo_anomalia,
                "Localização": anomalia.localizacao_referencia,
                "Observada na campanha": "Sim" if obs is not None else "Não",
                "Situação": (
                    obs.situacao_observada
                    if obs is not None and obs.situacao_observada
                    else "—"
                ),
            }
        )

    c1, c2 = st.columns(2)
    with c1:
        st.metric("Anomalias ativas", len(anomalias))
    with c2:
        st.metric("Observadas nesta campanha", f"{observadas}/{len(anomalias)}")

    if len(dados) > 0:
        st.dataframe(dados, width="stretch", hide_index=True)
    else:
        st.info("Nenhuma anomalia ativa está cadastrada para esta OAE.")

    st.caption(
        "Cadastre e atualize as anomalias no módulo ⚠️ Anomalias. "
        "Esta tela acompanha o que já está vinculado à campanha."
    )

    sintese = st.text_area(
        "Síntese das anomalias identificadas",
        value=registro.sintese_anomalias or "",
        key="extra_anom_sintese",
    )

    referencia = st.text_area(
        "Referência do mapeamento",
        value=registro.referencia_mapeamento or "",
        placeholder="Informe croqui, desenho ou referência do mapeamento.",
        key="extra_anom_mapeamento",
    )

    abrangencia = st.text_area(
        "Abrangência do mapeamento",
        value=registro.abrangencia_mapeamento or "",
        placeholder="Descreva os elementos e regiões efetivamente mapeados.",
        key="extra_anom_abrangencia",
    )

    atual = registro.anomalias_verificadas or "Não verificado"
    if atual not in STATUS_VERIFICACAO:
        atual = "Não verificado"

    status = st.selectbox(
        "Situação da etapa de anomalias",
        STATUS_VERIFICACAO,
        index=STATUS_VERIFICACAO.index(atual),
        key="extra_anom_status",
    )

    salvar = st.button(
        "💾 Salvar anomalias e mapeamento",
        type="primary",
        key="extra_anom_salvar",
    )

    if salvar:
        if status == "Verificado" and sintese.strip() == "":
            st.error("Informe a síntese das anomalias antes de concluir.")
            return

        db = SessionLocal()
        dado = (
            db.query(RegistroExtraordinaria)
            .filter(RegistroExtraordinaria.id == registro.id)
            .first()
        )
        dado.sintese_anomalias = sintese
        dado.referencia_mapeamento = referencia
        dado.abrangencia_mapeamento = abrangencia
        dado.anomalias_verificadas = status
        db.commit()
        db.close()
        st.success("Anomalias e mapeamento atualizados.")
        st.rerun()


# ============================================================
# 4 - DOCUMENTAÇÃO FOTOGRÁFICA
# ============================================================


def mostrar_fotografias(oae_ativa, inspecao_ativa, registro):
    st.subheader("4️⃣ Documentação fotográfica")

    quantidade = contar_fotografias(oae_ativa.id, inspecao_ativa.id)
    st.metric("Fotografias vinculadas à campanha", quantidade)

    abrangencia = st.text_area(
        "Abrangência da documentação fotográfica",
        value=registro.abrangencia_fotografica or "",
        key="extra_foto_abrangencia",
    )

    referencia = st.text_area(
        "Referência / observações das fotografias",
        value=registro.referencia_fotografica or "",
        key="extra_foto_referencia",
    )

    atual = registro.fotografias_verificadas or "Não verificado"
    if atual not in STATUS_VERIFICACAO:
        atual = "Não verificado"

    status = st.selectbox(
        "Situação da documentação fotográfica",
        STATUS_VERIFICACAO,
        index=STATUS_VERIFICACAO.index(atual),
        key="extra_foto_status",
    )

    salvar = st.button(
        "💾 Salvar documentação fotográfica",
        type="primary",
        key="extra_foto_salvar",
    )

    if salvar:
        if status == "Verificado" and quantidade == 0:
            st.error(
                "Não há fotografias vinculadas à inspeção. "
                "Adicione os registros no módulo 📷 Fotografias."
            )
            return

        db = SessionLocal()
        dado = (
            db.query(RegistroExtraordinaria)
            .filter(RegistroExtraordinaria.id == registro.id)
            .first()
        )
        dado.abrangencia_fotografica = abrangencia
        dado.referencia_fotografica = referencia
        dado.fotografias_verificadas = status
        db.commit()
        db.close()
        st.success("Documentação fotográfica atualizada.")
        st.rerun()


# ============================================================
# 5 - CLASSIFICAÇÃO
# ============================================================


def mostrar_classificacao_extraordinaria(oae_ativa, inspecao_ativa):
    st.subheader("5️⃣ Classificação da OAE")

    andamento = verificar_andamento_classificacao(
        oae_ativa.id,
        inspecao_ativa.id,
    )

    notas = calcular_classificacao_consolidada(
        oae_ativa.id,
        inspecao_ativa.id,
    )

    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric("Componentes cadastrados", andamento["total"])
    with c2:
        st.metric("Componentes avaliados", andamento["avaliados"])
    with c3:
        st.metric(
            "Pendentes",
            max(andamento["total"] - andamento["avaliados"], 0),
        )

    if andamento["concluida"]:
        st.success("Classificação da campanha concluída.")
    else:
        st.warning("Ainda existem componentes pendentes no módulo ⭐ Classificação.")

    if notas is not None:
        c1, c2, c3 = st.columns(3)
        with c1:
            st.metric("Estrutural", notas["estrutural"] if notas["estrutural"] is not None else "—")
        with c2:
            st.metric("Funcional", notas["funcional"] if notas["funcional"] is not None else "NA")
        with c3:
            st.metric("Durabilidade", notas["durabilidade"] if notas["durabilidade"] is not None else "—")


# ============================================================
# 6 - TERAPIA E PROVIDÊNCIAS
# ============================================================


def mostrar_terapia(inspecao_ativa, registro):
    st.subheader("6️⃣ Terapia e providências recomendadas")

    terapia = st.text_area(
        "Terapia recomendada",
        value=registro.terapia_recomendada or "",
        key="extra_terapia_texto",
    )

    emergenciais = st.text_area(
        "Medidas emergenciais, quando aplicáveis",
        value=registro.medidas_emergenciais or "",
        key="extra_terapia_emergenciais",
    )

    inter_atual = registro.necessidade_interdicao or "Não verificado"
    if inter_atual not in STATUS_SIM_NAO:
        inter_atual = "Não verificado"
    interdicao = st.selectbox(
        "Necessidade de interdição ou restrição de uso",
        STATUS_SIM_NAO,
        index=STATUS_SIM_NAO.index(inter_atual),
        key="extra_terapia_interdicao",
    )

    mon_atual = registro.necessidade_monitoramento or "Não verificado"
    if mon_atual not in STATUS_SIM_NAO:
        mon_atual = "Não verificado"
    monitoramento = st.selectbox(
        "Necessidade de monitoramento",
        STATUS_SIM_NAO,
        index=STATUS_SIM_NAO.index(mon_atual),
        key="extra_terapia_monitoramento",
    )

    esp_atual = registro.necessidade_especial or "Não verificado"
    if esp_atual not in STATUS_SIM_NAO:
        esp_atual = "Não verificado"
    necessidade_especial = st.selectbox(
        "Necessidade de avaliação/inspeção especial complementar",
        STATUS_SIM_NAO,
        index=STATUS_SIM_NAO.index(esp_atual),
        key="extra_terapia_especial",
    )

    complementares = st.text_area(
        "Recomendações complementares",
        value=registro.recomendacoes_complementares or "",
        key="extra_terapia_recomendacoes",
    )

    conclusao = st.text_area(
        "Conclusão técnica da inspeção extraordinária",
        value=registro.conclusao or "",
        key="extra_terapia_conclusao",
    )

    atual = registro.terapia_verificada or "Não verificado"
    if atual not in STATUS_VERIFICACAO:
        atual = "Não verificado"

    status = st.selectbox(
        "Situação desta etapa",
        STATUS_VERIFICACAO,
        index=STATUS_VERIFICACAO.index(atual),
        key="extra_terapia_status",
    )

    salvar = st.button(
        "💾 Salvar terapia e providências",
        type="primary",
        key="extra_terapia_salvar",
    )

    if salvar:
        if status == "Verificado" and terapia.strip() == "":
            st.error("Informe a terapia ou providência recomendada antes de concluir.")
            return

        db = SessionLocal()
        dado = (
            db.query(RegistroExtraordinaria)
            .filter(RegistroExtraordinaria.id == registro.id)
            .first()
        )
        dado.terapia_recomendada = terapia
        dado.medidas_emergenciais = emergenciais
        dado.necessidade_interdicao = interdicao
        dado.necessidade_monitoramento = monitoramento
        dado.necessidade_especial = necessidade_especial
        dado.recomendacoes_complementares = complementares
        dado.conclusao = conclusao
        dado.terapia_verificada = status

        detalhe = (
            db.query(models.DetalheInspecao)
            .filter(models.DetalheInspecao.inspecao_id == inspecao_ativa.id)
            .first()
        )
        if detalhe is not None:
            detalhe.terapia_recomendada = terapia

        db.commit()
        db.close()
        st.success("Terapia e providências atualizadas.")
        st.rerun()


# ============================================================
# 7 - ANDAMENTO
# ============================================================


def mostrar_andamento(oae_ativa, inspecao_ativa, registro):
    st.subheader("7️⃣ Andamento da inspeção extraordinária")

    andamento_classificacao = verificar_andamento_classificacao(
        oae_ativa.id,
        inspecao_ativa.id,
    )
    fotos = contar_fotografias(oae_ativa.id, inspecao_ativa.id)

    etapas = [
        (
            "Evento e escopo",
            registro.escopo_verificado == "Verificado",
        ),
        (
            "Descrição da obra / acesso",
            registro.descricao_verificada in ["Verificado", "Não se aplica"],
        ),
        (
            "Anomalias e mapeamento",
            registro.anomalias_verificadas == "Verificado",
        ),
        (
            "Documentação fotográfica",
            registro.fotografias_verificadas == "Verificado" and fotos > 0,
        ),
        (
            "Classificação",
            andamento_classificacao["concluida"],
        ),
        (
            "Terapia / providências",
            registro.terapia_verificada == "Verificado",
        ),
    ]

    concluidas = sum(1 for _, ok in etapas if ok)
    total = len(etapas)

    st.progress(concluidas / total)
    st.write(f"**Etapas concluídas:** {concluidas}/{total}")

    for nome, ok in etapas:
        st.checkbox(
            nome,
            value=ok,
            disabled=True,
            key=f"extra_and_{inspecao_ativa.id}_{nome}",
        )

    st.divider()

    if concluidas == total:
        st.success(
            "O preenchimento previsto no módulo está completo. "
            "A conclusão técnica permanece sob responsabilidade do profissional."
        )
        status_final = "Concluída"
    else:
        st.warning("Ainda existem etapas pendentes.")
        status_final = "Em preenchimento"

    salvar = st.button(
        "💾 Atualizar situação do preenchimento",
        type="primary",
        key="extra_and_salvar",
    )

    if salvar:
        db = SessionLocal()
        dado = (
            db.query(RegistroExtraordinaria)
            .filter(RegistroExtraordinaria.id == registro.id)
            .first()
        )
        dado.conclusao_preenchimento = status_final
        db.commit()
        db.close()
        st.success("Situação do preenchimento atualizada.")
        st.rerun()


# ============================================================
# PREENCHIMENTO
# ============================================================


def mostrar_preenchimento_extraordinaria(oae_ativa, inspecao_ativa):
    if inspecao_ativa is None:
        st.info("Selecione uma inspeção extraordinária.")
        return

    if inspecao_ativa.tipo_inspecao != "Extraordinária":
        st.warning("A inspeção selecionada não é do tipo Extraordinária.")
        return

    registro = garantir_registro_extraordinaria(inspecao_ativa.id)

    st.write(
        f"**Inspeção:** {inspecao_ativa.data_inspecao.strftime('%d/%m/%Y')}"
    )
    st.write(
        f"**Responsável:** {inspecao_ativa.responsavel or 'Não informado'}"
    )

    abas = st.tabs(
        [
            "🚨 Evento e escopo",
            "🌉 Descrição / acesso",
            "⚠️ Anomalias",
            "📷 Fotografias",
            "⭐ Classificação",
            "🛠️ Terapia",
            "✅ Andamento",
        ]
    )

    with abas[0]:
        mostrar_evento_escopo(oae_ativa, inspecao_ativa, registro)

    with abas[1]:
        mostrar_descricao_acesso(registro)

    with abas[2]:
        mostrar_anomalias_mapeamento(oae_ativa, inspecao_ativa, registro)

    with abas[3]:
        mostrar_fotografias(oae_ativa, inspecao_ativa, registro)

    with abas[4]:
        mostrar_classificacao_extraordinaria(oae_ativa, inspecao_ativa)

    with abas[5]:
        mostrar_terapia(inspecao_ativa, registro)

    with abas[6]:
        mostrar_andamento(oae_ativa, inspecao_ativa, registro)


# ============================================================
# MÓDULO PRINCIPAL
# ============================================================


def mostrar_modulo_extraordinaria(oae_ativa, inspecao_ativa=None):
    st.header("🟥 Inspeção Extraordinária")

    st.caption(
        "Módulo para demandas não programadas, estruturado com base "
        "no item 4.4 da ABNT NBR 9452:2023."
    )

    if oae_ativa is None:
        st.warning("Selecione ou cadastre uma OAE.")
        return

    tab_nova, tab_preencher = st.tabs(
        [
            "➕ Nova inspeção extraordinária",
            "📝 Preencher inspeção extraordinária",
        ]
    )

    with tab_nova:
        mostrar_nova_extraordinaria(oae_ativa)

    with tab_preencher:
        extraordinarias = buscar_inspecoes_extraordinarias(oae_ativa.id)

        if len(extraordinarias) == 0:
            st.info("Nenhuma inspeção extraordinária cadastrada para esta OAE.")
            return

        ids = [item.id for item in extraordinarias]
        mapa = {
            item.id: (
                f"{item.id} - {item.data_inspecao.strftime('%d/%m/%Y')}"
            )
            for item in extraordinarias
        }

        id_padrao = ids[0]
        if inspecao_ativa is not None and inspecao_ativa.id in ids:
            id_padrao = inspecao_ativa.id

        selecionada_id = st.selectbox(
            "Inspeção extraordinária",
            options=ids,
            format_func=lambda x: mapa[x],
            index=ids.index(id_padrao),
            key="extra_selecionada",
        )

        db = SessionLocal()
        selecionada = (
            db.query(models.Inspecao)
            .filter(models.Inspecao.id == selecionada_id)
            .first()
        )
        db.close()

        mostrar_preenchimento_extraordinaria(
            oae_ativa,
            selecionada,
        )