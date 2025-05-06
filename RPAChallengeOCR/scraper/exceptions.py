class BrowserClosedError(Exception):
    """Exceção lançada quando o navegador é fechado inesperadamente"""
    pass

class OCRProcessingError(Exception):
    """Exceção para erros no processamento OCR"""
    pass

class InvoiceDownloadError(Exception):
    """Exceção para falhas no download de faturas"""
    pass

class DataExtractionError(Exception):
    """Exceção para falhas na extração de dados"""
    pass

class CSVGenerationError(Exception):
    """Exceção para falhas na geração do CSV"""
    pass

class FormSubmitFailed(Exception):
    """Exceção para falhas no envio de formulários"""
    pass

class InvalidDataFormat(Exception):
    """Exceção para dados em formato inválido"""
    pass

class ResultsSaveError(Exception):
    """Exceção para falhas ao salvar resultados"""
    pass