import sys

try:
    from .main import main
except ImportError as erro:
    # Erro comum: rodar com um Python fora do ambiente virtual do projeto.
    sys.exit(
        f"Dependência ausente ({erro}).\n"
        f"Python em uso: {sys.executable}\n"
        "Use o Python do ambiente virtual:  .venv/bin/python -m solver\n"
        "ou ative o ambiente antes:         source .venv/bin/activate"
    )

raise SystemExit(main())
