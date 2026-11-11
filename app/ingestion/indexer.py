from pathlib import Path
from typing import List, Tuple
import logging

from app.chunking.parser import StructureAwareLegalParser
from app.chunking.schema import ParentSection, ChildChunk
from app.embeddings.embedder import LegalEmbedder
from app.retrieval.vector_store import FAISSVectorStore
from app.retrieval.bm25_store import BM25LegalStore
from app.retrieval.parent_store import ParentSectionStore
from app.config.settings import settings

logger = logging.getLogger(__name__)


def build_all_indexes(
    raw_data_dir: Path = settings.RAW_DATA_DIR,
    index_dir: Path = settings.INDEX_DIR
) -> Tuple[int, int]:
    """Ingests raw legal files, creates parent sections and child chunks, and saves all indexes."""
    raw_data_dir = Path(raw_data_dir)
    index_dir = Path(index_dir)
    index_dir.mkdir(parents=True, exist_ok=True)

    parser = StructureAwareLegalParser()
    all_parents: List[ParentSection] = []
    all_children: List[ChildChunk] = []

    files = list(raw_data_dir.glob("**/*.txt")) + list(raw_data_dir.glob("**/*.pdf"))
    if not files:
        raise FileNotFoundError(f"No text or PDF files found in {raw_data_dir}")

    for f in sorted(files):
        parents, children = parser.parse_document(f)
        all_parents.extend(parents)
        all_children.extend(children)
        logger.info(f"Ingested {f.name}: {len(parents)} sections, {len(children)} child chunks")

    print(f"Total parsed: {len(all_parents)} parent sections, {len(all_children)} child chunks.")

    # 1. Parent Store
    parent_store = ParentSectionStore()
    parent_store.add_sections(all_parents)
    parent_store.save(index_dir)
    print("Saved Parent Section Store.")

    # 2. BM25 Store
    bm25_store = BM25LegalStore()
    bm25_store.add_chunks(all_children)
    bm25_store.save(index_dir)
    print("Saved BM25 Keyword Store.")

    # 3. Embeddings & FAISS Vector Store
    embedder = LegalEmbedder()
    chunk_texts = [ch.text for ch in all_children]
    print(f"Generating dense embeddings for {len(chunk_texts)} chunks...")
    embeddings = embedder.embed_texts(chunk_texts)

    vector_store = FAISSVectorStore(dimension=embedder.dimension)
    vector_store.add_chunks(all_children, embeddings)
    vector_store.save(index_dir)
    print("Saved FAISS Vector Store.")

    return len(all_parents), len(all_children)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    build_all_indexes()
