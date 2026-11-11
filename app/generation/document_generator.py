from typing import Dict, Any, Optional
from datetime import datetime


class LegalDocumentGenerator:
    """Generates practical Indian legal documents with clear draft markings and placeholders."""

    @classmethod
    def generate_security_deposit_notice(cls, facts: Dict[str, Any]) -> str:
        today = datetime.now().strftime("%d %B, %Y")
        tenant_name = facts.get("tenant_name", "[TENANT FULL NAME]")
        landlord_name = facts.get("landlord_name", "[LANDLORD FULL NAME]")
        property_address = facts.get("property_address", "[COMPLETE RENTED PREMISES ADDRESS]")
        deposit_amount = facts.get("deposit_amount", "[SECURITY DEPOSIT AMOUNT, e.g. Rs. 50,000/-]")
        vacation_date = facts.get("vacation_date", "[DATE OF VACATING, e.g. 31st October 2024]")
        monthly_rent = facts.get("monthly_rent", "[MONTHLY RENT, e.g. Rs. 20,000/-]")
        bank_details = facts.get("bank_details", "[BANK NAME, ACCOUNT NO., IFSC CODE]")

        notice = f"""*** DRAFT LEGAL DEMAND NOTICE — FOR CLIENT REVIEW ***
(Under Section 10 of the Model Tenancy Act, 2021 & Section 108 of the Transfer of Property Act, 1882)

BY REGISTERED POST WITH ACKNOWLEDGEMENT DUE / SPEED POST & EMAIL

Date: {today}

TO:
{landlord_name}
Residing at: [LANDLORD ADDRESS]
Contact / Email: [LANDLORD EMAIL / PHONE]

FROM:
{tenant_name}
Current Address: [TENANT CURRENT ADDRESS]
Contact / Email: [TENANT EMAIL / PHONE]

SUBJECT: FORMAL DEMAND NOTICE FOR THE IMMEDIATE REFUND OF SECURITY DEPOSIT OF {deposit_amount} IN RESPECT OF PREMISES LOCATED AT {property_address}.

Sir/Madam,

Under instructions and in terms of our tenancy relation, I hereby state as under:

1. That I was the lawful tenant in respect of the residential premises situated at {property_address} under a tenancy agreement, paying a monthly agreed rent of {monthly_rent}.

2. That at the inception of the tenancy, I deposited an interest-free refundable security deposit of {deposit_amount} with you, which was agreed to be refunded in full upon handing over peaceful and vacant possession of the premises.

3. That on {vacation_date}, I duly vacated the said premises and handed over peaceful and vacant possession along with the keys to you. All outstanding rent and utility bills (electricity, water, maintenance) up to the date of vacating were fully paid and cleared.

4. That upon inspection, the premises were in good, clean, and tenantable condition, subject only to ordinary wear and tear resulting from normal habitation. As per settled law and Section 108(m) of the Transfer of Property Act, 1882, as well as binding high court precedents, a tenant is not liable for normal wear and tear or customary repainting.

5. That in terms of Section 10(3) of the Model Tenancy Act, 2021, you were legally obligated to refund the security deposit within one month of vacating the premises. However, despite repeated requests, you have unlawfully withheld the refund without providing any legitimate itemized bills or receipts for actual damage.

6. TAKE NOTICE that you are hereby called upon to refund the entire security deposit of {deposit_amount} into my bank account ({bank_details}) within FIFTEEN (15) DAYS from the receipt of this notice, failing which I shall be constrained to initiate legal proceedings against you:
   (a) Before the Rent Authority / Rent Court for recovery of the deposit with statutory interest and costs;
   (b) Before the District Consumer Disputes Redressal Commission for deficiency of service and unfair trade practice; and/or
   (c) A civil summary suit under Order XXXVII of the Code of Civil Procedure, 1908.

In the event of such legal action, you shall be solely liable for all litigation expenses, advocate fees, and interest thereon.

Yours faithfully,


_________________________
{tenant_name}
(Complainant / Former Tenant)
"""
        return notice

    @classmethod
    def generate_rent_authority_complaint(cls, facts: Dict[str, Any]) -> str:
        today = datetime.now().strftime("%d %B, %Y")
        tenant_name = facts.get("tenant_name", "[TENANT FULL NAME]")
        landlord_name = facts.get("landlord_name", "[LANDLORD FULL NAME]")
        property_address = facts.get("property_address", "[RENTED PREMISES ADDRESS]")
        deposit_amount = facts.get("deposit_amount", "[AMOUNT]")

        complaint = f"""*** DRAFT PETITION / COMPLAINT BEFORE THE RENT AUTHORITY ***
(Under Section 10 / Section 20 / Section 30 of the Model Tenancy Act, 2021)

BEFORE THE HON'BLE RENT AUTHORITY AT [DISTRICT / CITY NAME]

APPLICATION NO. ________ OF 2024

IN THE MATTER OF:
{tenant_name}
... APPLICANT / TENANT

VERSUS

{landlord_name}
... RESPONDENT / LANDLORD

APPLICATION UNDER THE MODEL TENANCY ACT FOR RECOVERY OF UNLAWFULLY WITHHELD SECURITY DEPOSIT / RESTORATION OF ESSENTIAL SERVICES

MOST RESPECTFULLY SHOWETH:
1. That the Applicant was the bona fide tenant of Respondent in respect of property: {property_address}.
2. That an amount of {deposit_amount} was paid as advance security deposit.
3. That the Applicant vacated the premises on [DATE] after fulfilling all contractual obligations.
4. That the Respondent has failed to return the security deposit within thirty days as mandated under Section 10(3) of the Act.
5. That no notice of damage or itemized repairs was ever provided to the Applicant.

PRAYER:
It is therefore respectfully prayed that this Hon'ble Authority may be pleased to:
(a) Direct the Respondent to immediately refund the security deposit of {deposit_amount} along with interest @ 12% per annum from the date of vacation;
(b) Award damages and litigation costs to the Applicant;
(c) Pass any other order deemed fit in the interest of justice.

Date: {today}
Place: [CITY]                                     APPLICANT THROUGH COUNSEL
"""
        return complaint

    @classmethod
    def generate_maintenance_notice(cls, facts: Dict[str, Any]) -> str:
        today = datetime.now().strftime("%d %B, %Y")
        tenant_name = facts.get("tenant_name", "[TENANT FULL NAME]")
        landlord_name = facts.get("landlord_name", "[LANDLORD FULL NAME]")
        property_address = facts.get("property_address", "[PREMISES ADDRESS]")
        defect_details = facts.get("defect_details", "[DETAILS OF REPAIR, e.g. Major roof leakage / severe seepage / plumbing failure]")

        letter = f"""*** FORMAL COMMUNICATION FOR URGENT REPAIRS & MAINTENANCE ***
(Under Section 15 of Model Tenancy Act & Section 108(f) of Transfer of Property Act, 1882)

Date: {today}

To:
{landlord_name}

From:
{tenant_name}
Tenant at: {property_address}

Subject: URGENT NOTICE FOR STRUCTURAL REPAIRS AT {property_address}

Dear Landlord,

I am writing to formally bring to your attention urgent repairs required at the rented premises:
Description of Defect: {defect_details}

Under Section 15(2) of the Model Tenancy Act and the Second Schedule, structural maintenance, major plumbing, and waterproofing are the statutory responsibility of the landlord.

Please arrange for qualified repair personnel to inspect and rectify this within SEVEN (7) DAYS of this letter.
Kindly note that under Section 108(f) of the Transfer of Property Act, 1882, if a landlord neglects to carry out essential repairs within a reasonable time after notice, the tenant has the right to carry out the repairs and deduct the reasonable expense from subsequent rent payments.

Thanking you,

Yours sincerely,

_________________________
{tenant_name}
"""
        return letter

    @classmethod
    def generate_lawyer_fact_summary(cls, facts: Dict[str, Any]) -> str:
        today = datetime.now().strftime("%d %B, %Y")
        summary = f"""*** CASE FACT SHEET & CHRONOLOGY FOR ADVOCATE CONSULTATION ***
Date Prepared: {today}

1. PARTIES:
   • Client (Tenant): {facts.get("tenant_name", "[NAME]")} | Phone: [PHONE]
   • Opposite Party (Landlord): {facts.get("landlord_name", "[NAME]")} | Phone: [PHONE]

2. TENANCY DETAILS:
   • Premises: {facts.get("property_address", "[ADDRESS]")}
   • Agreed Rent: {facts.get("monthly_rent", "[RENT AMOUNT]")} per month
   • Security Deposit Paid: {facts.get("deposit_amount", "[DEPOSIT AMOUNT]")} (Mode of payment: Bank Transfer / UPI / Cheque)
   • Tenancy Agreement: [Registered / Notarized / Oral] Dated: [DATE]

3. CHRONOLOGY OF EVENTS:
   • Date of Notice to Vacate: [DATE]
   • Date of Handover of Possession: {facts.get("vacation_date", "[DATE]")}
   • Proof of Handover: [Keys delivery receipt / Email / Video recording]
   • Landlord's Refusal / Deductions Claimed: [DETAILS OF DEDUCTION, e.g. Claimed Rs. 30,000 for repainting]

4. APPLICABLE LEGAL CITATIONS TO RAISE:
   • Model Tenancy Act, 2021: Section 10(2) & 10(3) (30-day refund mandate)
   • Transfer of Property Act, 1882: Section 108(m) (Normal wear and tear exception)
   • High Court Precedents: Suresh Kumar v. Bhupinder Singh (Landlord cannot deduct for normal wear and tear without invoices)

5. RELIEF SOUGHT BY CLIENT:
   • Full refund of security deposit with interest @ 12% p.a.
   • Compensation for mental harassment and litigation costs.
"""
        return summary
