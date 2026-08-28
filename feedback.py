import streamlit as st
from sqlalchemy import event
from sqlalchemy.orm import Session as SQLAlchemySession


_CHAVE_FEEDBACK = "_feedback_salvamento_pendente"
_LISTENER_ATIVO = False


def definir_feedback_salvamento(mensagem="Dados salvos com sucesso."):
    """Agenda uma confirmação visual para esta execução ou para o próximo rerun."""
    st.session_state[_CHAVE_FEEDBACK] = mensagem


def _registrar_commit_da_sessao(session):
    # Todo commit ORM realizado pelos módulos do sistema gera uma confirmação.
    definir_feedback_salvamento("Dados salvos com sucesso.")


def ativar_feedback_global():
    """Ativa uma única vez o monitoramento global de commits ORM."""
    global _LISTENER_ATIVO

    if _LISTENER_ATIVO:
        return

    event.listen(
        SQLAlchemySession,
        "after_commit",
        _registrar_commit_da_sessao,
    )
    _LISTENER_ATIVO = True


def mostrar_feedback_salvamento():
    """Mostra a confirmação pendente como toast e a remove da sessão."""
    mensagem = st.session_state.pop(
        _CHAVE_FEEDBACK,
        None,
    )

    if mensagem:
        st.toast(
            mensagem,
            icon="✅",
        )
