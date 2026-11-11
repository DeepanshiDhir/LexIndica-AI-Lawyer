from app.generation.document_generator import LegalDocumentGenerator


def test_security_deposit_notice_generation():
    facts = {
        "tenant_name": "Arun Kumar",
        "landlord_name": "Suresh Raina",
        "property_address": "Flat 101, Palm Meadows, Whitefield, Bengaluru",
        "deposit_amount": "Rs. 75,000/-",
        "monthly_rent": "Rs. 25,000/-",
        "vacation_date": "30th September 2024",
        "bank_details": "ICICI Bank A/c 123456789, IFSC: ICIC0001234"
    }

    doc = LegalDocumentGenerator.generate_security_deposit_notice(facts)

    assert "DRAFT LEGAL DEMAND NOTICE" in doc
    assert "Arun Kumar" in doc
    assert "Suresh Raina" in doc
    assert "Rs. 75,000/-" in doc
    assert "FIFTEEN (15) DAYS" in doc
    assert "Section 10 of the Model Tenancy Act, 2021" in doc
    assert "Section 108(m) of the Transfer of Property Act, 1882" in doc


def test_maintenance_notice_generation():
    facts = {
        "tenant_name": "Pooja Verma",
        "landlord_name": "Anil Kapoor",
        "property_address": "House 45, Sector 15, Noida",
        "defect_details": "Severe plumbing pipe rupture leaking water continuously"
    }

    doc = LegalDocumentGenerator.generate_maintenance_notice(facts)

    assert "FORMAL COMMUNICATION FOR URGENT REPAIRS" in doc
    assert "Pooja Verma" in doc
    assert "Severe plumbing pipe rupture" in doc
    assert "Section 15 of Model Tenancy Act" in doc
    assert "Section 108(f)" in doc


def test_rent_authority_complaint_generation():
    facts = {
        "tenant_name": "Deepak Mehta",
        "landlord_name": "Harish Patel",
        "property_address": "Flat 3B, Bandra West, Mumbai",
        "deposit_amount": "Rs. 1,00,000/-"
    }

    doc = LegalDocumentGenerator.generate_rent_authority_complaint(facts)

    assert "BEFORE THE HON'BLE RENT AUTHORITY" in doc
    assert "Deepak Mehta" in doc
    assert "Harish Patel" in doc
    assert "Rs. 1,00,000/-" in doc
