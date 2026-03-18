import os

def criar_arquivos_deploy():
    # 1. Criar o requirements.txt
    requirements = """streamlit
pandas
xlsxwriter
openpyxl
Pillow
"""
    with open("requirements.txt", "w") as f:
        f.write(requirements)
    print("✅ requirements.txt criado.")

    # 2. Criar o .gitignore (para não subir arquivos temporários ou seu banco de dados local)
    gitignore = """__pycache__/
.streamlit/
modulos_config.json
*.xlsx
*.csv
.env
"""
    with open(".gitignore", "w") as f:
        f.write(gitignore)
    print("✅ .gitignore criado.")

    # 3. Criar o Dockerfile (versão Março/2026)
    dockerfile = """FROM python:3.11-slim
WORKDIR /app
COPY . .
RUN pip install --no-cache-dir -r requirements.txt
EXPOSE 8501
ENTRYPOINT ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0", "--theme.base=dark", "--theme.primaryColor=#e30613"]
"""
    with open("Dockerfile", "w") as f:
        f.write(dockerfile)
    print("✅ Dockerfile criado.")

if __name__ == "__main__":
    criar_arquivos_deploy()
    print("\n" + "="*40)
    print("🎯 PRÓXIMOS PASSOS NO TERMINAL:")
    print("="*40)
    print("1. git init")
    print("2. git add .")
    print("3. git commit -m 'Initial commit Propeg Hub'")
    print("4. git remote add origin SEU_LINK_DO_GITHUB_AQUI")
    print("5. git push -u origin main")
    print("="*40)