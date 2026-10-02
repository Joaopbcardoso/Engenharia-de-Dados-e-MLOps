import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

# 1. CRIANDO O HISTÓRICO DE VENDAS DO PLAYSTATION 5 (24 MESES)
np.random.seed(7323)
meses_historico = pd.date_range(start="2024-09-01", periods=24, freq="MS")

# Tendência de crescimento + variação aleatória
tendencia = np.linspace(8000, 15000, 24)
ruido = np.random.normal(0, 1500, 24)
vendas_historicas = tendencia + ruido

# DataFrame
df = pd.DataFrame(
    {"Data": meses_historico, "Vendas": vendas_historicas}
).set_index("Data")

# 2. SIMULANDO A LÓGICA DO ARIMA (Tendência + AutoRegressão)
# Calculamos a taxa média de crescimento mês a mês (Diferenciação d=1)
crescimento_medio = np.diff(df["Vendas"]).mean()
ultima_venda = df["Vendas"].iloc[-1]
# Nesta amostra, a nova semente e o desvio de 1.500 elevaram a média observada
# de 254,22 para 282,96 unidades/mês; o ruído maior pode mover essa média,
# mas não altera o crescimento esperado, pois tem média zero.

# Projetando os próximos 12 meses
meses_futuros = pd.date_range(
    start=df.index[-1] + pd.offsets.MonthBegin(1), periods=12, freq="MS"
)
projecao_base = []
projecao_otimista = []
projecao_pessimista = []
margem_erro = []

venda_base = ultima_venda
venda_otimista = ultima_venda
venda_pessimista = ultima_venda
choques_mensais = np.random.normal(0, 100, len(meses_futuros))

for i, (data, choque) in enumerate(zip(meses_futuros, choques_mensais), start=1):
    # Os cenários compartilham o mesmo choque mensal para facilitar a comparação.
    venda_base += crescimento_medio + choque
    venda_otimista += crescimento_medio * 1.15 + choque
    venda_pessimista += crescimento_medio * 0.75 + choque

    previsao_base = venda_base
    previsao_otimista = venda_otimista
    previsao_pessimista = venda_pessimista

    # A sazonalidade de novembro e dezembro vale para todos os cenários.
    if data.month in (11, 12):
        previsao_base *= 1.35
        previsao_otimista *= 1.35
        previsao_pessimista *= 1.35

    projecao_base.append(previsao_base)
    projecao_otimista.append(previsao_otimista)
    projecao_pessimista.append(previsao_pessimista)

    # A incerteza da previsão base aumenta conforme avançamos no horizonte.
    margem_erro.append(800 * np.sqrt(i))

df_futuro = pd.DataFrame(
    {
        "Data": meses_futuros,
        "Cenário Base": projecao_base,
        "Cenário Otimista": projecao_otimista,
        "Cenário Pessimista": projecao_pessimista,
    },
    index=meses_futuros,
)

# 3. EXIBINDO OS RESULTADOS NO TERMINAL
print("--- PROJEÇÃO DE VENDAS (PRÓXIMOS 12 MESES) ---")
for data, valor in zip(df_futuro["Data"], df_futuro["Cenário Base"]):
    print(
        f"Mês: {data.strftime('%m/%Y')} | Previsão: {int(valor):,} unidades".replace(
            ",", "."
        )
    )

# 4. GERANDO O GRÁFICO COMPARATIVO
plt.figure(figsize=(10, 5))
plt.plot(
    df.index,
    df["Vendas"],
    label="Histórico de Vendas (PS5)",
    color="#003791",
    marker="o",
)
plt.plot(
    df_futuro.index,
    df_futuro["Cenário Base"],
    label="Cenário Base",
    color="#d62728",
    linestyle="--",
    marker="o",
)
plt.plot(
    df_futuro.index,
    df_futuro["Cenário Otimista"],
    label="Cenário Otimista (+15% no crescimento)",
    color="#2ca02c",
)
plt.plot(
    df_futuro.index,
    df_futuro["Cenário Pessimista"],
    label="Cenário Pessimista (-25% no crescimento)",
    color="#ff7f0e",
)

# Margem de Confiança (Sombra)
limite_superior = df_futuro["Cenário Base"] + margem_erro
limite_inferior = df_futuro["Cenário Base"] - margem_erro
plt.fill_between(
    df_futuro.index,
    limite_inferior,
    limite_superior,
    color="#ff9896",
    alpha=0.4,
    label="Margem de Incerteza",
)

plt.title("Simulação de Previsão de Vendas - PlayStation 5", fontsize=12)
plt.xlabel("Mês")
plt.ylabel("Unidades Vendidas")
plt.legend()
plt.grid(True, linestyle=":", alpha=0.6)
plt.tight_layout()
plt.show()