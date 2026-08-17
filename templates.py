"""
One underlying pitch (fragmentation -> consolidation), with a sector-specific
opening line. Everything else in the body stays constant across industries.
Edit freely -- this is your actual pitch copy.
"""

SUBJECT = "One platform behind everything {company} shows the world"

OPENERS = {
    "healthcare": (
        "Most healthcare platforms run their careers page, patient portal, "
        "partner network, and support desk on four unrelated tools -- and "
        "the same patient shows up as four disconnected records."
    ),
    "fintech": (
        "Most fintechs run onboarding, the partner/API portal, compliance "
        "content, and support on separate stacks -- so the same customer "
        "is a lead, an applicant, and a ticket, with no shared identity."
    ),
    "saas_tech": (
        "Most SaaS companies run their marketing site, docs, customer "
        "portal, and partner program on different tools that don't share "
        "a customer record -- so product, support, and sales all see a "
        "different version of the same user."
    ),
    "manufacturing": (
        "Most manufacturers run their product catalogue, dealer/partner "
        "portal, and service desk on separate systems -- so a spec change "
        "has to be re-entered in three places, and drifts within weeks."
    ),
    "retail_ecom": (
        "Most retail brands run their storefront, loyalty program, and "
        "support desk on disconnected tools -- so the same shopper looks "
        "like three different people depending on which system you check."
    ),
    "general": (
        "Most growing companies run their careers site, customer portal, "
        "partner network, and support desk on 12-20 disconnected tools -- "
        "each with its own login, data model, and contract."
    ),
}

BODY_TEMPLATE = """Hi {name},

{opener}

Nexus consolidates every outward-facing surface -- public web, customer portal, partner network, careers, support -- onto one platform: one identity graph, one content spine, one workflow engine, one analytics plane.

Worth a 15-minute conversation to see if this maps onto what {company} is dealing with?

Best,
Dipankar Mandal
UElement Technologies
"""


def render(contact: dict) -> tuple:
    sector = contact.get("sector") or "general"
    opener = OPENERS.get(sector, OPENERS["general"])
    subject = SUBJECT.format(company=contact.get("company") or "your team")
    body = BODY_TEMPLATE.format(
        name=(contact.get("name") or "there").split()[0] if contact.get("name") else "there",
        opener=opener,
        company=contact.get("company") or "your team",
    )
    return subject, body
