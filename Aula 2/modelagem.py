import duckdb
import pandas as pd

# Conectando ao DuckDB
con = duckdb.connect("meu_data_warehouse.duckdb")

print("--------------------------------------------------")
print("1. SIMULANDO O BANCO OPERACIONAL OLTP (3FN)")
print("--------------------------------------------------")

con.execute("""
CREATE OR REPLACE TABLE oltp_clientes (
    cliente_id INT PRIMARY KEY,
    nome VARCHAR,
    cidade VARCHAR,
    estado VARCHAR
);

CREATE OR REPLACE TABLE oltp_produtos (
    produto_id INT PRIMARY KEY,
    nome_produto VARCHAR,
    categoria VARCHAR,
    preco_unitario DECIMAL(10,2)
);

CREATE OR REPLACE TABLE oltp_pedidos (
    pedido_id INT PRIMARY KEY,
    cliente_id INT,
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

INSERT INTO oltp_produtos VALUES 
(1, 'Teclado Mecânico', 'Periféricos', 250.00),
(2, 'Mouse Vertical', 'Periféricos', 150.00),
(3, 'Monitor 27', 'Monitores', 1200.00);

INSERT INTO oltp_pedidos VALUES 
(5001, 101, '2026-08-01'),
(5002, 102, '2026-08-02'),
(5003, 101, '2026-08-05');

INSERT INTO oltp_itens_pedido VALUES 
(1, 5001, 1, 1, 250.00),
(2, 5001, 2, 1, 150.00),
(3, 5002, 3, 1, 1200.00),
(4, 5003, 2, 2, 300.00);
""")

print("✅ Dados operacionais em 3FN criados com sucesso!\n")


print("--------------------------------------------------")
print("2. APLICANDO KIMBALL: CONSTRUINDO O STAR SCHEMA (OLAP)")
print("--------------------------------------------------")

con.execute("""
-- 1. Dimensão Cliente (com SK)
CREATE OR REPLACE TABLE dim_cliente AS 
SELECT 
    ROW_NUMBER() OVER () AS sk_cliente,
    cliente_id AS nk_cliente,
    nome,
    cidade,
    estado
FROM oltp_clientes;

-- 2. Dimensão Produto (com SK)
CREATE OR REPLACE TABLE dim_produto AS 
SELECT 
    ROW_NUMBER() OVER () AS sk_produto,
    produto_id AS nk_produto,
    nome_produto,
    categoria,
    preco_unitario
FROM oltp_produtos;

-- 3. Dimensão Tempo
CREATE OR REPLACE TABLE dim_tempo AS 
SELECT DISTINCT
    CAST(STRFTIME(data_pedido, '%Y%m%d') AS INT) AS sk_tempo,
    data_pedido AS data_completa,
    EXTRACT(YEAR FROM data_pedido) AS ano,
    EXTRACT(MONTH FROM data_pedido) AS mes,
    STRFTIME(data_pedido, '%B') AS nome_mes
FROM oltp_pedidos;

-- 4. Tabela de Fatos Vendas
CREATE OR REPLACE TABLE fato_vendas AS
SELECT 
    ROW_NUMBER() OVER () AS sk_venda,
    c.sk_cliente,
    pr.sk_produto,
    t.sk_tempo,
    p.pedido_id AS nk_pedido_id,
    i.quantidade,
    i.valor_pago AS receita
FROM oltp_itens_pedido i
JOIN oltp_pedidos p ON i.pedido_id = p.pedido_id
JOIN dim_cliente c ON p.cliente_id = c.nk_cliente
JOIN dim_produto pr ON i.produto_id = pr.nk_produto
JOIN dim_tempo t ON p.data_pedido = t.data_completa;
""")

print("✅ Star Schema (Fato e Dimensões) gerado com sucesso!\n")


print("--------------------------------------------------")
print("3. EXPORTANDO O DATA WAREHOUSE PARA EXCEL (.xlsx)")
print("--------------------------------------------------")

# Extraindo todas as tabelas para DataFrames do Pandas
df_fato = con.execute("SELECT * FROM fato_vendas").df()
df_dim_cliente = con.execute("SELECT * FROM dim_cliente").df()
df_dim_produto = con.execute("SELECT * FROM dim_produto").df()
df_dim_tempo = con.execute("SELECT * FROM dim_tempo").df()

# Salvando todas em um único arquivo Excel com abas separadas
nome_arquivo = "data_warehouse_exportado.xlsx"

with pd.ExcelWriter(nome_arquivo, engine='openpyxl') as writer:
    df_fato.to_excel(writer, sheet_name='fato_vendas', index=False)
    df_dim_cliente.to_excel(writer, sheet_name='dim_cliente', index=False)
    df_dim_produto.to_excel(writer, sheet_name='dim_produto', index=False)
    df_dim_tempo.to_excel(writer, sheet_name='dim_tempo', index=False)

print(f"SUCESSO! O arquivo '{nome_arquivo}' foi gerado na pasta do seu projeto.")
print("Agora você pode abri-lo direto no Excel ou no VSCode com duas abas separadas para ver o Star Schema!")