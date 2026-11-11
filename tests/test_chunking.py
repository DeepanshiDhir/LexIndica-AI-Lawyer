from pathlib import Path
from app.chunking.parser import StructureAwareLegalParser
from app.chunking.schema import DocumentType


def test_structure_aware_chunking():
    parser = StructureAwareLegalParser(target_chunk_tokens=300, overlap_tokens=40)
    test_file = Path("data/raw/central/model_tenancy_act_2021.txt")
    assert test_file.exists(), "Model Tenancy Act raw file must exist"

    parents, children = parser.parse_document(test_file)

    # Assert parent sections extracted
    assert len(parents) > 5
    assert len(children) >= len(parents)

    # Check parent section 10 (Security Deposit)
    sec_10_parents = [p for p in parents if "Section 10" in (p.section_number or p.title)]
    assert len(sec_10_parents) == 1
    p10 = sec_10_parents[0]
    assert "Security Deposit" in p10.title
    assert p10.metadata.act_name == "Model Tenancy Act, 2021"
    assert p10.metadata.jurisdiction == "Central"
    assert p10.metadata.is_verified is True

    # Check that child chunks preserve parent_section_id
    for ch in children:
        assert ch.parent_section_id is not None
        assert len(ch.parent_section_id) > 0
        assert ch.token_count > 0
        assert ch.metadata.act_name == "Model Tenancy Act, 2021"
