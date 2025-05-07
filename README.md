# 📄 **RPAChallengeOCR - Automação com OCR usando Playwright**

Automação profissional para o RPA Challenge implementada com Python e Playwright.

## ⚙️ **Funcionalidades**

✅ **Leitura de tabelas dinâmicas na web**

✅ **Download automático de arquivos PDF de faturas**

✅ **Extração de texto com OCR (Tesseract)**

✅ **Geração automática de CSV apenas com faturas vencidas ou vencendo hoje**

✅ **Logging estruturado em terminal e arquivo**

✅ **Organização modular de código**

✅ **Configurações externas com dotenv**

## 🚀 **Tecnologias Utilizadas**

**Python 3.10+** (principal)

**Playwright** (automação web e scraping)

**Pytesseract** (OCR)

**Pillow** (manipulação de imagem)

**Rich** (logs coloridos no terminal)

**Python-Dotenv** (gerenciamento de variáveis de ambiente)

**Logging** (rastreamento de execução)

## ⚙️ **Instalação e Execução**

**Pré-requisitos**

Python 3.10 ou superior

Git (para clonar o repositório)

Tesseract OCR instalado e configurado no PATH ou via `.env` (`TESSERACT_PATH`)

1️⃣ Clone o repositório:

git clone https://github.com/Andregr99/RPAChallengeOCR.git

cd RPAChallengeOCR

2️⃣ Crie e ative um ambiente virtual:

python -m venv venv

Windows:
venv\Scripts\activate

Linux/Mac:
source venv/bin/activate

3️⃣ Instale as dependências e o Playwright:

pip install -r requirements.txt

playwright install chromium

Planilha de resultados em /results/

ℹ️ Aviso

O OCR é sensível à qualidade do PDF. Esse projeto foi ajustado especificamente para o layout do RPA Challenge OCR.

Todos os logs são registrados em logs/scraper.log.

ℹ️ Suporte ao Playwright

Caso encontre problemas com a instalação do Playwright:

No Windows, execute como Administrador

No Linux, pode ser necessário instalar dependências adicionais:
sudo apt-get install libnss3 libnspr4 libatk1.0-0 libatk-bridge2.0-0 libcups2 libdrm2 libxkbcommon0 libxcomposite1 libxdamage1 libxfixes3 libxrandr2 libgbm1 libasound2
