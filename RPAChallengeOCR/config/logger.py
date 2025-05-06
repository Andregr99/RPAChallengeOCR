import logging
from pathlib import Path
from datetime import datetime
from rich.logging import RichHandler

def configure_logger(name: str = "scraper") -> logging.Logger:
    """Configura um logger com saída para console (Rich) e arquivo"""
    # Configura diretório de logs
    log_dir = Path(__file__).parent.parent / "logs"
    log_dir.mkdir(exist_ok=True)
    
    # Cria o logger
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    
    # Remove handlers existentes
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # Configura RichHandler para console
    console_handler = RichHandler(
        rich_tracebacks=True,
        markup=True,
        show_time=False,
        show_level=True
    )
    console_handler.setLevel(logging.INFO)
    
    # Configura FileHandler para arquivo
    log_file = log_dir / f"{name}_{datetime.now().strftime('%Y%m%d')}.log"
    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setFormatter(
        logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    )
    
    # Adiciona handlers
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    
    return logger

# Logger padrão para importação
logger = configure_logger()