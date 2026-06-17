"""DocsBuilder — автоматическая сборка документации проекта."""

from __future__ import annotations

from pathlib import Path

from voyage_framework.chronicler.decision_log import DecisionLog
from voyage_framework.chronicler.journal import ProcessJournal
from voyage_framework.chronicler.tutorial_generator import TutorialGenerator


class DocsBuilder:
    """Собирает docs/ для GitHub Pages из Chronicler и исходников проекта."""

    # Маппинг фаз на correlation_id; если journal пуст, используется fallback-заголовок.
    PHASE_TUTORIALS: dict[str, str] = {
        "01-installation": "install",
        "02-first-agent": "first-agent",
        "03-semantic-search": "semantic-search",
        "04-self-improvement": "self-improvement",
        "05-langgraph": "langgraph",
        "06-chronicler": "chronicler",
    }

    FAQ: list[dict[str, str]] = [
        {
            "q": "What is Voyage Framework?",
            "a": "AI-Native Engineering Operating System for solo developers.",
        },
        {
            "q": "Which Python versions are supported?",
            "a": "Python 3.11 and 3.12.",
        },
        {
            "q": "How do I run an agent?",
            "a": 'Use `voyage run <role> --task "..." --plan "cmd1;cmd2"`.',
        },
        {
            "q": "Can I run commands in Docker?",
            "a": "Yes, use `--backend docker` with `voyage run` or `voyage graph run`.",
        },
        {
            "q": "What is Chronicler?",
            "a": "A module that records every development step for replay and tutorials.",
        },
        {
            "q": "How do I generate a replay script?",
            "a": "Use `voyage chronicler replay <correlation_id>`.",
        },
        {
            "q": "What is LangGraphRuntime?",
            "a": "A graph-based agent runtime with conditional edges and checkpointing.",
        },
        {
            "q": "How is the documentation published?",
            "a": "GitHub Pages from the `docs/` directory via `.github/workflows/docs.yml`.",
        },
        {
            "q": "Can I use Voyage without LangGraph?",
            "a": "Yes, a pure-Python `simple_graph` fallback is included.",
        },
        {
            "q": "Where are events stored?",
            "a": "In SQLite `.voyage/events.db` and JSONL `.voyage/events.jsonl`.",
        },
    ]

    def __init__(
        self,
        journal: ProcessJournal,
        decision_log: DecisionLog,
        generator: TutorialGenerator | None = None,
    ) -> None:
        self.journal = journal
        self.decision_log = decision_log
        self.generator = generator or TutorialGenerator(journal, decision_log)

    def build_all(
        self,
        project_id: str = "default",
        output_dir: Path | str = Path("docs"),
    ) -> Path:
        """Собрать всю документацию."""
        out = Path(output_dir)
        out.mkdir(parents=True, exist_ok=True)

        self._write_config(out)
        self._write_index(out)
        self._write_readme_copy(out)
        self.build_tutorials(out)
        self.build_examples(project_id, out)
        self._write_architecture_decision_log(out)
        self._write_architecture_components(out)
        self.build_faq(out)

        return out

    def build_tutorial(
        self,
        correlation_id: str,
        output_dir: Path | str = Path("docs"),
        filename: str | None = None,
    ) -> Path:
        """Сгенерировать один tutorial файл."""
        out = Path(output_dir) / "tutorial"
        out.mkdir(parents=True, exist_ok=True)
        name = filename or f"{correlation_id}.md"
        path = out / name
        path.write_text(
            self.generator.generate_tutorial(correlation_id),
            encoding="utf-8",
        )
        return path

    def build_examples(
        self,
        project_id: str,
        output_dir: Path | str = Path("docs"),
    ) -> Path:
        """Создать example-директории (stub)."""
        out = Path(output_dir) / "examples"
        out.mkdir(parents=True, exist_ok=True)

        for name in ["auth-module", "api-endpoint", "refactor-legacy"]:
            example_dir = out / name
            example_dir.mkdir(parents=True, exist_ok=True)
            (example_dir / "TASK.md").write_text(
                f"# TASK: {name}\n\nExample task captured by Chronicler.\n",
                encoding="utf-8",
            )
            (example_dir / "CONTEXT.json").write_text(
                '{"name": "' + name + '"}\n',
                encoding="utf-8",
            )
            (example_dir / "README.md").write_text(
                f"# Example: {name}\n\nSee `TASK.md` and `CONTEXT.json`.\n",
                encoding="utf-8",
            )

        return out

    def build_faq(self, output_dir: Path | str = Path("docs")) -> Path:
        """Сгенерировать FAQ."""
        out = Path(output_dir)
        out.mkdir(parents=True, exist_ok=True)
        path = out / "FAQ.md"

        lines = [
            self._frontmatter("Frequently Asked Questions"),
            "# Frequently Asked Questions",
            "",
        ]
        for item in self.FAQ:
            lines.append(f"## {item['q']}")
            lines.append("")
            lines.append(item["a"])
            lines.append("")

        path.write_text("\n".join(lines), encoding="utf-8")
        return path

    def _write_config(self, output_dir: Path) -> Path:
        """Создать _config.yml для Jekyll."""
        path = output_dir / "_config.yml"
        path.write_text(
            "theme: minima\n"
            "title: Voyage Framework\n"
            "description: AI-Native Engineering Operating System\n"
            "baseurl: /Framework-voyage-mvp\n"
            "url: https://andreyvoyage.github.io\n",
            encoding="utf-8",
        )
        return path

    def _write_index(self, output_dir: Path) -> Path:
        """Создать docs/index.md с frontmatter."""
        path = output_dir / "index.md"
        content = (
            self._frontmatter("Voyage Framework Documentation")
            + "\n"
            + "# Voyage Framework Documentation\n\n"
            "[![CI](https://github.com/AndreyVoyage/Framework-voyage-mvp/"
            "actions/workflows/ci.yml/badge.svg)]"
            "(https://github.com/AndreyVoyage/Framework-voyage-mvp/actions/workflows/ci.yml)\n\n"
            "AI-Native Engineering Operating System for solo developers.\n\n"
            "## Table of Contents\n\n"
            "- [Tutorials](tutorial/)\n"
            "- [Examples](examples/)\n"
            "- [Architecture](architecture/)\n"
            "- [FAQ](FAQ)\n\n"
            "## Quick start\n\n"
            "```bash\n"
            "pip install -e .\n"
            "voyage init\n"
            'voyage run developer --task "Hello" --plan "echo hello"\n'
            "```\n\n"
        )
        path.write_text(content, encoding="utf-8")
        return path

    def _write_readme_copy(self, output_dir: Path) -> Path:
        """Скопировать README.md в docs/README.md."""
        path = output_dir / "README.md"
        readme_src = Path("README.md")
        if readme_src.exists():
            path.write_text(readme_src.read_text(encoding="utf-8"), encoding="utf-8")
        return path

    def _write_architecture_decision_log(self, output_dir: Path) -> Path:
        """Создать architecture/decision-log.md."""
        out = output_dir / "architecture"
        out.mkdir(parents=True, exist_ok=True)
        path = out / "decision-log.md"

        decisions = self.decision_log.get_decisions(project_id=self.journal.project_id)
        lines = [
            self._frontmatter("Decision Log"),
            "# Decision Log",
            "",
        ]
        if not decisions:
            lines.append("No decisions recorded yet.")
            lines.append("")
        for event in decisions:
            payload = event.payload
            lines.append(f"## {payload.get('context', 'Decision')}")
            lines.append("")
            lines.append(f"**Question:** {payload.get('question', '')}")
            lines.append("")
            lines.append(f"**Chosen:** {payload.get('chosen', '')}")
            lines.append("")
            lines.append(f"**Rationale:** {payload.get('rationale', '')}")
            lines.append("")

        path.write_text("\n".join(lines), encoding="utf-8")
        return path

    def _write_architecture_components(self, output_dir: Path) -> Path:
        """Создать architecture/components.md из публичного API."""
        out = output_dir / "architecture"
        out.mkdir(parents=True, exist_ok=True)
        path = out / "components.md"

        lines = [
            self._frontmatter("Components"),
            "# Voyage Framework Components",
            "",
            "Public API exported by `voyage_framework`:",
            "",
        ]
        import voyage_framework

        for name in sorted(voyage_framework.__all__):
            lines.append(f"- `{name}`")
        lines.append("")

        path.write_text("\n".join(lines), encoding="utf-8")
        return path

    def build_tutorials(self, output_dir: Path | str = Path("docs")) -> Path:
        """Сгенерировать tutorial-файлы для известных correlation_id."""
        out = Path(output_dir) / "tutorial"
        out.mkdir(parents=True, exist_ok=True)

        for filename, correlation_id in self.PHASE_TUTORIALS.items():
            path = out / f"{filename}.md"
            # Если шаги есть — генерируем из journal, иначе placeholder.
            steps = self.journal.get_steps(correlation_id=correlation_id, limit=1)
            if steps:
                path.write_text(
                    self.generator.generate_tutorial(correlation_id),
                    encoding="utf-8",
                )
            else:
                path.write_text(
                    self._phase_placeholder(filename),
                    encoding="utf-8",
                )

        return out

    @staticmethod
    def _frontmatter(title: str) -> str:
        return f"---\nlayout: default\ntitle: {title}\n---\n"

    @staticmethod
    def _phase_placeholder(filename: str) -> str:
        title = filename.split("-", maxsplit=1)[1].replace("-", " ").title()
        return (
            f"---\nlayout: default\ntitle: {title}\n---\n\n"
            f"# {title}\n\n"
            "Tutorial placeholder. Run the corresponding phase and use "
            "`voyage docs tutorial <correlation_id>` to generate live content.\n"
        )
