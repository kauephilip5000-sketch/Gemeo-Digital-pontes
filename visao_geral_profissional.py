
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
    ultima_inspecao_classificada=None,
    notas_ultima_classificada=None,
):
    """
    Redesign do topo da Visão geral.

    Importante:
    - Cadastral, Rotineira e Extraordinária usam classificação geral da OAE.
    - Especial usa classificação por componente e consolidação.
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

    if inspecao_referencia is None:
        st.markdown(
            '<div class="gd-section-title">Condição da inspeção mais recente</div>',
            unsafe_allow_html=True,
        )
        st.info("Esta OAE ainda não possui inspeções.")
        return

    data_ref = (
        inspecao_referencia
        .data_inspecao
        .strftime("%d/%m/%Y")
    )
    tipo_ref = str(
        getattr(
            inspecao_referencia,
            "tipo_inspecao",
            "Inspeção"
        )
        or "Inspeção"
    )

    tipo_normalizado = (
        tipo_ref
        .strip()
        .lower()
    )

    eh_especial = (
        "especial"
        in tipo_normalizado
    )

    st.markdown(
        '<div class="gd-section-title">Última inspeção realizada</div>'
        '<div class="gd-section-subtitle">'
        'Campanha mais recente registrada para a OAE selecionada.'
        '</div>',
        unsafe_allow_html=True,
    )

    status_classificacao = (
        "Registrada"
        if notas is not None
        else "Pendente"
    )

    with st.container(border=True):
        c1, c2, c3 = st.columns(3)

        with c1:
            st.markdown("**Tipo de inspeção**")
            st.write(tipo_ref)

        with c2:
            st.markdown("**Data da inspeção**")
            st.write(data_ref)

        with c3:
            st.markdown("**Classificação da OAE**")
            st.write(status_classificacao)

        if (
            notas is None
            and ultima_inspecao_classificada is not None
            and ultima_inspecao_classificada.id
            != inspecao_referencia.id
        ):
            data_ultima = (
                ultima_inspecao_classificada
                .data_inspecao
                .strftime("%d/%m/%Y")
            )
            tipo_ultima = str(
                getattr(
                    ultima_inspecao_classificada,
                    "tipo_inspecao",
                    "Inspeção"
                )
                or "Inspeção"
            )

            st.caption(
                "Última classificação registrada no sistema: "
                f"{tipo_ultima} • {data_ultima}."
            )

    st.markdown(
        '<div class="gd-section-title">Condição da OAE</div>',
        unsafe_allow_html=True,
    )

    if notas is None:
        st.warning(
            "A inspeção mais recente ainda não possui classificação. "
            "As notas exibidas abaixo correspondem à última inspeção "
            "com classificação registrada e não representam a condição "
            "mais atual da OAE."
        )

        if (
            ultima_inspecao_classificada is not None
            and notas_ultima_classificada is not None
        ):
            data_ultima = (
                ultima_inspecao_classificada
                .data_inspecao
                .strftime("%d/%m/%Y")
            )

            tipo_ultima = str(
                getattr(
                    ultima_inspecao_classificada,
                    "tipo_inspecao",
                    "Inspeção"
                )
                or "Inspeção"
            )

            st.markdown(
                f"**Última classificação disponível:** "
                f"{tipo_ultima} • {data_ultima}"
            )

            renderizar_classificacao(
                notas_ultima_classificada,
                nota_texto_fn,
            )

            st.caption(
                "Referência histórica — existe uma inspeção posterior "
                "ainda sem classificação registrada."
            )

    else:
        st.success(
            "As notas abaixo correspondem à inspeção mais recente "
            "registrada para a OAE."
        )

        renderizar_classificacao(
            notas,
            nota_texto_fn,
        )

    # --------------------------------------------------------
    # ANDAMENTO
    # --------------------------------------------------------
    # Somente inspeção especial é classificada por componente.
    if eh_especial:
        st.markdown(
            '<div class="gd-section-title">'
            'Andamento da classificação por componente'
            '</div>'
            '<div class="gd-section-subtitle">'
            'Percentual de componentes classificados nesta inspeção especial.'
            '</div>',
            unsafe_allow_html=True,
        )

        renderizar_andamento(
            total_componentes,
            total_classificados,
        )

    elif notas is not None:
        st.success(
            "Classificação da OAE registrada para a inspeção mais recente."
        )
