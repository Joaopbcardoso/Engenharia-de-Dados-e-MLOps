import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.datasets import make_classification
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (accuracy_score, confusion_matrix, precision_score, 
                             recall_score, fbeta_score, roc_auc_score, roc_curve)
from fpdf import FPDF
import os

print("--------------------------------------------------")
print("--- Iniciando o Pipeline de MLOps ---")
print("--------------------------------------------------")

# 1. Geração de Dados Sintéticos
print("\n1. Gerando dados sintéticos desbalanceados (99.5% Operacional, 0.5% Falha)...")
X, y = make_classification(n_samples=100000, n_features=20, n_classes=2, 
                           weights=[0.995, 0.005], random_state=42)

# 2. Isolamento de Dados (Prevenção de Data Leakage)
print("2. Separando dados em Treino e Teste (Isolamento)...")
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, stratify=y, random_state=42)

# 3. Pré-processamento
print("3. Aplicando padronização... (fit apenas no treino)")
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)

# 4. Treinamento do Modelo
print("4. Treinando o modelo (RandomForest)...")
rf = RandomForestClassifier(n_estimators=100, random_state=42, n_jobs=-1, class_weight='balanced')
rf.fit(X_train_scaled, y_train)

# 5. Predições e Métricas com threshold padrão (0.5)
print("5. Calculando métricas de classificação...")
y_pred_proba = rf.predict_proba(X_test_scaled)[:, 1]
y_pred = (y_pred_proba >= 0.5).astype(int)

acc = accuracy_score(y_test, y_pred)
cm = confusion_matrix(y_test, y_pred)
tn, fp, fn, tp = cm.ravel()
prec = precision_score(y_test, y_pred, zero_division=0)
rec = recall_score(y_test, y_pred, zero_division=0)
f1 = fbeta_score(y_test, y_pred, beta=1, zero_division=0)
f2 = fbeta_score(y_test, y_pred, beta=2, zero_division=0)
f05 = fbeta_score(y_test, y_pred, beta=0.5, zero_division=0)
auc = roc_auc_score(y_test, y_pred_proba)

metrics_data = {
    "Métrica": ["Acurácia", "Precisão", "Recall", "F1-Score", "F2-Score", "F0.5-Score", "AUC-ROC"],
    "Valor": [f"{acc:.4f}", f"{prec:.4f}", f"{rec:.4f}", f"{f1:.4f}", f"{f2:.4f}", f"{f05:.4f}", f"{auc:.4f}"]
}
df_metrics = pd.DataFrame(metrics_data)

# 6. Ajuste Dinâmico do Threshold e Análise Financeira
print("\n6. Executando Análise Financeira do Threshold...")
# Custos reais de uma planta fabril (Exemplo)
custo_fp = 1000   # Falso Positivo: Manutenção desnecessária (parada programada, peças)
custo_fn = 50000  # Falso Negativo: Falha não detectada (acidente, parada de linha)

thresholds = np.linspace(0.0, 1.0, 101)
custos = []
for t in thresholds:
    y_pred_t = (y_pred_proba >= t).astype(int)
    cm_t = confusion_matrix(y_test, y_pred_t, labels=[0, 1])
    if cm_t.shape == (2,2):
        fp_t = cm_t[0, 1]
        fn_t = cm_t[1, 0]
    else:
        fp_t, fn_t = 0, sum(y_test)
           
    custo_t = (fp_t * custo_fp) + (fn_t * custo_fn)
    custos.append(custo_t)

idx_min_custo = np.argmin(custos)
best_threshold = thresholds[idx_min_custo]
menor_custo = custos[idx_min_custo]

# Custo com threshold padrão (0.5)
idx_padrao = 50 # Índice do 0.5 em linspace
custo_padrao = custos[idx_padrao]
economia = custo_padrao - menor_custo

print(f"  - Custo com Threshold Padrão (0.5): R$ {custo_padrao:,.2f}")
print(f"  - Custo com Threshold Ideal ({best_threshold:.2f}): R$ {menor_custo:,.2f}")
print(f"  - Economia Gerada: R$ {economia:,.2f}")

# Gerando Gráficos
plt.figure(figsize=(10, 5))
plt.plot(thresholds, custos, label='Custo Total', color='red', linewidth=2)
plt.axvline(best_threshold, color='green', linestyle='--', label=f'Ideal: {best_threshold:.2f} (R$ {menor_custo:,.2f})')
plt.axvline(0.5, color='blue', linestyle='-.', label=f'Padrão: 0.50 (R$ {custo_padrao:,.2f})')
plt.title('Análise Financeira: Custo Total vs Threshold de Decisão')
plt.xlabel('Threshold de Decisão')
plt.ylabel('Custo Total (R$)')
plt.legend()
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig('custo_threshold.png', dpi=150)
plt.close()

# 7. Geração do Relatório PDF
print("\n7. Gerando Relatório Executivo PDF...")
class PDF(FPDF):
    def header(self):
        self.set_font('helvetica', 'B', 15)
        self.cell(0, 10, 'Relatório Executivo de Engenharia de Dados e MLOps', border=False, align='C')
        self.ln(20)

    def footer(self):
        self.set_y(-15)
        self.set_font('helvetica', 'I', 8)
        self.cell(0, 10, f'Página {self.page_no()}', border=0, align='C')

pdf = PDF()
pdf.add_page()
pdf.set_font('helvetica', '', 11)

# Arquitetura da Solução
pdf.set_font('helvetica', 'B', 12)
pdf.cell(0, 10, '1. Arquitetura da Solução e Prevenção de Data Leakage', new_x="LMARGIN", new_y="NEXT")
pdf.set_font('helvetica', '', 11)
texto_arquitetura = (
    "Os dados foram gerados sinteticamente representando sensores de uma planta industrial, "
    "com forte desbalanceamento (99.5% Operacional vs 0.5% Falha). "
    "Para prevenir o Data Leakage (vazamento de dados), o conjunto total de dados foi dividido "
    "em Treino (80%) e Teste (20%) ANTES de qualquer etapa de pré-processamento. O objeto "
    "StandardScaler (responsável pela padronização das features) foi ajustado (fit) "
    "exclusivamente nos dados de Treino. Assim, garantimos que estatísticas globais não poluam "
    "o processo de avaliação do modelo nos dados de Teste."
)
pdf.multi_cell(0, 10, texto_arquitetura)
pdf.ln(5)

# Métricas
pdf.set_font('helvetica', 'B', 12)
pdf.cell(0, 10, '2. Quadro Comparativo de Métricas (Threshold Padrão = 0.5)', new_x="LMARGIN", new_y="NEXT")
pdf.set_font('helvetica', '', 11)
for i, row in df_metrics.iterrows():
    pdf.cell(50, 8, row['Métrica'], border=1)
    pdf.cell(40, 8, row['Valor'], border=1, new_x="LMARGIN", new_y="NEXT")

pdf.ln(5)
pdf.set_font('helvetica', 'B', 11)
pdf.cell(0, 10, f'Matriz de Confusão: TP={tp} | TN={tn} | FP={fp} | FN={fn}', new_x="LMARGIN", new_y="NEXT")
pdf.ln(5)

# Análise Financeira
pdf.set_font('helvetica', 'B', 12)
pdf.cell(0, 10, '3. Análise Financeira do Ajuste Dinâmico do Threshold', new_x="LMARGIN", new_y="NEXT")
pdf.set_font('helvetica', '', 11)
texto_financeiro = (
    f"Simulamos um cenário operacional real com custos atribuídos às falhas do modelo:\n"
    f" - Custo de Falso Positivo (FP - Manutenção indevida): R$ {custo_fp:,.2f}\n"
    f" - Custo de Falso Negativo (FN - Falha catastrófica não detectada): R$ {custo_fn:,.2f}\n\n"
    f"Abaixo observamos que o custo operando no threshold padrão de 0.5 seria de R$ {custo_padrao:,.2f}.\n"
    f"No entanto, ajustando o threshold de decisão para {best_threshold:.2f}, minimizamos o número "
    f"de Falsos Negativos (que são muito mais caros), reduzindo o custo total para R$ {menor_custo:,.2f}.\n"
    f"Isso gera uma economia projetada de R$ {economia:,.2f}."
)
pdf.multi_cell(0, 10, texto_financeiro)
pdf.ln(5)
pdf.image('custo_threshold.png', w=160)
pdf.ln(5)

# Recomendações
pdf.add_page()
pdf.set_font('helvetica', 'B', 12)
pdf.cell(0, 10, '4. Recomendações MLOps para Produção', new_x="LMARGIN", new_y="NEXT")
pdf.set_font('helvetica', '', 11)
texto_recomendacoes = (
    "Plano simples para monitoramento do modelo em produção:\n"
    " 1. Data Drift: Monitorar a distribuição das variáveis de entrada (ex: sensores de vibração e temperatura) "
    "para detectar mudanças estruturais que degradem o modelo.\n"
    " 2. Concept Drift: Acompanhar a taxa real de falhas observada no chão de fábrica e a relação com "
    "as predições para identificar degradação de performance, exigindo o retreino do modelo.\n"
    " 3. Automação: Integrar o pipeline (treino, validação e deploy) usando CI/CD e "
    "uma ferramenta de rastreamento de experimentos, como o MLflow.\n"
    " 4. Atualização da Regra Financeira: Revisar semestralmente os custos (FP e FN) junto à "
    "equipe de negócios e ajustar o threshold dinâmico em produção adequadamente."
)
pdf.multi_cell(0, 10, texto_recomendacoes)

pdf.output('Relatorio_Executivo.pdf')
print("Sucesso! Relatório 'Relatorio_Executivo.pdf' gerado com sucesso!")
