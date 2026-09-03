import duckdb
import pandas as pd
from pathlib import Path

PASTA_AULA = Path(__file__).resolve().parent.parent
PASTA_PROJETO = PASTA_AULA.parent
PASTA_SAIDAS = PASTA_AULA / "saidas"
PASTA_SAIDAS.mkdir(exist_ok=True)

# Este script mostra um fluxo completo de modelagem de dados:
# 1) cria um banco operacional simples (OLTP);
# 2) transforma esses dados em um modelo analítico (OLAP) com Star Schema;
# 3) faz análises de negócio;
# 4) exporta tudo para Excel.

# Conecta ao banco DuckDB local. O arquivo será criado automaticamente se não existir.
con = duckdb.connect(str(PASTA_PROJETO / "meu_data_warehouse.duckdb"))

print("--------------------------------------------------")
print("1. BANCO OPERACIONAL OLTP (3FN) - VERSAO EXPANDIDA")
print("--------------------------------------------------")

# Etapa 1: criar as tabelas do banco operacional.
# Essas tabelas representam dados do dia a dia da empresa, como clientes, produtos e pedidos.
con.execute("""
CREATE OR REPLACE TABLE oltp_clientes (
    cliente_id INT PRIMARY KEY,
    nome VARCHAR,
    cidade VARCHAR,
    estado VARCHAR
);

CREATE OR REPLACE TABLE oltp_vendedores (
    vendedor_id INT PRIMARY KEY,
    nome_vendedor VARCHAR,
    regiao VARCHAR
);

CREATE OR REPLACE TABLE oltp_produtos (
    produto_id INT PRIMARY KEY,
    nome_produto VARCHAR,
    categoria VARCHAR,
    preco_unitario DECIMAL(10,2),
    custo_unitario DECIMAL(10,2)
);

CREATE OR REPLACE TABLE oltp_pedidos (
    pedido_id INT PRIMARY KEY,
    cliente_id INT,
    vendedor_id INT,
    forma_pagamento VARCHAR,
    data_pedido DATE
);

CREATE OR REPLACE TABLE oltp_itens_pedido (
    item_id INT PRIMARY KEY,
    pedido_id INT,
    produto_id INT,
    quantidade INT,
    valor_pago DECIMAL(10,2)
);

INSERT INTO oltp_clientes VALUES
(101, 'Carlos Eduardo', 'Florianópolis', 'SC'),
(102, 'Beatriz Souza', 'São Paulo', 'SP');

-- Pelo menos 2 vendedores, com regiao
INSERT INTO oltp_vendedores VALUES
(101, 'Peter Parker', 'Sudeste'),
(102, 'Steve Rogers', 'Sul');

-- custo_unitario sempre inferior ao preco_unitario
INSERT INTO oltp_produtos VALUES
(1, 'Teclado Mecânico', 'Periféricos', 250.00, 80.00),
(2, 'Mouse Vertical', 'Periféricos', 150.00, 45.00),
(3, 'Monitor 27', 'Monitores', 1200.00, 500.00);

-- pedidos com vendedor_id e forma_pagamento
INSERT INTO oltp_pedidos VALUES
(5001, 101, 102, 'PIX', '2026-08-01'),
(5002, 102, 102, 'BOLETO', '2026-08-02'),
(5003, 101, 101, 'CARTAO DE CREDITO', '2026-08-05');

INSERT INTO oltp_itens_pedido VALUES
(1, 5001, 1, 1, 250.00),
(2, 5001, 2, 1, 150.00),
(3, 5002, 3, 1, 1200.00),
(4, 5003, 2, 2, 300.00);
""")

print("Dados operacionais em 3FN criados com sucesso (vendedores, forma_pagamento e custo_unitario incluidos).\n")


print("--------------------------------------------------")
print("2. STAR SCHEMA (OLAP) - KIMBALL")
print("--------------------------------------------------")

# Etapa 2: construir o Star Schema.
# As dimensões guardam atributos descritivos (quem, o quê, quando, como pagou).
# A tabela de fatos guarda as métricas da venda, como receita, quantidade e lucro.
con.execute("""
-- 1. Dimensao Cliente
CREATE OR REPLACE TABLE dim_cliente AS
SELECT
    ROW_NUMBER() OVER (ORDER BY cliente_id) AS sk_cliente,
    cliente_id AS nk_cliente,
    nome,
    cidade,
    estado
FROM oltp_clientes;

-- 2. Dimensao Vendedor
CREATE OR REPLACE TABLE dim_vendedor AS
SELECT
    ROW_NUMBER() OVER (ORDER BY vendedor_id) AS sk_vendedor,
    vendedor_id AS nk_vendedor,
    nome_vendedor,
    regiao
FROM oltp_vendedores;

-- 3. Dimensao Produto
CREATE OR REPLACE TABLE dim_produto AS
SELECT
    ROW_NUMBER() OVER (ORDER BY produto_id) AS sk_produto,
    produto_id AS nk_produto,
    nome_produto,
    categoria,
    preco_unitario,
    custo_unitario
FROM oltp_produtos;

-- 4. Dimensao Pagamento
CREATE OR REPLACE TABLE dim_pagamento AS
SELECT
    ROW_NUMBER() OVER (ORDER BY forma_pagamento) AS sk_pagamento,
    forma_pagamento
FROM (SELECT DISTINCT forma_pagamento FROM oltp_pedidos);

-- 5. Dimensao Tempo
CREATE OR REPLACE TABLE dim_tempo AS
SELECT DISTINCT
    CAST(STRFTIME(data_pedido, '%Y%m%d') AS INT) AS sk_tempo,
    data_pedido AS data_completa,
    EXTRACT(YEAR FROM data_pedido) AS ano,
    EXTRACT(MONTH FROM data_pedido) AS mes,
    STRFTIME(data_pedido, '%B') AS nome_mes
FROM oltp_pedidos;

-- 6. Fato Vendas (medidas de negócio)
-- A tabela fato_vendas é o centro do modelo analítico.
-- Ela conecta as dimensões e armazena as medidas numéricas da venda.
CREATE OR REPLACE TABLE fato_vendas AS
SELECT
    ROW_NUMBER() OVER () AS sk_venda,
    c.sk_cliente,
    v.sk_vendedor,
    pr.sk_produto,
    pg.sk_pagamento,
    t.sk_tempo,
    p.pedido_id AS nk_pedido_id,
    i.quantidade,
    i.valor_pago AS receita,
    ROUND(i.quantidade * pr.custo_unitario, 2) AS custo_total,
    ROUND(i.valor_pago - (i.quantidade * pr.custo_unitario), 2) AS lucro_bruto
FROM oltp_itens_pedido i
JOIN oltp_pedidos p ON i.pedido_id = p.pedido_id
JOIN dim_cliente c ON p.cliente_id = c.nk_cliente
JOIN dim_vendedor v ON p.vendedor_id = v.nk_vendedor
JOIN dim_produto pr ON i.produto_id = pr.nk_produto
JOIN dim_pagamento pg ON p.forma_pagamento = pg.forma_pagamento
JOIN dim_tempo t ON p.data_pedido = t.data_completa;
""")

print("Star Schema (fato_vendas + 5 dimensoes, com custo_total e lucro_bruto) gerado com sucesso!\n")


print("--------------------------------------------------")
print("3. CONSULTAS ANALITICAS (SQL OLAP)")
print("--------------------------------------------------")

# Etapa 3: realizar consultas analíticas para responder perguntas de negócio.
# Aqui usamos joins com as dimensões para transformar dados brutos em informações úteis.

# 3.1 Lucratividade por categoria de produto
relatorio_categoria = con.execute("""
SELECT
    dp.categoria,
    SUM(f.receita) AS receita_total,
    SUM(f.custo_total) AS custo_total,
    SUM(f.lucro_bruto) AS lucro_bruto_total
FROM fato_vendas f
JOIN dim_produto dp ON f.sk_produto = dp.sk_produto
GROUP BY dp.categoria
ORDER BY lucro_bruto_total DESC
""").df()

# 3.2 Desempenho por vendedor e regiao
relatorio_vendedor = con.execute("""
SELECT
    dv.nome_vendedor,
    dv.regiao,
    SUM(f.receita) AS receita_total,
    SUM(f.lucro_bruto) AS lucro_bruto_total
FROM fato_vendas f
JOIN dim_vendedor dv ON f.sk_vendedor = dv.sk_vendedor
GROUP BY dv.nome_vendedor, dv.regiao
ORDER BY receita_total DESC
""").df()

# 3.3 Analise por forma de pagamento (receita total e ticket medio)
relatorio_pagamento = con.execute("""
SELECT
    dpg.forma_pagamento,
    SUM(f.receita) AS receita_total,
    SUM(f.quantidade) AS itens_vendidos,
    ROUND(SUM(f.receita) / SUM(f.quantidade), 2) AS ticket_medio
FROM fato_vendas f
JOIN dim_pagamento dpg ON f.sk_pagamento = dpg.sk_pagamento
GROUP BY dpg.forma_pagamento
ORDER BY receita_total DESC
""").df()

print("\n1) Lucratividade por categoria:")
print(relatorio_categoria)
print("\n2) Desempenho por vendedor/regiao:")
print(relatorio_vendedor)
print("\n3) Analise por forma de pagamento:")
print(relatorio_pagamento)

# A aba 'relatorio_analitico' do Excel usara a consulta de lucratividade por categoria,
# que responde diretamente a pergunta-chave da diretoria (item 1 da Etapa 3)
relatorio_analitico = relatorio_categoria.copy()

print("\nConsultas analiticas concluidas.\n")


# Etapa 4: exportar os dados para Excel, com uma aba para cada tabela e uma aba para o relatório analítico.
print("--------------------------------------------------")
print("4. EXPORTACAO PARA EXCEL (data_warehouse.xlsx)")
print("--------------------------------------------------")

df_fato = con.execute("SELECT * FROM fato_vendas").df()
df_dim_cliente = con.execute("SELECT * FROM dim_cliente").df()
df_dim_produto = con.execute("SELECT * FROM dim_produto").df()
df_dim_vendedor = con.execute("SELECT * FROM dim_vendedor").df()
df_dim_pagamento = con.execute("SELECT * FROM dim_pagamento").df()
df_dim_tempo = con.execute("SELECT * FROM dim_tempo").df()

nome_arquivo = PASTA_SAIDAS / "data_warehouse_v2.xlsx"

with pd.ExcelWriter(nome_arquivo, engine='openpyxl') as writer:
    df_fato.to_excel(writer, sheet_name='fato_vendas', index=False)
    df_dim_cliente.to_excel(writer, sheet_name='dim_cliente', index=False)
    df_dim_produto.to_excel(writer, sheet_name='dim_produto', index=False)
    df_dim_vendedor.to_excel(writer, sheet_name='dim_vendedor', index=False)
    df_dim_pagamento.to_excel(writer, sheet_name='dim_pagamento', index=False)
    df_dim_tempo.to_excel(writer, sheet_name='dim_tempo', index=False)
    relatorio_analitico.to_excel(writer, sheet_name='relatorio_analitico', index=False)

print(f"SUCESSO! O arquivo '{nome_arquivo}' foi gerado com 7 abas:")
print(" - fato_vendas, dim_cliente, dim_produto, dim_vendedor, dim_pagamento, dim_tempo, relatorio_analitico")

# Salva as 3 consultas tambem para uso no relatorio em PDF
relatorio_categoria.to_csv(PASTA_SAIDAS / "saida_relatorio_categoria.csv", index=False)
relatorio_vendedor.to_csv(PASTA_SAIDAS / "saida_relatorio_vendedor.csv", index=False)
relatorio_pagamento.to_csv(PASTA_SAIDAS / "saida_relatorio_pagamento.csv", index=False)

con.close()
print("\nPipeline completo executado com sucesso.")
