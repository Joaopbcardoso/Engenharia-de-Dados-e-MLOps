import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, confusion_matrix, roc_auc_score
from sklearn.model_selection import train_test_split

# ==============================================================================
# PARTE 1: IMPLEMENTAÇÃO DO MODELO BASE
# ==============================================================================

# 1. Configuração de semente para reproducibilidade e geração de base sintética
np.random.seed(42)
n = 2000

dados = pd.DataFrame(
    {
        "RendaMensal": np.random.exponential(5000, n) + 1500,
        "ScoreCredito": np.random.randint(300, 950, n),
        "EmprestimosAtivos": np.random.poisson(1.5, n),
    }
)

# Cálculo da probabilidade de inadimplência e rotulagem
prob = 1 / (
    1
    + np.exp(
        -(
            -0.0003 * dados["RendaMensal"]
            - 0.005 * dados["ScoreCredito"]
            + 0.8 * dados["EmprestimosAtivos"]
        )
    )
)
dados["Inadimplente"] = (prob > np.random.uniform(0, 1, n)).astype(int)

# Divisão dos dados em treino e teste (estratificada pela classe alvo)
X = dados.drop(columns=["Inadimplente"])
y = dados["Inadimplente"]
X_tr, X_te, y_tr, y_te = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

# 2. Treinamento do modelo RandomForestClassifier
modelo_rf = RandomForestClassifier(
    n_estimators=200,
    max_depth=8,
    max_features="sqrt",
    oob_score=True,
    n_jobs=-1,
    random_state=42,
)
modelo_rf.fit(X_tr, y_tr)

# Previsões e avaliação inicial
preds_proba = modelo_rf.predict_proba(X_te)[:, 1]
print("==================================================")
print("PARTE 1: DESEMPENHO DO MODELO BASE")
print("==================================================")
print(f"Acurácia OOB (Treino): {modelo_rf.oob_score_:.4f}")
print(f"ROC-AUC no Teste: {roc_auc_score(y_te, preds_proba):.4f}")

# ==============================================================================
# PARTE 2: INTERPRETABILIDADE E IMPORTÂNCIA DAS VARIÁVEIS
# ==============================================================================

# 3. Importância das variáveis ordenadas de forma decrescente
importancias = pd.Series(
    modelo_rf.feature_importances_, index=X.columns
).sort_values(ascending=False)

print("\n==================================================")
print("PARTE 2: IMPORTÂNCIA DAS VARIÁVEIS")
print("==================================================")
print(importancias)
# 4. Resposta: A variável de maior impacto na probabilidade de inadimplência foi
# 'RendaMensal' (~41,2%), seguida por 'ScoreCredito' (~35,6%) e 'EmprestimosAtivos' (~23,2%).

# ==============================================================================
# PARTE 3: ANÁLISE CRÍTICA E DESBALANCEAMENTO DE CLASSES
# ==============================================================================

# 5. Proporção de clientes inadimplentes na base completa
print("\n==================================================")
print("PARTE 3: ANÁLISE DE DESBALANCEAMENTO DE CLASSES")
print("==================================================")
proporcao = dados["Inadimplente"].value_counts(normalize=True)
print("Proporção das classes na base completa:")
print(f"  - Adimplentes (0): {proporcao[0]:.2%}")
print(f"  - Inadimplentes (1): {proporcao[1]:.2%}")

# 6. Matriz de Confusão e Relatório de Classificação (Threshold padrão 0.5)
y_pred = modelo_rf.predict(X_te)

print("\nMatriz de Confusão no Teste (Modelo Base - Limiar padrão 0.5):")
print(confusion_matrix(y_te, y_pred))

print("\nRelatório de Classificação no Teste (Modelo Base - Limiar padrão 0.5):")
print(classification_report(y_te, y_pred, digits=4))

# 7. Reflexão Crítica:
# A acurácia OOB de ~93,4% NÃO é confiável para tomar decisões de negócio.
# Motivo: Em bases desbalanceadas (onde 93,25% dos clientes são bons pagadores),
# um classificador ingênuo que sempre previsse '0' teria ~93,25% de acurácia.
# Observando o relatório de classificação, o Recall da classe 1 foi de apenas ~7,4%
# (o modelo deixou passar 25 dos 27 inadimplentes reais no teste).
# Risco: A fintech aprovará crédito para dezenas de clientes com alto risco de
# calote (falsos negativos), causando grandes perdas financeiras.

# ==============================================================================
# PARTE 4: DESAFIO EXTRA
# ==============================================================================

print("\n==================================================")
print("PARTE 4: DESAFIO EXTRA (BALANCEAMENTO E THRESHOLD)")
print("==================================================")

# 8. Modelo com class_weight='balanced'
modelo_rf_bal = RandomForestClassifier(
    n_estimators=200,
    max_depth=8,
    max_features="sqrt",
    oob_score=True,
    class_weight="balanced",
    n_jobs=-1,
    random_state=42,
)
modelo_rf_bal.fit(X_tr, y_tr)
y_pred_bal = modelo_rf_bal.predict(X_te)

print("Matriz de Confusão (class_weight='balanced'):")
print(confusion_matrix(y_te, y_pred_bal))

print("\nRelatório de Classificação (class_weight='balanced'):")
print(classification_report(y_te, y_pred_bal, digits=4))

# Alternativa complementar: Reajuste do limiar (threshold) de corte de probabilidade
limiar = 0.20
y_pred_thresh = (preds_proba >= limiar).astype(int)

print(f"\nRelatório de Classificação (Modelo Base com Limiar = {limiar}):")
print(classification_report(y_te, y_pred_thresh, digits=4))

# Resposta Questão 8:
# Ao utilizar class_weight='balanced', a taxa de detecção dos inadimplentes
# (Recall da classe 1) saltou de ~7,4% (2/27) para ~70,4% (19/27).
# Da mesma forma, reduzir o limiar para 0.20 elevou o Recall para ~55,6% (15/27).
# O modelo passa a penalizar fortemente os erros na classe minoritária,
# protegendo o negócio do risco de inadimplência.
