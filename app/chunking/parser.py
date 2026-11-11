import re
from pathlib import Path
from typing import List, Tuple, Dict, Any, Optional
import pypdf

from app.chunking.schema import LegalMetadata, ParentSection, ChildChunk, DocumentType


def approximate_token_count(text: str) -> int:
    """Approximate tokens based on whitespace and punctuation."""
    words = text.strip().split()
    # Average token-to-word ratio in English legal text is ~1.3
    return int(len(words) * 1.3)


class StructureAwareLegalParser:
    def __init__(self, target_chunk_tokens: int = 380, overlap_tokens: int = 50):
        self.target_chunk_tokens = target_chunk_tokens
        self.overlap_tokens = overlap_tokens
        # Target words equivalent
        self.target_chunk_words = int(target_chunk_tokens / 1.3)
        self.overlap_words = int(overlap_tokens / 1.3)

    def parse_pdf(self, pdf_path: Path) -> str:
        """Extract text from PDF file."""
        reader = pypdf.PdfReader(str(pdf_path))
        pages_text = []
        for i, page in enumerate(reader.pages):
            text = page.extract_text() or ""
            pages_text.append(text)
        return "\n\n".join(pages_text)

    def parse_metadata_header(self, text: str) -> Tuple[Dict[str, str], str]:
        """Extract metadata key-value pairs from top of text file."""
        lines = text.splitlines()
        meta = {}
        body_lines = []
        in_header = True

        for line in lines:
            trimmed = line.strip()
            if in_header:
                if trimmed.startswith("# METADATA"):
                    continue
                elif trimmed.startswith("#") and ":" in trimmed:
                    raw_kv = trimmed.lstrip("#").strip()
                    k, v = raw_kv.split(":", 1)
                    meta[k.strip().lower()] = v.strip()
                elif trimmed == "---" or (not trimmed.startswith("#") and trimmed != ""):
                    in_header = False
                    body_lines.append(line)
            else:
                body_lines.append(line)

        return meta, "\n".join(body_lines)

    def parse_document(self, file_path: Path) -> Tuple[List[ParentSection], List[ChildChunk]]:
        """Parses a legal document file into parent sections and child chunks."""
        file_path = Path(file_path)
        if file_path.suffix.lower() == ".pdf":
            raw_text = self.parse_pdf(file_path)
            meta = {
                "act_name": file_path.stem.replace("_", " ").title(),
                "document_type": DocumentType.CENTRAL_ACT.value,
                "jurisdiction": "Central",
                "state": "All",
                "source_url": f"file://{file_path.name}"
            }
            body = raw_text
        else:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
            meta, body = self.parse_metadata_header(content)

        act_name = meta.get("act_name", file_path.stem.replace("_", " ").title())
        doc_type = meta.get("document_type", DocumentType.CENTRAL_ACT.value)
        jurisdiction = meta.get("jurisdiction", "Central")
        state = meta.get("state", "All")
        authority = meta.get("authority", "Official Authority")
        source_url = meta.get("source_url", f"https://indiacode.nic.in/{file_path.name}")
        effective_date = meta.get("effective_date", None)
        language = meta.get("language", "English")

        # Split into chapters or sections
        # Sections are marked by '### SECTION:' or 'Section X'
        section_blocks = self._split_into_sections(body)
        
        parent_sections: List[ParentSection] = []
        child_chunks: List[ChildChunk] = []

        for sec_data in section_blocks:
            chapter = sec_data.get("chapter", "")
            sec_num = sec_data.get("section_number", "")
            sec_title = sec_data.get("title", f"Section {sec_num}")
            sec_text = sec_data.get("text", "").strip()

            if not sec_text:
                continue

            sec_id = f"{self._slugify(act_name)}_{self._slugify(sec_num or sec_title)}"
            
            # Create base metadata for parent
            parent_meta = LegalMetadata(
                document_id=sec_id,
                document_title=f"{act_name} - {sec_title}",
                document_type=doc_type,
                act_name=act_name,
                chapter=chapter,
                section_number=sec_num,
                jurisdiction=jurisdiction,
                state=state,
                language=language,
                effective_date=effective_date,
                source_url=source_url,
                authority_info=authority,
                is_verified=True,
            )

            parent_sec = ParentSection(
                section_id=sec_id,
                act_name=act_name,
                chapter=chapter,
                section_number=sec_num,
                title=sec_title,
                full_text=sec_text,
                metadata=parent_meta,
                child_chunk_ids=[]
            )

            # Chunk the section text into child chunks
            sec_child_chunks = self._chunk_section_text(sec_text, parent_sec)
            for ch in sec_child_chunks:
                parent_sec.child_chunk_ids.append(ch.chunk_id)
                child_chunks.append(ch)

            parent_sections.append(parent_sec)

        return parent_sections, child_chunks

    def _split_into_sections(self, text: str) -> List[Dict[str, str]]:
        """Split text by Section headers or markdown delimiter blocks."""
        # Split on markdown dividers '---' or headers
        raw_parts = re.split(r'\n---\n', text)
        sections = []

        current_chapter = ""
        for part in raw_parts:
            part = part.strip()
            if not part:
                continue

            # Check if this part contains CHAPTER header
            chap_match = re.search(r'##\s*CHAPTER:\s*(.+)', part)
            if chap_match:
                current_chapter = chap_match.group(1).strip()

            # Check if this part contains SECTION header
            sec_match = re.search(r'###\s*SECTION:\s*(.+)', part)
            if sec_match:
                full_sec_header = sec_match.group(1).strip()
                # Parse section number and title (e.g., 'Section 10 - Security Deposit' or 'Precedent - Suresh Kumar')
                num_match = re.search(r'(Section\s+[0-9A-Za-z\(\)]+|Precedent|Guidance)(?:\s*-\s*(.+))?', full_sec_header, re.IGNORECASE)
                if num_match:
                    sec_num = num_match.group(1).strip()
                    sec_title = full_sec_header
                else:
                    sec_num = full_sec_header
                    sec_title = full_sec_header

                # Remove header lines from text
                body_lines = [l for l in part.splitlines() if not l.startswith("## ") and not l.startswith("### ")]
                sec_text = "\n".join(body_lines).strip()

                sections.append({
                    "chapter": current_chapter,
                    "section_number": sec_num,
                    "title": sec_title,
                    "text": sec_text
                })
            else:
                # If no explicit markdown header, check regex for 'Section X'
                fallback_match = re.search(r'^(Section\s+[0-9A-Za-z]+)\.?\s*(.*)', part, re.MULTILINE | re.IGNORECASE)
                if fallback_match:
                    sec_num = fallback_match.group(1).strip()
                    sec_title = fallback_match.group(0).strip()
                    sections.append({
                        "chapter": current_chapter,
                        "section_number": sec_num,
                        "title": sec_title,
                        "text": part
                    })
                elif len(part) > 50:
                    # Generic section block
                    sections.append({
                        "chapter": current_chapter,
                        "section_number": "General",
                        "title": "General Provisions",
                        "text": part
                    })

        return sections

    def _chunk_section_text(self, text: str, parent: ParentSection) -> List[ChildChunk]:
        """Split a section's text into child chunks of 300-500 tokens with overlap."""
        words = text.split()
        if len(words) <= self.target_chunk_words:
            # Entire section fits in 1 child chunk
            token_count = approximate_token_count(text)
            chunk_id = f"{parent.section_id}_c0"
            chunk_meta = parent.metadata.model_copy(update={
                "document_id": chunk_id,
                "parent_document_id": parent.section_id,
            })
            return [
                ChildChunk(
                    chunk_id=chunk_id,
                    parent_section_id=parent.section_id,
                    act_name=parent.act_name,
                    section_number=parent.section_number,
                    chunk_index=0,
                    text=f"[{parent.act_name} | {parent.title}]\n{text}",
                    token_count=token_count,
                    metadata=chunk_meta,
                )
            ]

        # Multi-chunk splitting with overlap within section
        chunks = []
        start = 0
        idx = 0
        while start < len(words):
            end = min(start + self.target_chunk_words, len(words))
            chunk_words = words[start:end]
            chunk_str = " ".join(chunk_words)
            token_count = approximate_token_count(chunk_str)

            chunk_id = f"{parent.section_id}_c{idx}"
            chunk_meta = parent.metadata.model_copy(update={
                "document_id": chunk_id,
                "parent_document_id": parent.section_id,
            })

            chunks.append(
                ChildChunk(
                    chunk_id=chunk_id,
                    parent_section_id=parent.section_id,
                    act_name=parent.act_name,
                    section_number=parent.section_number,
                    chunk_index=idx,
                    text=f"[{parent.act_name} | {parent.title} (Part {idx + 1})]\n{chunk_str}",
                    token_count=token_count,
                    metadata=chunk_meta,
                )
            )

            idx += 1
            if end >= len(words):
                break
            # Advance with overlap
            start += max(1, self.target_chunk_words - self.overlap_words)

        return chunks

    def _slugify(self, text: str) -> str:
        s = re.sub(r'[^a-zA-Z0-9]+', '_', text.strip().lower())
        return s.strip('_')[:40]
