import streamlit as st

from datetime import datetime
from html import escape
from io import BytesIO
from pathlib import Path
import re

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
    )

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
    canvas.drawRightString(largura - 16 * mm, 7.4 * mm, f"Página {doc.page}")

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


def _bloco_foto_pdf(foto, numero, componentes, estilos):
    caminho = caminho_foto_existente(foto)
    componente = componentes.get(getattr(foto, "componente_id", None))

    anomalia = None
    vinculo = buscar_vinculo_foto_anomalia(foto.id)

    if vinculo is not None:
        anomalia_id = getattr(vinculo, "anomalia_permanente_id", None)
        anomalia = buscar_anomalia_por_id(anomalia_id)
    elif getattr(foto, "anomalia_id", None) is not None:
        anomalia = buscar_anomalia_por_id(foto.anomalia_id)

    elementos = [
        Paragraph(f"<b>Foto {numero:02d}</b>", estilos["legenda_bold"]),
        Spacer(1, 1.2 * mm),
    ]

    imagem = _imagem_reportlab(caminho) if caminho is not None else None

    if imagem is not None:
        elementos.append(imagem)
    else:
        quadro = Table(
            [[Paragraph("Imagem não localizada no armazenamento local.", estilos["pequeno"])]],
            colWidths=[78 * mm],
            rowHeights=[36 * mm],
        )
        quadro.setStyle(
            TableStyle(
                [
                    ("BOX", (0, 0), (-1, -1), 0.5, _cor(COR_LINHA)),
                    ("BACKGROUND", (0, 0), (-1, -1), _cor(COR_CINZA)),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ]
            )
        )
        elementos.append(quadro)

    elementos.append(Spacer(1, 1.8 * mm))
    elementos.append(_p(foto.identificacao, estilos["legenda"]));

    referencias = [
        f"Data: {data_br(foto.data_foto)}",
        f"Tipo: {texto(foto.tipo_registro)}",
    ]

    if componente is not None:
        referencias.append(
            f"Componente: {limpar_nome_componente(componente.nome)}"
        )

    if anomalia is not None:
        referencias.append(
            f"Anomalia: {texto(anomalia.tipo_anomalia)}"
        )

    elementos.append(
        Paragraph(
            " | ".join(escape(item) for item in referencias),
            estilos["pequeno"],
        )
    )

    if texto(foto.observacoes, "") != "":
        elementos.append(Spacer(1, 1 * mm))
        elementos.append(_p(foto.observacoes, estilos["pequeno"], ""))

    return elementos


# ============================================================
# PDF - RELATÓRIO DE UMA INSPEÇÃO
# ============================================================

def gerar_pdf_inspecao(dados):
    if not REPORTLAB_DISPONIVEL:
        return None

    buffer = BytesIO()

    documento = SimpleDocTemplate(
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
    historia = []
    oae = dados["oae"]
    inspecao = dados["inspecao"]
    classificacao = dados["classificacao_geral"]
    componentes = dados["componentes"]

    historia.append(Spacer(1, 3 * mm))
    historia.append(Paragraph("RELATÓRIO TÉCNICO DE INSPEÇÃO DE OAE", estilos["titulo"]))
    historia.append(
        Paragraph(
            (
                f"{escape(texto(inspecao.tipo_inspecao))} | "
                f"{escape(data_br(inspecao.data_inspecao))} | "
                f"{escape(nome_oae_exibicao(oae))}"
            ),
            estilos["subtitulo"],
        )
    )
    historia.append(_nota_tecnica_pdf(estilos))
    historia.append(Spacer(1, 4 * mm))

    cards = [
        _card_pdf("Código", texto(oae.codigo), estilos),
        _card_pdf("Anomalias", len(dados["anomalias"]), estilos, destaque=True),
        _card_pdf("Fotos", len(dados["fotografias"]), estilos),
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

    tabela_cards = Table(
        [cards[:3], cards[3:]],
        colWidths=[58.3 * mm, 58.3 * mm, 58.3 * mm],
        hAlign="LEFT",
    )
    tabela_cards.setStyle(
        TableStyle(
            [
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 3),
                ("TOPPADDING", (0, 0), (-1, -1), 2),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
            ]
        )
    )
    historia.append(tabela_cards)
    historia.append(Spacer(1, 5 * mm))

    secao = 1

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
        historia.append(_secao_pdf(secao, titulo_secao, estilos))
        secao += 1
        historia.append(Spacer(1, 2 * mm))

        linhas = [(chave, valor) for chave, valor in campos.items()]
        historia.append(_tabela_chave_valor_pdf(linhas, estilos))
        historia.append(Spacer(1, 4 * mm))

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

    if len(dados["fotografias"]) == 0:
        historia.append(_p("Nenhuma fotografia vinculada à inspeção.", estilos["normal"]))
    else:
        fotos = dados["fotografias"]

        for inicio in range(0, len(fotos), 2):
            celulas = []

            for deslocamento in range(2):
                indice = inicio + deslocamento

                if indice < len(fotos):
                    foto = fotos[indice]
                    bloco = _bloco_foto_pdf(
                        foto,
                        indice + 1,
                        componentes,
                        estilos,
                    )
                    celulas.append(bloco)
                else:
                    celulas.append("")

            tabela_fotos = Table(
                [celulas],
                colWidths=[86.5 * mm, 86.5 * mm],
                hAlign="LEFT",
            )
            tabela_fotos.setStyle(
                TableStyle(
                    [
                        ("BOX", (0, 0), (-1, -1), 0.35, _cor(COR_LINHA)),
                        ("VALIGN", (0, 0), (-1, -1), "TOP"),
                        ("LEFTPADDING", (0, 0), (-1, -1), 4),
                        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                        ("TOPPADDING", (0, 0), (-1, -1), 4),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                    ]
                )
            )
            historia.append(KeepTogether(tabela_fotos))
            historia.append(Spacer(1, 3 * mm))

    # Síntese final sem inventar diagnóstico.
    registro_rotineira = (
        buscar_dados_rotineira(inspecao.id)
        if texto(inspecao.tipo_inspecao, "") == "Rotineira"
        else None
    )

    if registro_rotineira is not None:
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

    def pagina(canvas, doc):
        _cabecalho_rodape_pagina(
            canvas,
            doc,
            nome_oae=oae.nome,
            tipo_relatorio=f"Inspeção {texto(inspecao.tipo_inspecao)}",
        )

    documento.build(
        historia,
        onFirstPage=pagina,
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

    documento = SimpleDocTemplate(
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
    historia = []
    oae = dados["oae"]

    historia.append(Spacer(1, 3 * mm))
    historia.append(Paragraph("RELATÓRIO CONSOLIDADO DA OAE", estilos["titulo"]))
    historia.append(Paragraph(escape(nome_oae_exibicao(oae)), estilos["subtitulo"]))
    historia.append(_nota_tecnica_pdf(estilos))
    historia.append(Spacer(1, 5 * mm))

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

    def pagina(canvas, doc):
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

    buffer.seek(0)
    return buffer.getvalue()


# ============================================================
# PRÉVIAS NO STREAMLIT
# ============================================================

def mostrar_preview_inspecao(dados):
    oae = dados["oae"]
    inspecao = dados["inspecao"]
    classificacao = dados["classificacao_geral"]

    st.subheader("Prévia técnica do relatório")

    c1, c2, c3, c4 = st.columns(4)

    with c1:
        st.metric("Inspeção", inspecao.tipo_inspecao)

    with c2:
        st.metric("Anomalias relacionadas", len(dados["anomalias"]))

    with c3:
        st.metric("Fotografias", len(dados["fotografias"]))

    with c4:
        if eh_inspecao_especial(inspecao):
            st.metric(
                "Componentes classificados",
                len(dados["classificacoes_componentes"]),
            )
        else:
            st.metric(
                "Classificação da OAE",
                "Concluída" if dados["classificacao_direta"] is not None else "Pendente",
            )

    st.write(f"**OAE:** {nome_oae_exibicao(oae)}")
    st.write(f"**Data:** {data_br(inspecao.data_inspecao)}")
    st.write(f"**Responsável:** {texto(inspecao.responsavel)}")

    st.markdown("#### Classificação da condição")
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            "Estrutural",
            classificacao_com_condicao(classificacao["estrutural"]),
        )

    with col2:
        st.metric(
            "Funcional",
            classificacao_com_condicao(classificacao["funcional"]),
        )

    with col3:
        st.metric(
            "Durabilidade",
            classificacao_com_condicao(classificacao["durabilidade"]),
        )

    if dados["anomalias"]:
        st.markdown("#### Anomalias da campanha")
        componentes = dados["componentes"]
        tabela = []

        for indice, (anomalia, observacao) in enumerate(dados["anomalias"], start=1):
            componente = componentes.get(anomalia.componente_id)
            tabela.append(
                {
                    "Ref.": f"AN-{indice:02d}",
                    "Componente": limpar_nome_componente(
                        componente.nome if componente else None
                    ),
                    "Anomalia": anomalia.tipo_anomalia,
                    "Localização": anomalia.localizacao_referencia,
                    "Situação": (
                        observacao.situacao_observada
                        if observacao is not None
                        else "Identificada nesta inspeção"
                    ),
                }
            )

        st.dataframe(tabela, width="stretch", hide_index=True)

    if dados["fotografias"]:
        st.markdown("#### Levantamento fotográfico")
        st.caption(
            "O PDF técnico incluirá as imagens disponíveis no armazenamento local, "
            "organizadas em pranchas com duas fotografias por linha."
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
