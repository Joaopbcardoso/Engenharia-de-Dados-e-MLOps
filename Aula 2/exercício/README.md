# Trabalho II - Modelagem de Dados com DuckDB

Este README descreve a atividade do Trabalho II, que consiste em transformar um banco operacional em um modelo analítico usando o conceito de Star Schema.

## Objetivo

Criar um Data Warehouse simples a partir de dados de vendas, organizando as informações em:

- tabelas OLTP (operacionais)
- dimensões
- tabela de fatos
- exportação para Excel
- consultas analíticas básicas

## O que foi implementado

### 1. Simulação do banco operacional
Foram criadas tabelas com dados de:
- clientes
- vendedores
- produtos
- pedidos
- itens de pedido

### 2. Construção do Star Schema
Foram criadas as dimensões:
- cliente
- vendedor
- produto
- tempo

E a tabela de fatos `fato_vendas`, que armazena as métricas principais das vendas.

### 3. Exportação para Excel
Os dados foram exportados para um arquivo Excel com abas separadas para cada tabela e análise.

### 4. Análises básicas
Foram feitas consultas para responder perguntas de negócio, como:
- receita por cliente
- receita por produto
- receita por mês

## Arquivos principais

- modelagem-expandida.py: script principal da atividade
- data_warehouse_exportado.xlsx: arquivo gerado com os dados e análises
- meu_data_warehouse.duckdb: banco de dados criado localmente

## Como executar

Na pasta da atividade, execute:

```bash
python "modelagem-expandida.py"
```

O script irá gerar o banco DuckDB, criar o Star Schema e exportar o Excel automaticamente.
