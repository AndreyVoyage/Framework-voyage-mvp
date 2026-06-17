"""Unit tests for AST Tools."""

from pathlib import Path

from voyage_framework.ast_tools.indexer import CodeIndexer
from voyage_framework.ast_tools.parser import ASTParser
from voyage_framework.ast_tools.symbols import SymbolExtractor
from voyage_framework.memory.semantic_store import SemanticStore


class TestASTParser:
    def test_parse_python_source(self) -> None:
        parser = ASTParser(language="python")
        tree = parser.parse_source("def foo(): pass")

        assert tree.root_node.type == "module"

    def test_parse_python_file(self, tmp_path: Path) -> None:
        file = tmp_path / "sample.py"
        file.write_text("class Bar:\n    def baz(self): pass\n", encoding="utf-8")

        parser = ASTParser(language="python")
        tree = parser.parse_file(file)

        assert tree.root_node.type == "module"

    def test_parse_typescript_source(self) -> None:
        parser = ASTParser(language="typescript")
        tree = parser.parse_source("function greet(): string { return 'hi'; }")

        assert tree.root_node.type == "program"

    def test_detect_language(self) -> None:
        assert ASTParser.detect_language("auth.py") == "python"
        assert ASTParser.detect_language("app.ts") == "typescript"
        assert ASTParser.detect_language("page.tsx") == "typescript"


class TestSymbolExtractor:
    def test_extract_functions_python(self) -> None:
        parser = ASTParser(language="python")
        tree = parser.parse_source("def foo(): pass\ndef bar(): pass\n")
        extractor = SymbolExtractor(language="python")

        functions = extractor.extract_functions(tree)

        assert len(functions) == 2
        assert {f.name for f in functions} == {"foo", "bar"}

    def test_extract_classes_python(self) -> None:
        parser = ASTParser(language="python")
        tree = parser.parse_source("class Foo: pass\nclass Bar: pass\n")
        extractor = SymbolExtractor(language="python")

        classes = extractor.extract_classes(tree)

        assert len(classes) == 2
        assert {c.name for c in classes} == {"Foo", "Bar"}

    def test_extract_imports_python(self) -> None:
        parser = ASTParser(language="python")
        tree = parser.parse_source("import os\nfrom pathlib import Path\n")
        extractor = SymbolExtractor(language="python")

        imports = extractor.extract_imports(tree)

        assert len(imports) == 2

    def test_extract_functions_typescript(self) -> None:
        parser = ASTParser(language="typescript")
        tree = parser.parse_source("function hello(): string { return 'hi'; }")
        extractor = SymbolExtractor(language="typescript")

        functions = extractor.extract_functions(tree)

        assert len(functions) == 1
        assert functions[0].name == "hello"


class TestCodeIndexer:
    def test_index_project(self, tmp_path: Path) -> None:
        (tmp_path / "src").mkdir()
        (tmp_path / "src" / "auth.py").write_text(
            "def login(): pass\nclass User: pass\n",
            encoding="utf-8",
        )
        (tmp_path / "src" / "app.ts").write_text(
            "function greet(): string { return 'hi'; }\n",
            encoding="utf-8",
        )

        store = SemanticStore()
        indexer = CodeIndexer(store, exclude_patterns={"*/.venv/*"})
        stats = indexer.index_project(tmp_path)

        assert stats["files"] == 2
        assert stats["symbols"] >= 3
        assert store.count() == stats["symbols"]
