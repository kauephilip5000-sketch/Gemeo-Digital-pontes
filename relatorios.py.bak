import streamlit as st

from datetime import datetime
from html import escape
from io import BytesIO
from pathlib import Path
import re
from reportlab.platypus import Flowable
from database import SessionLocal
import models

from classificacao import (
    calcular_classificacao_consolidada,
    buscar_classificacao_oae,
    buscar_classificacoes_componentes as buscar_classificacoes_modulo,
    eh_inspecao_especial,
    nota_texto,
)


# ============================================================
# RELATÓRIOS DO GÊMEO DIGITAL
#
# Este módulo APENAS organiza e apresenta dados existentes no
# banco de dados. Não cria diagnóstico, nota ou terapia.
# A validação permanece sob responsabilidade do profissional.
# ============================================================


# ============================================================
# REPORTLAB
# ============================================================

try:
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_CENTER, TA_LEFT
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import mm
    from reportlab.platypus import (
        SimpleDocTemplate,
        Paragraph,
        Spacer,
        Table,
        TableStyle,
        PageBreak,
        KeepTogether,
        Image as RLImage,
        HRFlowable,
        Flowable,
    )
    from reportlab.platypus.tableofcontents import TableOfContents

    REPORTLAB_DISPONIVEL = True

except Exception:
    REPORTLAB_DISPONIVEL = False


# ============================================================
# CONSTANTES VISUAIS DO PDF
# ============================================================

COR_AZUL = "#173B63"
COR_AZUL_2 = "#2B6FAE"
COR_AZUL_CLARO = "#EAF2F9"
COR_CINZA = "#F4F6F8"
COR_LINHA = "#CCD5DF"
COR_TEXTO = "#24313D"
COR_LARANJA = "#E89B27"
COR_VERDE = "#3D8B62"
COR_VERMELHO = "#B94A48"


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
    valor = texto(valor, "relatorio")
    permitidos = []

    for caractere in valor:
        if caractere.isalnum() or caractere in ["-", "_"]:
            permitidos.append(caractere)
        elif caractere in [" ", ".", "/"]:
            permitidos.append("_")

    resultado = "".join(permitidos).strip("_")
    return resultado or "relatorio"


def limpar_nome_componente(valor):
    """
    Corrige apenas um artefato de nomenclatura antigo do banco,
    como 'a Longarina L2'. Não altera nomes normais.
    """
    nome = texto(valor, "Não localizado").strip()

    if re.match(r"^[aA]\s+[A-ZÁÉÍÓÚÂÊÔÃÕÇ]", nome):
        nome = nome[2:].strip()

    return nome


def nome_oae_exibicao(oae):
    return texto(getattr(oae, "nome", None))


def classificacao_com_condicao(nota):
    if nota is None:
        return "Não classificada"

    try:
        nota_int = int(nota)
        return f"{nota_int} - {nota_texto(nota_int)}"
    except Exception:
        return texto(nota)


def numero_visual_inspecao(inspecao, inspecoes_cronologicas):
    for indice, item in enumerate(inspecoes_cronologicas, start=1):
        if item.id == inspecao.id:
            return indice
    return None


def rotulo_inspecao(inspecao, inspecoes_cronologicas=None):
    numero = None

    if inspecoes_cronologicas is not None:
        numero = numero_visual_inspecao(
            inspecao,
            inspecoes_cronologicas,
        )

    prefixo = (
        f"Inspeção {numero:02d} — "
        if isinstance(numero, int)
        else ""
    )

    return (
        f"{prefixo}{texto(inspecao.tipo_inspecao)} — "
        f"{data_br(inspecao.data_inspecao)}"
    )


def caminho_foto_existente(foto):
    caminho_original = texto(
        getattr(foto, "caminho_arquivo", None),
        "",
    )

    if caminho_original == "":
        return None

    caminho = Path(caminho_original)

    candidatos = [
        caminho,
        Path.cwd() / caminho,
        Path(__file__).resolve().parent / caminho,
    ]

    for candidato in candidatos:
        try:
            if candidato.exists() and candidato.is_file():
                return candidato.resolve()
        except Exception:
            pass

    return None


def dict_objeto(objeto, campos):
    dados = {}

    if objeto is None:
        return dados

    for campo, titulo in campos:
        dados[titulo] = getattr(objeto, campo, None)

    return dados


# ============================================================
# CONSULTAS GERAIS
# ============================================================

def buscar_inspecoes_oae(oae_id):
    db = SessionLocal()

    dados = (
        db.query(models.Inspecao)
        .filter(models.Inspecao.oae_id == oae_id)
        .order_by(
            models.Inspecao.data_inspecao.asc(),
            models.Inspecao.id.asc(),
        )
        .all()
    )

    db.close()
    return dados


def buscar_componentes_oae(oae_id):
    db = SessionLocal()

    dados = (
        db.query(models.Componente)
        .filter(models.Componente.oae_id == oae_id)
        .order_by(
            models.Componente.categoria,
            models.Componente.nome,
            models.Componente.id,
        )
        .all()
    )

    db.close()
    return dados


def buscar_fotografias_inspecao(inspecao_id):
    db = SessionLocal()

    dados = (
        db.query(models.Fotografia)
        .filter(models.Fotografia.inspecao_id == inspecao_id)
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
        .filter(models.AnomaliaPermanente.oae_id == oae_id)
        .order_by(
            models.AnomaliaPermanente.componente_id,
            models.AnomaliaPermanente.id,
        )
        .all()
    )

    db.close()
    return dados


def buscar_anomalias_relacionadas_inspecao(oae_id, inspecao):
    todas = buscar_anomalias_oae(oae_id)
    resultado = []
    db = SessionLocal()

    for anomalia in todas:
        origem = (
            db.query(models.Inspecao)
            .filter(models.Inspecao.id == anomalia.inspecao_origem_id)
            .first()
        )

        if origem is None:
            continue

        nasceu_antes_ou_na_inspecao = (
            origem.data_inspecao < inspecao.data_inspecao
            or (
                origem.data_inspecao == inspecao.data_inspecao
                and origem.id <= inspecao.id
            )
        )

        if not nasceu_antes_ou_na_inspecao:
            continue

        observacao = (
            db.query(models.ObservacaoAnomalia)
            .filter(models.ObservacaoAnomalia.anomalia_id == anomalia.id)
            .filter(models.ObservacaoAnomalia.inspecao_id == inspecao.id)
            .first()
        )

        if (
            anomalia.inspecao_origem_id == inspecao.id
            or observacao is not None
        ):
            resultado.append((anomalia, observacao))

    db.close()
    return resultado


def mapa_componentes(oae_id):
    return {
        item.id: item
        for item in buscar_componentes_oae(oae_id)
    }


def buscar_vinculo_foto_anomalia(fotografia_id):
    if not hasattr(models, "VinculoFotografiaAnomalia"):
        return None

    db = SessionLocal()

    try:
        vinculo = (
            db.query(models.VinculoFotografiaAnomalia)
            .filter(
                models.VinculoFotografiaAnomalia.fotografia_id
                == fotografia_id
            )
            .first()
        )
    except Exception:
        vinculo = None

    db.close()
    return vinculo


def buscar_anomalia_por_id(anomalia_id):
    if anomalia_id is None:
        return None

    db = SessionLocal()

    dado = (
        db.query(models.AnomaliaPermanente)
        .filter(models.AnomaliaPermanente.id == anomalia_id)
        .first()
    )

    db.close()
    return dado


# ============================================================
# DADOS ESPECÍFICOS DE CADA MODALIDADE
# ============================================================

def buscar_detalhe_generico(inspecao_id):
    db = SessionLocal()

    dado = (
        db.query(models.DetalheInspecao)
        .filter(models.DetalheInspecao.inspecao_id == inspecao_id)
        .first()
    )

    db.close()
    return dado


def buscar_dados_cadastral(inspecao_id):
    db = SessionLocal()

    dado = (
        db.query(models.InspecaoCadastral)
        .filter(models.InspecaoCadastral.inspecao_id == inspecao_id)
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
        .filter(RegistroRotineira.inspecao_id == inspecao_id)
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
        .filter(RegistroEspecial.inspecao_id == inspecao_id)
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
        .filter(RegistroExtraordinaria.inspecao_id == inspecao_id)
        .first()
    )

    db.close()
    return dado


def secoes_especificas_inspecao(inspecao):
    tipo = texto(inspecao.tipo_inspecao, "").strip()
    secoes = []

    detalhe = buscar_detalhe_generico(inspecao.id)

    if detalhe is not None:
        campos_detalhe = [
            ("procedimento_utilizado", "Procedimento utilizado"),
            ("ensaios_previstos", "Ensaios previstos"),
            ("diagnostico", "Diagnóstico"),
            ("recomendacoes", "Recomendações"),
        ]

        dados = dict_objeto(detalhe, campos_detalhe)

        if any(texto(v, "") != "" for v in dados.values()):
            secoes.append(("Informações técnicas gerais", dados))

    if tipo == "Cadastral":
        registro = buscar_dados_cadastral(inspecao.id)

        if registro is not None:
            campos = []

            for coluna in registro.__table__.columns:
                if coluna.name in ["id", "inspecao_id"]:
                    continue

                titulo = (
                    coluna.name
                    .replace("_", " ")
                    .strip()
                    .capitalize()
                )
                campos.append((coluna.name, titulo))

            secoes.append(
                (
                    "Dados da inspeção cadastral",
                    dict_objeto(registro, campos),
                )
            )

    elif tipo == "Rotineira":
        registro = buscar_dados_rotineira(inspecao.id)

        if registro is not None:
            intervencoes = dict_objeto(
                registro,
                [
                    ("reparos", "Reparos"),
                    ("alargamento", "Alargamento"),
                    ("reforcos", "Reforços"),
                    ("outras_intervencoes", "Outras intervenções"),
                ],
            )

            alteracoes = dict_objeto(
                registro,
                [
                    (
                        "comentarios_alteracoes",
                        "Alterações em relação à inspeção anterior",
                    ),
                    (
                        "informacoes_complementares",
                        "Informações complementares",
                    ),
                    (
                        "abrangencia_fotografica",
                        "Abrangência fotográfica",
                    ),
                ],
            )

            terapia = dict_objeto(
                registro,
                [
                    (
                        "recomendacoes_terapeuticas",
                        "Recomendações terapêuticas",
                    ),
                ],
            )

            secoes.append(("Intervenções verificadas", intervencoes))
            secoes.append(("Alterações e informações da campanha", alteracoes))
            secoes.append(("Recomendações terapêuticas", terapia))

    elif tipo == "Especial":
        registro = buscar_dados_especial(inspecao.id)

        if registro is not None:
            grupos = [
                (
                    "Localização - inspeção especial",
                    [
                        ("rodovia_ferrovia", "Rodovia ou ferrovia"),
                        ("nome_obra", "Nome da obra"),
                        ("quilometro", "Quilômetro"),
                        ("coordenadas", "Coordenadas"),
                        ("sentido", "Sentido"),
                        ("jurisdicao", "Jurisdição"),
                    ],
                ),
                (
                    "Descrição da obra - inspeção especial",
                    [
                        ("descricao_obra", "Descrição da obra"),
                        ("historico_obra", "Histórico da obra"),
                        ("classe_portante", "Classe portante provável"),
                        ("desenhos_memoriais", "Desenhos e memoriais"),
                        (
                            "diferencas_projeto_original",
                            "Diferenças do projeto original",
                        ),
                        ("condicoes_ambientais", "Condições ambientais"),
                        ("caracteristicas_trafego", "Características do tráfego"),
                    ],
                ),
                (
                    "Patologia - inspeção especial",
                    [
                        ("sintese_patologia", "Síntese de patologia"),
                        (
                            "mecanismo_deterioracao",
                            "Mecanismos de deterioração",
                        ),
                        ("causas_provaveis", "Causas prováveis"),
                    ],
                ),
                (
                    "Ensaios - inspeção especial",
                    [
                        ("descricao_ensaios", "Descrição dos ensaios"),
                        ("localizacao_ensaios", "Localização dos ensaios"),
                        ("resultados_ensaios", "Resultados"),
                        ("interpretacao_ensaios", "Interpretação"),
                        ("metodologia_ensaios", "Metodologia"),
                        (
                            "normas_referencia_ensaios",
                            "Normas de referência",
                        ),
                    ],
                ),
                (
                    "Diagnóstico e terapia - inspeção especial",
                    [
                        ("diagnostico", "Diagnóstico"),
                        (
                            "resumo_analise_estrutural",
                            "Resumo da análise estrutural",
                        ),
                        ("terapia_recomendada", "Terapia recomendada"),
                        (
                            "metodologia_recuperacao",
                            "Metodologia de recuperação",
                        ),
                        ("reparos_recomendados", "Reparos recomendados"),
                        (
                            "recuperacao_recomendada",
                            "Recuperação recomendada",
                        ),
                        ("reforco_recomendado", "Reforço recomendado"),
                        (
                            "conclusoes_recomendacoes",
                            "Conclusões e recomendações",
                        ),
                    ],
                ),
            ]

            for titulo, campos in grupos:
                secoes.append((titulo, dict_objeto(registro, campos)))

    elif tipo == "Extraordinária":
        registro = buscar_dados_extraordinaria(inspecao.id)

        if registro is not None:
            campos = []

            for coluna in registro.__table__.columns:
                if coluna.name in ["id", "inspecao_id"]:
                    continue

                titulo = (
                    coluna.name
                    .replace("_", " ")
                    .strip()
                    .capitalize()
                )
                campos.append((coluna.name, titulo))

            secoes.append(
                (
                    "Dados da inspeção extraordinária",
                    dict_objeto(registro, campos),
                )
            )

    return secoes


# ============================================================
# MONTAGEM DOS DADOS
# ============================================================

def montar_relatorio_inspecao(oae, inspecao):
    componentes = mapa_componentes(oae.id)
    fotografias = buscar_fotografias_inspecao(inspecao.id)
    anomalias = buscar_anomalias_relacionadas_inspecao(oae.id, inspecao)

    classificacao_geral = calcular_classificacao_consolidada(
        oae.id,
        inspecao.id,
    )

    if eh_inspecao_especial(inspecao):
        classificacoes_componentes = buscar_classificacoes_modulo(
            oae.id,
            inspecao.id,
        )
        classificacao_direta = None
    else:
        classificacoes_componentes = []
        classificacao_direta = buscar_classificacao_oae(
            oae.id,
            inspecao.id,
        )

    inspecoes_cronologicas = buscar_inspecoes_oae(oae.id)

    historico_ate_campanha = [
        item
        for item in inspecoes_cronologicas
        if (
            item.data_inspecao < inspecao.data_inspecao
            or (
                item.data_inspecao == inspecao.data_inspecao
                and item.id <= inspecao.id
            )
        )
    ]

    return {
        "oae": oae,
        "inspecao": inspecao,
        "componentes": componentes,
        "fotografias": fotografias,
        "anomalias": anomalias,
        "classificacao_geral": classificacao_geral,
        "classificacao_direta": classificacao_direta,
        "classificacoes_componentes": classificacoes_componentes,
        "secoes_especificas": secoes_especificas_inspecao(inspecao),
        "inspecoes_cronologicas": inspecoes_cronologicas,
        "historico_ate_campanha": historico_ate_campanha,
    }


def montar_relatorio_consolidado(oae):
    inspecoes = buscar_inspecoes_oae(oae.id)
    componentes = buscar_componentes_oae(oae.id)
    anomalias = buscar_anomalias_oae(oae.id)
    campanhas = []

    for inspecao in inspecoes:
        classificacao = calcular_classificacao_consolidada(
            oae.id,
            inspecao.id,
        )

        campanhas.append(
            {
                "inspecao": inspecao,
                "classificacao": classificacao,
                "quantidade_fotos": len(
                    buscar_fotografias_inspecao(inspecao.id)
                ),
                "quantidade_anomalias": len(
                    buscar_anomalias_relacionadas_inspecao(
                        oae.id,
                        inspecao,
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
# HTML
# ============================================================

def html_cabecalho(titulo):
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
                color: #24313D;
                line-height: 1.45;
            }}
            .topo {{
                background: {COR_AZUL};
                color: white;
                padding: 22px;
                margin-bottom: 18px;
            }}
            h1 {{ margin: 0; font-size: 25px; }}
            h2 {{
                margin-top: 28px;
                background: {COR_AZUL_CLARO};
                padding: 9px 12px;
                border-left: 5px solid {COR_AZUL_2};
                font-size: 18px;
            }}
            table {{
                width: 100%;
                border-collapse: collapse;
                margin: 12px 0 22px 0;
            }}
            th, td {{
                border: 1px solid #CCD5DF;
                padding: 7px;
                text-align: left;
                vertical-align: top;
            }}
            th {{ background: #F4F6F8; }}
            .aviso {{
                padding: 12px;
                border: 1px solid #E7C577;
                background: #FFF8E4;
                margin: 18px 0;
            }}
            .cards {{ display: flex; gap: 10px; flex-wrap: wrap; }}
            .card {{
                border: 1px solid #CCD5DF;
                border-top: 4px solid {COR_AZUL_2};
                padding: 10px;
                min-width: 150px;
                flex: 1;
            }}
            .card b {{ display: block; color: #52606D; font-size: 12px; }}
            .card span {{ font-size: 20px; font-weight: bold; }}
            .foto {{
                display: inline-block;
                width: 47%;
                vertical-align: top;
                margin: 1%;
            }}
            .foto img {{ max-width: 100%; max-height: 330px; }}
            .rodape {{ margin-top: 40px; font-size: 11px; color: #666; }}
        </style>
    </head>
    <body>
    """


def html_linha(titulo, valor):
    return (
        "<tr>"
        f"<th>{escape(texto(titulo))}</th>"
        f"<td>{escape(texto(valor))}</td>"
        "</tr>"
    )


def gerar_html_inspecao(dados):
    oae = dados["oae"]
    inspecao = dados["inspecao"]
    classificacao = dados["classificacao_geral"]
    componentes = dados["componentes"]

    partes = [
        html_cabecalho("Relatório técnico de inspeção de OAE"),
        "<div class='topo'>",
        "<h1>RELATÓRIO TÉCNICO DE INSPEÇÃO DE OAE</h1>",
        (
            f"<div>{escape(texto(inspecao.tipo_inspecao))} | "
            f"{escape(data_br(inspecao.data_inspecao))} | "
            f"{escape(nome_oae_exibicao(oae))}</div>"
        ),
        "</div>",
        (
            "<div class='aviso'><b>Nota técnica.</b> "
            "Este documento consolida informações registradas no Gêmeo Digital. "
            "A validação do diagnóstico, da classificação e das decisões de intervenção "
            "permanece sob responsabilidade do profissional competente.</div>"
        ),
        "<div class='cards'>",
        f"<div class='card'><b>Código da OAE</b><span>{escape(texto(oae.codigo))}</span></div>",
        f"<div class='card'><b>Anomalias</b><span>{len(dados['anomalias'])}</span></div>",
        f"<div class='card'><b>Fotografias</b><span>{len(dados['fotografias'])}</span></div>",
        f"<div class='card'><b>Estrutural</b><span>{escape(classificacao_com_condicao(classificacao['estrutural']))}</span></div>",
        f"<div class='card'><b>Funcional</b><span>{escape(classificacao_com_condicao(classificacao['funcional']))}</span></div>",
        f"<div class='card'><b>Durabilidade</b><span>{escape(classificacao_com_condicao(classificacao['durabilidade']))}</span></div>",
        "</div>",
        "<h2>1. Identificação da OAE</h2>",
        "<table>",
        html_linha("Nome", oae.nome),
        html_linha("Código", oae.codigo),
        html_linha("Rodovia", oae.rodovia),
        html_linha(
            "Município / UF",
            f"{texto(oae.municipio, '')}{' / ' if oae.municipio and oae.uf else ''}{texto(oae.uf, '')}",
        ),
        html_linha("Tipo de estrutura", oae.tipo_estrutura),
        html_linha("Ano de construção", oae.ano_construcao),
        html_linha("Número de vãos", oae.numero_vaos),
        html_linha("Comprimento total", f"{numero_br(oae.comprimento_total)} m"),
        html_linha("Largura total", f"{numero_br(oae.largura)} m"),
        html_linha("Protensão", oae.tipo_protensao),
        "</table>",
        "<h2>2. Identificação e objetivo da inspeção</h2>",
        "<table>",
        html_linha("Modalidade", inspecao.tipo_inspecao),
        html_linha("Data", data_br(inspecao.data_inspecao)),
        html_linha("Responsável", inspecao.responsavel),
        html_linha("Registro profissional", inspecao.registro_profissional),
        html_linha("Objetivo / observações", inspecao.observacoes),
        "</table>",
        "<h2>3. Histórico das inspeções</h2>",
        "<table><tr><th>Inspeção</th><th>Modalidade</th><th>Data</th></tr>",
    ]

    for numero, item in enumerate(dados["historico_ate_campanha"], start=1):
        partes.append(
            "<tr>"
            f"<td>{numero:02d}</td>"
            f"<td>{escape(texto(item.tipo_inspecao))}</td>"
            f"<td>{escape(data_br(item.data_inspecao))}</td>"
            "</tr>"
        )

    partes.append("</table>")

    numero_secao = 4

    for titulo, campos in dados["secoes_especificas"]:
        partes.append(f"<h2>{numero_secao}. {escape(titulo)}</h2><table>")

        for chave, valor in campos.items():
            partes.append(html_linha(chave, valor))

        partes.append("</table>")
        numero_secao += 1

    partes.append(f"<h2>{numero_secao}. Registro e evolução das anomalias</h2>")

    if len(dados["anomalias"]) == 0:
        partes.append("<p>Nenhuma anomalia relacionada à campanha.</p>")
    else:
        partes.append(
            "<table><tr><th>Ref.</th><th>Componente</th><th>Anomalia</th>"
            "<th>Localização</th><th>Situação na campanha</th></tr>"
        )

        for indice, (anomalia, observacao) in enumerate(dados["anomalias"], start=1):
            componente = componentes.get(anomalia.componente_id)
            situacao = (
                observacao.situacao_observada
                if observacao is not None
                else "Identificada nesta inspeção"
            )

            partes.append(
                "<tr>"
                f"<td>AN-{indice:02d}</td>"
                f"<td>{escape(limpar_nome_componente(componente.nome if componente else None))}</td>"
                f"<td>{escape(texto(anomalia.tipo_anomalia))}</td>"
                f"<td>{escape(texto(anomalia.localizacao_referencia))}</td>"
                f"<td>{escape(texto(situacao))}</td>"
                "</tr>"
            )

        partes.append("</table>")

    numero_secao += 1
    partes.append(f"<h2>{numero_secao}. Classificação da condição da OAE</h2>")
    partes.append(
        "<table>"
        + html_linha("Estrutural", classificacao_com_condicao(classificacao["estrutural"]))
        + html_linha("Funcional", classificacao_com_condicao(classificacao["funcional"]))
        + html_linha("Durabilidade", classificacao_com_condicao(classificacao["durabilidade"]))
        + "</table>"
    )

    if eh_inspecao_especial(inspecao) and dados["classificacoes_componentes"]:
        partes.append("<h3>Classificação detalhada por componente</h3>")
        partes.append(
            "<table><tr><th>Componente</th><th>Estrutural</th>"
            "<th>Funcional</th><th>Durabilidade</th></tr>"
        )

        for item in dados["classificacoes_componentes"]:
            componente = componentes.get(item.componente_id)
            partes.append(
                "<tr>"
                f"<td>{escape(limpar_nome_componente(componente.nome if componente else None))}</td>"
                f"<td>{escape(texto(item.nota_estrutural))}</td>"
                f"<td>{escape(texto(item.nota_funcional, 'NA'))}</td>"
                f"<td>{escape(texto(item.nota_durabilidade))}</td>"
                "</tr>"
            )
        partes.append("</table>")

    numero_secao += 1
    partes.append(f"<h2>{numero_secao}. Levantamento fotográfico</h2>")

    if len(dados["fotografias"]) == 0:
        partes.append("<p>Nenhuma fotografia vinculada à inspeção.</p>")
    else:
        partes.append(
            "<p>As imagens permanecem vinculadas à campanha e aos respectivos "
            "componentes/anomalias conforme os registros do sistema.</p>"
        )
        partes.append(
            "<table><tr><th>Foto</th><th>Data</th><th>Identificação</th>"
            "<th>Tipo</th><th>Observações</th></tr>"
        )

        for indice, foto in enumerate(dados["fotografias"], start=1):
            partes.append(
                "<tr>"
                f"<td>Foto {indice:02d}</td>"
                f"<td>{escape(data_br(foto.data_foto))}</td>"
                f"<td>{escape(texto(foto.identificacao))}</td>"
                f"<td>{escape(texto(foto.tipo_registro))}</td>"
                f"<td>{escape(texto(foto.observacoes))}</td>"
                "</tr>"
            )

        partes.append("</table>")

    partes.extend(
        [
            "<div class='rodape'>",
            (
                "Relatório gerado em "
                f"{datetime.now().strftime('%d/%m/%Y às %H:%M')} "
                "a partir dos dados armazenados no sistema."
            ),
            "</div>",
            "</body></html>",
        ]
    )

    return "".join(partes)


def gerar_html_consolidado(dados):
    oae = dados["oae"]

    partes = [
        html_cabecalho("Relatório consolidado da OAE"),
        "<div class='topo'><h1>RELATÓRIO CONSOLIDADO DA OAE</h1>",
        f"<div>{escape(nome_oae_exibicao(oae))}</div></div>",
        (
            "<div class='aviso'>Síntese histórica produzida a partir dos dados "
            "registrados no sistema. A interpretação e validação técnica permanecem "
            "sob responsabilidade do profissional.</div>"
        ),
        "<h2>1. Identificação da OAE</h2><table>",
        html_linha("Nome", oae.nome),
        html_linha("Código", oae.codigo),
        html_linha("Rodovia", oae.rodovia),
        html_linha(
            "Município / UF",
            f"{texto(oae.municipio, '')}{' / ' if oae.municipio and oae.uf else ''}{texto(oae.uf, '')}",
        ),
        html_linha("Tipo de estrutura", oae.tipo_estrutura),
        html_linha("Ano de construção", oae.ano_construcao),
        "</table>",
        "<h2>2. Histórico de inspeções e classificações</h2>",
        (
            "<table><tr><th>Nº</th><th>Data</th><th>Tipo</th><th>Estrutural</th>"
            "<th>Funcional</th><th>Durabilidade</th><th>Anomalias</th><th>Fotos</th></tr>"
        ),
    ]

    for indice, campanha in enumerate(dados["campanhas"], start=1):
        inspecao = campanha["inspecao"]
        classificacao = campanha["classificacao"]

        partes.append(
            "<tr>"
            f"<td>{indice:02d}</td>"
            f"<td>{escape(data_br(inspecao.data_inspecao))}</td>"
            f"<td>{escape(texto(inspecao.tipo_inspecao))}</td>"
            f"<td>{escape(classificacao_com_condicao(classificacao['estrutural']))}</td>"
            f"<td>{escape(classificacao_com_condicao(classificacao['funcional']))}</td>"
            f"<td>{escape(classificacao_com_condicao(classificacao['durabilidade']))}</td>"
            f"<td>{campanha['quantidade_anomalias']}</td>"
            f"<td>{campanha['quantidade_fotos']}</td>"
            "</tr>"
        )

    partes.append("</table>")
    partes.append("<h2>3. Inventário atual de anomalias</h2>")

    if not dados["anomalias"]:
        partes.append("<p>Nenhuma anomalia permanente cadastrada.</p>")
    else:
        componentes = {item.id: item for item in dados["componentes"]}
        partes.append(
            "<table><tr><th>Ref.</th><th>Componente</th><th>Tipo</th>"
            "<th>Localização</th><th>Status</th></tr>"
        )

        for indice, anomalia in enumerate(dados["anomalias"], start=1):
            componente = componentes.get(anomalia.componente_id)
            partes.append(
                "<tr>"
                f"<td>AN-{indice:02d}</td>"
                f"<td>{escape(limpar_nome_componente(componente.nome if componente else None))}</td>"
                f"<td>{escape(texto(anomalia.tipo_anomalia))}</td>"
                f"<td>{escape(texto(anomalia.localizacao_referencia))}</td>"
                f"<td>{'Ativa' if anomalia.ativa else 'Encerrada'}</td>"
                "</tr>"
            )

        partes.append("</table>")

    partes.extend(
        [
            "<div class='rodape'>",
            f"Relatório consolidado gerado em {datetime.now().strftime('%d/%m/%Y às %H:%M')}.",
            "</div></body></html>",
        ]
    )

    return "".join(partes)


# ============================================================
# AUXILIARES PDF
# ============================================================

def _cor(hexadecimal):
    return colors.HexColor(hexadecimal)


def _estilos_pdf():
    base = getSampleStyleSheet()

    return {
        "titulo": ParagraphStyle(
            "TituloTecnico",
            parent=base["Title"],
            fontName="Helvetica-Bold",
            textColor=_cor(COR_AZUL),
            fontSize=18,
            leading=21,
            alignment=TA_LEFT,
            spaceAfter=4,
        ),
        "subtitulo": ParagraphStyle(
            "SubtituloTecnico",
            parent=base["BodyText"],
            fontName="Helvetica",
            textColor=_cor("#5E6C78"),
            fontSize=9,
            leading=12,
            spaceAfter=8,
        ),
        "secao": ParagraphStyle(
            "SecaoTecnica",
            parent=base["Heading2"],
            fontName="Helvetica-Bold",
            textColor=_cor(COR_AZUL),
            fontSize=12.2,
            leading=15,
            spaceBefore=8,
            spaceAfter=6,
        ),
        "normal": ParagraphStyle(
            "TextoTecnico",
            parent=base["BodyText"],
            fontName="Helvetica",
            textColor=_cor(COR_TEXTO),
            fontSize=8.2,
            leading=10.5,
        ),
        "pequeno": ParagraphStyle(
            "TextoPequeno",
            parent=base["BodyText"],
            fontName="Helvetica",
            textColor=_cor("#5E6C78"),
            fontSize=7.1,
            leading=9,
        ),
        "legenda": ParagraphStyle(
            "LegendaFoto",
            parent=base["BodyText"],
            fontName="Helvetica",
            textColor=_cor(COR_TEXTO),
            fontSize=7.4,
            leading=9.2,
            spaceAfter=2,
        ),
        "legenda_bold": ParagraphStyle(
            "LegendaFotoBold",
            parent=base["BodyText"],
            fontName="Helvetica-Bold",
            textColor=_cor(COR_AZUL),
            fontSize=7.7,
            leading=9.5,
        ),
        "card_titulo": ParagraphStyle(
            "CardTitulo",
            parent=base["BodyText"],
            fontName="Helvetica-Bold",
            textColor=_cor("#667481"),
            fontSize=6.8,
            leading=8,
        ),
        "card_valor": ParagraphStyle(
            "CardValor",
            parent=base["BodyText"],
            fontName="Helvetica-Bold",
            textColor=_cor(COR_AZUL),
            fontSize=10.2,
            leading=12,
        ),
    }


def _p(valor, estilo, padrao="Não informado"):
    conteudo = escape(texto(valor, padrao)).replace("\n", "<br/>")
    return Paragraph(conteudo, estilo)



class _MarcadorSumario(Flowable):
    """
    Flowable invisível usado para registrar uma seção no sumário do PDF
    sem alterar o layout visual da página.
    """

    def __init__(self, titulo, nivel=0, chave=None):
        super().__init__()
        self.titulo_sumario = str(titulo)
        self.nivel_sumario = int(nivel)
        self.chave_sumario = chave or (
            "secao_"
            + re.sub(
                r"[^a-zA-Z0-9_]+",
                "_",
                self.titulo_sumario,
            ).strip("_")
        )
        self.width = 0
        self.height = 0

    def wrap(self, availWidth, availHeight):
        return 0, 0

    def draw(self):
        pass


class _DocumentoComSumario(SimpleDocTemplate):
    """
    Documento ReportLab com captura automática dos marcadores de seção.

    A capa é a página física 1, mas não recebe numeração no rodapé.
    Por isso, o número exibido no sumário acompanha a mesma lógica do
    rodapé do relatório: página física - 1.
    """

    def afterFlowable(self, flowable):
        if isinstance(flowable, _MarcadorSumario):
            titulo = flowable.titulo_sumario
            nivel = flowable.nivel_sumario
            chave = flowable.chave_sumario

            pagina_logica = max(self.page - 1, 1)

            try:
                self.canv.bookmarkPage(chave)
                self.canv.addOutlineEntry(
                    titulo,
                    chave,
                    level=nivel,
                    closed=False,
                )
            except Exception:
                pass

            self.notify(
                "TOCEntry",
                (
                    nivel,
                    titulo,
                    pagina_logica,
                    chave,
                ),
            )


def _marcador_sumario(numero, titulo):
    return _MarcadorSumario(
        f"{numero}. {titulo}",
        nivel=0,
        chave=f"secao_{numero}_{re.sub(r'[^a-zA-Z0-9_]+', '_', str(titulo)).strip('_')}",
    )


def _sumario_pdf(estilos):
    """
    Monta uma página de sumário automático.
    Os números das páginas são resolvidos pelo multiBuild do ReportLab.
    """
    elementos = []

    elementos.append(
        Paragraph(
            "SUMÁRIO",
            ParagraphStyle(
                "TituloSumario",
                parent=estilos["titulo"],
                fontName="Helvetica-Bold",
                textColor=_cor(COR_AZUL),
                fontSize=17,
                leading=20,
                spaceAfter=4,
            ),
        )
    )

    elementos.append(
        Paragraph(
            "Seções do relatório técnico",
            ParagraphStyle(
                "SubtituloSumario",
                parent=estilos["subtitulo"],
                fontName="Helvetica",
                textColor=_cor("#667481"),
                fontSize=8.5,
                leading=11,
                spaceAfter=8,
            ),
        )
    )

    elementos.append(
        HRFlowable(
            width="100%",
            thickness=0.7,
            color=_cor(COR_LINHA),
        )
    )
    elementos.append(Spacer(1, 5 * mm))

    toc = TableOfContents()
    toc.levelStyles = [
        ParagraphStyle(
            "TOCNivel0",
            parent=estilos["normal"],
            fontName="Helvetica",
            fontSize=9,
            leading=13,
            textColor=_cor(COR_TEXTO),
            leftIndent=0,
            firstLineIndent=0,
            spaceBefore=2,
            spaceAfter=2,
        ),
        ParagraphStyle(
            "TOCNivel1",
            parent=estilos["pequeno"],
            fontName="Helvetica",
            fontSize=8,
            leading=11,
            textColor=_cor("#5E6C78"),
            leftIndent=8 * mm,
            firstLineIndent=0,
            spaceBefore=1,
            spaceAfter=1,
        ),
    ]

    toc.dotsMinLevel = 0

    elementos.append(toc)

    return elementos


def _secao_pdf(numero, titulo, estilos):
    tabela = Table(
        [[
            Paragraph(
                f"<b>{numero}</b>",
                estilos["normal"],
            ),
            Paragraph(
                f"<b>{escape(titulo)}</b>",
                estilos["secao"],
            ),
        ]],
        colWidths=[10 * mm, 165 * mm],
    )

    tabela.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (0, 0), _cor(COR_AZUL_2)),
                ("TEXTCOLOR", (0, 0), (0, 0), colors.white),
                ("BACKGROUND", (1, 0), (1, 0), _cor(COR_AZUL_CLARO)),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (-1, -1), 5),
                ("RIGHTPADDING", (0, 0), (-1, -1), 5),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ("BOX", (0, 0), (-1, -1), 0.4, _cor(COR_LINHA)),
            ]
        )
    )

    return tabela


def _tabela_chave_valor_pdf(dados, estilos):
    linhas = []

    for chave, valor in dados:
        linhas.append(
            [
                _p(chave, estilos["pequeno"]),
                _p(valor, estilos["normal"]),
            ]
        )

    tabela = Table(
        linhas,
        colWidths=[48 * mm, 127 * mm],
    )

    tabela.setStyle(
        TableStyle(
            [
                ("GRID", (0, 0), (-1, -1), 0.35, _cor(COR_LINHA)),
                ("BACKGROUND", (0, 0), (0, -1), _cor(COR_CINZA)),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 5),
                ("RIGHTPADDING", (0, 0), (-1, -1), 5),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ]
        )
    )

    return tabela


def _card_pdf(titulo, valor, estilos, destaque=False):
    cor_barra = COR_LARANJA if destaque else COR_AZUL_2

    tabela = Table(
        [[
            Paragraph(
                f"<b>{escape(texto(titulo))}</b><br/>"
                f"<font size='10'><b>{escape(texto(valor))}</b></font>",
                estilos["card_titulo"],
            )
        ]],
        colWidths=[27.8 * mm],
        rowHeights=[18 * mm],
    )

    tabela.setStyle(
        TableStyle(
            [
                ("BOX", (0, 0), (-1, -1), 0.4, _cor(COR_LINHA)),
                ("LINEBEFORE", (0, 0), (0, -1), 2.4, _cor(cor_barra)),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (-1, -1), 5),
                ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )

    return tabela


def _cabecalho_rodape_pagina(canvas, doc, nome_oae, tipo_relatorio):
    canvas.saveState()
    largura, altura = A4

    canvas.setFillColor(_cor(COR_AZUL))
    canvas.rect(0, altura - 13 * mm, largura, 13 * mm, fill=1, stroke=0)

    canvas.setFillColor(colors.white)
    canvas.setFont("Helvetica-Bold", 7.4)
    canvas.drawString(16 * mm, altura - 8.2 * mm, "GÊMEO DIGITAL PARA INSPEÇÃO DE PONTES")

    canvas.setStrokeColor(_cor(COR_LINHA))
    canvas.line(15 * mm, 12 * mm, largura - 15 * mm, 12 * mm)

    canvas.setFillColor(_cor("#667481"))
    canvas.setFont("Helvetica", 6.7)
    canvas.drawString(16 * mm, 7.4 * mm, f"{texto(nome_oae)} | {texto(tipo_relatorio)}")
    canvas.drawRightString(largura - 16 * mm, 7.4 * mm, f"Página {max(doc.page - 1, 1)}")

    canvas.restoreState()


def _pagina_capa(canvas, doc, subtitulo_topo="Sistema de apoio à gestão de obras de arte especiais (OAE)"):
    canvas.saveState()
    largura, altura = A4

    canvas.setFillColor(_cor(COR_AZUL))
    canvas.rect(0, altura - 42 * mm, largura, 42 * mm, fill=1, stroke=0)

    canvas.setFillColor(_cor(COR_AZUL_2))
    canvas.rect(0, altura - 44 * mm, largura, 2 * mm, fill=1, stroke=0)

    canvas.setFillColor(colors.white)
    canvas.setFont("Helvetica-Bold", 13)
    canvas.drawString(20 * mm, altura - 20 * mm, "GÊMEO DIGITAL PARA INSPEÇÃO DE PONTES")

    canvas.setFont("Helvetica", 9)
    canvas.drawString(20 * mm, altura - 28 * mm, subtitulo_topo)

    canvas.setFillColor(_cor("#8A97A3"))
    canvas.setFont("Helvetica", 7)
    canvas.drawString(
        20 * mm,
        12 * mm,
        "Documento técnico gerado eletronicamente. Sujeito à validação e conferência do profissional responsável.",
    )

    canvas.restoreState()


def _nota_tecnica_pdf(estilos):
    tabela = Table(
        [[
            Paragraph(
                "<b>Nota técnica</b><br/>"
                "Este documento consolida informações registradas no Gêmeo Digital. "
                "A validação do diagnóstico, da classificação e das decisões de "
                "intervenção permanece sob responsabilidade do profissional competente.",
                estilos["pequeno"],
            )
        ]],
        colWidths=[175 * mm],
    )

    tabela.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), _cor("#FFF8E4")),
                ("BOX", (0, 0), (-1, -1), 0.6, _cor("#E7C577")),
                ("LINEBEFORE", (0, 0), (0, -1), 2.4, _cor(COR_LARANJA)),
                ("LEFTPADDING", (0, 0), (-1, -1), 7),
                ("RIGHTPADDING", (0, 0), (-1, -1), 7),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )

    return tabela


def _bloco_capa(oae, titulo_relatorio, linhas_info, estilos, classificacao=None):
    """
    Monta o conteúdo da capa (abaixo da faixa azul desenhada pelo
    canvas em _pagina_capa) e termina com um PageBreak, deixando o
    conteúdo técnico começar sempre em uma página nova.
    """
    elementos = [Spacer(1, 26 * mm)]

    elementos.append(
        Paragraph(
            f"<font size=19 color='{COR_AZUL}'><b>{escape(titulo_relatorio)}</b></font>",
            estilos["titulo"],
        )
    )
    elementos.append(Spacer(1, 2 * mm))
    elementos.append(
        Paragraph(
            f"<font size=13 color='{COR_TEXTO}'><b>{escape(nome_oae_exibicao(oae))}</b></font>",
            estilos["subtitulo"],
        )
    )
    elementos.append(Spacer(1, 10 * mm))

    linhas = []

    for chave, valor in linhas_info:
        linhas.append(
            [
                _p(chave, estilos["pequeno"]),
                _p(valor, estilos["normal"]),
            ]
        )

    tabela = Table(linhas, colWidths=[50 * mm, 110 * mm])
    tabela.setStyle(
        TableStyle(
            [
                ("GRID", (0, 0), (-1, -1), 0.35, _cor(COR_LINHA)),
                ("BACKGROUND", (0, 0), (0, -1), _cor(COR_CINZA)),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    elementos.append(tabela)
    elementos.append(Spacer(1, 10 * mm))

    if classificacao is not None:
        cards = [
            _card_pdf(
                "Estrutural",
                classificacao_com_condicao(classificacao["estrutural"]),
                estilos,
                destaque=(classificacao["estrutural"] is not None and int(classificacao["estrutural"]) <= 3),
            ),
            _card_pdf(
                "Funcional",
                classificacao_com_condicao(classificacao["funcional"]),
                estilos,
                destaque=(classificacao["funcional"] is not None and int(classificacao["funcional"]) <= 3),
            ),
            _card_pdf(
                "Durabilidade",
                classificacao_com_condicao(classificacao["durabilidade"]),
                estilos,
                destaque=(classificacao["durabilidade"] is not None and int(classificacao["durabilidade"]) <= 3),
            ),
        ]

        tabela_cards = Table([cards], colWidths=[53.3 * mm] * 3)
        tabela_cards.setStyle(
            TableStyle(
                [
                    ("LEFTPADDING", (0, 0), (-1, -1), 0),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 3),
                    ("TOPPADDING", (0, 0), (-1, -1), 0),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
                ]
            )
        )

        elementos.append(Paragraph("<b>Classificação da condição</b>", estilos["normal"]))
        elementos.append(Spacer(1, 2 * mm))
        elementos.append(tabela_cards)
        elementos.append(Spacer(1, 10 * mm))

    elementos.append(HRFlowable(width="55%", thickness=0.6, color=_cor(COR_LINHA)))
    elementos.append(Spacer(1, 3 * mm))
    elementos.append(
        Paragraph(
            f"Relatório gerado em {datetime.now().strftime('%d/%m/%Y às %H:%M')} "
            "a partir dos dados armazenados no sistema.",
            estilos["pequeno"],
        )
    )
    elementos.append(PageBreak())

    return elementos


COR_CINZA_ESTAVEL = "#8A97A3"


def _cor_severidade_foto(situacao):
    """
    Define a cor da faixa lateral do card de foto conforme a
    situação da anomalia associada. Fotos de vista geral (sem
    anomalia) usam o azul institucional.
    """
    if situacao is None:
        return COR_AZUL_2

    situacao_lower = situacao.strip().lower()

    if "identificada nesta inspeção" in situacao_lower:
        return COR_VERMELHO
    if "evolução" in situacao_lower:
        return COR_LARANJA
    if "estáve" in situacao_lower or "estave" in situacao_lower:
        return COR_CINZA_ESTAVEL

    return COR_AZUL_2


def _situacao_anomalia_foto(anomalia, inspecao_id):
    """
    Busca a situação da anomalia associada à foto (mesma lógica da
    seção 7), usada aqui só para decidir a cor do card da foto.
    """
    if anomalia is None:
        return None

    db = SessionLocal()
    observacao = (
        db.query(models.ObservacaoAnomalia)
        .filter(models.ObservacaoAnomalia.anomalia_id == anomalia.id)
        .filter(models.ObservacaoAnomalia.inspecao_id == inspecao_id)
        .first()
    )
    db.close()

    if observacao is not None:
        return texto(observacao.situacao_observada, "")

    return "Identificada nesta inspeção"


def _imagem_reportlab(caminho, max_largura=78 * mm, max_altura=52 * mm):
    try:
        imagem = RLImage(str(caminho))
        largura = float(imagem.imageWidth)
        altura = float(imagem.imageHeight)

        if largura <= 0 or altura <= 0:
            return None

        fator = min(max_largura / largura, max_altura / altura)
        imagem.drawWidth = largura * fator
        imagem.drawHeight = altura * fator
        return imagem
    except Exception:
        return None


def _imagem_com_moldura(caminho, estilos, largura=78 * mm, altura=48 * mm):
    """
    Envolve a imagem (ou o aviso de 'não localizada') em uma célula
    de altura fixa, com a imagem centralizada dentro. Garante que
    fotos verticais e horizontais fiquem com a mesma altura de card
    quando exibidas lado a lado.
    """
    imagem = (
        _imagem_reportlab(caminho, max_largura=largura - 4 * mm, max_altura=altura - 4 * mm)
        if caminho
        else None
    )

    conteudo = imagem if imagem is not None else Paragraph(
        "Imagem não localizada no armazenamento local.", estilos["pequeno"]
    )

    moldura = Table(
        [[conteudo]],
        colWidths=[largura],
        rowHeights=[altura],
    )
    moldura.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), _cor(COR_CINZA) if imagem is None else colors.white),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("TOPPADDING", (0, 0), (-1, -1), 2),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
            ]
        )
    )
    return moldura


def _bloco_foto_pdf(foto, numero, componentes, estilos, inspecao_id=None):
    caminho = caminho_foto_existente(foto)
    componente = componentes.get(getattr(foto, "componente_id", None))

    anomalia = None
    vinculo = buscar_vinculo_foto_anomalia(foto.id)

    if vinculo is not None:
        anomalia_id = getattr(vinculo, "anomalia_permanente_id", None)
        anomalia = buscar_anomalia_por_id(anomalia_id)
    elif getattr(foto, "anomalia_id", None) is not None:
        anomalia = buscar_anomalia_por_id(foto.anomalia_id)

    situacao = _situacao_anomalia_foto(anomalia, inspecao_id) if anomalia else None
    cor_faixa = _cor_severidade_foto(situacao)

    if anomalia is not None:
        cabecalho = Table(
            [[
                Paragraph(f"<b>Foto {numero:02d}</b>", estilos["legenda_bold"]),
                Paragraph(
                    f"<font color='{cor_faixa}'><b>ANOMALIA · {escape(texto(anomalia.tipo_anomalia))}</b></font>",
                    estilos["pequeno"],
                ),
            ]],
            colWidths=[30 * mm, 48 * mm],
        )
        cabecalho.setStyle(
            TableStyle(
                [
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 0),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                    ("TOPPADDING", (0, 0), (-1, -1), 0),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
                ]
            )
        )
        elementos = [cabecalho, Spacer(1, 1.2 * mm)]
    else:
        elementos = [
            Paragraph(f"<b>Foto {numero:02d}</b> · Vista geral", estilos["legenda_bold"]),
            Spacer(1, 1.2 * mm),
        ]

    elementos.append(_imagem_com_moldura(caminho, estilos))
    elementos.append(Spacer(1, 1.8 * mm))
    elementos.append(_p(foto.identificacao, estilos["legenda"]))

    referencias = [
        f"Data: {data_br(foto.data_foto)}",
        f"Tipo: {texto(foto.tipo_registro)}",
    ]

    if componente is not None:
        referencias.append(f"Componente: {limpar_nome_componente(componente.nome)}")

    elementos.append(
        Paragraph(" | ".join(escape(item) for item in referencias), estilos["pequeno"])
    )

    if texto(foto.observacoes, "") != "":
        elementos.append(Spacer(1, 1 * mm))
        elementos.append(_p(foto.observacoes, estilos["pequeno"], ""))

    card = Table([[elementos]], colWidths=[84 * mm])
    card.setStyle(
        TableStyle(
            [
                ("BOX", (0, 0), (-1, -1), 0.35, _cor(COR_LINHA)),
                ("LINEBEFORE", (0, 0), (0, -1), 2.6, _cor(cor_faixa)),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 5),
                ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ]
        )
    )
    return card


def montar_secao_fotos(historia, dados, componentes, estilos, inspecao_id):
    """
    Monta a prancha fotográfica dividida em duas seções:
    'Registro fotográfico geral' e 'Evidências fotográficas de
    anomalias', cada foto de anomalia com faixa lateral colorida
    conforme a situação observada na campanha.
    """
    fotos = dados["fotografias"]

    if len(fotos) == 0:
        historia.append(_p("Nenhuma fotografia vinculada à inspeção.", estilos["normal"]))
        return

    fotos_numeradas = list(enumerate(fotos, start=1))

    def tem_anomalia(item):
        _, foto = item
        vinculo = buscar_vinculo_foto_anomalia(foto.id)
        if vinculo is not None and getattr(vinculo, "anomalia_permanente_id", None):
            return True
        return getattr(foto, "anomalia_id", None) is not None

    fotos_anomalia = [item for item in fotos_numeradas if tem_anomalia(item)]
    fotos_gerais = [item for item in fotos_numeradas if not tem_anomalia(item)]

    def _monta_pranchas(lista):
        for inicio in range(0, len(lista), 2):
            par = lista[inicio:inicio + 2]
            celulas = []

            for numero, foto in par:
                celulas.append(
                    _bloco_foto_pdf(foto, numero, componentes, estilos, inspecao_id=inspecao_id)
                )

            if len(celulas) == 1:
                celulas.append("")

            linha = Table([celulas], colWidths=[87.5 * mm, 87.5 * mm], hAlign="LEFT")
            linha.setStyle(
                TableStyle(
                    [
                        ("VALIGN", (0, 0), (-1, -1), "TOP"),
                        ("LEFTPADDING", (0, 0), (-1, -1), 0),
                        ("RIGHTPADDING", (0, 0), (-1, -1), 3),
                        ("TOPPADDING", (0, 0), (-1, -1), 0),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                    ]
                )
            )
            historia.append(KeepTogether(linha))

    if fotos_gerais:
        historia.append(Paragraph("<b>Registro fotográfico geral</b>", estilos["normal"]))
        historia.append(Spacer(1, 2 * mm))
        _monta_pranchas(fotos_gerais)
        historia.append(Spacer(1, 3 * mm))

    if fotos_anomalia:
        historia.append(Paragraph("<b>Evidências fotográficas de anomalias</b>", estilos["normal"]))
        historia.append(Spacer(1, 2 * mm))
        _monta_pranchas(fotos_anomalia)


# ============================================================
# PDF - RELATÓRIO DE UMA INSPEÇÃO
# ============================================================

def gerar_pdf_inspecao(dados):
    if not REPORTLAB_DISPONIVEL:
        return None

    buffer = BytesIO()

    documento = _DocumentoComSumario(
        buffer,
        pagesize=A4,
        rightMargin=17.5 * mm,
        leftMargin=17.5 * mm,
        topMargin=20 * mm,
        bottomMargin=18 * mm,
        title="Relatório técnico de inspeção de OAE",
        author="Gêmeo Digital para Inspeção de Pontes",
    )

    estilos = _estilos_pdf()
    oae = dados["oae"]
    inspecao = dados["inspecao"]
    classificacao = dados["classificacao_geral"]
    componentes = dados["componentes"]

    linhas_capa = [
        ("Código da OAE", oae.codigo),
        ("Rodovia", oae.rodovia),
        (
            "Município / UF",
            f"{texto(oae.municipio, '')}{' / ' if oae.municipio and oae.uf else ''}{texto(oae.uf, '')}",
        ),
        ("Modalidade da inspeção", inspecao.tipo_inspecao),
        ("Data da inspeção", data_br(inspecao.data_inspecao)),
        ("Responsável técnico", inspecao.responsavel),
        ("Registro profissional", inspecao.registro_profissional),
    ]

    historia = _bloco_capa(
        oae,
        "RELATÓRIO TÉCNICO DE INSPEÇÃO DE OAE",
        linhas_capa,
        estilos,
        classificacao=classificacao,
    )

    # Sumário automático: capa -> sumário -> conteúdo técnico.
    historia.extend(_sumario_pdf(estilos))
    historia.append(PageBreak())

    historia.append(_nota_tecnica_pdf(estilos))
    historia.append(Spacer(1, 5 * mm))

    secao = 1

    historia.append(_marcador_sumario(secao, "Identificação da OAE"))
    historia.append(_secao_pdf(secao, "Identificação da OAE", estilos))
    secao += 1
    historia.append(Spacer(1, 2 * mm))
    historia.append(
        _tabela_chave_valor_pdf(
            [
                ("Nome", oae.nome),
                ("Código", oae.codigo),
                ("Rodovia", oae.rodovia),
                (
                    "Município / UF",
                    f"{texto(oae.municipio, '')}{' / ' if oae.municipio and oae.uf else ''}{texto(oae.uf, '')}",
                ),
                ("Tipo de estrutura", oae.tipo_estrutura),
                ("Ano de construção", oae.ano_construcao),
                ("Número de vãos", oae.numero_vaos),
                ("Comprimento total", f"{numero_br(oae.comprimento_total)} m"),
                ("Largura total", f"{numero_br(oae.largura)} m"),
                ("Protensão", oae.tipo_protensao),
            ],
            estilos,
        )
    )
    historia.append(Spacer(1, 4 * mm))

    historia.append(_marcador_sumario(secao, "Identificação e objetivo da inspeção"))
    historia.append(_secao_pdf(secao, "Identificação e objetivo da inspeção", estilos))
    secao += 1
    historia.append(Spacer(1, 2 * mm))
    historia.append(
        _tabela_chave_valor_pdf(
            [
                ("Modalidade", inspecao.tipo_inspecao),
                ("Data", data_br(inspecao.data_inspecao)),
                ("Responsável", inspecao.responsavel),
                ("Registro profissional", inspecao.registro_profissional),
                ("Objetivo / observações", inspecao.observacoes),
            ],
            estilos,
        )
    )
    historia.append(Spacer(1, 4 * mm))

    historia.append(_marcador_sumario(secao, "Histórico das inspeções"))
    historia.append(_secao_pdf(secao, "Histórico das inspeções", estilos))
    secao += 1
    historia.append(Spacer(1, 2 * mm))

    linhas_hist = [[
        _p("Inspeção", estilos["pequeno"]),
        _p("Modalidade", estilos["pequeno"]),
        _p("Data", estilos["pequeno"]),
    ]]

    for indice, item in enumerate(dados["historico_ate_campanha"], start=1):
        linhas_hist.append(
            [
                _p(f"{indice:02d}", estilos["normal"]),
                _p(item.tipo_inspecao, estilos["normal"]),
                _p(data_br(item.data_inspecao), estilos["normal"]),
            ]
        )

    tabela_hist = Table(
        linhas_hist,
        colWidths=[25 * mm, 95 * mm, 55 * mm],
        repeatRows=1,
    )
    tabela_hist.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), _cor(COR_AZUL)),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("GRID", (0, 0), (-1, -1), 0.35, _cor(COR_LINHA)),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 4),
                ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    historia.append(tabela_hist)
    historia.append(Spacer(1, 4 * mm))

    for titulo_secao, campos in dados["secoes_especificas"]:
        historia.append(_marcador_sumario(secao, titulo_secao))
        historia.append(_secao_pdf(secao, titulo_secao, estilos))
        secao += 1
        historia.append(Spacer(1, 2 * mm))

        linhas = [(chave, valor) for chave, valor in campos.items()]
        historia.append(_tabela_chave_valor_pdf(linhas, estilos))
        historia.append(Spacer(1, 4 * mm))

    historia.append(_marcador_sumario(secao, "Registro e evolução das anomalias"))
    historia.append(_secao_pdf(secao, "Registro e evolução das anomalias", estilos))
    secao += 1
    historia.append(Spacer(1, 2 * mm))

    if len(dados["anomalias"]) == 0:
        historia.append(_p("Nenhuma anomalia relacionada à campanha.", estilos["normal"]))
    else:
        linhas = [[
            _p("Ref.", estilos["pequeno"]),
            _p("Componente", estilos["pequeno"]),
            _p("Anomalia", estilos["pequeno"]),
            _p("Localização", estilos["pequeno"]),
            _p("Situação", estilos["pequeno"]),
        ]]

        for indice, (anomalia, observacao) in enumerate(dados["anomalias"], start=1):
            componente = componentes.get(anomalia.componente_id)
            situacao = (
                observacao.situacao_observada
                if observacao is not None
                else "Identificada nesta inspeção"
            )

            linhas.append(
                [
                    _p(f"AN-{indice:02d}", estilos["pequeno"]),
                    _p(
                        limpar_nome_componente(
                            componente.nome if componente else None
                        ),
                        estilos["pequeno"],
                    ),
                    _p(anomalia.tipo_anomalia, estilos["pequeno"]),
                    _p(anomalia.localizacao_referencia, estilos["pequeno"]),
                    _p(situacao, estilos["pequeno"]),
                ]
            )

        tabela_anomalias = Table(
            linhas,
            colWidths=[16 * mm, 35 * mm, 40 * mm, 54 * mm, 30 * mm],
            repeatRows=1,
        )
        tabela_anomalias.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), _cor(COR_AZUL)),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("GRID", (0, 0), (-1, -1), 0.35, _cor(COR_LINHA)),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 3),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 3),
                    ("TOPPADDING", (0, 0), (-1, -1), 4),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ]
            )
        )
        historia.append(tabela_anomalias)

    historia.append(Spacer(1, 4 * mm))
    historia.append(_marcador_sumario(secao, "Classificação da condição da OAE"))
    historia.append(_secao_pdf(secao, "Classificação da condição da OAE", estilos))
    secao += 1
    historia.append(Spacer(1, 2 * mm))

    tabela_notas = Table(
        [[
            _card_pdf(
                "Estrutural",
                classificacao_com_condicao(classificacao["estrutural"]),
                estilos,
                destaque=(classificacao["estrutural"] is not None and int(classificacao["estrutural"]) <= 3),
            ),
            _card_pdf(
                "Funcional",
                classificacao_com_condicao(classificacao["funcional"]),
                estilos,
                destaque=(classificacao["funcional"] is not None and int(classificacao["funcional"]) <= 3),
            ),
            _card_pdf(
                "Durabilidade",
                classificacao_com_condicao(classificacao["durabilidade"]),
                estilos,
                destaque=(classificacao["durabilidade"] is not None and int(classificacao["durabilidade"]) <= 3),
            ),
        ]],
        colWidths=[58.3 * mm, 58.3 * mm, 58.3 * mm],
    )
    tabela_notas.setStyle(
        TableStyle(
            [
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 3),
                ("TOPPADDING", (0, 0), (-1, -1), 0),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
            ]
        )
    )
    historia.append(tabela_notas)

    if dados["classificacao_direta"] is not None:
        registro = dados["classificacao_direta"]
        justificativas = [
            ("Justificativa estrutural", registro.get("justificativa_estrutural")),
            ("Justificativa funcional", registro.get("justificativa_funcional")),
            ("Justificativa de durabilidade", registro.get("justificativa_durabilidade")),
            ("Observações da classificação", registro.get("observacoes")),
        ]

        if any(texto(v, "") != "" for _, v in justificativas):
            historia.append(Spacer(1, 3 * mm))
            historia.append(_tabela_chave_valor_pdf(justificativas, estilos))

    if eh_inspecao_especial(inspecao) and dados["classificacoes_componentes"]:
        historia.append(Spacer(1, 3 * mm))
        historia.append(
            Paragraph(
                "<b>Classificação detalhada por componente</b>",
                estilos["normal"],
            )
        )
        historia.append(Spacer(1, 1.5 * mm))

        linhas = [[
            _p("Componente", estilos["pequeno"]),
            _p("Estrutural", estilos["pequeno"]),
            _p("Funcional", estilos["pequeno"]),
            _p("Durabilidade", estilos["pequeno"]),
        ]]

        for item in dados["classificacoes_componentes"]:
            componente = componentes.get(item.componente_id)
            linhas.append(
                [
                    _p(
                        limpar_nome_componente(
                            componente.nome if componente else None
                        ),
                        estilos["pequeno"],
                    ),
                    _p(item.nota_estrutural, estilos["pequeno"]),
                    _p(item.nota_funcional, estilos["pequeno"], "NA"),
                    _p(item.nota_durabilidade, estilos["pequeno"]),
                ]
            )

        tabela_componentes = Table(
            linhas,
            colWidths=[85 * mm, 30 * mm, 30 * mm, 30 * mm],
            repeatRows=1,
        )
        tabela_componentes.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), _cor(COR_AZUL)),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("GRID", (0, 0), (-1, -1), 0.35, _cor(COR_LINHA)),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 4),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                    ("TOPPADDING", (0, 0), (-1, -1), 4),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ]
            )
        )
        historia.append(tabela_componentes)

    historia.append(Spacer(1, 4 * mm))
    historia.append(_marcador_sumario(secao, "Levantamento fotográfico"))
    historia.append(_secao_pdf(secao, "Levantamento fotográfico", estilos))
    secao += 1
    historia.append(Spacer(1, 2 * mm))

    historia.append(
        _p(
            (
                f"Foram vinculadas {len(dados['fotografias'])} fotografia(s) "
                "à campanha. As imagens abaixo são apresentadas com identificação "
                "e referência aos dados registrados no sistema."
            ),
            estilos["normal"],
        )
    )
    historia.append(Spacer(1, 3 * mm))

    montar_secao_fotos(historia, dados, componentes, estilos, inspecao.id)

    registro_rotineira = (
        buscar_dados_rotineira(inspecao.id)
        if texto(inspecao.tipo_inspecao, "") == "Rotineira"
        else None
    )

    if registro_rotineira is not None:
        historia.append(_marcador_sumario(secao, "Síntese dos registros e recomendações"))
        historia.append(_secao_pdf(secao, "Síntese dos registros e recomendações", estilos))
        secao += 1
        historia.append(Spacer(1, 2 * mm))
        historia.append(
            _tabela_chave_valor_pdf(
                [
                    (
                        "Alterações observadas",
                        getattr(registro_rotineira, "comentarios_alteracoes", None),
                    ),
                    (
                        "Informações complementares",
                        getattr(registro_rotineira, "informacoes_complementares", None),
                    ),
                    (
                        "Recomendações terapêuticas",
                        getattr(registro_rotineira, "recomendacoes_terapeuticas", None),
                    ),
                ],
                estilos,
            )
        )
        historia.append(Spacer(1, 4 * mm))

    historia.append(
        HRFlowable(
            width="100%",
            thickness=0.5,
            color=_cor(COR_LINHA),
        )
    )
    historia.append(Spacer(1, 3 * mm))
    historia.append(
        Paragraph(
            (
                f"<b>Profissional responsável:</b> {escape(texto(inspecao.responsavel))}<br/>"
                f"<b>Registro profissional:</b> {escape(texto(inspecao.registro_profissional))}<br/><br/>"
                "Este relatório deve ser tecnicamente conferido e validado pelo profissional responsável."
            ),
            estilos["normal"],
        )
    )
    historia.append(Spacer(1, 4 * mm))
    historia.append(
        Paragraph(
            (
                "Relatório gerado em "
                f"{datetime.now().strftime('%d/%m/%Y às %H:%M')} "
                "a partir dos dados armazenados no sistema."
            ),
            estilos["pequeno"],
        )
    )

    def capa(canvas, doc):
        _pagina_capa(canvas, doc)

    def pagina(canvas, doc):
        _cabecalho_rodape_pagina(
            canvas,
            doc,
            nome_oae=oae.nome,
            tipo_relatorio=f"Inspeção {texto(inspecao.tipo_inspecao)}",
        )

    documento.multiBuild(
        historia,
        onFirstPage=capa,
        onLaterPages=pagina,
    )

    buffer.seek(0)
    return buffer.getvalue()


# ============================================================
# PDF - RELATÓRIO CONSOLIDADO
# ============================================================

def gerar_pdf_consolidado(dados):
    if not REPORTLAB_DISPONIVEL:
        return None

    buffer = BytesIO()

    documento = _DocumentoComSumario(
        buffer,
        pagesize=A4,
        rightMargin=17.5 * mm,
        leftMargin=17.5 * mm,
        topMargin=20 * mm,
        bottomMargin=18 * mm,
        title="Relatório consolidado da OAE",
        author="Gêmeo Digital para Inspeção de Pontes",
    )

    estilos = _estilos_pdf()
    oae = dados["oae"]

    linhas_capa = [
        ("Código da OAE", oae.codigo),
        ("Rodovia", oae.rodovia),
        (
            "Município / UF",
            f"{texto(oae.municipio, '')}{' / ' if oae.municipio and oae.uf else ''}{texto(oae.uf, '')}",
        ),
        ("Tipo de estrutura", oae.tipo_estrutura),
        ("Ano de construção", oae.ano_construcao),
        ("Inspeções registradas", len(dados["inspecoes"])),
    ]

    historia = _bloco_capa(
        oae,
        "RELATÓRIO CONSOLIDADO DA OAE",
        linhas_capa,
        estilos,
        classificacao=None,
    )

    # Sumário automático: capa -> sumário -> conteúdo técnico.
    historia.extend(_sumario_pdf(estilos))
    historia.append(PageBreak())

    historia.append(_nota_tecnica_pdf(estilos))
    historia.append(Spacer(1, 5 * mm))

    historia.append(_marcador_sumario(1, "Identificação da OAE"))
    historia.append(_secao_pdf(1, "Identificação da OAE", estilos))
    historia.append(Spacer(1, 2 * mm))
    historia.append(
        _tabela_chave_valor_pdf(
            [
                ("Nome", oae.nome),
                ("Código", oae.codigo),
                ("Rodovia", oae.rodovia),
                (
                    "Município / UF",
                    f"{texto(oae.municipio, '')}{' / ' if oae.municipio and oae.uf else ''}{texto(oae.uf, '')}",
                ),
                ("Tipo de estrutura", oae.tipo_estrutura),
                ("Ano de construção", oae.ano_construcao),
                ("Número de vãos", oae.numero_vaos),
            ],
            estilos,
        )
    )
    historia.append(Spacer(1, 4 * mm))

    historia.append(_marcador_sumario(2, "Histórico de inspeções e classificações"))
    historia.append(_secao_pdf(2, "Histórico de inspeções e classificações", estilos))
    historia.append(Spacer(1, 2 * mm))

    linhas = [[
        _p("Nº", estilos["pequeno"]),
        _p("Data", estilos["pequeno"]),
        _p("Tipo", estilos["pequeno"]),
        _p("E", estilos["pequeno"]),
        _p("F", estilos["pequeno"]),
        _p("D", estilos["pequeno"]),
        _p("Anom.", estilos["pequeno"]),
        _p("Fotos", estilos["pequeno"]),
    ]]

    for indice, campanha in enumerate(dados["campanhas"], start=1):
        inspecao = campanha["inspecao"]
        clas = campanha["classificacao"]

        linhas.append(
            [
                _p(f"{indice:02d}", estilos["pequeno"]),
                _p(data_br(inspecao.data_inspecao), estilos["pequeno"]),
                _p(inspecao.tipo_inspecao, estilos["pequeno"]),
                _p(clas["estrutural"], estilos["pequeno"]),
                _p(clas["funcional"], estilos["pequeno"]),
                _p(clas["durabilidade"], estilos["pequeno"]),
                _p(campanha["quantidade_anomalias"], estilos["pequeno"]),
                _p(campanha["quantidade_fotos"], estilos["pequeno"]),
            ]
        )

    tabela = Table(
        linhas,
        colWidths=[12 * mm, 27 * mm, 39 * mm, 18 * mm, 18 * mm, 18 * mm, 22 * mm, 21 * mm],
        repeatRows=1,
    )
    tabela.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), _cor(COR_AZUL)),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("GRID", (0, 0), (-1, -1), 0.35, _cor(COR_LINHA)),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 3),
                ("RIGHTPADDING", (0, 0), (-1, -1), 3),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    historia.append(tabela)
    historia.append(Spacer(1, 4 * mm))

    historia.append(_marcador_sumario(3, "Inventário atual de anomalias"))
    historia.append(_secao_pdf(3, "Inventário atual de anomalias", estilos))
    historia.append(Spacer(1, 2 * mm))

    if not dados["anomalias"]:
        historia.append(_p("Nenhuma anomalia permanente cadastrada.", estilos["normal"]))
    else:
        componentes = {item.id: item for item in dados["componentes"]}
        linhas = [[
            _p("Ref.", estilos["pequeno"]),
            _p("Componente", estilos["pequeno"]),
            _p("Anomalia", estilos["pequeno"]),
            _p("Localização", estilos["pequeno"]),
            _p("Status", estilos["pequeno"]),
        ]]

        for indice, anomalia in enumerate(dados["anomalias"], start=1):
            componente = componentes.get(anomalia.componente_id)
            linhas.append(
                [
                    _p(f"AN-{indice:02d}", estilos["pequeno"]),
                    _p(
                        limpar_nome_componente(
                            componente.nome if componente else None
                        ),
                        estilos["pequeno"],
                    ),
                    _p(anomalia.tipo_anomalia, estilos["pequeno"]),
                    _p(anomalia.localizacao_referencia, estilos["pequeno"]),
                    _p("Ativa" if anomalia.ativa else "Encerrada", estilos["pequeno"]),
                ]
            )

        tabela_anomalias = Table(
            linhas,
            colWidths=[16 * mm, 38 * mm, 42 * mm, 54 * mm, 25 * mm],
            repeatRows=1,
        )
        tabela_anomalias.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), _cor(COR_AZUL)),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("GRID", (0, 0), (-1, -1), 0.35, _cor(COR_LINHA)),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 3),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 3),
                    ("TOPPADDING", (0, 0), (-1, -1), 4),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ]
            )
        )
        historia.append(tabela_anomalias)

    historia.append(Spacer(1, 6 * mm))
    historia.append(
        HRFlowable(
            width="100%",
            thickness=0.5,
            color=_cor(COR_LINHA),
        )
    )
    historia.append(Spacer(1, 2 * mm))
    historia.append(
        Paragraph(
            f"Relatório consolidado gerado em {datetime.now().strftime('%d/%m/%Y às %H:%M')}.",
            estilos["pequeno"],
        )
    )

    def capa(canvas, doc):
        _pagina_capa(canvas, doc)

    def pagina(canvas, doc):
        _cabecalho_rodape_pagina(
            canvas,
            doc,
            nome_oae=oae.nome,
            tipo_relatorio="Relatório consolidado",
        )

    documento.multiBuild(
        historia,
        onFirstPage=capa,
        onLaterPages=pagina,
    )

    buffer.seek(0)
    return buffer.getvalue()


# ============================================================
# PRÉVIAS NO STREAMLIT
# ============================================================

def mostrar_cards_classificacao_preview(classificacao):
    """
    Exibe as três notas da classificação com o mesmo padrão
    semântico de cores usado no módulo de Classificação.
    """

    cores = {
        5: ("#E7F6EC", "#17643A", "#A9D6B8"),
        4: ("#EEF7E4", "#4E6F22", "#CFE2A7"),
        3: ("#FFF6D8", "#765600", "#E8D37E"),
        2: ("#FFF0DD", "#8C5000", "#EDC38B"),
        1: ("#FCE5E2", "#9C332B", "#E5ADA7"),
        0: ("#F4D6D8", "#841D24", "#D99BA0"),
    }

    def nome_condicao(nota):
        mapa = {
            5: "Excelente",
            4: "Boa",
            3: "Regular",
            2: "Ruim",
            1: "Crítica",
            0: "Emergencial",
        }
        return mapa.get(nota, "Não classificada")

    itens = [
        ("Estrutural", classificacao.get("estrutural")),
        ("Funcional", classificacao.get("funcional")),
        ("Durabilidade", classificacao.get("durabilidade")),
    ]

    colunas = st.columns(3)

    for coluna, (rotulo, nota) in zip(colunas, itens):
        with coluna:

            if nota is None:
                valor = "NA" if rotulo == "Funcional" else "—"
                condicao = (
                    "Não aplicável"
                    if rotulo == "Funcional"
                    else "Não classificada"
                )
                fundo = "#EFF3F6"
                texto_cor = "#53616E"
                borda = "#D7DFE5"

            else:
                nota = int(nota)
                valor = str(nota)
                condicao = nome_condicao(nota)
                fundo, texto_cor, borda = cores.get(
                    nota,
                    ("#EFF3F6", "#53616E", "#D7DFE5")
                )

            st.markdown(
                f"""
                <div style="
                    background:{fundo};
                    color:{texto_cor};
                    border:1px solid {borda};
                    border-radius:14px;
                    padding:16px 18px;
                    min-height:118px;
                ">
                    <div style="
                        font-size:.78rem;
                        font-weight:700;
                        text-transform:uppercase;
                        letter-spacing:.04em;
                        opacity:.78;
                    ">
                        {rotulo}
                    </div>
                    <div style="
                        font-size:1.75rem;
                        font-weight:800;
                        line-height:1;
                        margin:8px 0 5px;
                    ">
                        {valor}
                    </div>
                    <div style="
                        font-size:.92rem;
                        font-weight:700;
                    ">
                        {condicao}
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

def mostrar_preview_inspecao(dados):
    """
    Prévia resumida e organizada do relatório de uma inspeção.

    A prévia da interface não tenta reproduzir todas as páginas do PDF.
    Ela apresenta apenas as informações essenciais para conferência
    antes da geração do documento.
    """

    oae = dados["oae"]
    inspecao = dados["inspecao"]
    classificacao = dados["classificacao_geral"]

    st.markdown("### Prévia técnica")

    # ========================================================
    # IDENTIFICAÇÃO DA CAMPANHA
    # ========================================================

    with st.container(border=True):

        st.markdown(
            f"#### {inspecao.tipo_inspecao} • "
            f"{data_br(inspecao.data_inspecao)}"
        )

        c1, c2 = st.columns(2)

        with c1:
            st.markdown("**OAE**")
            st.write(
                nome_oae_exibicao(oae)
            )

        with c2:
            st.markdown("**Responsável técnico**")
            st.write(
                texto(inspecao.responsavel)
            )

    # ========================================================
    # RESUMO DO CONTEÚDO
    # ========================================================

    st.markdown("#### Resumo do relatório")

    if eh_inspecao_especial(inspecao):
        c1, c2, c3 = st.columns(3)

        with c1:
            st.metric(
                "Anomalias relacionadas",
                len(dados["anomalias"]),
            )

        with c2:
            st.metric(
                "Fotografias",
                len(dados["fotografias"]),
            )

        with c3:
            st.metric(
                "Componentes classificados",
                len(
                    dados[
                        "classificacoes_componentes"
                    ]
                ),
            )

    else:
        c1, c2, c3 = st.columns(3)

        with c1:
            st.metric(
                "Anomalias relacionadas",
                len(dados["anomalias"]),
            )

        with c2:
            st.metric(
                "Fotografias",
                len(dados["fotografias"]),
            )

        with c3:
            classificacao_concluida = (
                dados["classificacao_direta"]
                is not None
            )

            st.metric(
                "Classificação da OAE",
                (
                    "Concluída"
                    if classificacao_concluida
                    else "Pendente"
                ),
            )

    # ========================================================
    # CLASSIFICAÇÃO
    # ========================================================

    st.markdown("#### Classificação da condição")

    mostrar_cards_classificacao_preview(
        classificacao
    )

    # ========================================================
    # ANOMALIAS
    # ========================================================

    if dados["anomalias"]:

        st.markdown("#### Anomalias da campanha")

        st.caption(
            "Resumo das manifestações relacionadas à inspeção. "
            "As localizações completas podem ser consultadas logo abaixo."
        )

        componentes = dados["componentes"]
        tabela = []
        localizacoes = []

        for indice, (
            anomalia,
            observacao
        ) in enumerate(
            dados["anomalias"],
            start=1
        ):

            componente = componentes.get(
                anomalia.componente_id
            )

            referencia = (
                f"AN-{indice:02d}"
            )

            nome_componente = (
                limpar_nome_componente(
                    componente.nome
                    if componente
                    else None
                )
            )

            situacao = (
                observacao.situacao_observada
                if observacao is not None
                else "Identificada nesta inspeção"
            )

            tabela.append(
                {
                    "Ref.": referencia,
                    "Componente": nome_componente,
                    "Anomalia":
                        anomalia.tipo_anomalia,
                    "Situação": situacao,
                }
            )

            localizacoes.append(
                {
                    "ref": referencia,
                    "componente": nome_componente,
                    "anomalia":
                        anomalia.tipo_anomalia,
                    "localizacao":
                        anomalia.localizacao_referencia,
                }
            )

        st.dataframe(
            tabela,
            width="stretch",
            hide_index=True,
            column_config={
                "Ref.": st.column_config.TextColumn(
                    "Ref.",
                    width="small",
                ),
                "Componente":
                    st.column_config.TextColumn(
                        "Componente",
                        width="medium",
                    ),
                "Anomalia":
                    st.column_config.TextColumn(
                        "Anomalia",
                        width="medium",
                    ),
                "Situação":
                    st.column_config.TextColumn(
                        "Situação",
                        width="medium",
                    ),
            },
        )

        with st.expander(
            "📍 Ver localização completa das anomalias",
            expanded=False,
        ):

            for item in localizacoes:

                st.markdown(
                    f"**{item['ref']} • "
                    f"{item['componente']}**"
                )

                st.write(
                    item["anomalia"]
                )

                st.caption(
                    item["localizacao"]
                    or
                    "Localização não informada."
                )

                st.divider()

    else:

        st.info(
            "Nenhuma anomalia relacionada a esta campanha."
        )

    # ========================================================
    # LEVANTAMENTO FOTOGRÁFICO
    # ========================================================

    if dados["fotografias"]:

        st.markdown("#### Levantamento fotográfico")

        st.info(
            f"{len(dados['fotografias'])} fotografia(s) "
            "será(ão) incluída(s) no PDF técnico, organizadas "
            "em pranchas e separadas por tipo de registro."
        )

    else:

        st.warning(
            "Nenhuma fotografia está vinculada a esta campanha."
        )

def mostrar_preview_consolidado(dados):
    st.subheader("Prévia do relatório consolidado")

    c1, c2, c3 = st.columns(3)

    with c1:
        st.metric("Inspeções", len(dados["inspecoes"]))

    with c2:
        st.metric("Componentes", len(dados["componentes"]))

    with c3:
        st.metric(
            "Anomalias ativas",
            sum(1 for item in dados["anomalias"] if item.ativa),
        )

    if dados["campanhas"]:
        tabela = []

        for indice, campanha in enumerate(dados["campanhas"], start=1):
            inspecao = campanha["inspecao"]
            classificacao = campanha["classificacao"]

            tabela.append(
                {
                    "Inspeção": f"{indice:02d}",
                    "Data": data_br(inspecao.data_inspecao),
                    "Tipo": inspecao.tipo_inspecao,
                    "Estrutural": classificacao_com_condicao(
                        classificacao["estrutural"]
                    ),
                    "Funcional": classificacao_com_condicao(
                        classificacao["funcional"]
                    ),
                    "Durabilidade": classificacao_com_condicao(
                        classificacao["durabilidade"]
                    ),
                    "Anomalias": campanha["quantidade_anomalias"],
                    "Fotos": campanha["quantidade_fotos"],
                }
            )

        st.dataframe(tabela, width="stretch", hide_index=True)


# ============================================================
# MÓDULO PRINCIPAL
# ============================================================

def mostrar_modulo_relatorios(oae_ativa, inspecao_ativa=None):
    st.header("📄 Relatórios")

    st.caption(
        "Relatórios técnicos organizados a partir dos dados registrados no Gêmeo Digital."
    )

    st.info(
        "O relatório reproduz informações existentes no banco de dados. "
        "O sistema não substitui a análise, a validação ou a responsabilidade "
        "técnica do profissional."
    )

    if oae_ativa is None:
        st.warning("Selecione uma OAE.")
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
        inspecoes_cronologicas = buscar_inspecoes_oae(oae_ativa.id)

        if len(inspecoes_cronologicas) == 0:
            st.warning("Não existem inspeções cadastradas para esta OAE.")
            return

        # Exibição mais recente primeiro, mas a numeração visual é cronológica.
        inspecoes_exibicao = list(reversed(inspecoes_cronologicas))
        ids = [item.id for item in inspecoes_exibicao]

        mapa = {
            item.id: rotulo_inspecao(
                item,
                inspecoes_cronologicas,
            )
            for item in inspecoes_exibicao
        }

        id_padrao = ids[0]

        if inspecao_ativa is not None and inspecao_ativa.id in ids:
            id_padrao = inspecao_ativa.id

        selecionada_id = st.selectbox(
            "Inspeção",
            options=ids,
            format_func=lambda x: mapa[x],
            index=ids.index(id_padrao),
            key="rel_inspecao_selecionada",
        )

        db = SessionLocal()
        selecionada = (
            db.query(models.Inspecao)
            .filter(models.Inspecao.id == selecionada_id)
            .first()
        )
        db.close()

        if selecionada is None:
            st.error("A inspeção selecionada não foi localizada.")
            return

        dados = montar_relatorio_inspecao(
            oae_ativa,
            selecionada,
        )

        mostrar_preview_inspecao(dados)
        st.divider()

        html = gerar_html_inspecao(dados)
        nome_base = (
            "relatorio_"
            f"{sanitizar_nome_arquivo(oae_ativa.nome)}_"
            f"{sanitizar_nome_arquivo(selecionada.tipo_inspecao)}_"
            f"{selecionada.data_inspecao.strftime('%Y%m%d')}"
        )

        col_html, col_pdf = st.columns(2)

        with col_html:
            st.download_button(
                "⬇️ Baixar relatório HTML",
                data=html.encode("utf-8"),
                file_name=f"{nome_base}.html",
                mime="text/html",
                use_container_width=True,
            )

        with col_pdf:
            if REPORTLAB_DISPONIVEL:
                try:
                    pdf = gerar_pdf_inspecao(dados)
                except Exception as erro:
                    pdf = None
                    st.error(
                        "Não foi possível gerar o PDF técnico. "
                        f"Detalhe: {erro}"
                    )

                if pdf is not None:
                    st.download_button(
                        "⬇️ Baixar relatório técnico em PDF",
                        data=pdf,
                        file_name=f"{nome_base}.pdf",
                        mime="application/pdf",
                        use_container_width=True,
                    )
            else:
                st.warning(
                    "PDF indisponível. Instale a biblioteca ReportLab: pip install reportlab"
                )

    else:
        dados = montar_relatorio_consolidado(oae_ativa)
        mostrar_preview_consolidado(dados)
        st.divider()

        html = gerar_html_consolidado(dados)
        nome_base = (
            "relatorio_consolidado_"
            f"{sanitizar_nome_arquivo(oae_ativa.nome)}"
        )

        col_html, col_pdf = st.columns(2)

        with col_html:
            st.download_button(
                "⬇️ Baixar consolidado HTML",
                data=html.encode("utf-8"),
                file_name=f"{nome_base}.html",
                mime="text/html",
                use_container_width=True,
            )

        with col_pdf:
            if REPORTLAB_DISPONIVEL:
                try:
                    pdf = gerar_pdf_consolidado(dados)
                except Exception as erro:
                    pdf = None
                    st.error(
                        "Não foi possível gerar o PDF consolidado. "
                        f"Detalhe: {erro}"
                    )

                if pdf is not None:
                    st.download_button(
                        "⬇️ Baixar consolidado PDF",
                        data=pdf,
                        file_name=f"{nome_base}.pdf",
                        mime="application/pdf",
                        use_container_width=True,
                    )
            else:
                st.warning(
                    "PDF indisponível. Instale a biblioteca ReportLab: pip install reportlab"
                )