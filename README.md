# NDIS Provider Registration Resources

DGTG Pty Ltd maintains independent Australian resources for businesses preparing for NDIS provider registration.

## Practical guides

- [NDIS Provider Registration — Complete Australian Guide](https://ndisproviderregistration.au/ndis-provider-registration)
- [NDIS Provider Registration Checklist 2026](https://ndisproviderregistration.au/ndis-registration-checklist-2026)
- [NDIS Registration Groups Explained](https://ndisproviderregistration.au/ndis-registration-groups)
- [NDIS Registration Cost](https://ndisproviderregistration.au/ndis-registration-cost)
- [NDIS Provider Audit Guide](https://ndisproviderregistration.au/ndis-provider-audit)
- [SIL 0138 Registration Checklist 2026](https://ndisproviderregistration.au/sil-0138-registration-checklist)
- [Free National Webinar: Starting as an NDIS Provider](https://ndisproviderregistration.au/free-ndis-provider-readiness-webinar)

These resources cover registration scoping, self-assessment preparation, policies and procedures, verification or certification audit preparation, and ongoing compliance considerations.

## Media and expert-source information

Journalists, professional associations, advisers and community organisations can use the [media and expert resources page](MEDIA_AND_EXPERT_RESOURCES.md) for commentary topics, attribution wording, public resources, editorial safeguards and contact details.

## Provider Register analysis project

This repository contains a reproducible, aggregate-only analysis pipeline for the public NDIS Quality and Safeguards Commission Provider Register.

- [Analysis generator](scripts/update_provider_register_stats.py)
- [Manual GitHub Actions workflow](.github/workflows/update-provider-register-statistics.yml)
- [Official NDIS Commission Provider Register](https://www.ndiscommission.gov.au/provider-registration/find-registered-provider)

**Current status:** the official dynamically generated CSV endpoint did not deliver data to the automated GitHub runner during repeated tests in August 2026. No aggregate report or statistics have been published, and no figures should be attributed to this project yet. The workflow is manual-only until a reliable official data route is available.

The project is designed not to republish provider names, ABNs, contact details or row-level records. Any future output will disclose its source, methodology and limitations.

## Independence

NDIS Provider Registration is an independent service operated by DGTG Pty Ltd and is not affiliated with or endorsed by the NDIA or the NDIS Quality and Safeguards Commission. Registration decisions are made by the NDIS Quality and Safeguards Commission. The Commission's public register remains the authoritative source for current provider information.
