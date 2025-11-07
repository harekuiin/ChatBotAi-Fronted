"""Script utilitario para cargar contenidos locales en MongoDB como base de conocimiento."""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path
from typing import Iterable, List, Sequence, Set

from app.config import settings
from app.database import mongodb_service
from app.document_processor import DocumentProcessor


DEFAULT_EXTENSIONS: Sequence[str] = (".md", ".txt", ".svg")
EXCLUDED_DIRECTORIES: Set[str] = {"data", "models", "node_modules", "__pycache__"}


def configure_logging(verbose: bool) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(level=level, format="[%(levelname)s] %(message)s")


def discover_files(root: Path, extensions: Iterable[str]) -> List[Path]:
    exts = {ext.lower() for ext in extensions}
    collected: List[Path] = []

    for path in root.rglob("*"):
        if not path.is_file():
            continue

        if any(part in EXCLUDED_DIRECTORIES for part in path.parts):
            continue

        if path.suffix.lower() in exts:
            collected.append(path)

    return collected


def ingest_file(file_path: Path, source_root: Path) -> bool:
    try:
        content = DocumentProcessor.process_file(str(file_path))
    except Exception as exc:  # pylint: disable=broad-except
        logging.warning("No se pudo procesar %s: %s", file_path, exc)
        return False

    if not content or not content.strip():
        logging.debug("Contenido vacío en %s, se omite", file_path)
        return False

    relative_path = file_path.relative_to(source_root)
    metadata = {
        "filename": file_path.name,
        "source_path": str(file_path.resolve()),
        "relative_path": str(relative_path).replace("\\", "/"),
        "directory": "bd_a_imlementar",
        "tags": list(relative_path.parts[:-1]),
        "ingest_tool": "load_knowledge.py",
    }

    doc_id = metadata["relative_path"]
    stored_id = mongodb_service.upsert_knowledge_document(doc_id, content, metadata)
    if stored_id:
        logging.info("Documento almacenado: %s", stored_id)
        return True

    return False


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Carga archivos locales en la colección de conocimiento de MongoDB"
    )
    parser.add_argument(
        "--source",
        type=Path,
        default=Path("..") / "BD_a_imlementar",
        help="Ruta base desde la cual se leerán los documentos (default: ../BD_a_imlementar)",
    )
    parser.add_argument(
        "--extensions",
        nargs="*",
        default=list(DEFAULT_EXTENSIONS),
        help="Extensiones permitidas para ingesta (default: .md .txt .svg)",
    )
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Vacía la colección de conocimiento antes de cargar nuevos documentos",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Muestra información detallada de depuración",
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str]) -> int:
    args = parse_args(argv)
    configure_logging(args.verbose)

    source_path = args.source.resolve()
    if not source_path.exists() or not source_path.is_dir():
        logging.error("La ruta especificada no existe o no es un directorio: %s", source_path)
        return 1

    logging.info("Usando fuente de conocimiento: %s", source_path)

    if not mongodb_service.connect():
        logging.error("No se pudo conectar a MongoDB con la configuración actual (%s)", settings.mongodb_url)
        return 1

    if args.reset:
        mongodb_service.clear_knowledge_documents()

    files = discover_files(source_path, args.extensions)
    if not files:
        logging.warning("No se encontraron archivos con las extensiones especificadas")
        return 0

    stored = 0
    for file_path in files:
        if ingest_file(file_path, source_path):
            stored += 1

    logging.info("Documentos procesados: %s | Documentos almacenados: %s", len(files), stored)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

