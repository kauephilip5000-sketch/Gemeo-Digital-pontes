
from pathlib import Path

import streamlit as st

from ui_style import (
    renderizar_hero,
    renderizar_metricas,
    renderizar_resumo_oae,
    renderizar_classificacao,
    renderizar_andamento,
)


def mostrar_topo_visao_geral(
    *,
    oae_ativa,
    inspecao_referencia,
    totais,
    notas,
    total_componentes,
    total_classificados,
    nota_texto_fn,
):
    """
    Redesign do topo da Visão geral.
    Mantém todos os cálculos e regras de negócio fora desta camada visual.
    """

    hero_local = Path("assets/hero_ponte.jpg")
    hero = hero_local if hero_local.exists() else None

    renderizar_hero(
        oae=oae_ativa,
        image=hero,
    )

    st.markdown(
        '<div class="gd-section-title">Painel geral</div>'
        '<div class="gd-section-subtitle">'
        'Síntese dos registros da OAE selecionada e do acervo armazenado no sistema.'
        '</div>',
        unsafe_allow_html=True,
    )

    renderizar_metricas(totais)

    if oae_ativa is None:
        st.warning("Nenhuma OAE cadastrada.")
        return

    st.markdown(
        '<div class="gd-section-title">Identificação da OAE</div>',
        unsafe_allow_html=True,
    )
    renderizar_resumo_oae(oae_ativa)

    st.markdown(
        '<div class="gd-section-title">Condição da inspeção mais recente</div>'
        '<div class="gd-section-subtitle">'
        'Classificação estrutural, funcional e de durabilidade registrada para a campanha mais recente.'
        '</div>',
        unsafe_allow_html=True,
    )

    if inspecao_referencia is None:
        st.info("Esta OAE ainda não possui inspeções.")
        return

    renderizar_classificacao(
        notas,
        nota_texto_fn,
    )

    renderizar_andamento(
        total_componentes,
        total_classificados,
    )
