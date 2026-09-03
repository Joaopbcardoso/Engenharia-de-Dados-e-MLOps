import re
import unicodedata
from pathlib import Path

import duckdb
import pandas as pd


PASTA_AULA = Path(__file__).resolve().parent
PASTA_PROJETO = PASTA_AULA.parent
ARQUIVO_BANCO = PASTA_PROJETO / "meu_data_warehouse.duckdb"
COTACAO_USD_BRL = 5.20


def corrigir_codificacao(texto):
    if not isinstance(texto, str) or not any(
        marcador in texto for marcador in ("Ã", "Â", "â")
    ):
        return texto

    try:
        return texto.encode("latin1").decode("utf-8")
    except UnicodeError:
        return texto


def padronizar_texto(texto):
    if not isinstance(texto, str):
        return texto

    texto = corrigir_codificacao(texto)
    return (
        unicodedata.normalize("NFKD", texto.lower())
        .encode("ASCII", "ignore")
        .decode("ASCII")
    )


def padronizar_documento(documento):
    if pd.isna(documento):
        return None
    return re.sub(r"\D", "", str(documento))


def ler_fontes():
    try:
        envios = pd.read_csv(PASTA_AULA / "envios_brutos.csv", encoding="utf-8")
        clientes = pd.read_json(PASTA_AULA / "clientes_crm.json")
        print(f"Fontes lidas: {len(envios)} envios e {len(clientes)} clientes")
        return envios, clientes
    except (FileNotFoundError, ValueError, UnicodeDecodeError) as erro:
        raise RuntimeError(f"Falha ao ler as fontes: {erro}") from erro


def transformar_dados(envios, clientes):
    try:
        envios = envios.map(padronizar_texto)
        clientes = clientes.map(padronizar_texto)
        envios = envios.drop_duplicates(subset="ID_Transacao")
        envios = envios.rename(columns={"ID_Cliente": "cliente_id"})

        datas_com_barra = envios["Data_Envio"].str.contains("/", na=False)
        envios.loc[datas_com_barra, "Data_Envio"] = pd.to_datetime(
            envios.loc[datas_com_barra, "Data_Envio"],
            format="%d/%m/%Y",
            errors="coerce",
        ).dt.strftime("%Y-%m-%d")
        envios.loc[~datas_com_barra, "Data_Envio"] = pd.to_datetime(
            envios.loc[~datas_com_barra, "Data_Envio"],
            format="%Y-%m-%d",
            errors="coerce",
        ).dt.strftime("%Y-%m-%d")

        envios["Valor_Frete_USD"] = envios["Valor_Frete_USD"].fillna(
            envios["Valor_Frete_USD"].median()
        )
        clientes["documento_cpf_cnpj"] = clientes[
            "documento_cpf_cnpj"
        ].apply(padronizar_documento)
        clientes["categoria_conta"] = clientes["categoria_conta"].fillna(
            "nao informado"
        )

        envios_clientes = envios.merge(
            clientes,
            on="cliente_id",
            how="left",
            validate="many_to_one",
        )
        envios_clientes["Valor_Frete_BRL"] = (
            envios_clientes["Valor_Frete_USD"] * COTACAO_USD_BRL
        )
        print(f"Dados transformados: {len(envios_clientes)} envios")
        return envios_clientes, clientes
    except (KeyError, ValueError, TypeError) as erro:
        raise RuntimeError(f"Falha ao transformar os dados: {erro}") from erro


def carregar_data_warehouse(envios_clientes, clientes):
    con = None
    try:
        con = duckdb.connect(str(ARQUIVO_BANCO))
        con.register("envios_clientes", envios_clientes)
        con.register("clientes", clientes)
        con.execute("""
            CREATE OR REPLACE TABLE dim_cliente AS
            SELECT
                ROW_NUMBER() OVER (ORDER BY cliente_id) AS sk_cliente,
                cliente_id AS nk_cliente,
                nome_completo,
                documento_cpf_cnpj,
                regiao_estado,
                categoria_conta
            FROM clientes
        """)
        con.execute("""
            CREATE OR REPLACE TABLE dim_tempo AS
            SELECT DISTINCT
                CAST(REPLACE(Data_Envio, '-', '') AS INTEGER) AS sk_tempo,
                CAST(Data_Envio AS DATE) AS data_completa,
                EXTRACT(YEAR FROM CAST(Data_Envio AS DATE)) AS ano,
                EXTRACT(MONTH FROM CAST(Data_Envio AS DATE)) AS mes
            FROM envios_clientes
        """)
        con.execute("""
            CREATE OR REPLACE TABLE dim_status AS
            SELECT
                ROW_NUMBER() OVER (ORDER BY Status_Entrega) AS sk_status,
                Status_Entrega AS descricao_status
            FROM (SELECT DISTINCT Status_Entrega FROM envios_clientes)
        """)
        con.execute("""
            CREATE OR REPLACE TABLE fato_envios AS
            SELECT
                ROW_NUMBER() OVER (ORDER BY e.ID_Transacao) AS sk_envio,
                e.ID_Transacao AS nk_transacao,
                c.sk_cliente,
                t.sk_tempo,
                s.sk_status,
                e.Valor_Frete_USD AS valor_frete_usd,
                e.Valor_Frete_BRL AS valor_frete_brl
            FROM envios_clientes e
            JOIN dim_cliente c ON e.cliente_id = c.nk_cliente
            JOIN dim_tempo t ON CAST(e.Data_Envio AS DATE) = t.data_completa
            JOIN dim_status s ON e.Status_Entrega = s.descricao_status
        """)
        print(f"Data Warehouse carregado: {ARQUIVO_BANCO}")
        return con
    except (duckdb.Error, ValueError) as erro:
        if con is not None:
            con.close()
        raise RuntimeError(f"Falha ao carregar o Data Warehouse: {erro}") from erro


def executar_consultas(con):
    consulta_frete_estado = con.execute("""
        SELECT
            c.regiao_estado AS estado,
            ROUND(SUM(f.valor_frete_brl), 2) AS total_frete_brl
        FROM fato_envios f
        JOIN dim_cliente c ON f.sk_cliente = c.sk_cliente
        GROUP BY c.regiao_estado
        ORDER BY total_frete_brl DESC
    """).df()
    consulta_status_mes = con.execute("""
        WITH envios_por_mes AS (
            SELECT
                STRFTIME(t.data_completa, '%Y-%m') AS mes,
                s.descricao_status AS status_entrega
            FROM fato_envios f
            JOIN dim_tempo t ON f.sk_tempo = t.sk_tempo
            JOIN dim_status s ON f.sk_status = s.sk_status
        ), totais AS (
            SELECT mes, status_entrega, COUNT(*) AS quantidade_envios
            FROM envios_por_mes
            GROUP BY mes, status_entrega
        )
        SELECT
            mes,
            status_entrega,
            quantidade_envios,
            ROUND(
                100.0 * quantidade_envios
                / SUM(quantidade_envios) OVER (PARTITION BY mes),
                2
            ) AS percentual
        FROM totais
        ORDER BY mes, status_entrega
    """).df()
    print("\nConsulta 1 - Total de fretes em BRL por estado")
    print(consulta_frete_estado.to_string(index=False))
    print("\nConsulta 2 - Percentual de status por mes")
    print(consulta_status_mes.to_string(index=False))


def main():
    con = None
    try:
        envios, clientes = ler_fontes()
        envios_clientes, clientes = transformar_dados(envios, clientes)
        con = carregar_data_warehouse(envios_clientes, clientes)
        executar_consultas(con)
    except RuntimeError as erro:
        print(f"ERRO: {erro}")
        raise SystemExit(1) from erro
    finally:
        if con is not None:
            con.close()
            print("Conexao com o DuckDB encerrada")


if __name__ == "__main__":
    main()
