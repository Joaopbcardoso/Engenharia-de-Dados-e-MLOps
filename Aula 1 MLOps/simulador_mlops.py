import json
import random
import time
from pathlib import Path

PASTA_AULA = Path(__file__).resolve().parent

def carregar_configuracao():
    with open(PASTA_AULA / "config.json", "r", encoding="utf-8") as f:
        return json.load(f)

def simular_pipeline():
    config = carregar_configuracao()
    print("\n" + "=" *50)
    print(
        f"INICIANDO SIMULADOR DE MLOPS - João Benvenutti: {config.get('nome_aluno')}"
    )

    print("=" * 50)
    time.sleep(1)


    # Etapa 1 - DADOS BRUTOS
    print("\n[1. INGESTÃO DE DADOS]")
    dados_brutos = [
        {"id": 1, "idade": 22, "renda": 3500},
        {"id": 2, "idade": None, "renda": 1500}, #dado sujo
        {"id": 3, "idade": 25, "renda": 7500},
        {"id": 4, "idade": 37, "renda": None}, #Dado sujo
        {"id": 5, "idade": 98, "renda": 9500}

    ]

    print(f" Recebidos {len(dados_brutos)} registros da fonte")

    # ETAPA 2 - ENGENHARIA DE DADOS
    print("\n [2. ENGENHARIA DE DADOS (ETL)]")
    time.sleep(1)
    if config["limpar_dados_nulos"]:
        dados_limpos = [
            d
            for d in dados_brutos
            if d["idade"] is not None and d["renda"] is not None
        ]
        removidos = len(dados_brutos) - len(dados_limpos)
        print(f"🧹 filtro ativado! {removidos} registros com erro foram REMOVIDOS")
    else:
        dados_limpos = dados_brutos
        print(
            "⚠️ ALERTA: Limpeza desativada! Registros corrompidos passaram para o modelo."
        )

    print(f"Base pronta para treino: {len(dados_limpos)} registros válidos")

    #ETAPA 3 - MACHINE LEARNING
    print("\n[3. TREINAMENTO DE MODELO (ML)]")
    time.sleep(1)
    pct_treino = config["tamanho_treino_porcentagem"]
    print(f"Usando {pct_treino}% dos dados para treinar o modelo...")

    #Casualidade simples para acurácia simulada
    if not config["limpar_dados_nulos"]:
        acuracia = random.randint(40, 55) # Acurácia ruim devido aos dados sujos
        status_dados = "Sujos"
    else:
        # Acurácia melhora com mais dados de treino
        acuracia = min(
            98,
            int(
                (pct_treino * 0.8) + (config["fator_qualidade_modelo"] * 15)
            ),
        )
        status_dados = "Limpos"

    print(f"📊 Modelo treinado! Acurácia obtida: {acuracia}%")

    # ETAPA 4: MLOPS & MONITORAÇÃO
    print("\n 4. MLOPS E DEPLOY")
    time.sleep(1)
    print("📝 Salvando registro de experimento (log)...")
    print(f"   Status dos Dados: {status_dados}")
    print(f"   Acurácia Final: {acuracia}")

    if acuracia >= 75:
        print(
            "\n [SISTEMA]: Acurácia alta! Modelo APROVADO para ir para Produção."
        )
    else:
        print(
            "\n [SISTEMA: Acurácia muito baixa! Modelo REPROVADO. Corrija o Pipeline]"
        )
    print("=" * 50 + "\n")

if __name__ == "__main__":
    simular_pipeline()