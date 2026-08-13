from database import SessionLocal
import models


db = SessionLocal()


classificacoes = (
    db.query(models.Classificacao)
    .order_by(models.Classificacao.id.desc())
    .all()
)


combinacoes_encontradas = set()

ids_excluidos = []


for classificacao in classificacoes:

    chave = (
        classificacao.oae_id,
        classificacao.inspecao_id,
        classificacao.componente_id
    )

    if chave in combinacoes_encontradas:

        ids_excluidos.append(
            classificacao.id
        )

        db.delete(
            classificacao
        )

    else:

        combinacoes_encontradas.add(
            chave
        )


db.commit()

db.close()


print()
print("Limpeza concluida.")

if len(ids_excluidos) == 0:

    print(
        "Nenhuma classificacao duplicada foi encontrada."
    )

else:

    print(
        "Classificacoes duplicadas removidas:"
    )

    print(
        ids_excluidos
    )

print()
print(
    "Foi mantida a classificacao de ID mais recente "
    "para cada combinacao de OAE + inspecao + componente."
)