"""AST Parser — обёртка над tree-sitter для Python и TypeScript."""

from __future__ import annotations

from pathlib import Path

try:
    import tree_sitter_python as tspython
    import tree_sitter_typescript as tsts
    from tree_sitter import Language, Parser, Tree
except ImportError as exc:
    raise ImportError('tree-sitter extras not installed. Run: pip install -e ".[ast,dev]"') from exc


SUPPORTED_LANGUAGES = {"python", "typescript"}


def _get_language(name: str) -> Language:
    """Получить tree-sitter Language по имени."""
    if name == "python":
        return Language(tspython.language())
    if name == "typescript":
        return Language(tsts.language_typescript())
    raise ValueError(f"Unsupported language: {name}. Use one of {SUPPORTED_LANGUAGES}")


class ASTParser:
    """Парсер исходного кода на Python и TypeScript."""

    def __init__(self, language: str = "python") -> None:
        if language not in SUPPORTED_LANGUAGES:
            raise ValueError(f"Unsupported language: {language}. Use one of {SUPPORTED_LANGUAGES}")
        self.language = language
        self._parser = Parser(_get_language(language))

    def parse_file(self, path: Path | str) -> Tree:
        """Парсить файл и вернуть AST."""
        path = Path(path)
        try:
            source = path.read_text(encoding="utf-8")
        except UnicodeDecodeError as exc:
            raise ValueError(f"Cannot read {path} as UTF-8") from exc
        return self.parse_source(source)

    def parse_source(self, source: str) -> Tree:
        """Парсить строку с исходным кодом и вернуть AST."""
        return self._parser.parse(source.encode("utf-8"))

    @staticmethod
    def detect_language(path: Path | str) -> str:
        """Определить язык по расширению файла."""
        suffix = Path(path).suffix.lower()
        if suffix in {".py"}:
            return "python"
        if suffix in {".ts", ".tsx"}:
            return "typescript"
        raise ValueError(f"Cannot detect language for: {path}")

    def __repr__(self) -> str:
        return f"ASTParser(language={self.language})"
