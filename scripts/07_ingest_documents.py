"""Parse and store the synthetic maintenance manual."""

from __future__ import annotations

from _bootstrap import bootstrap

ROOT = bootstrap()

from maintenance_investigator.clients.local_repository import LocalRepository
from maintenance_investigator.contextualization.document_linking import parse_manual
from maintenance_investigator.ingestion import ingest_documents


def main() -> None:
    repository = LocalRepository(ROOT)
    document = parse_manual(repository.load_manual_text())
    ingest_documents(repository, [document])
    print(f"Stored {document.external_id} with {len(document.sections)} sections.")


if __name__ == "__main__":
    main()
