import streamlit as st
from database import engine, Base, SessionLocal
import models

Base.metadata.create_all(bind=engine)

st.set_page_config(
    page_title="Gêmeo Digital - Pontes",
    page_icon="🌉",
    layout="wide"
)

st.title("🌉 Gêmeo Digital para Inspeção de Pontes")

st.subheader(
    "Sistema de apoio à inspeção e ao acompanhamento da integridade estrutural"
)

st.write(
    """
    Este protótipo está sendo desenvolvido em Python como parte do Trabalho
    de Conclusão de Curso 2.
    """
)

st.divider()

st.header("Funcionalidades previstas")

st.write("✅ Cadastro da OAE")
st.write("✅ Cadastro dos componentes estruturais")
st.write("✅ Registro de inspeções")
st.write("✅ Registro de anomalias")
st.write("✅ Armazenamento de fotografias")
st.write("✅ Classificação estrutural, funcional e de durabilidade")
st.write("✅ Histórico das inspeções")
st.write("✅ Emissão de relatórios")

st.divider()

st.header("Cadastro da OAE")

with st.form("form_cadastro_oae"):

    col1, col2 = st.columns(2)

    with col1:
        nome_oae = st.text_input("Nome da OAE")

        codigo_oae = st.text_input(
            "Código ou identificação da OAE"
        )

        rodovia = st.text_input("Rodovia")

        municipio = st.text_input("Município")

        uf = st.selectbox(
            "UF",
            [
                "AC", "AL", "AP", "AM", "BA", "CE", "DF",
                "ES", "GO", "MA", "MT", "MS", "MG", "PA",
                "PB", "PR", "PE", "PI", "RJ", "RN", "RS",
                "RO", "RR", "SC", "SP", "SE", "TO"
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

    observacoes = st.text_area("Observações")

    enviar = st.form_submit_button("Salvar cadastro")


if enviar:

    if nome_oae == "":
        st.error("O nome da OAE é obrigatório.")

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

        db.add(nova_oae)
        db.commit()
        db.refresh(nova_oae)

        id_gerado = nova_oae.id

        db.close()

        st.success(
            f"OAE cadastrada com sucesso. ID gerado: {id_gerado}"
        )

        st.write("### Dados cadastrados")

        st.write("Nome da OAE:", nome_oae)
        st.write("Código:", codigo_oae)
        st.write("Rodovia:", rodovia)
        st.write("Município:", municipio)
        st.write("UF:", uf)
        st.write("Ano de construção:", ano_construcao)
        st.write("Tipo estrutural:", tipo_estrutura)
        st.write("Número de vãos:", numero_vaos)
        st.write("Comprimento total:", comprimento_total, "m")
        st.write("Largura:", largura, "m")
        st.write("Tipo de protensão:", tipo_protensao)
        st.write("Observações:", observacoes)


st.divider()

st.header("OAEs cadastradas")

db = SessionLocal()

oaes = db.query(
    models.OAE
).order_by(
    models.OAE.id
).all()

db.close()


if len(oaes) == 0:

    st.info("Nenhuma OAE cadastrada.")

else:

    dados_oaes = []

    for oae in oaes:
        dados_oaes.append(
            {
                "ID": oae.id,
                "Nome": oae.nome,
                "Código": oae.codigo,
                "Rodovia": oae.rodovia,
                "Município": oae.municipio,
                "UF": oae.uf,
                "Tipo estrutural": oae.tipo_estrutura
            }
        )

    st.dataframe(
        dados_oaes,
        width="stretch"
    )

    st.subheader("Selecionar OAE ativa")

    opcoes_oae = {
        f"{oae.id} - {oae.nome}": oae
        for oae in oaes
    }

    oae_escolhida = st.selectbox(
        "Escolha uma OAE",
        options=list(opcoes_oae.keys())
    )

    oae_ativa = opcoes_oae[oae_escolhida]

    st.success(
        f"OAE ativa: {oae_ativa.nome}"
    )

    st.write("### Dados da OAE selecionada")

    st.write("ID:", oae_ativa.id)
    st.write("Nome:", oae_ativa.nome)
    st.write("Código:", oae_ativa.codigo)
    st.write("Rodovia:", oae_ativa.rodovia)
    st.write("Município:", oae_ativa.municipio)
    st.write("UF:", oae_ativa.uf)
    st.write("Tipo estrutural:", oae_ativa.tipo_estrutura)

    st.divider()

    st.header("Cadastro de componente")

    st.write(
        f"Componente vinculado à OAE: "
        f"{oae_ativa.id} - {oae_ativa.nome}"
    )

    with st.form("form_cadastro_componente"):

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

        salvar_componente = st.form_submit_button(
            "Salvar componente"
        )

    if salvar_componente:

        if nome_componente == "":
            st.error(
                "O nome ou identificação do componente é obrigatório."
            )

        else:
            db = SessionLocal()

            novo_componente = models.Componente(
                oae_id=oae_ativa.id,
                categoria=categoria_componente,
                nome=nome_componente,
                classificacao_elemento=classificacao_elemento,
                observacoes=observacoes_componente
            )

            db.add(novo_componente)
            db.commit()
            db.refresh(novo_componente)

            componente_id = novo_componente.id

            db.close()

            st.success(
                f"Componente cadastrado com sucesso. "
                f"ID gerado: {componente_id}"
            )

    st.divider()

    st.header("Componentes cadastrados da OAE ativa")

    db = SessionLocal()

    componentes = db.query(
        models.Componente
    ).filter(
        models.Componente.oae_id == oae_ativa.id
    ).order_by(
        models.Componente.id
    ).all()

    db.close()

    if len(componentes) == 0:

        st.info(
            "Nenhum componente cadastrado para esta OAE."
        )

    else:

        dados_componentes = []

        for componente in componentes:
            dados_componentes.append(
                {
                    "ID": componente.id,
                    "Categoria": componente.categoria,
                    "Elemento": componente.nome,
                    "Classificação": componente.classificacao_elemento,
                    "Observações": componente.observacoes
                }
            )

        st.dataframe(
            dados_componentes,
            width="stretch"
        )

        st.subheader("Selecionar componente ativo")

        opcoes_componentes = {
            f"{componente.id} - {componente.nome}": componente
            for componente in componentes
        }

        componente_escolhido = st.selectbox(
            "Escolha um componente",
            options=list(opcoes_componentes.keys())
        )

        componente_ativo = opcoes_componentes[
            componente_escolhido
        ]

        st.success(
            f"Componente ativo: {componente_ativo.nome}"
        )

        st.write("### Dados do componente selecionado")

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