import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import train_test_split
# Configuração de semente para reproducibilidade
np.random.seed(42)
n = 2000
# Criação do conjunto de dados sintético
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
# Divisão dos dados em treino e teste
X = dados.drop(columns=["Inadimplente"])
y = dados["Inadimplente"]
X_tr, X_te, y_tr, y_te = train_test_split(
 X, y, test_size=0.2, random_state=42, stratify=y
)
# Treinamento do modelo RandomForest
modelo_rf = RandomForestClassifier(
 n_estimators=2000,
 max_depth=8,
 max_features="sqrt",
 oob_score=True,
 n_jobs=-1,
 random_state=42,
)
modelo_rf.fit(X_tr, y_tr)
# Previsões e avaliação
preds = modelo_rf.predict_proba(X_te)[:, 1]
print(f"Acurácia OOB (Treino): {modelo_rf.oob_score_:.4f}")
print(f"ROC-AUC no Teste: {roc_auc_score(y_te, preds):.4f}")
