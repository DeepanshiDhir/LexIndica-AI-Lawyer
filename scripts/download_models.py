import os
import sys
from pathlib import Path

# Fix macOS duplicate libomp
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

# Ensure project root in sys.path
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from sentence_transformers import SentenceTransformer, CrossEncoder
from app.config.settings import settings


def download_all_models():
    print("=" * 60)
    print("📥 DOWNLOADING LOCAL MODELS FOR INDIAN LEGAL AI")
    print("=" * 60)

    # 1. Embedding Model (BAAI/bge-m3)
    emb_name = settings.EMBEDDING_MODEL
    print(f"\n1. Downloading Embedding Model: '{emb_name}' (~2.2 GB)...")
    print("   (This runs locally on your Mac M4 for dense legal retrieval)\n")
    try:
        emb_model = SentenceTransformer(emb_name, device=settings.EMBEDDING_DEVICE)
        print(f"   ✅ '{emb_name}' downloaded & verified! (Dimension: {emb_model.get_sentence_embedding_dimension()})")
    except Exception as e:
        print(f"   ❌ Error downloading {emb_name}: {e}")
        return

    # 2. Cross-Encoder Reranker
    rerank_name = settings.RERANKER_MODEL
    print(f"\n2. Downloading Cross-Encoder Reranker: '{rerank_name}' (~80 MB)...")
    try:
        rerank_model = CrossEncoder(rerank_name, max_length=512)
        print(f"   ✅ '{rerank_name}' downloaded & verified!")
    except Exception as e:
        print(f"   ⚠️ Could not download cross-encoder: {e}")

    # 3. Rebuild indexes with real embeddings
    print("\n3. Building FAISS vector store with the downloaded model...")
    from app.ingestion.indexer import build_all_indexes
    parents_count, chunks_count = build_all_indexes()
    print(f"   ✅ Built FAISS & BM25 indexes with {chunks_count} chunks.")

    print("\n" + "=" * 60)
    print("🎉 All local models downloaded and knowledge base indexed successfully!")
    print("=" * 60)


if __name__ == "__main__":
    download_all_models()
