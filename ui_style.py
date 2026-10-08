from __future__ import annotations
import base64
import textwrap
from html import escape
from pathlib import Path
import streamlit as st
def _svg_icon(kind: str, size: int = 22, color: str = "currentColor") -> str:
    paths = {
        "bridge": '<path d="M3 18h18M5 18V9m14 9V9M5 10c2.2-3.6 4.5-5.4 7-5.4S16.8 6.4 19 10M7 10h10M8 10v8m4-8v8m4-8v8"/>',
        "clipboard": '<path d="M9 5h6m-7 2H6a2 2 0 0 0-2 2v10a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V9a2 2 0 0 0-2-2h-2M9 3h6v4H9zM8 12h8M8 16h5"/>',
        "alert": '<path d="M12 3 2.8 20h18.4L12 3Z"/><path d="M12 9v5m0 3h.01"/>',
        "camera": '<path d="M4 8h4l1.5-2h5L16 8h4v11H4z"/><circle cx="12" cy="13.5" r="3.2"/>',
        "structure": '<path d="M4 20h16M6 20V8h12v12M4 8h16M9 8V4h6v4M9 12h6m-6 4h6"/>',
    }
    path = paths.get(kind, paths["bridge"])
    return (
        f'<svg viewBox="0 0 24 24" width="{size}" height="{size}" '
        f'fill="none" stroke="{color}" stroke-width="1.8" '
        f'stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">'
        f'{path}</svg>'
    )
def _imagem_css(image) -> str:
    if image:
        path = Path(str(image))
        if path.exists() and path.is_file():
            mime = "image/jpeg"
            if path.suffix.lower() == ".png":
                mime = "image/png"
            elif path.suffix.lower() == ".webp":
                mime = "image/webp"
            encoded = base64.b64encode(path.read_bytes()).decode("ascii")
            return f"url('data:{mime};base64,{encoded}')"
    return "linear-gradient(135deg, #082F49 0%, #0B3C5D 55%, #135C82 100%)"
def aplicar_estilo_global():
    st.markdown(
        """
        <style>
        :root {
            --gd-primary: #0B3C5D;
            --gd-primary2: #135C82;
            --gd-accent: #FF6B35;
            --gd-accent2: #F2994A;
            --gd-bg: #F5F7FA;
            --gd-card: #FFFFFF;
            --gd-text: #17202A;
            --gd-muted: #64717D;
            --gd-border: #DCE3E9;
        }
        html, body, [class*="css"] {
            font-family: "Inter", "Segoe UI", Arial, sans-serif;
        }
        [data-testid="stAppViewContainer"] {
            background:
                radial-gradient(circle at 88% 0%, rgba(19,92,130,.07), transparent 28rem),
                var(--gd-bg);
        }
        [data-testid="stMainBlockContainer"] {
            max-width: 1540px;
            padding-top: 3.25rem;
            padding-bottom: 3rem;
        }
        /* SIDEBAR */
        [data-testid="stSidebar"] {
            background: linear-gradient(180deg, #082F49 0%, #0B3C5D 58%, #07283D 100%);
            border-right: 1px solid rgba(255,255,255,.08);
        }
        /* Evita aplicar texto branco a TODOS os elementos da sidebar,
           pois isso deixava o valor do selectbox branco sobre fundo branco. */
        [data-testid="stSidebar"] h1,
        [data-testid="stSidebar"] h2,
        [data-testid="stSidebar"] h3,
        [data-testid="stSidebar"] label,
        [data-testid="stSidebar"] p,
        [data-testid="stSidebar"] [data-testid="stMarkdownContainer"],
        [data-testid="stSidebar"] [data-testid="stRadio"] {
            color: #F7FAFC;
        }
        [data-testid="stSidebar"] hr {
            border-color: rgba(255,255,255,.14);
        }
        [data-testid="stSidebar"] small,
        [data-testid="stSidebar"] [data-testid="stCaptionContainer"] {
            color: rgba(255,255,255,.67) !important;
        }
        [data-testid="stSidebar"] [data-baseweb="select"] > div {
            background: #FFFFFF !important;
            border-color: rgba(255,255,255,.28) !important;
        }
        /* O seletor da OAE usa fundo branco; o texto precisa ficar escuro. */
        [data-testid="stSidebar"] [data-baseweb="select"] span,
        [data-testid="stSidebar"] [data-baseweb="select"] input,
        [data-testid="stSidebar"] [data-baseweb="select"] svg {
            color: #17324A !important;
            fill: #17324A !important;
        }
        [data-testid="stSidebar"] [data-baseweb="select"] input::placeholder {
            color: #6F7D89 !important;
            opacity: 1 !important;
        }
        /* Força a cor do valor selecionado no selectbox da sidebar.
           Algumas versões do Streamlit/BaseWeb renderizam o texto
           em DIV/P em vez de SPAN. */
        [data-testid="stSidebar"] [data-baseweb="select"],
        [data-testid="stSidebar"] [data-baseweb="select"] *,
        [data-testid="stSidebar"] [data-baseweb="select"] div,
        [data-testid="stSidebar"] [data-baseweb="select"] p {
            color: #17324A !important;
            -webkit-text-fill-color: #17324A !important;
            opacity: 1 !important;
        }
        [data-testid="stSidebar"] [data-baseweb="select"] svg {
            stroke: #17324A !important;
            fill: #17324A !important;
        }
        [data-testid="stSidebar"] div[role="radiogroup"] label {
            padding: .42rem .58rem;
            border-radius: 9px;
            margin: .05rem 0;
            transition: background .15s ease, transform .15s ease;
        }
        [data-testid="stSidebar"] div[role="radiogroup"] label:hover {
            background: rgba(255,255,255,.08);
        }
        [data-testid="stSidebar"] div[role="radiogroup"] label:has(input:checked) {
            background: linear-gradient(90deg, #FF6B35, #F2994A);
            box-shadow: 0 6px 17px rgba(0,0,0,.17);
        }
        /* Títulos das páginas internas */
        h1, h2, h3 {
            letter-spacing: -.025em;
        }
        .gd-page-brand {
            display: flex;
            align-items: center;
            gap: 10px;
            color: #0B3C5D;
            margin: .15rem 0 1rem 0;
        }
        .gd-page-brand-icon {
            width: 34px;
            height: 34px;
            border-radius: 9px;
            display: grid;
            place-items: center;
            color: white;
            background: linear-gradient(135deg, #0B3C5D, #135C82);
        }
        .gd-page-brand-title {
            font-size: .92rem;
            font-weight: 750;
        }
        .gd-page-brand-sub {
            color: #77838E;
            font-size: .74rem;
        }
        /* Cards */
        .gd-section-title {
            color: #0B3C5D;
            font-size: 1.42rem;
            font-weight: 780;
            letter-spacing: -.025em;
            margin: 1.3rem 0 .18rem;
        }
        .gd-section-subtitle {
            color: #6A7681;
            font-size: .90rem;
            margin-bottom: .85rem;
        }
        .gd-metric-grid {
            display: grid;
            grid-template-columns: repeat(4, minmax(0, 1fr));
            gap: 14px;
            margin: .8rem 0 1.25rem 0;
        }
        .gd-metric-card {
            min-height: 112px;
            background: rgba(255,255,255,.97);
            border: 1px solid #DCE3E9;
            border-radius: 14px;
            padding: 16px 17px;
            box-shadow: 0 7px 22px rgba(11,60,93,.055);
            position: relative;
            overflow: hidden;
        }
        .gd-metric-card:before {
            content: "";
            position: absolute;
            inset: 0 auto 0 0;
            width: 4px;
            background: #FF6B35;
        }
        .gd-metric-head {
            display: flex;
            align-items: center;
            gap: 9px;
            color: #66727D;
            font-size: .84rem;
            font-weight: 680;
        }
        .gd-metric-icon {
            width: 34px;
            height: 34px;
            display: grid;
            place-items: center;
            border-radius: 9px;
            background: #EDF4F8;
            color: #0B3C5D;
        }
        .gd-metric-value {
            color: #17202A;
            font-size: 1.95rem;
            font-weight: 800;
            line-height: 1;
            letter-spacing: -.04em;
            margin-top: 10px;
        }
        .gd-oae-card {
            background: white;
            border: 1px solid #DCE3E9;
            border-radius: 14px;
            padding: 18px 20px;
            box-shadow: 0 7px 22px rgba(11,60,93,.045);
        }
        .gd-oae-title {
            display: flex;
            align-items: center;
            gap: 9px;
            color: #0B3C5D;
            font-size: 1.12rem;
            font-weight: 780;
            margin-bottom: 15px;
        }
        .gd-oae-data-grid {
            display: grid;
            grid-template-columns: repeat(4, minmax(0, 1fr));
            gap: 18px;
        }
        .gd-data-label {
            color: #74808B;
            font-size: .74rem;
            font-weight: 720;
            text-transform: uppercase;
            letter-spacing: .055em;
            margin-bottom: 4px;
        }
        .gd-data-value {
            color: #1B2630;
            font-size: .94rem;
            font-weight: 620;
        }
        .gd-class-grid {
            display: grid;
            grid-template-columns: repeat(3, minmax(0, 1fr));
            gap: 12px;
            margin: .8rem 0 1rem;
        }
        .gd-class-card {
            border-radius: 13px;
            padding: 15px 16px;
            border: 1px solid rgba(0,0,0,.08);
        }
        .gd-class-label {
            font-size: .76rem;
            font-weight: 740;
            text-transform: uppercase;
            letter-spacing: .04em;
            opacity: .77;
        }
        .gd-class-value {
            font-size: 1.55rem;
            font-weight: 820;
            line-height: 1;
            margin: 7px 0 4px;
        }
        .gd-class-name {
            font-size: .87rem;
            font-weight: 670;
        }
        .gd-progress-wrap {
            background: #FFFFFF;
            border: 1px solid #DCE3E9;
            border-radius: 14px;
            padding: 15px 18px;
            box-shadow: 0 7px 22px rgba(11,60,93,.045);
        }
        .gd-progress-track {
            height: 9px;
            border-radius: 99px;
            overflow: hidden;
            background: #E8EDF2;
            margin-top: 11px;
        }
        .gd-progress-bar {
            height: 100%;
            border-radius: 99px;
            background: linear-gradient(90deg, #135C82, #FF6B35);
        }
        .gd-progress-meta {
            display: flex;
            justify-content: space-between;
            color: #6B7782;
            font-size: .81rem;
            margin-top: 7px;
        }
        [data-testid="stVerticalBlockBorderWrapper"] {
            border-radius: 13px;
            border-color: #DCE3E9;
        }
        [data-testid="stAlert"] {
            border-radius: 11px;
        }
        .stButton > button,
        .stDownloadButton > button,
        [data-testid="stFormSubmitButton"] > button {
            border-radius: 9px;
            font-weight: 700;
        }
        @media (max-width: 1000px) {
            .gd-metric-grid,
            .gd-oae-data-grid {
                grid-template-columns: repeat(2, minmax(0, 1fr));
            }
            .gd-class-grid {
                grid-template-columns: 1fr;
            }
        }
        @media (max-width: 620px) {
            .gd-metric-grid,
            .gd-oae-data-grid {
                grid-template-columns: 1fr;
            }
        }
        /* Seletor da OAE na sidebar */
        [data-testid="stSidebar"] [data-baseweb="select"] > div {
            background: rgba(255,255,255,.10) !important;
            border: 1px solid rgba(255,255,255,.24) !important;
            box-shadow: none !important;
        }
        [data-testid="stSidebar"] [data-baseweb="select"],
        [data-testid="stSidebar"] [data-baseweb="select"] *,
        [data-testid="stSidebar"] [data-baseweb="select"] div,
        [data-testid="stSidebar"] [data-baseweb="select"] span,
        [data-testid="stSidebar"] [data-baseweb="select"] p,
        [data-testid="stSidebar"] [data-baseweb="select"] input {
            color: #FFFFFF !important;
            -webkit-text-fill-color: #FFFFFF !important;
            opacity: 1 !important;
        }
        [data-testid="stSidebar"] [data-baseweb="select"] svg {
            stroke: #FFFFFF !important;
            fill: #FFFFFF !important;
            color: #FFFFFF !important;
        }
        [data-testid="stSidebar"] [data-baseweb="select"]:focus-within > div {
            border-color: #FF6B35 !important;
            box-shadow: 0 0 0 1px #FF6B35 !important;
        }
        /* Selectbox da OAE: fundo branco + texto escuro */
        [data-testid="stSidebar"] div[data-baseweb="select"] > div {
            background: #FFFFFF !important;
            border: 1px solid #D6DEE5 !important;
        }
        [data-testid="stSidebar"] div[data-baseweb="select"] > div *,
        [data-testid="stSidebar"] div[data-baseweb="select"] span,
        [data-testid="stSidebar"] div[data-baseweb="select"] input {
            color: #17324A !important;
            -webkit-text-fill-color: #17324A !important;
            opacity: 1 !important;
        }
        [data-testid="stSidebar"] div[data-baseweb="select"] svg {
            color: #17324A !important;
            fill: #17324A !important;
            stroke: #17324A !important;
        }
        /* =====================================================
           FORMULÁRIOS E CAMPOS — MAIOR CONTRASTE VISUAL
           Aplicado somente à área principal, não à sidebar.
           ===================================================== */
        /* Formulários com superfície branca e separação do fundo */
        [data-testid="stMain"] [data-testid="stForm"],
        [data-testid="stMainBlockContainer"] [data-testid="stForm"] {
            background: #FFFFFF !important;
            border: 1px solid #D2DCE5 !important;
            border-radius: 16px !important;
            padding: 1rem 1.15rem 1.15rem 1.15rem !important;
            box-shadow: 0 7px 22px rgba(11, 60, 93, 0.045) !important;
        }
        /* Labels mais legíveis */
        [data-testid="stMain"] label,
        [data-testid="stMainBlockContainer"] label {
            color: #22384A !important;
            font-weight: 600 !important;
        }
        /* Text input e number input */
        [data-testid="stMain"] div[data-baseweb="input"] > div,
        [data-testid="stMainBlockContainer"] div[data-baseweb="input"] > div {
            background: #FFFFFF !important;
            border: 1.5px solid #C7D2DC !important;
            border-radius: 10px !important;
            box-shadow: 0 1px 2px rgba(11, 60, 93, 0.03) !important;
        }
        /* Selectbox da área principal */
        [data-testid="stMain"] div[data-baseweb="select"] > div,
        [data-testid="stMainBlockContainer"] div[data-baseweb="select"] > div {
            background: #FFFFFF !important;
            border: 1.5px solid #C7D2DC !important;
            border-radius: 10px !important;
            box-shadow: 0 1px 2px rgba(11, 60, 93, 0.03) !important;
        }
        /* Textarea */
        [data-testid="stMain"] div[data-baseweb="textarea"] > div,
        [data-testid="stMainBlockContainer"] div[data-baseweb="textarea"] > div {
            background: #FFFFFF !important;
            border: 1.5px solid #C7D2DC !important;
            border-radius: 10px !important;
            box-shadow: 0 1px 2px rgba(11, 60, 93, 0.03) !important;
        }
        /* Texto digitado nos campos */
        [data-testid="stMain"] div[data-baseweb="input"] input,
        [data-testid="stMainBlockContainer"] div[data-baseweb="input"] input,
        [data-testid="stMain"] div[data-baseweb="textarea"] textarea,
        [data-testid="stMainBlockContainer"] div[data-baseweb="textarea"] textarea,
        [data-testid="stMain"] div[data-baseweb="select"] span,
        [data-testid="stMainBlockContainer"] div[data-baseweb="select"] span {
            color: #17324A !important;
            -webkit-text-fill-color: #17324A !important;
        }
        /* Placeholder */
        [data-testid="stMain"] input::placeholder,
        [data-testid="stMainBlockContainer"] input::placeholder,
        [data-testid="stMain"] textarea::placeholder,
        [data-testid="stMainBlockContainer"] textarea::placeholder {
            color: #8794A0 !important;
            opacity: 1 !important;
        }
        /* Foco — destaque laranja discreto */
        [data-testid="stMain"] div[data-baseweb="input"] > div:focus-within,
        [data-testid="stMainBlockContainer"] div[data-baseweb="input"] > div:focus-within,
        [data-testid="stMain"] div[data-baseweb="select"] > div:focus-within,
        [data-testid="stMainBlockContainer"] div[data-baseweb="select"] > div:focus-within,
        [data-testid="stMain"] div[data-baseweb="textarea"] > div:focus-within,
        [data-testid="stMainBlockContainer"] div[data-baseweb="textarea"] > div:focus-within {
            border-color: #FF6B35 !important;
            box-shadow: 0 0 0 2px rgba(255, 107, 53, 0.14) !important;
        }
        /* Uploader com área branca e borda pontilhada */
        [data-testid="stMain"] [data-testid="stFileUploader"] section,
        [data-testid="stMainBlockContainer"] [data-testid="stFileUploader"] section {
            background: #FFFFFF !important;
            border: 1.5px dashed #BFCBD6 !important;
            border-radius: 12px !important;
        }
        /* Fundo de widgets numéricos e controles auxiliares */
        [data-testid="stMain"] [data-testid="stNumberInput"] button,
        [data-testid="stMainBlockContainer"] [data-testid="stNumberInput"] button {
            background: #F7F9FB !important;
            border-color: #C7D2DC !important;
            color: #17324A !important;
        }
        /* Botões dos formulários */
        [data-testid="stMain"] [data-testid="stFormSubmitButton"] > button,
        [data-testid="stMainBlockContainer"] [data-testid="stFormSubmitButton"] > button {
            background: #FFFFFF !important;
            color: #17324A !important;
            border: 1.5px solid #BCC9D4 !important;
            border-radius: 10px !important;
            font-weight: 700 !important;
            transition: all .15s ease !important;
        }
        [data-testid="stMain"] [data-testid="stFormSubmitButton"] > button:hover,
        [data-testid="stMainBlockContainer"] [data-testid="stFormSubmitButton"] > button:hover {
            color: #FF6B35 !important;
            border-color: #FF6B35 !important;
            background: #FFF8F5 !important;
        }
        /* Radio buttons: melhora contraste sem alterar cor semântica */
        [data-testid="stMain"] [data-testid="stRadio"] label,
        [data-testid="stMainBlockContainer"] [data-testid="stRadio"] label {
            color: #263B4B !important;
            font-weight: 500 !important;
        }
        /* =====================================================
           INSPEÇÕES — CONTRASTE REFORÇADO PARA TODOS OS CAMPOS
           ===================================================== */
        /* Campo de data */
        [data-testid="stMain"] [data-testid="stDateInput"] div[data-baseweb="input"] > div,
        [data-testid="stMainBlockContainer"] [data-testid="stDateInput"] div[data-baseweb="input"] > div {
            background: #FFFFFF !important;
            border: 1.5px solid #BFCBD6 !important;
            border-radius: 10px !important;
        }
        [data-testid="stMain"] [data-testid="stDateInput"] input,
        [data-testid="stMainBlockContainer"] [data-testid="stDateInput"] input {
            background: #FFFFFF !important;
            color: #17324A !important;
            -webkit-text-fill-color: #17324A !important;
        }
        /* Inputs de texto — força fundo branco inclusive quando
           o módulo usa wrappers diferentes do BaseWeb */
        [data-testid="stMain"] [data-testid="stTextInput"] input,
        [data-testid="stMainBlockContainer"] [data-testid="stTextInput"] input {
            background: #FFFFFF !important;
            color: #17324A !important;
            -webkit-text-fill-color: #17324A !important;
            border-radius: 9px !important;
        }
        /* Textarea */
        [data-testid="stMain"] [data-testid="stTextArea"] textarea,
        [data-testid="stMainBlockContainer"] [data-testid="stTextArea"] textarea {
            background: #FFFFFF !important;
            color: #17324A !important;
            -webkit-text-fill-color: #17324A !important;
            border-radius: 9px !important;
        }
        /* Selectbox — reforço na área principal */
        [data-testid="stMain"] [data-testid="stSelectbox"] div[data-baseweb="select"] > div,
        [data-testid="stMainBlockContainer"] [data-testid="stSelectbox"] div[data-baseweb="select"] > div {
            background: #FFFFFF !important;
            border: 1.5px solid #BFCBD6 !important;
            border-radius: 10px !important;
        }
        [data-testid="stMain"] [data-testid="stSelectbox"] div[data-baseweb="select"] *,
        [data-testid="stMainBlockContainer"] [data-testid="stSelectbox"] div[data-baseweb="select"] * {
            color: #17324A !important;
            -webkit-text-fill-color: #17324A !important;
        }
        /* Number input */
        [data-testid="stMain"] [data-testid="stNumberInput"] input,
        [data-testid="stMainBlockContainer"] [data-testid="stNumberInput"] input {
            background: #FFFFFF !important;
            color: #17324A !important;
            -webkit-text-fill-color: #17324A !important;
        }
        /* File uploader */
        [data-testid="stMain"] [data-testid="stFileUploader"] section,
        [data-testid="stMainBlockContainer"] [data-testid="stFileUploader"] section {
            background: #FFFFFF !important;
            border-color: #BFCBD6 !important;
        }
        /* Foco visual mais evidente */
        [data-testid="stMain"] [data-testid="stTextInput"]:focus-within,
        [data-testid="stMain"] [data-testid="stTextArea"]:focus-within,
        [data-testid="stMain"] [data-testid="stDateInput"]:focus-within,
        [data-testid="stMain"] [data-testid="stSelectbox"]:focus-within,
        [data-testid="stMain"] [data-testid="stNumberInput"]:focus-within {
            outline: none !important;
        }
        [data-testid="stMain"] [data-testid="stTextInput"] div[data-baseweb="input"] > div:focus-within,
        [data-testid="stMain"] [data-testid="stDateInput"] div[data-baseweb="input"] > div:focus-within,
        [data-testid="stMain"] [data-testid="stSelectbox"] div[data-baseweb="select"] > div:focus-within,
        [data-testid="stMain"] [data-testid="stNumberInput"] div[data-baseweb="input"] > div:focus-within {
            border-color: #FF6B35 !important;
            box-shadow: 0 0 0 2px rgba(255,107,53,.14) !important;
        }
        /* =====================================================
           ANOMALIAS / SELECTBOXES — CONTRASTE REFORÇADO
           ===================================================== */
        /* Alguns módulos renderizam o selectbox com estrutura
           interna diferente. Estas regras atingem diretamente
           o controle visível e o combobox. */
        [data-testid="stMain"] [data-testid="stSelectbox"] div[role="combobox"],
        [data-testid="stMainBlockContainer"] [data-testid="stSelectbox"] div[role="combobox"],
        [data-testid="stMain"] [data-baseweb="select"] div[role="combobox"],
        [data-testid="stMainBlockContainer"] [data-baseweb="select"] div[role="combobox"] {
            background: #FFFFFF !important;
            color: #17324A !important;
            -webkit-text-fill-color: #17324A !important;
            border-radius: 10px !important;
        }
        /* Wrapper do select */
        [data-testid="stMain"] [data-baseweb="select"] > div,
        [data-testid="stMainBlockContainer"] [data-baseweb="select"] > div {
            background: #FFFFFF !important;
            border: 1.5px solid #BFCBD6 !important;
            border-radius: 10px !important;
            box-shadow: 0 1px 2px rgba(11,60,93,.04) !important;
        }
        /* Texto e seta do select */
        [data-testid="stMain"] [data-baseweb="select"] > div *,
        [data-testid="stMainBlockContainer"] [data-baseweb="select"] > div * {
            color: #17324A !important;
            -webkit-text-fill-color: #17324A !important;
        }
        [data-testid="stMain"] [data-baseweb="select"] svg,
        [data-testid="stMainBlockContainer"] [data-baseweb="select"] svg {
            color: #17324A !important;
            fill: #17324A !important;
            stroke: #17324A !important;
        }
        /* Foco do select */
        [data-testid="stMain"] [data-baseweb="select"]:focus-within > div,
        [data-testid="stMainBlockContainer"] [data-baseweb="select"]:focus-within > div {
            border-color: #FF6B35 !important;
            box-shadow: 0 0 0 2px rgba(255,107,53,.14) !important;
        }
        /* Mantém os campos numéricos claramente separados do fundo */
        [data-testid="stMain"] [data-testid="stNumberInput"] div[data-baseweb="input"] > div,
        [data-testid="stMainBlockContainer"] [data-testid="stNumberInput"] div[data-baseweb="input"] > div {
            background: #FFFFFF !important;
            border: 1.5px solid #BFCBD6 !important;
            border-radius: 10px !important;
        }
        /* Áreas de texto longas */
        [data-testid="stMain"] [data-testid="stTextArea"] div[data-baseweb="textarea"] > div,
        [data-testid="stMainBlockContainer"] [data-testid="stTextArea"] div[data-baseweb="textarea"] > div {
            background: #FFFFFF !important;
            border: 1.5px solid #BFCBD6 !important;
            border-radius: 10px !important;
        }
</style>
        """,
        unsafe_allow_html=True,
    )
def renderizar_marca_sidebar():
    st.markdown(
        f"""
        <div style="display:flex;align-items:center;gap:11px;margin:.15rem 0 .35rem">
            <div style="
                width:42px;height:42px;border-radius:11px;
                display:grid;place-items:center;
                background:linear-gradient(135deg,#FF6B35,#F2994A);
                box-shadow:0 6px 18px rgba(0,0,0,.18);
            ">
                {_svg_icon("bridge", 25, "#FFFFFF")}
            </div>
            <div>
                <div style="font-size:1.14rem;font-weight:820;color:#fff;line-height:1.05">
                    Ferramenta Web para Inspeções de Pontes
                </div>
                <div style="font-size:.72rem;color:rgba(255,255,255,.62);margin-top:4px">
                    Inspeção e gestão de OAEs
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
def renderizar_marca_pagina():
    st.markdown(
        f"""
        <div class="gd-page-brand">
            <div class="gd-page-brand-icon">{_svg_icon("bridge", 20, "#FFFFFF")}</div>
            <div>
                <div class="gd-page-brand-title">Ferramenta Web para Inspeções de Pontes</div>
                <div class="gd-page-brand-sub">Sistema de apoio à inspeção e acompanhamento de OAEs</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
def renderizar_hero(*, oae=None, image=None):
    bg = _imagem_css(image)
    nome = getattr(oae, "nome", None) if oae is not None else None
    codigo = getattr(oae, "codigo", None) if oae is not None else None
    rodovia = getattr(oae, "rodovia", None) if oae is not None else None
    municipio = getattr(oae, "municipio", None) if oae is not None else None
    uf = getattr(oae, "uf", None) if oae is not None else None
    local = " / ".join(str(v) for v in [municipio, uf] if v)
    meta = " • ".join(str(v) for v in [codigo, rodovia, local] if v)
    contexto = ""
    if nome:
        contexto = (
            '<div class="gd-hero-context">'
            '<span class="gd-dot"></span>'
            f'<strong>{escape(str(nome))}</strong>'
            + (f'<span class="gd-hero-meta">{escape(meta)}</span>' if meta else '')
            + '</div>'
        )
    st.markdown(
        textwrap.dedent(
            f"""
            <style>
        .gd-hero {{
            position: relative;
            min-height: 250px;
            overflow: hidden;
            border-radius: 18px;
            background-image:
                linear-gradient(90deg, rgba(4,31,48,.94) 0%, rgba(11,60,93,.82) 48%, rgba(11,60,93,.28) 100%),
                {bg};
            background-size: cover;
            background-position: center;
            box-shadow: 0 14px 34px rgba(11,60,93,.17);
            margin: .1rem 0 1.35rem;
        }}
        .gd-hero-inner {{
            min-height: 250px;
            box-sizing: border-box;
            padding: 31px 36px;
            display: flex;
            flex-direction: column;
            justify-content: flex-end;
            color: #fff;
        }}
        .gd-hero-kicker {{
            display:flex;
            align-items:center;
            gap:8px;
            color:#FFD3C2;
            font-size:.75rem;
            font-weight:800;
            letter-spacing:.09em;
            text-transform:uppercase;
            margin-bottom:8px;
        }}
        .gd-hero-title {{
            font-size: clamp(2rem, 4vw, 3.05rem);
            line-height: 1.02;
            letter-spacing: -.045em;
            font-weight: 830;
            max-width: 920px;
        }}
        .gd-hero-sub {{
            color: rgba(255,255,255,.79);
            font-size: .98rem;
            max-width: 760px;
            margin-top: 9px;
        }}
        .gd-hero-context {{
            display:flex;
            flex-wrap:wrap;
            align-items:center;
            gap:8px;
            width:fit-content;
            margin-top:18px;
            padding:8px 11px;
            border-radius:10px;
            border:1px solid rgba(255,255,255,.17);
            background:rgba(3,25,39,.50);
        }}
        .gd-dot {{
            width:8px;height:8px;border-radius:99px;
            background:#FF6B35;
            box-shadow:0 0 0 4px rgba(255,107,53,.20);
        }}
        .gd-hero-meta {{
            color:rgba(255,255,255,.67);
            font-size:.84rem;
        }}
        </style>
        <div class="gd-hero">
            <div class="gd-hero-inner">
                <div class="gd-hero-kicker">
                    {_svg_icon("structure", 16, "#FFB18F")}
                    Engenharia • Inspeção • Integridade estrutural
                </div>
                <div class="gd-hero-title">Ferramenta Web para Inspeções de Pontes</div>
                <div class="gd-hero-sub">
                    Sistema de apoio à inspeção, diagnóstico e acompanhamento temporal de Obras de Arte Especiais.
                </div>
                {contexto}
            </div>
        </div>
            """
        ).strip(),
        unsafe_allow_html=True,
    )
def renderizar_metricas(totais):
    itens = [
        ("bridge", "OAEs cadastradas", totais.get("oaes", 0)),
        ("clipboard", "Inspeções", totais.get("inspecoes", 0)),
        ("alert", "Anomalias acompanhadas", totais.get("anomalias", 0)),
        ("camera", "Fotografias", totais.get("fotografias", 0)),
    ]
    html = []
    for icone, rotulo, valor in itens:
        html.append(
            textwrap.dedent(
                f"""
                <div class="gd-metric-card">
                    <div class="gd-metric-head">
                        <div class="gd-metric-icon">{_svg_icon(icone, 19)}</div>
                        <span>{escape(str(rotulo))}</span>
                    </div>
                    <div class="gd-metric-value">{escape(str(valor))}</div>
                </div>
                """
            ).strip()
        )
    st.markdown(
        '<div class="gd-metric-grid">' + "".join(html) + '</div>',
        unsafe_allow_html=True,
    )
def renderizar_resumo_oae(oae):
    local = " - ".join(
        str(v)
        for v in [getattr(oae, "municipio", None), getattr(oae, "uf", None)]
        if v
    )
    dados = [
        ("Código", getattr(oae, "codigo", None) or "Não informado"),
        ("Localização", local or "Não informada"),
        ("Rodovia", getattr(oae, "rodovia", None) or "Não informada"),
        ("Tipo estrutural", getattr(oae, "tipo_estrutura", None) or "Não informado"),
    ]
    corpo = "".join(
        f'<div><div class="gd-data-label">{escape(rotulo)}</div>'
        f'<div class="gd-data-value">{escape(str(valor))}</div></div>'
        for rotulo, valor in dados
    )
    bloco_oae = textwrap.dedent(
        f"""
        <div class="gd-oae-card">
            <div class="gd-oae-title">
                {_svg_icon("bridge", 20, "#0B3C5D")}
                <span>{escape(str(getattr(oae, "nome", "OAE")))}</span>
            </div>
            <div class="gd-oae-data-grid">{corpo}</div>
        </div>
        """
    ).strip()
    st.markdown(
        bloco_oae,
        unsafe_allow_html=True,
    )
def _cor_nota(nota):
    mapa = {
        5: ("#E7F6EC", "#17643A", "#A9D6B8"),
        4: ("#EEF7E4", "#4E6F22", "#CFE2A7"),
        3: ("#FFF6D8", "#765600", "#E8D37E"),
        2: ("#FFF0DD", "#8C5000", "#EDC38B"),
        1: ("#FCE5E2", "#9C332B", "#E5ADA7"),
        0: ("#F4D6D8", "#841D24", "#D99BA0"),
    }
    return mapa.get(nota, ("#EFF3F6", "#53616E", "#D7DFE5"))
def renderizar_classificacao(notas, nota_texto_fn):
    if notas is None:
        st.info("Esta inspeção ainda não possui classificação registrada.")
        return
    html = []
    for rotulo, chave in [
        ("Estrutural", "estrutural"),
        ("Funcional", "funcional"),
        ("Durabilidade", "durabilidade"),
    ]:
        nota = notas.get(chave)
        if nota is None:
            valor = "NA" if chave == "funcional" else "—"
            nome = "Não aplicável" if chave == "funcional" else "Não classificada"
            bg, fg, borda = _cor_nota(None)
        else:
            nota = int(nota)
            valor = str(nota)
            nome = nota_texto_fn(nota)
            bg, fg, borda = _cor_nota(nota)
        html.append(
            textwrap.dedent(
                f"""
                <div class="gd-class-card" style="background:{bg};color:{fg};border-color:{borda}">
                    <div class="gd-class-label">{rotulo}</div>
                    <div class="gd-class-value">{escape(valor)}</div>
                    <div class="gd-class-name">{escape(str(nome))}</div>
                </div>
                """
            ).strip()
        )
    st.markdown(
        '<div class="gd-class-grid">' + "".join(html) + '</div>',
        unsafe_allow_html=True,
    )
def renderizar_andamento(total, classificados):
    total = max(int(total or 0), 0)
    classificados = max(int(classificados or 0), 0)
    if total:
        classificados = min(classificados, total)
        percentual = classificados / total * 100
    else:
        percentual = 0.0
    pendentes = max(total - classificados, 0)
    st.markdown(
        f"""
        <div class="gd-progress-wrap">
            <div style="display:flex;align-items:center;justify-content:space-between;gap:12px">
                <div>
                    <div style="font-weight:780;color:#0B3C5D">Andamento da classificação</div>
                    <div style="color:#697681;font-size:.84rem;margin-top:2px">
                        {classificados} de {total} componentes classificados
                    </div>
                </div>
                <div style="font-size:1.32rem;font-weight:820;color:#17202A">{percentual:.0f}%</div>
            </div>
            <div class="gd-progress-track">
                <div class="gd-progress-bar" style="width:{percentual:.1f}%"></div>
            </div>
            <div class="gd-progress-meta">
                <span>{classificados} classificados</span>
                <span>{pendentes} pendentes</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
