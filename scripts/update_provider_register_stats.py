#!/usr/bin/env python3
"""Generate an aggregate-only report from the public NDIS Commission Provider Register.

The script deliberately does not publish provider names, ABNs, contact details, or
row-level data. It downloads the public CSV, detects commonly used fields, reduces
rows to provider-level records where a stable provider key can be identified, and
writes a transparent JSON summary plus a human-readable Markdown report.

Source:
https://www.ndiscommission.gov.au/provider-registration/find-registered-provider
"""

from __future__ import annotations

import csv
import hashlib
import io
import json
import os
import re
import sys
import urllib.error
import urllib.request
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, Mapping, Sequence

SOURCE_PAGE = (
    "https://www.ndiscommission.gov.au/provider-registration/"
    "find-registered-provider"
)
SOURCE_CSV = f"{SOURCE_PAGE}/download-csv"
ROOT = Path(__file__).resolve().parents[1]
SUMMARY_PATH = ROOT / "data" / "provider-register-summary.json"
REPORT_PATH = ROOT / "PROVIDER_REGISTER_STATISTICS.md"

# Candidate names are normalised before matching: lowercase, punctuation removed.
FIELD_CANDIDATES: dict[str, Sequence[str]] = {
    "provider_id": (
        "providerregistrationnumber",
        "registrationnumber",
        "providerregistrationid",
        "registeredproviderid",
        "providerid",
        "registrationid",
    ),
    "legal_name": (
        "legalname",
        "providerlegalname",
        "registeredproviderlegalname",
        "organisationlegalname",
    ),
    "business_name": (
        "businessname",
        "providerbusinessname",
        "registeredproviderbusinessname",
        "tradingname",
    ),
    "abn": (
        "abn",
        "providernumberabn",
        "australianbusinessnumber",
    ),
    "status": (
        "registrationstatus",
        "providerregistrationstatus",
        "status",
    ),
    "state": (
        "state",
        "providerstate",
        "stateorterritory",
        "principalplaceofbusinessstate",
        "registeredaddressstate",
        "addressstate",
    ),
    "registration_group": (
        "registrationgroup",
        "registrationgroupname",
        "registrationgroupnumber",
        "registrationgrouporclassofsupport",
        "classofsupport",
        "supportclass",
    ),
    "audit_type": (
        "audittype",
        "typeofaudit",
        "auditpathway",
    ),
}

MAX_PUBLIC_CATEGORIES = 100


@dataclass(frozen=True)
class DownloadResult:
    content: bytes
    content_type: str | None
    last_modified: str | None
    etag: str | None


def normalise_header(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", value.casefold())


def clean(value: object) -> str:
    if value is None:
        return ""
    return re.sub(r"\s+", " ", str(value)).strip()


def download_csv() -> DownloadResult:
    request = urllib.request.Request(
        SOURCE_CSV,
        headers={
            "User-Agent": (
                "Mozilla/5.0 (compatible; DGTG-Provider-Register-Research/1.0; "
                "+https://github.com/softdevglobal/DGTG-COM)"
            ),
            "Accept": "text/csv,text/plain;q=0.9,*/*;q=0.1",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=90) as response:
            return DownloadResult(
                content=response.read(),
                content_type=response.headers.get("Content-Type"),
                last_modified=response.headers.get("Last-Modified"),
                etag=response.headers.get("ETag"),
            )
    except urllib.error.HTTPError as exc:
        body = exc.read(500).decode("utf-8", errors="replace")
        raise RuntimeError(
            f"Provider Register download failed with HTTP {exc.code}: {body}"
        ) from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Provider Register download failed: {exc}") from exc


def decode_csv(content: bytes) -> str:
    for encoding in ("utf-8-sig", "utf-8", "cp1252"):
        try:
            return content.decode(encoding)
        except UnicodeDecodeError:
            continue
    raise RuntimeError("Could not decode the Provider Register CSV")


def match_fields(headers: Sequence[str]) -> dict[str, str | None]:
    by_normalised = {normalise_header(header): header for header in headers}
    matches: dict[str, str | None] = {}
    for field, candidates in FIELD_CANDIDATES.items():
        matches[field] = next(
            (by_normalised[candidate] for candidate in candidates if candidate in by_normalised),
            None,
        )
    return matches


def make_provider_key(row: Mapping[str, str], fields: Mapping[str, str | None]) -> str:
    provider_id_field = fields.get("provider_id")
    if provider_id_field:
        value = clean(row.get(provider_id_field))
        if value:
            return f"id:{value.casefold()}"

    abn_field = fields.get("abn")
    if abn_field:
        digits = re.sub(r"\D", "", clean(row.get(abn_field)))
        if digits:
            return f"abn:{digits}"

    legal_field = fields.get("legal_name")
    business_field = fields.get("business_name")
    identity_parts = [
        clean(row.get(field)).casefold()
        for field in (legal_field, business_field)
        if field and clean(row.get(field))
    ]
    if identity_parts:
        # Hash the identity so no provider name is retained in the generated summary.
        digest = hashlib.sha256("|".join(identity_parts).encode("utf-8")).hexdigest()
        return f"namehash:{digest}"

    # No stable provider identifier was detected. Keep each row unique and disclose
    # this limitation in the methodology.
    row_digest = hashlib.sha256(
        json.dumps(dict(row), sort_keys=True, ensure_ascii=False).encode("utf-8")
    ).hexdigest()
    return f"row:{row_digest}"


def category_values(
    rows: Iterable[Mapping[str, str]], field: str | None
) -> set[str]:
    if not field:
        return set()
    return {clean(row.get(field)) for row in rows if clean(row.get(field))}


def sorted_counts(counter: Counter[str]) -> list[dict[str, object]]:
    return [
        {"label": label, "count": count}
        for label, count in sorted(counter.items(), key=lambda item: (-item[1], item[0]))[
            :MAX_PUBLIC_CATEGORIES
        ]
    ]


def render_table(items: Sequence[Mapping[str, object]], noun: str) -> str:
    if not items:
        return f"_The source file did not expose a reliable {noun} field._\n"
    lines = ["| Category | Provider count |", "|---|---:|"]
    for item in items:
        label = str(item["label"]).replace("|", "\\|")
        lines.append(f"| {label} | {int(item['count']):,} |")
    return "\n".join(lines) + "\n"


def generate_summary(download: DownloadResult) -> dict[str, object]:
    text = decode_csv(download.content)
    reader = csv.DictReader(io.StringIO(text))
    headers = [clean(header) for header in (reader.fieldnames or []) if clean(header)]
    if not headers:
        raise RuntimeError("Provider Register CSV has no header row")

    rows = [{header: clean(row.get(header)) for header in headers} for row in reader]
    if not rows:
        raise RuntimeError("Provider Register CSV contains no data rows")

    fields = match_fields(headers)
    providers: dict[str, list[Mapping[str, str]]] = defaultdict(list)
    for row in rows:
        providers[make_provider_key(row, fields)].append(row)

    provider_identity_basis = (
        "provider_id"
        if fields.get("provider_id")
        else "abn"
        if fields.get("abn")
        else "hashed_name"
        if fields.get("legal_name") or fields.get("business_name")
        else "row_only"
    )

    status_counts: Counter[str] = Counter()
    state_counts: Counter[str] = Counter()
    group_counts: Counter[str] = Counter()
    audit_counts: Counter[str] = Counter()

    for provider_rows in providers.values():
        statuses = category_values(provider_rows, fields.get("status"))
        states = category_values(provider_rows, fields.get("state"))
        groups = category_values(provider_rows, fields.get("registration_group"))
        audit_types = category_values(provider_rows, fields.get("audit_type"))

        # A provider should normally have one current status/state; if the public file
        # contains multiple values, count each association and disclose the method.
        status_counts.update(statuses)
        state_counts.update(states)
        group_counts.update(groups)
        audit_counts.update(audit_types)

    generated_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    summary: dict[str, object] = {
        "title": "NDIS Provider Register Statistics",
        "source_page": SOURCE_PAGE,
        "source_csv": SOURCE_CSV,
        "generated_at_utc": generated_at,
        "source_last_modified": download.last_modified,
        "source_etag": download.etag,
        "source_content_type": download.content_type,
        "source_sha256": hashlib.sha256(download.content).hexdigest(),
        "source_columns": headers,
        "detected_fields": fields,
        "identity_basis": provider_identity_basis,
        "source_row_count": len(rows),
        "aggregate_provider_count": len(providers),
        "counts": {
            "registration_status": sorted_counts(status_counts),
            "state_or_territory": sorted_counts(state_counts),
            "registration_group": sorted_counts(group_counts),
            "audit_type": sorted_counts(audit_counts),
        },
        "limitations": [
            "This is an independent aggregation of the public Provider Register, not an official NDIS Commission publication.",
            "Counts describe public register records and associations only; they do not measure participant demand, revenue, service capacity, application success rates, or provider quality.",
            "A provider associated with more than one registration group is counted once in each relevant group.",
            "The Commission source remains authoritative and may change between scheduled snapshots.",
            "No provider names, ABNs, contact details, or row-level records are published by this project.",
        ],
    }
    return summary


def write_outputs(summary: Mapping[str, object]) -> None:
    SUMMARY_PATH.parent.mkdir(parents=True, exist_ok=True)
    SUMMARY_PATH.write_text(
        json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )

    counts = summary["counts"]
    assert isinstance(counts, Mapping)
    status = counts.get("registration_status", [])
    states = counts.get("state_or_territory", [])
    groups = counts.get("registration_group", [])
    audits = counts.get("audit_type", [])

    generated = str(summary["generated_at_utc"])
    source_modified = summary.get("source_last_modified") or "Not supplied by source"
    identity_basis = str(summary["identity_basis"])

    report = f"""# NDIS Provider Register Statistics

**Independent public-data project maintained by DGTG Pty Ltd**  
**Snapshot generated:** {generated}  
**Official source:** [NDIS Quality and Safeguards Commission Provider Register]({SOURCE_PAGE})

This report automatically downloads the public NDIS Commission Provider Register CSV and publishes **aggregate statistics only**. It does not republish provider names, ABNs, contact details, or row-level records.

## Snapshot summary

| Measure | Count |
|---|---:|
| Source CSV rows | {int(summary['source_row_count']):,} |
| Aggregate provider identities detected | {int(summary['aggregate_provider_count']):,} |

Provider identity basis used by the script: `{identity_basis}`.  
Source `Last-Modified` header: `{source_modified}`.

## Registration status

{render_table(status if isinstance(status, Sequence) else [], 'registration-status')}

## State or territory

{render_table(states if isinstance(states, Sequence) else [], 'state-or-territory')}

## Registration groups or classes of support

A provider may appear in more than one group. These counts therefore describe provider-to-group associations and should not be added together to estimate a unique provider total.

{render_table(groups if isinstance(groups, Sequence) else [], 'registration-group')}

## Audit type

{render_table(audits if isinstance(audits, Sequence) else [], 'audit-type')}

## Methodology

1. The workflow downloads the public CSV linked from the Commission's Provider Register page.
2. Header names are detected without assuming a fixed schema.
3. Rows are reduced to provider-level records using, in order of preference: a public provider identifier, ABN, a non-reversible hash of available legal/business names, or a row-only fallback.
4. Status and state counts represent unique detected providers associated with each value.
5. Registration-group and audit-type counts represent unique detected providers associated with each category.
6. Only aggregate counts and source metadata are written to this repository.

The complete machine-readable aggregate summary is available at [`data/provider-register-summary.json`](data/provider-register-summary.json). The generator is [`scripts/update_provider_register_stats.py`](scripts/update_provider_register_stats.py).

## Important limitations

- This is an independent analysis, not an official NDIS Commission publication.
- The figures describe public register records. They do **not** measure participant demand, market revenue, service capacity, registration approval rates, processing times, or provider quality.
- The source may change after this snapshot. Always check the official register for current provider information.
- DGTG Pty Ltd and NDIS Provider Registration are not affiliated with or endorsed by the NDIA or the NDIS Quality and Safeguards Commission.

## Registration guidance and free resources

- [NDIS Provider Registration — Complete Australian Guide](https://ndisproviderregistration.au/ndis-provider-registration)
- [NDIS Provider Registration Checklist 2026](https://ndisproviderregistration.au/ndis-registration-checklist-2026)
- [NDIS Registration Groups Explained](https://ndisproviderregistration.au/ndis-registration-groups)
- [NDIS Registration Cost Guide](https://ndisproviderregistration.au/ndis-registration-cost)
- [NDIS Provider Audit Guide](https://ndisproviderregistration.au/ndis-provider-audit)

## Citation and media contact

Journalists, researchers, advisers, and sector organisations may cite this aggregate analysis with attribution to **NDIS Provider Registration / DGTG Pty Ltd** and a link to this report or to [ndisproviderregistration.au](https://ndisproviderregistration.au).

Contact: **Sarch Gurusinghe** — [sarch@rhodiumit.com.au](mailto:sarch@rhodiumit.com.au) — 03 5911 1456.
"""
    REPORT_PATH.write_text(report, encoding="utf-8")


def main() -> int:
    try:
        download = download_csv()
        summary = generate_summary(download)
        write_outputs(summary)
    except Exception as exc:  # noqa: BLE001 - CLI must report all failures clearly.
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    print(
        "Generated aggregate report: "
        f"{summary['aggregate_provider_count']} provider identities from "
        f"{summary['source_row_count']} source rows"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
