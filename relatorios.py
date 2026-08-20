import streamlit as st

from datetime import datetime
from html import escape
from io import BytesIO
from pathlib import Path

from database import SessionLocal
import models


# ============================================================
# RELATÓRIOS DO GÊMEO DIGITAL
#
# O módulo consolida informações já registradas nos demais
# módulos. Ele não cria diagnóstico, classificação ou
# recomendação técnica automaticamente.
#
# A responsabilidade pelas informações técnicas e pela
# validação do relatório permanece com o profissional.
# ============================================================


# ============================================================
# REPORTLAB
#
# O PDF é opcional para evitar que a ausência da biblioteca
# impeça a inicialização de todo o sistema.
# ============================================================

try:
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import (
        getSampleStyleSheet,
        ParagraphStyle,
    )
    from reportlab.lib.units import mm
    from reportlab.platypus import (
        SimpleDocTemplate,
        Paragraph,
        Spacer,
        Table,
        TableStyle,
        PageBreak,
        KeepTogether,
        HRFlowable,
    )

    REPORTLAB_DISPONIVEL = True

except Exception:
    REPORTLAB_DISPONIVEL = False


# ============================================================
# FUNÇÕES AUXILIARES
# ============================================================

def texto(valor, padrao="Não informado"):

    if valor is None:
        return padrao

    valor_str = str(valor).strip()

    if valor_str == "":
        return padrao

    return valor_str


def data_br(valor):

    if valor is None:
        return "Não informado"

    try:
        return valor.strftime("%d/%m/%Y")

    except Exception:
        return texto(valor)


def numero_br(valor, casas=2):

    if valor is None:
        return "Não informado"

    try:
        return f"{float(valor):.{casas}f}".replace(".", ",")

    except Exception:
        return texto(valor)


def sanitizar_nome_arquivo(valor):

    valor = texto(
        valor,
        "relatorio",
    )

    permitidos = []

    for caractere in valor:

        if (
            caractere.isalnum()
            or caractere in ["-", "_"]
        ):
            permitidos.append(
                caractere
            )

        elif caractere in [" ", ".", "/"]:

            permitidos.append("_")

    resultado = "".join(
        permitidos
    ).strip("_")

    if resultado == "":
        resultado = "relatorio"

    return resultado


def dict_objeto(objeto, campos):

    dados = {}

    if objeto is None:
        return dados

    for campo, titulo in campos:

        dados[titulo] = getattr(
            objeto,
            campo,
            None,
        )

    return dados


# ============================================================
# CONSULTAS GERAIS
# ============================================================

def buscar_inspecoes_oae(oae_id):

    db = SessionLocal()

    dados = (
        db.query(models.Inspecao)
        .filter(
            models.Inspecao.oae_id
            == oae_id
        )
        .order_by(
            models.Inspecao.data_inspecao.desc(),
            models.Inspecao.id.desc(),
        )
        .all()
    )

    db.close()

    return dados


def buscar_componentes_oae(oae_id):

    db = SessionLocal()

    dados = (
        db.query(models.Componente)
        .filter(
            models.Componente.oae_id
            == oae_id
        )
        .order_by(
            models.Componente.categoria,
            models.Componente.nome,
            models.Componente.id,
        )
        .all()
    )

    db.close()

    return dados


def buscar_classificacoes_inspecao(inspecao_id):

    db = SessionLocal()

    dados = (
        db.query(models.Classificacao)
        .filter(
            models.Classificacao.inspecao_id
            == inspecao_id
        )
        .order_by(
            models.Classificacao.componente_id
        )
        .all()
    )

    db.close()

    return dados


def buscar_fotografias_inspecao(inspecao_id):

    db = SessionLocal()

    dados = (
        db.query(models.Fotografia)
        .filter(
            models.Fotografia.inspecao_id
            == inspecao_id
        )
        .order_by(
            models.Fotografia.data_foto,
            models.Fotografia.id,
        )
        .all()
    )

    db.close()

    return dados


def buscar_anomalias_oae(oae_id):

    db = SessionLocal()

    dados = (
        db.query(models.AnomaliaPermanente)
        .filter(
            models.AnomaliaPermanente.oae_id
            == oae_id
        )
        .order_by(
            models.AnomaliaPermanente.componente_id,
            models.AnomaliaPermanente.id,
        )
        .all()
    )

    db.close()

    return dados


def buscar_anomalias_relacionadas_inspecao(
    oae_id,
    inspecao,
):

    todas = buscar_anomalias_oae(
        oae_id
    )

    resultado = []

    db = SessionLocal()

    for anomalia in todas:

        origem = (
            db.query(models.Inspecao)
            .filter(
                models.Inspecao.id
                == anomalia.inspecao_origem_id
            )
            .first()
        )

        if origem is None:
            continue

        nasceu_antes_ou_na_inspecao = (
            origem.data_inspecao
            < inspecao.data_inspecao
            or (
                origem.data_inspecao
                == inspecao.data_inspecao
                and origem.id
                <= inspecao.id
            )
        )

        if not nasceu_antes_ou_na_inspecao:
            continue

        observacao = (
            db.query(models.ObservacaoAnomalia)
            .filter(
                models.ObservacaoAnomalia.anomalia_id
                == anomalia.id
            )
            .filter(
                models.ObservacaoAnomalia.inspecao_id
                == inspecao.id
            )
            .first()
        )

        if (
            anomalia.inspecao_origem_id
            == inspecao.id
            or observacao is not None
        ):

            resultado.append(
                (
                    anomalia,
                    observacao,
                )
            )

    db.close()

    return resultado


def mapa_componentes(oae_id):

    return {
        item.id: item
        for item in buscar_componentes_oae(
            oae_id
        )
    }


# ============================================================
# CLASSIFICAÇÃO CONSOLIDADA
#
# A consolidação abaixo considera a menor nota atribuída
# entre os componentes para cada parâmetro.
#
# É apenas consolidação de registros já informados pelo
# profissional no módulo de classificação.
# ============================================================

def consolidar_classificacao(classificacoes):

    if len(classificacoes) == 0:

        return {
            "estrutural": None,
            "funcional": None,
            "durabilidade": None,
        }

    estruturais = [
        item.nota_estrutural
        for item in classificacoes
        if item.nota_estrutural is not None
    ]

    funcionais = [
        item.nota_funcional
        for item in classificacoes
        if item.nota_funcional is not None
    ]

    durabilidades = [
        item.nota_durabilidade
        for item in classificacoes
        if item.nota_durabilidade is not None
    ]

    return {
        "estrutural":
            min(estruturais)
            if len(estruturais) > 0
            else None,

        "funcional":
            min(funcionais)
            if len(funcionais) > 0
            else None,

        "durabilidade":
            min(durabilidades)
            if len(durabilidades) > 0
            else None,
    }


# ============================================================
# DADOS ESPECÍFICOS DE CADA MODALIDADE
# ============================================================

def buscar_detalhe_generico(inspecao_id):

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


def buscar_dados_cadastral(inspecao_id):

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


def buscar_dados_rotineira(inspecao_id):

    try:
        from rotineira import RegistroRotineira

    except Exception:
        return None

    db = SessionLocal()

    dado = (
        db.query(RegistroRotineira)
        .filter(
            RegistroRotineira.inspecao_id
            == inspecao_id
        )
        .first()
    )

    db.close()

    return dado


def buscar_dados_especial(inspecao_id):

    try:
        from especial import RegistroEspecial

    except Exception:
        return None

    db = SessionLocal()

    dado = (
        db.query(RegistroEspecial)
        .filter(
            RegistroEspecial.inspecao_id
            == inspecao_id
        )
        .first()
    )

    db.close()

    return dado


def buscar_dados_extraordinaria(inspecao_id):

    try:
        from extraordinaria import RegistroExtraordinaria

    except Exception:
        return None

    db = SessionLocal()

    dado = (
        db.query(RegistroExtraordinaria)
        .filter(
            RegistroExtraordinaria.inspecao_id
            == inspecao_id
        )
        .first()
    )

    db.close()

    return dado


def secoes_especificas_inspecao(inspecao):

    tipo = (
        inspecao.tipo_inspecao
        or ""
    ).strip()

    secoes = []

    detalhe = buscar_detalhe_generico(
        inspecao.id
    )

    if detalhe is not None:

        campos_detalhe = [
            (
                "procedimento_utilizado",
                "Procedimento utilizado",
            ),
            (
                "ensaios_previstos",
                "Ensaios previstos",
            ),
            (
                "diagnostico",
                "Diagnóstico",
            ),
            (
                "recomendacoes",
                "Recomendações",
            ),
        ]

        dados = dict_objeto(
            detalhe,
            campos_detalhe,
        )

        if any(
            texto(v, "") != ""
            for v in dados.values()
        ):

            secoes.append(
                (
                    "Informações técnicas gerais",
                    dados,
                )
            )

    if tipo == "Cadastral":

        registro = buscar_dados_cadastral(
            inspecao.id
        )

        if registro is not None:

            campos = []

            for coluna in registro.__table__.columns:

                if coluna.name in [
                    "id",
                    "inspecao_id",
                ]:
                    continue

                titulo = (
                    coluna.name
                    .replace("_", " ")
                    .strip()
                    .capitalize()
                )

                campos.append(
                    (
                        coluna.name,
                        titulo,
                    )
                )

            secoes.append(
                (
                    "Dados da inspeção cadastral",
                    dict_objeto(
                        registro,
                        campos,
                    ),
                )
            )

    elif tipo == "Rotineira":

        registro = buscar_dados_rotineira(
            inspecao.id
        )

        if registro is not None:

            campos = [
                (
                    "reparos",
                    "Reparos",
                ),
                (
                    "alargamento",
                    "Alargamento",
                ),
                (
                    "reforcos",
                    "Reforços",
                ),
                (
                    "outras_intervencoes",
                    "Outras intervenções",
                ),
                (
                    "comentarios_alteracoes",
                    "Alterações em relação à inspeção anterior",
                ),
                (
                    "informacoes_complementares",
                    "Informações complementares",
                ),
                (
                    "recomendacoes_terapeuticas",
                    "Recomendações terapêuticas",
                ),
                (
                    "abrangencia_fotografica",
                    "Abrangência fotográfica",
                ),
            ]

            secoes.append(
                (
                    "Síntese da inspeção rotineira",
                    dict_objeto(
                        registro,
                        campos,
                    ),
                )
            )

    elif tipo == "Especial":

        registro = buscar_dados_especial(
            inspecao.id
        )

        if registro is not None:

            secoes.append(
                (
                    "Localização - inspeção especial",
                    dict_objeto(
                        registro,
                        [
                            (
                                "rodovia_ferrovia",
                                "Rodovia ou ferrovia",
                            ),
                            (
                                "nome_obra",
                                "Nome da obra",
                            ),
                            (
                                "quilometro",
                                "Quilômetro",
                            ),
                            (
                                "coordenadas",
                                "Coordenadas",
                            ),
                            (
                                "sentido",
                                "Sentido",
                            ),
                            (
                                "jurisdicao",
                                "Jurisdição",
                            ),
                        ],
                    ),
                )
            )

            secoes.append(
                (
                    "Descrição da obra - inspeção especial",
                    dict_objeto(
                        registro,
                        [
                            (
                                "descricao_obra",
                                "Descrição da obra",
                            ),
                            (
                                "historico_obra",
                                "Histórico da obra",
                            ),
                            (
                                "classe_portante",
                                "Classe portante provável",
                            ),
                            (
                                "desenhos_memoriais",
                                "Desenhos e memoriais",
                            ),
                            (
                                "diferencas_projeto_original",
                                "Diferenças do projeto original",
                            ),
                            (
                                "condicoes_ambientais",
                                "Condições ambientais",
                            ),
                            (
                                "caracteristicas_trafego",
                                "Características do tráfego",
                            ),
                        ],
                    ),
                )
            )

            secoes.append(
                (
                    "Patologia - inspeção especial",
                    dict_objeto(
                        registro,
                        [
                            (
                                "sintese_patologia",
                                "Síntese de patologia",
                            ),
                            (
                                "mecanismo_deterioracao",
                                "Mecanismos de deterioração",
                            ),
                            (
                                "causas_provaveis",
                                "Causas prováveis",
                            ),
                        ],
                    ),
                )
            )

            secoes.append(
                (
                    "Ensaios - inspeção especial",
                    dict_objeto(
                        registro,
                        [
                            (
                                "descricao_ensaios",
                                "Descrição dos ensaios",
                            ),
                            (
                                "localizacao_ensaios",
                                "Localização dos ensaios",
                            ),
                            (
                                "resultados_ensaios",
                                "Resultados",
                            ),
                            (
                                "interpretacao_ensaios",
                                "Interpretação",
                            ),
                            (
                                "metodologia_ensaios",
                                "Metodologia",
                            ),
                            (
                                "normas_referencia_ensaios",
                                "Normas de referência",
                            ),
                        ],
                    ),
                )
            )

            secoes.append(
                (
                    "Diagnóstico e terapia - inspeção especial",
                    dict_objeto(
                        registro,
                        [
                            (
                                "diagnostico",
                                "Diagnóstico",
                            ),
                            (
                                "resumo_analise_estrutural",
                                "Resumo da análise estrutural",
                            ),
                            (
                                "terapia_recomendada",
                                "Terapia recomendada",
                            ),
                            (
                                "metodologia_recuperacao",
                                "Metodologia de recuperação",
                            ),
                            (
                                "reparos_recomendados",
                                "Reparos recomendados",
                            ),
                            (
                                "recuperacao_recomendada",
                                "Recuperação recomendada",
                            ),
                            (
                                "reforco_recomendado",
                                "Reforço recomendado",
                            ),
                            (
                                "conclusoes_recomendacoes",
                                "Conclusões e recomendações",
                            ),
                        ],
                    ),
                )
            )

            secoes.append(
                (
                    "Relatórios complementares - inspeção especial",
                    dict_objeto(
                        registro,
                        [
                            (
                                "necessidade_relatorios_complementares",
                                "Necessidade de relatórios complementares",
                            ),
                            (
                                "relatorios_complementares",
                                "Relatórios complementares",
                            ),
                            (
                                "justificativa_relatorios",
                                "Justificativa",
                            ),
                        ],
                    ),
                )
            )

    elif tipo in [
        "Extraordinária",
        "Extraordinaria",
    ]:

        registro = buscar_dados_extraordinaria(
            inspecao.id
        )

        if registro is not None:

            campos = []

            for coluna in registro.__table__.columns:

                if coluna.name in [
                    "id",
                    "inspecao_id",
                ]:
                    continue

                titulo = (
                    coluna.name
                    .replace("_", " ")
                    .strip()
                    .capitalize()
                )

                campos.append(
                    (
                        coluna.name,
                        titulo,
                    )
                )

            secoes.append(
                (
                    "Dados da inspeção extraordinária",
                    dict_objeto(
                        registro,
                        campos,
                    ),
                )
            )

    return secoes


# ============================================================
# MONTAGEM DOS DADOS DO RELATÓRIO
# ============================================================

def montar_relatorio_inspecao(
    oae,
    inspecao,
):

    componentes = mapa_componentes(
        oae.id
    )

    classificacoes = (
        buscar_classificacoes_inspecao(
            inspecao.id
        )
    )

    classificacao_geral = (
        consolidar_classificacao(
            classificacoes
        )
    )

    fotografias = (
        buscar_fotografias_inspecao(
            inspecao.id
        )
    )

    anomalias = (
        buscar_anomalias_relacionadas_inspecao(
            oae.id,
            inspecao,
        )
    )

    return {
        "oae": oae,
        "inspecao": inspecao,
        "componentes": componentes,
        "classificacoes": classificacoes,
        "classificacao_geral": classificacao_geral,
        "fotografias": fotografias,
        "anomalias": anomalias,
        "secoes_especificas":
            secoes_especificas_inspecao(
                inspecao
            ),
    }


def montar_relatorio_consolidado(
    oae,
):

    inspecoes = buscar_inspecoes_oae(
        oae.id
    )

    componentes = buscar_componentes_oae(
        oae.id
    )

    anomalias = buscar_anomalias_oae(
        oae.id
    )

    campanhas = []

    for inspecao in reversed(
        inspecoes
    ):

        classificacoes = (
            buscar_classificacoes_inspecao(
                inspecao.id
            )
        )

        campanhas.append(
            {
                "inspecao": inspecao,
                "classificacao":
                    consolidar_classificacao(
                        classificacoes
                    ),
                "quantidade_fotos":
                    len(
                        buscar_fotografias_inspecao(
                            inspecao.id
                        )
                    ),
            }
        )

    return {
        "oae": oae,
        "inspecoes": inspecoes,
        "componentes": componentes,
        "anomalias": anomalias,
        "campanhas": campanhas,
    }


# ============================================================
# HTML - RELATÓRIO DE INSPEÇÃO
# ============================================================

def html_cabecalho(
    titulo,
):

    return f"""
    <!DOCTYPE html>
    <html lang="pt-BR">
    <head>
        <meta charset="utf-8">
        <title>{escape(titulo)}</title>

        <style>
            body {{
                font-family: Arial, Helvetica, sans-serif;
                margin: 38px;
                color: #222;
                line-height: 1.45;
            }}

            h1 {{
                font-size: 25px;
                margin-bottom: 3px;
            }}

            h2 {{
                margin-top: 30px;
                border-bottom: 1px solid #aaa;
                padding-bottom: 5px;
            }}

            h3 {{
                margin-top: 22px;
            }}

            table {{
                width: 100%;
                border-collapse: collapse;
                margin: 12px 0 22px 0;
            }}

            th, td {{
                border: 1px solid #bbb;
                padding: 7px;
                text-align: left;
                vertical-align: top;
            }}

            th {{
                background: #f2f2f2;
            }}

            .aviso {{
                padding: 12px;
                border: 1px solid #aaa;
                background: #fafafa;
                margin: 18px 0;
            }}

            .rodape {{
                margin-top: 40px;
                font-size: 11px;
                color: #666;
            }}
        </style>
    </head>
    <body>
    """


def html_linha(
    titulo,
    valor,
):

    return (
        "<tr>"
        f"<th>{escape(texto(titulo))}</th>"
        f"<td>{escape(texto(valor))}</td>"
        "</tr>"
    )


def gerar_html_inspecao(
    dados,
):

    oae = dados["oae"]
    inspecao = dados["inspecao"]
    componentes = dados["componentes"]

    partes = [
        html_cabecalho(
            "Relatório de inspeção"
        ),
        "<h1>Relatório de inspeção de OAE</h1>",
        (
            "<div class='aviso'>"
            "Documento gerado a partir dos registros do "
            "Gêmeo Digital. O diagnóstico, a classificação "
            "e as decisões técnicas devem ser validados "
            "pelo profissional responsável."
            "</div>"
        ),
        "<h2>1. Identificação da OAE</h2>",
        "<table>",
        html_linha(
            "Nome",
            oae.nome,
        ),
        html_linha(
            "Código",
            oae.codigo,
        ),
        html_linha(
            "Rodovia",
            oae.rodovia,
        ),
        html_linha(
            "Município / UF",
            (
                f"{texto(oae.municipio, '')}"
                f"{' / ' if oae.municipio and oae.uf else ''}"
                f"{texto(oae.uf, '')}"
            ),
        ),
        html_linha(
            "Tipo de estrutura",
            oae.tipo_estrutura,
        ),
        html_linha(
            "Número de vãos",
            oae.numero_vaos,
        ),
        html_linha(
            "Comprimento total (m)",
            numero_br(
                oae.comprimento_total
            ),
        ),
        html_linha(
            "Largura (m)",
            numero_br(
                oae.largura
            ),
        ),
        "</table>",
        "<h2>2. Identificação da inspeção</h2>",
        "<table>",
        html_linha(
            "Tipo",
            inspecao.tipo_inspecao,
        ),
        html_linha(
            "Data",
            data_br(
                inspecao.data_inspecao
            ),
        ),
        html_linha(
            "Responsável",
            inspecao.responsavel,
        ),
        html_linha(
            "Registro profissional",
            inspecao.registro_profissional,
        ),
        html_linha(
            "Observações",
            inspecao.observacoes,
        ),
        "</table>",
    ]

    for titulo_secao, campos in dados[
        "secoes_especificas"
    ]:

        partes.append(
            f"<h2>{escape(titulo_secao)}</h2>"
        )

        partes.append(
            "<table>"
        )

        for titulo, valor in campos.items():

            partes.append(
                html_linha(
                    titulo,
                    valor,
                )
            )

        partes.append(
            "</table>"
        )

    partes.extend(
        [
            "<h2>3. Anomalias relacionadas à campanha</h2>",
        ]
    )

    if len(
        dados["anomalias"]
    ) == 0:

        partes.append(
            "<p>Nenhuma anomalia relacionada a esta "
            "campanha foi localizada no banco de dados.</p>"
        )

    else:

        partes.append(
            """
            <table>
                <tr>
                    <th>ID</th>
                    <th>Componente</th>
                    <th>Anomalia</th>
                    <th>Localização</th>
                    <th>Situação nesta campanha</th>
                    <th>Abertura (mm)</th>
                    <th>Extensão (cm)</th>
                </tr>
            """
        )

        for anomalia, observacao in dados[
            "anomalias"
        ]:

            componente = componentes.get(
                anomalia.componente_id
            )

            partes.append(
                "<tr>"
                f"<td>{anomalia.id}</td>"
                f"<td>{escape(texto(componente.nome if componente else None))}</td>"
                f"<td>{escape(texto(anomalia.tipo_anomalia))}</td>"
                f"<td>{escape(texto(anomalia.localizacao_referencia))}</td>"
                f"<td>{escape(texto(observacao.situacao_observada if observacao else 'Registrada nesta inspeção'))}</td>"
                f"<td>{escape(numero_br(observacao.abertura_fissura_mm) if observacao else 'Não informado')}</td>"
                f"<td>{escape(numero_br(observacao.extensao_anomalia_cm) if observacao else 'Não informado')}</td>"
                "</tr>"
            )

        partes.append(
            "</table>"
        )

    partes.append(
        "<h2>4. Classificação</h2>"
    )

    classificacao = dados[
        "classificacao_geral"
    ]

    partes.extend(
        [
            "<table>",
            html_linha(
                "Estrutural",
                classificacao["estrutural"],
            ),
            html_linha(
                "Funcional",
                (
                    classificacao["funcional"]
                    if classificacao["funcional"] is not None
                    else "Não se aplica / não informado"
                ),
            ),
            html_linha(
                "Durabilidade",
                classificacao["durabilidade"],
            ),
            "</table>",
        ]
    )

    if len(
        dados["classificacoes"]
    ) > 0:

        partes.append(
            """
            <table>
                <tr>
                    <th>Componente</th>
                    <th>Estrutural</th>
                    <th>Funcional</th>
                    <th>Durabilidade</th>
                </tr>
            """
        )

        for classificacao_item in dados[
            "classificacoes"
        ]:

            componente = componentes.get(
                classificacao_item.componente_id
            )

            partes.append(
                "<tr>"
                f"<td>{escape(texto(componente.nome if componente else classificacao_item.componente_id))}</td>"
                f"<td>{escape(texto(classificacao_item.nota_estrutural))}</td>"
                f"<td>{escape(texto(classificacao_item.nota_funcional, 'NA'))}</td>"
                f"<td>{escape(texto(classificacao_item.nota_durabilidade))}</td>"
                "</tr>"
            )

        partes.append(
            "</table>"
        )

    partes.append(
        "<h2>5. Registro fotográfico</h2>"
    )

    if len(
        dados["fotografias"]
    ) == 0:

        partes.append(
            "<p>Nenhum registro fotográfico localizado "
            "para esta campanha.</p>"
        )

    else:

        partes.append(
            """
            <table>
                <tr>
                    <th>ID</th>
                    <th>Data</th>
                    <th>Identificação</th>
                    <th>Tipo</th>
                    <th>Arquivo</th>
                    <th>Observações</th>
                </tr>
            """
        )

        for foto in dados[
            "fotografias"
        ]:

            partes.append(
                "<tr>"
                f"<td>{foto.id}</td>"
                f"<td>{escape(data_br(foto.data_foto))}</td>"
                f"<td>{escape(texto(foto.identificacao))}</td>"
                f"<td>{escape(texto(foto.tipo_registro))}</td>"
                f"<td>{escape(texto(foto.nome_arquivo))}</td>"
                f"<td>{escape(texto(foto.observacoes))}</td>"
                "</tr>"
            )

        partes.append(
            "</table>"
        )

    partes.extend(
        [
            "<div class='rodape'>",
            (
                "Gerado pelo Gêmeo Digital para Inspeção "
                f"de Pontes em {datetime.now().strftime('%d/%m/%Y %H:%M')}."
            ),
            "</div>",
            "</body></html>",
        ]
    )

    return "".join(
        partes
    )


# ============================================================
# HTML - RELATÓRIO CONSOLIDADO DA OAE
# ============================================================

def gerar_html_consolidado(
    dados,
):

    oae = dados["oae"]

    partes = [
        html_cabecalho(
            "Relatório consolidado da OAE"
        ),
        "<h1>Relatório consolidado da OAE</h1>",
        (
            "<div class='aviso'>"
            "Síntese histórica produzida a partir dos dados "
            "registrados no sistema. A interpretação técnica "
            "deve ser realizada pelo profissional responsável."
            "</div>"
        ),
        "<h2>1. Identificação</h2>",
        "<table>",
        html_linha(
            "Nome",
            oae.nome,
        ),
        html_linha(
            "Código",
            oae.codigo,
        ),
        html_linha(
            "Rodovia",
            oae.rodovia,
        ),
        html_linha(
            "Município / UF",
            (
                f"{texto(oae.municipio, '')}"
                f"{' / ' if oae.municipio and oae.uf else ''}"
                f"{texto(oae.uf, '')}"
            ),
        ),
        html_linha(
            "Tipo de estrutura",
            oae.tipo_estrutura,
        ),
        html_linha(
            "Ano de construção",
            oae.ano_construcao,
        ),
        html_linha(
            "Número de vãos",
            oae.numero_vaos,
        ),
        "</table>",
        "<h2>2. Componentes cadastrados</h2>",
    ]

    if len(
        dados["componentes"]
    ) == 0:

        partes.append(
            "<p>Nenhum componente cadastrado.</p>"
        )

    else:

        partes.append(
            """
            <table>
                <tr>
                    <th>ID</th>
                    <th>Categoria</th>
                    <th>Componente</th>
                    <th>Classificação do elemento</th>
                </tr>
            """
        )

        for componente in dados[
            "componentes"
        ]:

            partes.append(
                "<tr>"
                f"<td>{componente.id}</td>"
                f"<td>{escape(texto(componente.categoria))}</td>"
                f"<td>{escape(texto(componente.nome))}</td>"
                f"<td>{escape(texto(componente.classificacao_elemento))}</td>"
                "</tr>"
            )

        partes.append(
            "</table>"
        )

    partes.append(
        "<h2>3. Histórico das inspeções e classificações</h2>"
    )

    if len(
        dados["campanhas"]
    ) == 0:

        partes.append(
            "<p>Nenhuma inspeção cadastrada.</p>"
        )

    else:

        partes.append(
            """
            <table>
                <tr>
                    <th>Data</th>
                    <th>Tipo</th>
                    <th>Estrutural</th>
                    <th>Funcional</th>
                    <th>Durabilidade</th>
                    <th>Fotos</th>
                </tr>
            """
        )

        for campanha in dados[
            "campanhas"
        ]:

            inspecao = campanha[
                "inspecao"
            ]

            classificacao = campanha[
                "classificacao"
            ]

            partes.append(
                "<tr>"
                f"<td>{escape(data_br(inspecao.data_inspecao))}</td>"
                f"<td>{escape(texto(inspecao.tipo_inspecao))}</td>"
                f"<td>{escape(texto(classificacao['estrutural']))}</td>"
                f"<td>{escape(texto(classificacao['funcional'], 'NA'))}</td>"
                f"<td>{escape(texto(classificacao['durabilidade']))}</td>"
                f"<td>{campanha['quantidade_fotos']}</td>"
                "</tr>"
            )

        partes.append(
            "</table>"
        )

    partes.append(
        "<h2>4. Inventário das anomalias</h2>"
    )

    if len(
        dados["anomalias"]
    ) == 0:

        partes.append(
            "<p>Nenhuma anomalia permanente cadastrada.</p>"
        )

    else:

        componentes = {
            item.id: item
            for item in dados[
                "componentes"
            ]
        }

        partes.append(
            """
            <table>
                <tr>
                    <th>ID</th>
                    <th>Componente</th>
                    <th>Tipo</th>
                    <th>Localização</th>
                    <th>Status</th>
                </tr>
            """
        )

        for anomalia in dados[
            "anomalias"
        ]:

            componente = componentes.get(
                anomalia.componente_id
            )

            partes.append(
                "<tr>"
                f"<td>{anomalia.id}</td>"
                f"<td>{escape(texto(componente.nome if componente else None))}</td>"
                f"<td>{escape(texto(anomalia.tipo_anomalia))}</td>"
                f"<td>{escape(texto(anomalia.localizacao_referencia))}</td>"
                f"<td>{'Ativa' if anomalia.ativa else 'Encerrada'}</td>"
                "</tr>"
            )

        partes.append(
            "</table>"
        )

    partes.extend(
        [
            "<div class='rodape'>",
            (
                "Gerado pelo Gêmeo Digital para Inspeção "
                f"de Pontes em {datetime.now().strftime('%d/%m/%Y %H:%M')}."
            ),
            "</div>",
            "</body></html>",
        ]
    )

    return "".join(
        partes
    )



# ============================================================
# IDENTIDADE VISUAL DOS RELATÓRIOS
# ============================================================

COR_PRIMARIA = colors.HexColor("#17365D") if REPORTLAB_DISPONIVEL else None
COR_SECUNDARIA = colors.HexColor("#2F75B5") if REPORTLAB_DISPONIVEL else None
COR_DESTAQUE = colors.HexColor("#E67E22") if REPORTLAB_DISPONIVEL else None
COR_FUNDO_CLARO = colors.HexColor("#F5F8FC") if REPORTLAB_DISPONIVEL else None
COR_LINHA = colors.HexColor("#D9E2F3") if REPORTLAB_DISPONIVEL else None
COR_TEXTO = colors.HexColor("#263238") if REPORTLAB_DISPONIVEL else None
COR_TEXTO_SUAVE = colors.HexColor("#607D8B") if REPORTLAB_DISPONIVEL else None

COR_NOTA_5 = colors.HexColor("#1B5E20") if REPORTLAB_DISPONIVEL else None
COR_NOTA_4 = colors.HexColor("#43A047") if REPORTLAB_DISPONIVEL else None
COR_NOTA_3 = colors.HexColor("#F9A825") if REPORTLAB_DISPONIVEL else None
COR_NOTA_2 = colors.HexColor("#EF6C00") if REPORTLAB_DISPONIVEL else None
COR_NOTA_1 = colors.HexColor("#C62828") if REPORTLAB_DISPONIVEL else None
COR_NOTA_NA = colors.HexColor("#78909C") if REPORTLAB_DISPONIVEL else None


def cor_nota(valor):

    try:
        nota = int(valor)
    except Exception:
        return COR_NOTA_NA

    mapa = {
        5: COR_NOTA_5,
        4: COR_NOTA_4,
        3: COR_NOTA_3,
        2: COR_NOTA_2,
        1: COR_NOTA_1,
    }

    return mapa.get(
        nota,
        COR_NOTA_NA,
    )


def estilos_pdf_profissional():

    estilos_base = getSampleStyleSheet()

    return {
        "titulo": ParagraphStyle(
            "RelTituloPrincipal",
            parent=estilos_base["Title"],
            fontName="Helvetica-Bold",
            fontSize=19,
            leading=23,
            textColor=colors.white,
            alignment=TA_LEFT,
            spaceAfter=0,
        ),

        "subtitulo": ParagraphStyle(
            "RelSubtitulo",
            parent=estilos_base["BodyText"],
            fontName="Helvetica",
            fontSize=8.5,
            leading=11,
            textColor=colors.HexColor("#DCE6F1"),
            alignment=TA_LEFT,
        ),

        "secao": ParagraphStyle(
            "RelSecao",
            parent=estilos_base["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=12,
            leading=15,
            textColor=COR_PRIMARIA,
            spaceBefore=9,
            spaceAfter=6,
        ),

        "subsecao": ParagraphStyle(
            "RelSubsecao",
            parent=estilos_base["Heading3"],
            fontName="Helvetica-Bold",
            fontSize=9.5,
            leading=12,
            textColor=COR_SECUNDARIA,
            spaceBefore=7,
            spaceAfter=4,
        ),

        "normal": ParagraphStyle(
            "RelNormal",
            parent=estilos_base["BodyText"],
            fontName="Helvetica",
            fontSize=8.2,
            leading=11,
            textColor=COR_TEXTO,
        ),

        "normal_pequeno": ParagraphStyle(
            "RelNormalPequeno",
            parent=estilos_base["BodyText"],
            fontName="Helvetica",
            fontSize=7.2,
            leading=9,
            textColor=COR_TEXTO,
        ),

        "rotulo": ParagraphStyle(
            "RelRotulo",
            parent=estilos_base["BodyText"],
            fontName="Helvetica-Bold",
            fontSize=7.1,
            leading=8.5,
            textColor=COR_TEXTO_SUAVE,
            uppercase=True,
        ),

        "valor_card": ParagraphStyle(
            "RelValorCard",
            parent=estilos_base["BodyText"],
            fontName="Helvetica-Bold",
            fontSize=10.5,
            leading=13,
            textColor=COR_PRIMARIA,
        ),

        "aviso": ParagraphStyle(
            "RelAviso",
            parent=estilos_base["BodyText"],
            fontName="Helvetica",
            fontSize=7.5,
            leading=10,
            textColor=colors.HexColor("#5D4037"),
        ),

        "rodape": ParagraphStyle(
            "RelRodape",
            parent=estilos_base["BodyText"],
            fontName="Helvetica",
            fontSize=6.5,
            leading=8,
            textColor=COR_TEXTO_SUAVE,
        ),
    }


def _cabecalho_relatorio_pdf(
    titulo,
    subtitulo,
    estilos,
):

    conteudo = Table(
        [
            [
                Paragraph(
                    titulo,
                    estilos["titulo"],
                ),
            ],
            [
                Paragraph(
                    subtitulo,
                    estilos["subtitulo"],
                ),
            ],
        ],
        colWidths=[175 * mm],
    )

    conteudo.setStyle(
        TableStyle(
            [
                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, -1),
                    COR_PRIMARIA,
                ),
                (
                    "LEFTPADDING",
                    (0, 0),
                    (-1, -1),
                    9,
                ),
                (
                    "RIGHTPADDING",
                    (0, 0),
                    (-1, -1),
                    9,
                ),
                (
                    "TOPPADDING",
                    (0, 0),
                    (-1, 0),
                    11,
                ),
                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, 0),
                    2,
                ),
                (
                    "TOPPADDING",
                    (0, 1),
                    (-1, 1),
                    0,
                ),
                (
                    "BOTTOMPADDING",
                    (0, 1),
                    (-1, 1),
                    10,
                ),
            ]
        )
    )

    return conteudo


def _barra_secao_pdf(
    numero,
    titulo,
    estilos,
):

    tabela = Table(
        [
            [
                Paragraph(
                    str(numero),
                    ParagraphStyle(
                        f"RelNumeroSecao{numero}",
                        parent=estilos["normal"],
                        fontName="Helvetica-Bold",
                        fontSize=9,
                        leading=11,
                        textColor=colors.white,
                        alignment=TA_CENTER,
                    ),
                ),
                Paragraph(
                    escape(titulo),
                    estilos["secao"],
                ),
            ]
        ],
        colWidths=[
            10 * mm,
            165 * mm,
        ],
    )

    tabela.setStyle(
        TableStyle(
            [
                (
                    "BACKGROUND",
                    (0, 0),
                    (0, 0),
                    COR_SECUNDARIA,
                ),
                (
                    "BACKGROUND",
                    (1, 0),
                    (1, 0),
                    COR_FUNDO_CLARO,
                ),
                (
                    "BOX",
                    (0, 0),
                    (-1, -1),
                    0.5,
                    COR_LINHA,
                ),
                (
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "MIDDLE",
                ),
                (
                    "LEFTPADDING",
                    (0, 0),
                    (-1, -1),
                    6,
                ),
                (
                    "RIGHTPADDING",
                    (0, 0),
                    (-1, -1),
                    6,
                ),
                (
                    "TOPPADDING",
                    (0, 0),
                    (-1, -1),
                    5,
                ),
                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    5,
                ),
            ]
        )
    )

    return tabela


def _card_pdf(
    rotulo,
    valor,
    estilos,
    cor_borda=None,
):

    if cor_borda is None:
        cor_borda = COR_SECUNDARIA

    tabela = Table(
        [
            [
                Paragraph(
                    escape(texto(rotulo)),
                    estilos["rotulo"],
                )
            ],
            [
                Paragraph(
                    escape(texto(valor)),
                    estilos["valor_card"],
                )
            ],
        ],
        colWidths=[41 * mm],
    )

    tabela.setStyle(
        TableStyle(
            [
                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, -1),
                    colors.white,
                ),
                (
                    "BOX",
                    (0, 0),
                    (-1, -1),
                    0.7,
                    COR_LINHA,
                ),
                (
                    "LINEBEFORE",
                    (0, 0),
                    (0, -1),
                    3,
                    cor_borda,
                ),
                (
                    "LEFTPADDING",
                    (0, 0),
                    (-1, -1),
                    7,
                ),
                (
                    "RIGHTPADDING",
                    (0, 0),
                    (-1, -1),
                    6,
                ),
                (
                    "TOPPADDING",
                    (0, 0),
                    (-1, 0),
                    6,
                ),
                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, 0),
                    1,
                ),
                (
                    "TOPPADDING",
                    (0, 1),
                    (-1, 1),
                    0,
                ),
                (
                    "BOTTOMPADDING",
                    (0, 1),
                    (-1, 1),
                    7,
                ),
            ]
        )
    )

    return tabela


def _linha_cards_pdf(
    cards,
):

    tabela = Table(
        [cards],
        colWidths=[
            43.75 * mm
            for _ in cards
        ],
    )

    tabela.setStyle(
        TableStyle(
            [
                (
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "TOP",
                ),
                (
                    "LEFTPADDING",
                    (0, 0),
                    (-1, -1),
                    1.5,
                ),
                (
                    "RIGHTPADDING",
                    (0, 0),
                    (-1, -1),
                    1.5,
                ),
            ]
        )
    )

    return tabela


def _tabela_info_profissional_pdf(
    dados,
    estilos,
):

    linhas = []

    for chave, valor in dados:

        linhas.append(
            [
                Paragraph(
                    escape(texto(chave)),
                    estilos["rotulo"],
                ),
                _paragrafo_pdf(
                    valor,
                    estilos["normal"],
                ),
            ]
        )

    tabela = Table(
        linhas,
        colWidths=[
            48 * mm,
            127 * mm,
        ],
    )

    tabela.setStyle(
        TableStyle(
            [
                (
                    "BACKGROUND",
                    (0, 0),
                    (0, -1),
                    COR_FUNDO_CLARO,
                ),
                (
                    "GRID",
                    (0, 0),
                    (-1, -1),
                    0.35,
                    COR_LINHA,
                ),
                (
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "TOP",
                ),
                (
                    "LEFTPADDING",
                    (0, 0),
                    (-1, -1),
                    6,
                ),
                (
                    "RIGHTPADDING",
                    (0, 0),
                    (-1, -1),
                    6,
                ),
                (
                    "TOPPADDING",
                    (0, 0),
                    (-1, -1),
                    5,
                ),
                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    5,
                ),
            ]
        )
    )

    return tabela


def _classificacao_cards_pdf(
    classificacao,
    estilos,
):

    cards = []

    for rotulo, chave in [
        (
            "Estrutural",
            "estrutural",
        ),
        (
            "Funcional",
            "funcional",
        ),
        (
            "Durabilidade",
            "durabilidade",
        ),
    ]:

        valor = classificacao.get(
            chave
        )

        exibicao = (
            valor
            if valor is not None
            else "NA"
        )

        cards.append(
            _card_pdf(
                rotulo,
                exibicao,
                estilos,
                cor_borda=cor_nota(
                    valor
                ),
            )
        )

    tabela = Table(
        [cards],
        colWidths=[
            58.33 * mm,
            58.33 * mm,
            58.33 * mm,
        ],
    )

    tabela.setStyle(
        TableStyle(
            [
                (
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "TOP",
                ),
                (
                    "LEFTPADDING",
                    (0, 0),
                    (-1, -1),
                    2,
                ),
                (
                    "RIGHTPADDING",
                    (0, 0),
                    (-1, -1),
                    2,
                ),
            ]
        )
    )

    return tabela


def _aviso_tecnico_pdf(
    estilos,
):

    tabela = Table(
        [
            [
                Paragraph(
                    "<b>Nota técnica</b><br/>"
                    "Este documento consolida informações "
                    "registradas no Gêmeo Digital. A validação "
                    "do diagnóstico, da classificação e das "
                    "decisões de intervenção permanece sob "
                    "responsabilidade do profissional competente.",
                    estilos["aviso"],
                )
            ]
        ],
        colWidths=[175 * mm],
    )

    tabela.setStyle(
        TableStyle(
            [
                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, -1),
                    colors.HexColor("#FFF8E1"),
                ),
                (
                    "BOX",
                    (0, 0),
                    (-1, -1),
                    0.6,
                    colors.HexColor("#F0B429"),
                ),
                (
                    "LINEBEFORE",
                    (0, 0),
                    (0, -1),
                    3,
                    COR_DESTAQUE,
                ),
                (
                    "LEFTPADDING",
                    (0, 0),
                    (-1, -1),
                    8,
                ),
                (
                    "RIGHTPADDING",
                    (0, 0),
                    (-1, -1),
                    8,
                ),
                (
                    "TOPPADDING",
                    (0, 0),
                    (-1, -1),
                    7,
                ),
                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    7,
                ),
            ]
        )
    )

    return tabela


def _cabecalho_rodape_pagina(
    canvas,
    doc,
    nome_oae,
    tipo_relatorio,
):

    canvas.saveState()

    largura, altura = A4

    canvas.setFillColor(
        COR_PRIMARIA
    )

    canvas.rect(
        0,
        altura - 8 * mm,
        largura,
        8 * mm,
        fill=1,
        stroke=0,
    )

    canvas.setFont(
        "Helvetica-Bold",
        6.8,
    )

    canvas.setFillColor(
        colors.white
    )

    canvas.drawString(
        15 * mm,
        altura - 5.2 * mm,
        "GÊMEO DIGITAL PARA INSPEÇÃO DE PONTES",
    )

    canvas.setStrokeColor(
        COR_LINHA
    )

    canvas.line(
        15 * mm,
        11 * mm,
        largura - 15 * mm,
        11 * mm,
    )

    canvas.setFont(
        "Helvetica",
        6.3,
    )

    canvas.setFillColor(
        COR_TEXTO_SUAVE
    )

    canvas.drawString(
        15 * mm,
        7 * mm,
        (
            f"{texto(nome_oae)} | "
            f"{texto(tipo_relatorio)}"
        )[:95],
    )

    canvas.drawRightString(
        largura - 15 * mm,
        7 * mm,
        f"Página {doc.page}",
    )

    canvas.restoreState()


def _tabela_anomalias_pdf(
    dados,
    estilos,
):

    componentes = dados[
        "componentes"
    ]

    if len(
        dados["anomalias"]
    ) == 0:

        return _tabela_info_profissional_pdf(
            [
                (
                    "Situação",
                    (
                        "Nenhuma anomalia relacionada a esta "
                        "campanha foi localizada no banco de dados."
                    ),
                )
            ],
            estilos,
        )

    linhas = [
        [
            Paragraph(
                "ID",
                estilos["rotulo"],
            ),
            Paragraph(
                "Componente",
                estilos["rotulo"],
            ),
            Paragraph(
                "Anomalia",
                estilos["rotulo"],
            ),
            Paragraph(
                "Localização",
                estilos["rotulo"],
            ),
            Paragraph(
                "Situação",
                estilos["rotulo"],
            ),
        ]
    ]

    for anomalia, observacao in dados[
        "anomalias"
    ]:

        componente = componentes.get(
            anomalia.componente_id
        )

        linhas.append(
            [
                _paragrafo_pdf(
                    anomalia.id,
                    estilos["normal_pequeno"],
                ),
                _paragrafo_pdf(
                    (
                        componente.nome
                        if componente
                        else "Não localizado"
                    ),
                    estilos["normal_pequeno"],
                ),
                _paragrafo_pdf(
                    anomalia.tipo_anomalia,
                    estilos["normal_pequeno"],
                ),
                _paragrafo_pdf(
                    anomalia.localizacao_referencia,
                    estilos["normal_pequeno"],
                ),
                _paragrafo_pdf(
                    (
                        observacao.situacao_observada
                        if observacao
                        else "Registrada nesta inspeção"
                    ),
                    estilos["normal_pequeno"],
                ),
            ]
        )

    tabela = Table(
        linhas,
        colWidths=[
            10 * mm,
            34 * mm,
            42 * mm,
            44 * mm,
            45 * mm,
        ],
        repeatRows=1,
    )

    comandos = [
        (
            "BACKGROUND",
            (0, 0),
            (-1, 0),
            COR_PRIMARIA,
        ),
        (
            "TEXTCOLOR",
            (0, 0),
            (-1, 0),
            colors.white,
        ),
        (
            "GRID",
            (0, 0),
            (-1, -1),
            0.35,
            COR_LINHA,
        ),
        (
            "VALIGN",
            (0, 0),
            (-1, -1),
            "TOP",
        ),
        (
            "LEFTPADDING",
            (0, 0),
            (-1, -1),
            4,
        ),
        (
            "RIGHTPADDING",
            (0, 0),
            (-1, -1),
            4,
        ),
        (
            "TOPPADDING",
            (0, 0),
            (-1, -1),
            4,
        ),
        (
            "BOTTOMPADDING",
            (0, 0),
            (-1, -1),
            4,
        ),
    ]

    for indice in range(
        1,
        len(linhas),
    ):

        if indice % 2 == 0:

            comandos.append(
                (
                    "BACKGROUND",
                    (0, indice),
                    (-1, indice),
                    COR_FUNDO_CLARO,
                )
            )

    tabela.setStyle(
        TableStyle(
            comandos
        )
    )

    return tabela


def _tabela_fotografias_pdf(
    fotografias,
    estilos,
):

    if len(
        fotografias
    ) == 0:

        return _tabela_info_profissional_pdf(
            [
                (
                    "Registro fotográfico",
                    (
                        "Nenhuma fotografia vinculada "
                        "a esta inspeção."
                    ),
                )
            ],
            estilos,
        )

    linhas = [
        [
            Paragraph(
                "ID",
                estilos["rotulo"],
            ),
            Paragraph(
                "Data",
                estilos["rotulo"],
            ),
            Paragraph(
                "Identificação",
                estilos["rotulo"],
            ),
            Paragraph(
                "Tipo",
                estilos["rotulo"],
            ),
            Paragraph(
                "Arquivo",
                estilos["rotulo"],
            ),
        ]
    ]

    for foto in fotografias:

        linhas.append(
            [
                _paragrafo_pdf(
                    foto.id,
                    estilos["normal_pequeno"],
                ),
                _paragrafo_pdf(
                    data_br(
                        foto.data_foto
                    ),
                    estilos["normal_pequeno"],
                ),
                _paragrafo_pdf(
                    foto.identificacao,
                    estilos["normal_pequeno"],
                ),
                _paragrafo_pdf(
                    foto.tipo_registro,
                    estilos["normal_pequeno"],
                ),
                _paragrafo_pdf(
                    foto.nome_arquivo,
                    estilos["normal_pequeno"],
                ),
            ]
        )

    tabela = Table(
        linhas,
        colWidths=[
            10 * mm,
            25 * mm,
            52 * mm,
            38 * mm,
            50 * mm,
        ],
        repeatRows=1,
    )

    comandos = [
        (
            "BACKGROUND",
            (0, 0),
            (-1, 0),
            COR_PRIMARIA,
        ),
        (
            "TEXTCOLOR",
            (0, 0),
            (-1, 0),
            colors.white,
        ),
        (
            "GRID",
            (0, 0),
            (-1, -1),
            0.35,
            COR_LINHA,
        ),
        (
            "VALIGN",
            (0, 0),
            (-1, -1),
            "TOP",
        ),
        (
            "LEFTPADDING",
            (0, 0),
            (-1, -1),
            4,
        ),
        (
            "RIGHTPADDING",
            (0, 0),
            (-1, -1),
            4,
        ),
        (
            "TOPPADDING",
            (0, 0),
            (-1, -1),
            4,
        ),
        (
            "BOTTOMPADDING",
            (0, 0),
            (-1, -1),
            4,
        ),
    ]

    for indice in range(
        1,
        len(linhas),
    ):

        if indice % 2 == 0:

            comandos.append(
                (
                    "BACKGROUND",
                    (0, indice),
                    (-1, indice),
                    COR_FUNDO_CLARO,
                )
            )

    tabela.setStyle(
        TableStyle(
            comandos
        )
    )

    return tabela


# ============================================================
# PDF
# ============================================================

def _paragrafo_pdf(
    valor,
    estilo,
):

    valor = escape(
        texto(valor)
    ).replace(
        "\n",
        "<br/>",
    )

    return Paragraph(
        valor,
        estilo,
    )


def _tabela_chave_valor_pdf(
    dados,
    estilo_texto,
):

    linhas = []

    for chave, valor in dados:

        linhas.append(
            [
                _paragrafo_pdf(
                    chave,
                    estilo_texto,
                ),
                _paragrafo_pdf(
                    valor,
                    estilo_texto,
                ),
            ]
        )

    tabela = Table(
        linhas,
        colWidths=[
            55 * mm,
            120 * mm,
        ],
        repeatRows=0,
    )

    tabela.setStyle(
        TableStyle(
            [
                (
                    "GRID",
                    (0, 0),
                    (-1, -1),
                    0.4,
                    colors.grey,
                ),
                (
                    "BACKGROUND",
                    (0, 0),
                    (0, -1),
                    colors.whitesmoke,
                ),
                (
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "TOP",
                ),
                (
                    "LEFTPADDING",
                    (0, 0),
                    (-1, -1),
                    5,
                ),
                (
                    "RIGHTPADDING",
                    (0, 0),
                    (-1, -1),
                    5,
                ),
                (
                    "TOPPADDING",
                    (0, 0),
                    (-1, -1),
                    5,
                ),
                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    5,
                ),
            ]
        )
    )

    return tabela


def gerar_pdf_inspecao(
    dados,
):

    if not REPORTLAB_DISPONIVEL:
        return None

    buffer = BytesIO()

    oae = dados[
        "oae"
    ]

    inspecao = dados[
        "inspecao"
    ]

    estilos = estilos_pdf_profissional()

    documento = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=17.5 * mm,
        leftMargin=17.5 * mm,
        topMargin=15 * mm,
        bottomMargin=15 * mm,
        title=(
            "Relatório de inspeção - "
            + texto(
                oae.nome
            )
        ),
        author="Gêmeo Digital para Inspeção de Pontes",
    )

    historia = []

    historia.append(
        _cabecalho_relatorio_pdf(
            "RELATÓRIO DE INSPEÇÃO DE OAE",
            (
                f"{texto(inspecao.tipo_inspecao)} | "
                f"{data_br(inspecao.data_inspecao)} | "
                f"{texto(oae.nome)}"
            ),
            estilos,
        )
    )

    historia.append(
        Spacer(
            1,
            5 * mm,
        )
    )

    historia.append(
        _aviso_tecnico_pdf(
            estilos
        )
    )

    historia.append(
        Spacer(
            1,
            5 * mm,
        )
    )

    classificacao = dados[
        "classificacao_geral"
    ]

    cards_resumo = [
        _card_pdf(
            "Código da OAE",
            oae.codigo,
            estilos,
        ),
        _card_pdf(
            "Tipo de inspeção",
            inspecao.tipo_inspecao,
            estilos,
        ),
        _card_pdf(
            "Anomalias",
            len(
                dados[
                    "anomalias"
                ]
            ),
            estilos,
            cor_borda=COR_DESTAQUE,
        ),
        _card_pdf(
            "Fotografias",
            len(
                dados[
                    "fotografias"
                ]
            ),
            estilos,
        ),
    ]

    historia.append(
        _linha_cards_pdf(
            cards_resumo
        )
    )

    historia.append(
        Spacer(
            1,
            6 * mm,
        )
    )

    # ========================================================
    # 1. OAE
    # ========================================================

    historia.append(
        _barra_secao_pdf(
            1,
            "Identificação da OAE",
            estilos,
        )
    )

    historia.append(
        Spacer(
            1,
            2.5 * mm,
        )
    )

    historia.append(
        _tabela_info_profissional_pdf(
            [
                (
                    "Nome",
                    oae.nome,
                ),
                (
                    "Código",
                    oae.codigo,
                ),
                (
                    "Rodovia",
                    oae.rodovia,
                ),
                (
                    "Município / UF",
                    (
                        f"{texto(oae.municipio, '')}"
                        f"{' / ' if oae.municipio and oae.uf else ''}"
                        f"{texto(oae.uf, '')}"
                    ),
                ),
                (
                    "Tipo de estrutura",
                    oae.tipo_estrutura,
                ),
                (
                    "Ano de construção",
                    oae.ano_construcao,
                ),
                (
                    "Número de vãos",
                    oae.numero_vaos,
                ),
                (
                    "Comprimento total",
                    (
                        f"{numero_br(oae.comprimento_total)} m"
                        if oae.comprimento_total is not None
                        else "Não informado"
                    ),
                ),
                (
                    "Largura total",
                    (
                        f"{numero_br(oae.largura)} m"
                        if oae.largura is not None
                        else "Não informado"
                    ),
                ),
                (
                    "Protensão",
                    oae.tipo_protensao,
                ),
            ],
            estilos,
        )
    )

    historia.append(
        Spacer(
            1,
            5 * mm,
        )
    )

    # ========================================================
    # 2. INSPEÇÃO
    # ========================================================

    historia.append(
        _barra_secao_pdf(
            2,
            "Identificação da inspeção",
            estilos,
        )
    )

    historia.append(
        Spacer(
            1,
            2.5 * mm,
        )
    )

    historia.append(
        _tabela_info_profissional_pdf(
            [
                (
                    "Modalidade",
                    inspecao.tipo_inspecao,
                ),
                (
                    "Data",
                    data_br(
                        inspecao.data_inspecao
                    ),
                ),
                (
                    "Responsável",
                    inspecao.responsavel,
                ),
                (
                    "Registro profissional",
                    inspecao.registro_profissional,
                ),
                (
                    "Observações",
                    inspecao.observacoes,
                ),
            ],
            estilos,
        )
    )

    # ========================================================
    # 3. DADOS ESPECÍFICOS
    # ========================================================

    if len(
        dados[
            "secoes_especificas"
        ]
    ) > 0:

        historia.append(
            Spacer(
                1,
                5 * mm,
            )
        )

        historia.append(
            _barra_secao_pdf(
                3,
                "Informações técnicas da campanha",
                estilos,
            )
        )

        for titulo_secao, campos in dados[
            "secoes_especificas"
        ]:

            campos_validos = [
                (
                    chave,
                    valor,
                )
                for chave, valor in campos.items()
                if texto(
                    valor,
                    "",
                ) != ""
            ]

            if len(
                campos_validos
            ) == 0:
                continue

            historia.append(
                Paragraph(
                    escape(
                        titulo_secao
                    ),
                    estilos[
                        "subsecao"
                    ],
                )
            )

            historia.append(
                _tabela_info_profissional_pdf(
                    campos_validos,
                    estilos,
                )
            )

    # ========================================================
    # 4. ANOMALIAS
    # ========================================================

    historia.append(
        Spacer(
            1,
            5 * mm,
        )
    )

    historia.append(
        _barra_secao_pdf(
            4,
            "Anomalias relacionadas à campanha",
            estilos,
        )
    )

    historia.append(
        Spacer(
            1,
            2.5 * mm,
        )
    )

    historia.append(
        _tabela_anomalias_pdf(
            dados,
            estilos,
        )
    )

    # ========================================================
    # 5. CLASSIFICAÇÃO
    # ========================================================

    historia.append(
        Spacer(
            1,
            5 * mm,
        )
    )

    historia.append(
        _barra_secao_pdf(
            5,
            "Classificação da OAE",
            estilos,
        )
    )

    historia.append(
        Spacer(
            1,
            3 * mm,
        )
    )

    historia.append(
        _classificacao_cards_pdf(
            classificacao,
            estilos,
        )
    )

    historia.append(
        Spacer(
            1,
            2.5 * mm,
        )
    )

    historia.append(
        Paragraph(
            (
                "As cores são utilizadas apenas como recurso "
                "visual para facilitar a leitura das notas "
                "registradas no sistema."
            ),
            estilos[
                "normal_pequeno"
            ],
        )
    )

    if len(
        dados[
            "classificacoes"
        ]
    ) > 0:

        componentes = dados[
            "componentes"
        ]

        linhas_classificacao = [
            [
                Paragraph(
                    "Componente",
                    estilos["rotulo"],
                ),
                Paragraph(
                    "Estrutural",
                    estilos["rotulo"],
                ),
                Paragraph(
                    "Funcional",
                    estilos["rotulo"],
                ),
                Paragraph(
                    "Durabilidade",
                    estilos["rotulo"],
                ),
            ]
        ]

        for item in dados[
            "classificacoes"
        ]:

            componente = componentes.get(
                item.componente_id
            )

            linhas_classificacao.append(
                [
                    _paragrafo_pdf(
                        (
                            componente.nome
                            if componente
                            else item.componente_id
                        ),
                        estilos[
                            "normal_pequeno"
                        ],
                    ),
                    _paragrafo_pdf(
                        item.nota_estrutural,
                        estilos[
                            "normal_pequeno"
                        ],
                    ),
                    _paragrafo_pdf(
                        (
                            item.nota_funcional
                            if item.nota_funcional
                            is not None
                            else "NA"
                        ),
                        estilos[
                            "normal_pequeno"
                        ],
                    ),
                    _paragrafo_pdf(
                        item.nota_durabilidade,
                        estilos[
                            "normal_pequeno"
                        ],
                    ),
                ]
            )

        tabela_classificacao = Table(
            linhas_classificacao,
            colWidths=[
                85 * mm,
                30 * mm,
                30 * mm,
                30 * mm,
            ],
            repeatRows=1,
        )

        tabela_classificacao.setStyle(
            TableStyle(
                [
                    (
                        "BACKGROUND",
                        (0, 0),
                        (-1, 0),
                        COR_PRIMARIA,
                    ),
                    (
                        "TEXTCOLOR",
                        (0, 0),
                        (-1, 0),
                        colors.white,
                    ),
                    (
                        "GRID",
                        (0, 0),
                        (-1, -1),
                        0.35,
                        COR_LINHA,
                    ),
                    (
                        "VALIGN",
                        (0, 0),
                        (-1, -1),
                        "MIDDLE",
                    ),
                    (
                        "ALIGN",
                        (1, 1),
                        (-1, -1),
                        "CENTER",
                    ),
                    (
                        "LEFTPADDING",
                        (0, 0),
                        (-1, -1),
                        5,
                    ),
                    (
                        "RIGHTPADDING",
                        (0, 0),
                        (-1, -1),
                        5,
                    ),
                    (
                        "TOPPADDING",
                        (0, 0),
                        (-1, -1),
                        4,
                    ),
                    (
                        "BOTTOMPADDING",
                        (0, 0),
                        (-1, -1),
                        4,
                    ),
                ]
            )
        )

        historia.append(
            Spacer(
                1,
                3 * mm,
            )
        )

        historia.append(
            tabela_classificacao
        )

    # ========================================================
    # 6. FOTOGRAFIAS
    # ========================================================

    historia.append(
        Spacer(
            1,
            5 * mm,
        )
    )

    historia.append(
        _barra_secao_pdf(
            6,
            "Registro fotográfico",
            estilos,
        )
    )

    historia.append(
        Spacer(
            1,
            2.5 * mm,
        )
    )

    historia.append(
        _tabela_fotografias_pdf(
            dados[
                "fotografias"
            ],
            estilos,
        )
    )

    historia.append(
        Spacer(
            1,
            6 * mm,
        )
    )

    historia.append(
        HRFlowable(
            width="100%",
            thickness=0.5,
            color=COR_LINHA,
        )
    )

    historia.append(
        Spacer(
            1,
            2 * mm,
        )
    )

    historia.append(
        Paragraph(
            (
                "Relatório gerado em "
                f"{datetime.now().strftime('%d/%m/%Y às %H:%M')} "
                "a partir dos dados armazenados no sistema."
            ),
            estilos[
                "rodape"
            ],
        )
    )

    def pagina(
        canvas,
        doc,
    ):

        _cabecalho_rodape_pagina(
            canvas,
            doc,
            nome_oae=oae.nome,
            tipo_relatorio=(
                "Inspeção "
                + texto(
                    inspecao.tipo_inspecao
                )
            ),
        )

    documento.build(
        historia,
        onFirstPage=pagina,
        onLaterPages=pagina,
    )

    buffer.seek(
        0
    )

    return buffer.getvalue()


def gerar_pdf_consolidado(
    dados,
):

    if not REPORTLAB_DISPONIVEL:
        return None

    buffer = BytesIO()

    oae = dados[
        "oae"
    ]

    estilos = estilos_pdf_profissional()

    documento = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=17.5 * mm,
        leftMargin=17.5 * mm,
        topMargin=15 * mm,
        bottomMargin=15 * mm,
        title=(
            "Relatório consolidado - "
            + texto(
                oae.nome
            )
        ),
        author="Gêmeo Digital para Inspeção de Pontes",
    )

    historia = []

    historia.append(
        _cabecalho_relatorio_pdf(
            "RELATÓRIO CONSOLIDADO DA OAE",
            (
                f"Histórico de inspeções | "
                f"{texto(oae.nome)} | "
                f"{texto(oae.codigo)}"
            ),
            estilos,
        )
    )

    historia.append(
        Spacer(
            1,
            5 * mm,
        )
    )

    historia.append(
        _aviso_tecnico_pdf(
            estilos
        )
    )

    historia.append(
        Spacer(
            1,
            5 * mm,
        )
    )

    total_ativas = sum(
        1
        for item in dados[
            "anomalias"
        ]
        if item.ativa
    )

    cards = [
        _card_pdf(
            "Inspeções",
            len(
                dados[
                    "inspecoes"
                ]
            ),
            estilos,
        ),
        _card_pdf(
            "Componentes",
            len(
                dados[
                    "componentes"
                ]
            ),
            estilos,
        ),
        _card_pdf(
            "Anomalias cadastradas",
            len(
                dados[
                    "anomalias"
                ]
            ),
            estilos,
            cor_borda=COR_DESTAQUE,
        ),
        _card_pdf(
            "Anomalias ativas",
            total_ativas,
            estilos,
            cor_borda=(
                COR_NOTA_1
                if total_ativas > 0
                else COR_NOTA_5
            ),
        ),
    ]

    historia.append(
        _linha_cards_pdf(
            cards
        )
    )

    historia.append(
        Spacer(
            1,
            6 * mm,
        )
    )

    # ========================================================
    # 1. IDENTIFICAÇÃO
    # ========================================================

    historia.append(
        _barra_secao_pdf(
            1,
            "Identificação da OAE",
            estilos,
        )
    )

    historia.append(
        Spacer(
            1,
            2.5 * mm,
        )
    )

    historia.append(
        _tabela_info_profissional_pdf(
            [
                (
                    "Nome",
                    oae.nome,
                ),
                (
                    "Código",
                    oae.codigo,
                ),
                (
                    "Rodovia",
                    oae.rodovia,
                ),
                (
                    "Município / UF",
                    (
                        f"{texto(oae.municipio, '')}"
                        f"{' / ' if oae.municipio and oae.uf else ''}"
                        f"{texto(oae.uf, '')}"
                    ),
                ),
                (
                    "Tipo de estrutura",
                    oae.tipo_estrutura,
                ),
                (
                    "Ano de construção",
                    oae.ano_construcao,
                ),
                (
                    "Número de vãos",
                    oae.numero_vaos,
                ),
                (
                    "Comprimento total",
                    (
                        f"{numero_br(oae.comprimento_total)} m"
                        if oae.comprimento_total is not None
                        else "Não informado"
                    ),
                ),
                (
                    "Largura",
                    (
                        f"{numero_br(oae.largura)} m"
                        if oae.largura is not None
                        else "Não informado"
                    ),
                ),
            ],
            estilos,
        )
    )

    # ========================================================
    # 2. HISTÓRICO
    # ========================================================

    historia.append(
        Spacer(
            1,
            5 * mm,
        )
    )

    historia.append(
        _barra_secao_pdf(
            2,
            "Linha do tempo das inspeções",
            estilos,
        )
    )

    historia.append(
        Spacer(
            1,
            2.5 * mm,
        )
    )

    if len(
        dados[
            "campanhas"
        ]
    ) == 0:

        historia.append(
            _tabela_info_profissional_pdf(
                [
                    (
                        "Situação",
                        "Nenhuma inspeção cadastrada.",
                    )
                ],
                estilos,
            )
        )

    else:

        linhas = [
            [
                Paragraph(
                    "Data",
                    estilos["rotulo"],
                ),
                Paragraph(
                    "Modalidade",
                    estilos["rotulo"],
                ),
                Paragraph(
                    "E",
                    estilos["rotulo"],
                ),
                Paragraph(
                    "F",
                    estilos["rotulo"],
                ),
                Paragraph(
                    "D",
                    estilos["rotulo"],
                ),
                Paragraph(
                    "Fotos",
                    estilos["rotulo"],
                ),
            ]
        ]

        for campanha in dados[
            "campanhas"
        ]:

            inspecao = campanha[
                "inspecao"
            ]

            classificacao = campanha[
                "classificacao"
            ]

            linhas.append(
                [
                    _paragrafo_pdf(
                        data_br(
                            inspecao.data_inspecao
                        ),
                        estilos[
                            "normal_pequeno"
                        ],
                    ),
                    _paragrafo_pdf(
                        inspecao.tipo_inspecao,
                        estilos[
                            "normal_pequeno"
                        ],
                    ),
                    _paragrafo_pdf(
                        (
                            classificacao[
                                "estrutural"
                            ]
                            if classificacao[
                                "estrutural"
                            ] is not None
                            else "NA"
                        ),
                        estilos[
                            "normal_pequeno"
                        ],
                    ),
                    _paragrafo_pdf(
                        (
                            classificacao[
                                "funcional"
                            ]
                            if classificacao[
                                "funcional"
                            ] is not None
                            else "NA"
                        ),
                        estilos[
                            "normal_pequeno"
                        ],
                    ),
                    _paragrafo_pdf(
                        (
                            classificacao[
                                "durabilidade"
                            ]
                            if classificacao[
                                "durabilidade"
                            ] is not None
                            else "NA"
                        ),
                        estilos[
                            "normal_pequeno"
                        ],
                    ),
                    _paragrafo_pdf(
                        campanha[
                            "quantidade_fotos"
                        ],
                        estilos[
                            "normal_pequeno"
                        ],
                    ),
                ]
            )

        tabela_historico = Table(
            linhas,
            colWidths=[
                29 * mm,
                66 * mm,
                20 * mm,
                20 * mm,
                20 * mm,
                20 * mm,
            ],
            repeatRows=1,
        )

        tabela_historico.setStyle(
            TableStyle(
                [
                    (
                        "BACKGROUND",
                        (0, 0),
                        (-1, 0),
                        COR_PRIMARIA,
                    ),
                    (
                        "TEXTCOLOR",
                        (0, 0),
                        (-1, 0),
                        colors.white,
                    ),
                    (
                        "GRID",
                        (0, 0),
                        (-1, -1),
                        0.35,
                        COR_LINHA,
                    ),
                    (
                        "VALIGN",
                        (0, 0),
                        (-1, -1),
                        "MIDDLE",
                    ),
                    (
                        "ALIGN",
                        (2, 1),
                        (-1, -1),
                        "CENTER",
                    ),
                    (
                        "LEFTPADDING",
                        (0, 0),
                        (-1, -1),
                        4,
                    ),
                    (
                        "RIGHTPADDING",
                        (0, 0),
                        (-1, -1),
                        4,
                    ),
                    (
                        "TOPPADDING",
                        (0, 0),
                        (-1, -1),
                        4,
                    ),
                    (
                        "BOTTOMPADDING",
                        (0, 0),
                        (-1, -1),
                        4,
                    ),
                ]
            )
        )

        historia.append(
            tabela_historico
        )

    # ========================================================
    # 3. COMPONENTES
    # ========================================================

    historia.append(
        Spacer(
            1,
            5 * mm,
        )
    )

    historia.append(
        _barra_secao_pdf(
            3,
            "Inventário de componentes",
            estilos,
        )
    )

    historia.append(
        Spacer(
            1,
            2.5 * mm,
        )
    )

    if len(
        dados[
            "componentes"
        ]
    ) == 0:

        historia.append(
            _tabela_info_profissional_pdf(
                [
                    (
                        "Situação",
                        "Nenhum componente cadastrado.",
                    )
                ],
                estilos,
            )
        )

    else:

        linhas_componentes = [
            [
                Paragraph(
                    "ID",
                    estilos["rotulo"],
                ),
                Paragraph(
                    "Categoria",
                    estilos["rotulo"],
                ),
                Paragraph(
                    "Componente",
                    estilos["rotulo"],
                ),
                Paragraph(
                    "Classificação do elemento",
                    estilos["rotulo"],
                ),
            ]
        ]

        for componente in dados[
            "componentes"
        ]:

            linhas_componentes.append(
                [
                    _paragrafo_pdf(
                        componente.id,
                        estilos[
                            "normal_pequeno"
                        ],
                    ),
                    _paragrafo_pdf(
                        componente.categoria,
                        estilos[
                            "normal_pequeno"
                        ],
                    ),
                    _paragrafo_pdf(
                        componente.nome,
                        estilos[
                            "normal_pequeno"
                        ],
                    ),
                    _paragrafo_pdf(
                        componente.classificacao_elemento,
                        estilos[
                            "normal_pequeno"
                        ],
                    ),
                ]
            )

        tabela_componentes = Table(
            linhas_componentes,
            colWidths=[
                12 * mm,
                48 * mm,
                65 * mm,
                50 * mm,
            ],
            repeatRows=1,
        )

        tabela_componentes.setStyle(
            TableStyle(
                [
                    (
                        "BACKGROUND",
                        (0, 0),
                        (-1, 0),
                        COR_PRIMARIA,
                    ),
                    (
                        "TEXTCOLOR",
                        (0, 0),
                        (-1, 0),
                        colors.white,
                    ),
                    (
                        "GRID",
                        (0, 0),
                        (-1, -1),
                        0.35,
                        COR_LINHA,
                    ),
                    (
                        "VALIGN",
                        (0, 0),
                        (-1, -1),
                        "TOP",
                    ),
                    (
                        "LEFTPADDING",
                        (0, 0),
                        (-1, -1),
                        4,
                    ),
                    (
                        "RIGHTPADDING",
                        (0, 0),
                        (-1, -1),
                        4,
                    ),
                    (
                        "TOPPADDING",
                        (0, 0),
                        (-1, -1),
                        4,
                    ),
                    (
                        "BOTTOMPADDING",
                        (0, 0),
                        (-1, -1),
                        4,
                    ),
                ]
            )
        )

        historia.append(
            tabela_componentes
        )

    # ========================================================
    # 4. ANOMALIAS
    # ========================================================

    historia.append(
        Spacer(
            1,
            5 * mm,
        )
    )

    historia.append(
        _barra_secao_pdf(
            4,
            "Inventário de anomalias",
            estilos,
        )
    )

    historia.append(
        Spacer(
            1,
            2.5 * mm,
        )
    )

    if len(
        dados[
            "anomalias"
        ]
    ) == 0:

        historia.append(
            _tabela_info_profissional_pdf(
                [
                    (
                        "Situação",
                        "Nenhuma anomalia cadastrada.",
                    )
                ],
                estilos,
            )
        )

    else:

        componentes = {
            item.id: item
            for item in dados[
                "componentes"
            ]
        }

        linhas_anomalias = [
            [
                Paragraph(
                    "ID",
                    estilos["rotulo"],
                ),
                Paragraph(
                    "Componente",
                    estilos["rotulo"],
                ),
                Paragraph(
                    "Anomalia",
                    estilos["rotulo"],
                ),
                Paragraph(
                    "Localização",
                    estilos["rotulo"],
                ),
                Paragraph(
                    "Status",
                    estilos["rotulo"],
                ),
            ]
        ]

        for anomalia in dados[
            "anomalias"
        ]:

            componente = componentes.get(
                anomalia.componente_id
            )

            linhas_anomalias.append(
                [
                    _paragrafo_pdf(
                        anomalia.id,
                        estilos[
                            "normal_pequeno"
                        ],
                    ),
                    _paragrafo_pdf(
                        (
                            componente.nome
                            if componente
                            else "Não localizado"
                        ),
                        estilos[
                            "normal_pequeno"
                        ],
                    ),
                    _paragrafo_pdf(
                        anomalia.tipo_anomalia,
                        estilos[
                            "normal_pequeno"
                        ],
                    ),
                    _paragrafo_pdf(
                        anomalia.localizacao_referencia,
                        estilos[
                            "normal_pequeno"
                        ],
                    ),
                    _paragrafo_pdf(
                        (
                            "Ativa"
                            if anomalia.ativa
                            else "Encerrada"
                        ),
                        estilos[
                            "normal_pequeno"
                        ],
                    ),
                ]
            )

        tabela_anomalias = Table(
            linhas_anomalias,
            colWidths=[
                10 * mm,
                40 * mm,
                42 * mm,
                55 * mm,
                28 * mm,
            ],
            repeatRows=1,
        )

        tabela_anomalias.setStyle(
            TableStyle(
                [
                    (
                        "BACKGROUND",
                        (0, 0),
                        (-1, 0),
                        COR_PRIMARIA,
                    ),
                    (
                        "TEXTCOLOR",
                        (0, 0),
                        (-1, 0),
                        colors.white,
                    ),
                    (
                        "GRID",
                        (0, 0),
                        (-1, -1),
                        0.35,
                        COR_LINHA,
                    ),
                    (
                        "VALIGN",
                        (0, 0),
                        (-1, -1),
                        "TOP",
                    ),
                    (
                        "LEFTPADDING",
                        (0, 0),
                        (-1, -1),
                        4,
                    ),
                    (
                        "RIGHTPADDING",
                        (0, 0),
                        (-1, -1),
                        4,
                    ),
                    (
                        "TOPPADDING",
                        (0, 0),
                        (-1, -1),
                        4,
                    ),
                    (
                        "BOTTOMPADDING",
                        (0, 0),
                        (-1, -1),
                        4,
                    ),
                ]
            )
        )

        historia.append(
            tabela_anomalias
        )

    historia.append(
        Spacer(
            1,
            6 * mm,
        )
    )

    historia.append(
        HRFlowable(
            width="100%",
            thickness=0.5,
            color=COR_LINHA,
        )
    )

    historia.append(
        Spacer(
            1,
            2 * mm,
        )
    )

    historia.append(
        Paragraph(
            (
                "Relatório consolidado gerado em "
                f"{datetime.now().strftime('%d/%m/%Y às %H:%M')}."
            ),
            estilos[
                "rodape"
            ],
        )
    )

    def pagina(
        canvas,
        doc,
    ):

        _cabecalho_rodape_pagina(
            canvas,
            doc,
            nome_oae=oae.nome,
            tipo_relatorio="Relatório consolidado",
        )

    documento.build(
        historia,
        onFirstPage=pagina,
        onLaterPages=pagina,
    )

    buffer.seek(
        0
    )

    return buffer.getvalue()


# ============================================================
# PREVISUALIZAÇÃO NO STREAMLIT
# ============================================================

def mostrar_preview_inspecao(
    dados,
):

    oae = dados[
        "oae"
    ]

    inspecao = dados[
        "inspecao"
    ]

    classificacao = dados[
        "classificacao_geral"
    ]

    st.subheader(
        "Prévia do relatório"
    )

    c1, c2, c3, c4 = st.columns(
        4
    )

    with c1:

        st.metric(
            "Inspeção",
            inspecao.tipo_inspecao,
        )

    with c2:

        st.metric(
            "Anomalias relacionadas",
            len(
                dados[
                    "anomalias"
                ]
            ),
        )

    with c3:

        st.metric(
            "Fotografias",
            len(
                dados[
                    "fotografias"
                ]
            ),
        )

    with c4:

        st.metric(
            "Componentes classificados",
            len(
                dados[
                    "classificacoes"
                ]
            ),
        )

    st.write(
        f"**OAE:** {oae.id} - {oae.nome}"
    )

    st.write(
        f"**Data:** {data_br(inspecao.data_inspecao)}"
    )

    st.write(
        f"**Responsável:** {texto(inspecao.responsavel)}"
    )

    st.markdown(
        "#### Classificação consolidada"
    )

    col1, col2, col3 = st.columns(
        3
    )

    with col1:

        st.metric(
            "Estrutural",
            texto(
                classificacao[
                    "estrutural"
                ]
            ),
        )

    with col2:

        st.metric(
            "Funcional",
            texto(
                classificacao[
                    "funcional"
                ],
                "NA",
            ),
        )

    with col3:

        st.metric(
            "Durabilidade",
            texto(
                classificacao[
                    "durabilidade"
                ]
            ),
        )

    if len(
        dados["anomalias"]
    ) > 0:

        componentes = dados[
            "componentes"
        ]

        st.markdown(
            "#### Anomalias da campanha"
        )

        tabela = []

        for anomalia, observacao in dados[
            "anomalias"
        ]:

            componente = componentes.get(
                anomalia.componente_id
            )

            tabela.append(
                {
                    "ID":
                        anomalia.id,

                    "Componente":
                        (
                            componente.nome
                            if componente
                            else "Não localizado"
                        ),

                    "Anomalia":
                        anomalia.tipo_anomalia,

                    "Localização":
                        anomalia.localizacao_referencia,

                    "Situação":
                        (
                            observacao.situacao_observada
                            if observacao
                            else "Registrada nesta inspeção"
                        ),
                }
            )

        st.dataframe(
            tabela,
            width="stretch",
            hide_index=True,
        )


def mostrar_preview_consolidado(
    dados,
):

    st.subheader(
        "Prévia do relatório consolidado"
    )

    c1, c2, c3 = st.columns(
        3
    )

    with c1:

        st.metric(
            "Inspeções",
            len(
                dados[
                    "inspecoes"
                ]
            ),
        )

    with c2:

        st.metric(
            "Componentes",
            len(
                dados[
                    "componentes"
                ]
            ),
        )

    with c3:

        st.metric(
            "Anomalias ativas",
            sum(
                1
                for item in dados[
                    "anomalias"
                ]
                if item.ativa
            ),
        )

    if len(
        dados["campanhas"]
    ) > 0:

        tabela = []

        for campanha in dados[
            "campanhas"
        ]:

            inspecao = campanha[
                "inspecao"
            ]

            classificacao = campanha[
                "classificacao"
            ]

            tabela.append(
                {
                    "Data":
                        data_br(
                            inspecao.data_inspecao
                        ),

                    "Tipo":
                        inspecao.tipo_inspecao,

                    "Estrutural":
                        classificacao[
                            "estrutural"
                        ],

                    "Funcional":
                        classificacao[
                            "funcional"
                        ],

                    "Durabilidade":
                        classificacao[
                            "durabilidade"
                        ],

                    "Fotos":
                        campanha[
                            "quantidade_fotos"
                        ],
                }
            )

        st.dataframe(
            tabela,
            width="stretch",
            hide_index=True,
        )


# ============================================================
# MÓDULO PRINCIPAL
# ============================================================

def mostrar_modulo_relatorios(
    oae_ativa,
    inspecao_ativa=None,
):

    st.header(
        "📄 Relatórios"
    )

    st.caption(
        "Relatórios técnicos organizados a partir dos dados "
        "registrados no Gêmeo Digital."
    )

    st.info(
        "O relatório reproduz informações existentes no "
        "banco de dados. O sistema não substitui a análise, "
        "a validação ou a responsabilidade técnica do "
        "profissional."
    )

    if oae_ativa is None:

        st.warning(
            "Selecione uma OAE."
        )

        return

    modo = st.radio(
        "Tipo de relatório",
        [
            "Relatório de uma inspeção",
            "Relatório consolidado da OAE",
        ],
        horizontal=True,
        key="rel_tipo_relatorio",
    )

    if modo == "Relatório de uma inspeção":

        inspecoes = buscar_inspecoes_oae(
            oae_ativa.id
        )

        if len(inspecoes) == 0:

            st.warning(
                "Não existem inspeções cadastradas "
                "para esta OAE."
            )

            return

        ids = [
            item.id
            for item in inspecoes
        ]

        mapa = {
            item.id:
                (
                    f"{item.id} - "
                    f"{item.tipo_inspecao} - "
                    f"{data_br(item.data_inspecao)}"
                )
            for item in inspecoes
        }

        id_padrao = ids[0]

        if (
            inspecao_ativa is not None
            and inspecao_ativa.id in ids
        ):

            id_padrao = (
                inspecao_ativa.id
            )

        selecionada_id = st.selectbox(
            "Inspeção",
            options=ids,
            format_func=lambda valor:
                mapa[valor],
            index=ids.index(
                id_padrao
            ),
            key="rel_inspecao_selecionada",
        )

        selecionada = next(
            item
            for item in inspecoes
            if item.id
            == selecionada_id
        )

        dados = montar_relatorio_inspecao(
            oae_ativa,
            selecionada,
        )

        mostrar_preview_inspecao(
            dados
        )

        st.divider()

        st.subheader(
            "Gerar arquivos"
        )

        html = gerar_html_inspecao(
            dados
        )

        nome_base = (
            "relatorio_"
            + sanitizar_nome_arquivo(
                oae_ativa.nome
            )
            + "_"
            + sanitizar_nome_arquivo(
                selecionada.tipo_inspecao
            )
            + "_"
            + selecionada.data_inspecao.strftime(
                "%Y%m%d"
            )
        )

        st.download_button(
            "⬇️ Baixar relatório em HTML",
            data=html.encode(
                "utf-8"
            ),
            file_name=(
                nome_base
                + ".html"
            ),
            mime="text/html",
            key="rel_download_html_inspecao",
        )

        if REPORTLAB_DISPONIVEL:

            pdf = gerar_pdf_inspecao(
                dados
            )

            st.download_button(
                "⬇️ Baixar relatório em PDF",
                data=pdf,
                file_name=(
                    nome_base
                    + ".pdf"
                ),
                mime="application/pdf",
                key="rel_download_pdf_inspecao",
            )

        else:

            st.warning(
                "Para habilitar a geração de PDF, instale "
                "a biblioteca ReportLab no ambiente virtual:"
            )

            st.code(
                "pip install reportlab"
            )

    else:

        dados = montar_relatorio_consolidado(
            oae_ativa
        )

        mostrar_preview_consolidado(
            dados
        )

        st.divider()

        st.subheader(
            "Gerar arquivos"
        )

        html = gerar_html_consolidado(
            dados
        )

        nome_base = (
            "relatorio_consolidado_"
            + sanitizar_nome_arquivo(
                oae_ativa.nome
            )
        )

        st.download_button(
            "⬇️ Baixar relatório consolidado em HTML",
            data=html.encode(
                "utf-8"
            ),
            file_name=(
                nome_base
                + ".html"
            ),
            mime="text/html",
            key="rel_download_html_consolidado",
        )

        if REPORTLAB_DISPONIVEL:

            pdf = gerar_pdf_consolidado(
                dados
            )

            st.download_button(
                "⬇️ Baixar relatório consolidado em PDF",
                data=pdf,
                file_name=(
                    nome_base
                    + ".pdf"
                ),
                mime="application/pdf",
                key="rel_download_pdf_consolidado",
            )

        else:

            st.warning(
                "Para habilitar a geração de PDF, instale "
                "a biblioteca ReportLab no ambiente virtual:"
            )

            st.code(
                "pip install reportlab"
            )