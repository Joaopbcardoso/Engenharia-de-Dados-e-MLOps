# Engenharia de Dados e MLOps

Materiais e exercícios práticos da disciplina, organizados por aula.

## Aula 3: simulador IoT

Instale as dependências em um ambiente virtual:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

Gere os modelos locais e execute o simulador:

```powershell
python "Aula 3/treinar_modelo.py"
streamlit run "Aula 3/teste_compressor.py"
```

Os arquivos `.joblib`, bancos locais, exportações e ambientes virtuais são artefatos de execução e não são versionados. Os modelos devem ser gerados pelo script de treinamento antes de iniciar o Streamlit.
