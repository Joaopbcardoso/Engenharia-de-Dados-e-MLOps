dados_brutos = [
    {
        "id": 101,
        "idade": 30,
        "renda": 4500
    },
    {
        "id": 102,
        "idade": "desconhecido",
        "renda": 3200   
    },
    {
        "id": 103,
        "idade": 0,
        "renda": -1000
    },
    {
        "id": 104,
        "idade": 42,
        "renda": None
    },
]

dados_limpos = [
 d for d in dados_brutos
 if d["idade"] is not None and d['idade'] is int and d['idade'] > 0 and
 d["renda"] is not None and d['renda'] is int and d['renda'] > 0
]

print("Dados originais:", dados_brutos)
print("Dados limpos:", dados_limpos)