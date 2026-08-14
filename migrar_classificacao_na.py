import sqlite3
import re
from pathlib import Path


# ============================================================
# CONFIGURAÇÃO
# ============================================================

CAMINHO_BANCO = Path("gemeo_digital.db")

TABELA = "classificacoes"
TABELA_TEMPORARIA = "classificacoes_nova"


# ============================================================
# VERIFICAÇÃO INICIAL
# ============================================================

if not CAMINHO_BANCO.exists():

    print()
    print("ERRO:")
    print(
        f"O banco '{CAMINHO_BANCO}' não foi encontrado."
    )
    print()

    raise SystemExit(1)


print()
print("=" * 60)
print("MIGRAÇÃO - CLASSIFICAÇÃO FUNCIONAL NA")
print("=" * 60)

print()
print(
    f"Banco encontrado: {CAMINHO_BANCO.resolve()}"
)


# ============================================================
# CONEXÃO
# ============================================================

conexao = sqlite3.connect(
    CAMINHO_BANCO
)

conexao.row_factory = (
    sqlite3.Row
)

cursor = conexao.cursor()


try:

    # ========================================================
    # DESABILITA TEMPORARIAMENTE AS CHAVES ESTRANGEIRAS
    # ========================================================

    cursor.execute(
        "PRAGMA foreign_keys = OFF;"
    )


    # ========================================================
    # CONFIRMA SE A TABELA EXISTE
    # ========================================================

    cursor.execute(
        """
        SELECT sql
        FROM sqlite_master
        WHERE
            type = 'table'
            AND
            name = ?
        """,
        (
            TABELA,
        )
    )

    resultado = cursor.fetchone()


    if resultado is None:

        print()
        print(
            f"ERRO: a tabela '{TABELA}' "
            f"não foi encontrada."
        )

        raise SystemExit(1)


    sql_original = resultado[
        "sql"
    ]


    print()
    print(
        "Tabela 'classificacoes' encontrada."
    )


    # ========================================================
    # VERIFICA COMO ESTÁ NOTA_FUNCIONAL
    # ========================================================

    cursor.execute(
        f"""
        PRAGMA table_info({TABELA});
        """
    )

    colunas_info = (
        cursor.fetchall()
    )


    coluna_funcional = None


    for coluna in colunas_info:

        if (
            coluna["name"]
            == "nota_funcional"
        ):

            coluna_funcional = coluna

            break


    if coluna_funcional is None:

        print()
        print(
            "ERRO: a coluna 'nota_funcional' "
            "não foi encontrada."
        )

        raise SystemExit(1)


    print()
    print(
        "Coluna nota_funcional encontrada."
    )

    print(
        "NOT NULL atual:",
        coluna_funcional["notnull"]
    )


    # ========================================================
    # SE JÁ ACEITAR NULL, NÃO FAZ NADA
    # ========================================================

    if (
        coluna_funcional["notnull"]
        == 0
    ):

        print()
        print(
            "A coluna nota_funcional já aceita NULL."
        )

        print(
            "Nenhuma migração é necessária."
        )

        print()

        raise SystemExit(0)


    # ========================================================
    # CAPTURA ÍNDICES E TRIGGERS
    #
    # Isso ajuda a preservar estruturas adicionais existentes.
    # ========================================================

    cursor.execute(
        """
        SELECT
            type,
            name,
            sql
        FROM sqlite_master
        WHERE
            tbl_name = ?
            AND
            type IN ('index', 'trigger')
            AND
            sql IS NOT NULL
        """,
        (
            TABELA,
        )
    )


    objetos_adicionais = (
        cursor.fetchall()
    )


    # ========================================================
    # REMOVE TABELA TEMPORÁRIA ANTIGA, CASO EXISTA
    # ========================================================

    cursor.execute(
        f"""
        DROP TABLE IF EXISTS {TABELA_TEMPORARIA};
        """
    )


    # ========================================================
    # CRIA SQL DA NOVA TABELA
    #
    # Primeiro troca apenas o nome da tabela.
    # Depois remove NOT NULL exclusivamente de nota_funcional.
    # ========================================================

    sql_novo = re.sub(
        r'CREATE\s+TABLE\s+["`\[]?'
        + re.escape(TABELA)
        + r'["`\]]?',
        f"CREATE TABLE {TABELA_TEMPORARIA}",
        sql_original,
        count=1,
        flags=re.IGNORECASE
    )


    # Remove NOT NULL somente da definição de nota_funcional.
    #
    # Exemplo:
    #
    # nota_funcional INTEGER NOT NULL
    #
    # passa para:
    #
    # nota_funcional INTEGER
    #

    padrao_nota_funcional = (
        r'(["`\[]?nota_funcional["`\]]?'
        r'\s+[A-Za-z0-9_()]+)'
        r'\s+NOT\s+NULL'
    )


    sql_novo, quantidade_substituicoes = (
        re.subn(
            padrao_nota_funcional,
            r'\1',
            sql_novo,
            count=1,
            flags=re.IGNORECASE
        )
    )


    if quantidade_substituicoes != 1:

        print()
        print(
            "ERRO: não foi possível modificar "
            "com segurança a definição de nota_funcional."
        )

        print()
        print(
            "Nenhuma alteração foi aplicada."
        )

        conexao.rollback()

        raise SystemExit(1)


    # ========================================================
    # NOMES DAS COLUNAS
    # ========================================================

    nomes_colunas = [
        coluna["name"]
        for coluna in colunas_info
    ]


    texto_colunas = ", ".join(
        f'"{nome}"'
        for nome in nomes_colunas
    )


    # ========================================================
    # INICIA TRANSAÇÃO
    # ========================================================

    cursor.execute(
        "BEGIN TRANSACTION;"
    )


    # ========================================================
    # 1 - CRIA NOVA TABELA
    # ========================================================

    cursor.execute(
        sql_novo
    )


    # ========================================================
    # 2 - COPIA TODOS OS REGISTROS
    # ========================================================

    cursor.execute(
        f"""
        INSERT INTO {TABELA_TEMPORARIA}
        ({texto_colunas})

        SELECT
            {texto_colunas}

        FROM {TABELA};
        """
    )


    # ========================================================
    # CONFERE QUANTIDADE ANTES DE TROCAR AS TABELAS
    # ========================================================

    cursor.execute(
        f"""
        SELECT COUNT(*)
        FROM {TABELA};
        """
    )

    quantidade_antiga = (
        cursor.fetchone()[0]
    )


    cursor.execute(
        f"""
        SELECT COUNT(*)
        FROM {TABELA_TEMPORARIA};
        """
    )

    quantidade_nova = (
        cursor.fetchone()[0]
    )


    if (
        quantidade_antiga
        != quantidade_nova
    ):

        raise RuntimeError(
            "A quantidade de registros copiados "
            "não corresponde à tabela original."
        )


    print()
    print(
        f"Registros encontrados: "
        f"{quantidade_antiga}"
    )

    print(
        f"Registros copiados: "
        f"{quantidade_nova}"
    )


    # ========================================================
    # 3 - REMOVE TABELA ANTIGA
    # ========================================================

    cursor.execute(
        f"""
        DROP TABLE {TABELA};
        """
    )


    # ========================================================
    # 4 - RENOMEIA A NOVA TABELA
    # ========================================================

    cursor.execute(
        f"""
        ALTER TABLE {TABELA_TEMPORARIA}
        RENAME TO {TABELA};
        """
    )


    # ========================================================
    # 5 - RECRIA ÍNDICES E TRIGGERS
    # ========================================================

    for objeto in objetos_adicionais:

        sql_objeto = (
            objeto["sql"]
        )

        if sql_objeto:

            cursor.execute(
                sql_objeto
            )


    # ========================================================
    # COMMIT
    # ========================================================

    conexao.commit()


    # ========================================================
    # VERIFICAÇÃO FINAL
    # ========================================================

    cursor.execute(
        f"""
        PRAGMA table_info({TABELA});
        """
    )


    colunas_finais = (
        cursor.fetchall()
    )


    nota_funcional_final = None


    for coluna in colunas_finais:

        if (
            coluna["name"]
            == "nota_funcional"
        ):

            nota_funcional_final = coluna

            break


    print()
    print("=" * 60)


    if (
        nota_funcional_final is not None
        and
        nota_funcional_final["notnull"] == 0
    ):

        print(
            "MIGRAÇÃO CONCLUÍDA COM SUCESSO."
        )

        print()
        print(
            "A coluna 'nota_funcional' agora aceita NULL."
        )

        print(
            "NULL será utilizado pelo sistema "
            "para representar NA quando aplicável."
        )

    else:

        print(
            "ATENÇÃO: a verificação final "
            "não confirmou a alteração."
        )


    print("=" * 60)
    print()


except SystemExit:

    raise


except Exception as erro:

    conexao.rollback()

    print()
    print("=" * 60)

    print(
        "ERRO DURANTE A MIGRAÇÃO."
    )

    print(
        "As alterações foram revertidas."
    )

    print()
    print(
        "Detalhes:"
    )

    print(
        erro
    )

    print("=" * 60)
    print()

    raise


finally:

    try:

        cursor.execute(
            "PRAGMA foreign_keys = ON;"
        )

    except Exception:

        pass


    conexao.close()