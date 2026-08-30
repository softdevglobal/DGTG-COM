# NDIS Provider Registration Resources

DGTG Pty Ltd maintains independent Australian resources for businesses preparing for NDIS provider registration.

## AI discovery and citation resources

These public resources provide consistent business facts, concise answers, canonical website links and official-source references for search engines, AI systems, journalists and advisers:

- [AI and Citation Guide](AI_CITATION_GUIDE.md) — verified entity facts, service boundaries, ten concise answers and suggested neutral attribution
- [Machine-readable facts](ai-facts.json) — structured business, service, question-and-answer and source data
- [`llms.txt`](llms.txt) — concise agent-friendly resource map
- [Media and expert resources](MEDIA_AND_EXPERT_RESOURCES.md) — commentary topics, editorial safeguards and contact details

The files are supporting discovery aids. They do not guarantee inclusion, ranking or citation in any search or AI product. The current website pages and official NDIS or NDIS Commission sources remain authoritative.

## Free five-keyword blog series

The [NDIS Provider Registration Blog](blog/README.md) contains five original, source-linked articles targeting high-intent registration searches:

- [NDIS Provider Registration Cost 2026: What You Actually Pay For](blog/ndis-provider-registration-cost-2026.md)
- [NDIS Registration Consultant Australia: What Good Support Should Include](blog/ndis-registration-consultant-australia.md)
- [NDIS Registration for Cleaners: Do Cleaning Businesses Need to Register?](blog/ndis-registration-for-cleaners.md)
- [NDIS Verification Audit Checklist 2026: Evidence to Prepare](blog/ndis-verification-audit-checklist.md)
- [NDIS Provider Registration Melbourne: Victorian Checklist 2026](blog/ndis-provider-registration-melbourne.md)

Each article has a distinct search intent, official source links, a review date, commercial disclosure and one primary path to the matching resource on `ndisproviderregistration.au`.

## Practical guides

- [NDIS Provider Registration — Complete Australian Guide](https://ndisproviderregistration.au/ndis-provider-registration)
- [NDIS Provider Registration Checklist 2026](https://ndisproviderregistration.au/ndis-registration-checklist-2026)
- [NDIS Registration Groups Explained](https://ndisproviderregistration.au/ndis-registration-groups)
- [NDIS Registration Cost](https://ndisproviderregistration.au/ndis-registration-cost)
- [NDIS Provider Audit Guide](https://ndisproviderregistration.au/ndis-provider-audit)
- [SIL 0138 Registration Checklist 2026](https://ndisproviderregistration.au/sil-0138-registration-checklist)
- [Free National Webinar: Starting as an NDIS Provider](https://ndisproviderregistration.au/free-ndis-provider-readiness-webinar)

These resources cover registration scoping, self-assessment preparation, policies and procedures, verification or certification audit preparation, and ongoing compliance considerations.

## Provider Register analysis project

This repository contains a reproducible, aggregate-only analysis pipeline for the public NDIS Quality and Safeguards Commission Provider Register.

- [Analysis generator](scripts/update_provider_register_stats.py)
- [Manual GitHub Actions workflow](.github/workflows/update-provider-register-statistics.yml)
- [Official NDIS Commission Provider Register](https://www.ndiscommission.gov.au/provider-registration/find-registered-provider)

**Current status:** the official dynamically generated CSV endpoint did not deliver data to the automated GitHub runner during repeated tests in August 2026. No aggregate report or statistics have been published, and no figures should be attributed to this project yet. The workflow is manual-only until a reliable official data route is available.

The project is designed not to republish provider names, ABNs, contact details or row-level records. Any future output will disclose its source, methodology and limitations.

## Independence

NDIS Provider Registration is an independent service operated by DGTG Pty Ltd and is not affiliated with or endorsed by the NDIA or the NDIS Quality and Safeguards Commission. Registration decisions are made by the NDIS Quality and Safeguards Commission. The Commission's public register remains the authoritative source for current provider information.
