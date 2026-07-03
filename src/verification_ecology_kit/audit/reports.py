"""Shared audit reports and aggregate audit engine."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any

from verification_ecology_kit.canonicalization import Canonicalizer
from verification_ecology_kit.digest import DigestPolicy
from verification_ecology_kit.model.aperture import Aperture
from verification_ecology_kit.model.ecology_state import VerifierEcologyState
from verification_ecology_kit.model.packets import VerifierPacket


@dataclass(frozen=True)
class AuditFinding:
    code: str
    message: str
    severity: str = "medium"
    evidence_refs: tuple[str, ...] = ()
    suggested_repair_hooks: tuple[str, ...] = ()


@dataclass
class AuditReport:
    audit_name: str
    decision: str
    findings: list[AuditFinding] = field(default_factory=list)
    passed_checks: list[str] = field(default_factory=list)
    residualized_failures: list[str] = field(default_factory=list)
    support_blocking_failures: list[str] = field(default_factory=list)
    evidence_refs: list[str] = field(default_factory=list)
    provenance: list[str] = field(default_factory=list)
    report_digest: str = ""

    def finalize(self) -> AuditReport:
        payload = self.to_dict(include_digest=False)
        self.report_digest = (
            DigestPolicy().digest_json(payload, canonicalizer=Canonicalizer()).value
        )
        return self

    def to_dict(self, *, include_digest: bool = True) -> dict[str, Any]:
        data: dict[str, Any] = {
            "audit_name": self.audit_name,
            "decision": self.decision,
            "findings": [
                {
                    "code": finding.code,
                    "message": finding.message,
                    "severity": finding.severity,
                    "evidence_refs": list(finding.evidence_refs),
                    "suggested_repair_hooks": list(finding.suggested_repair_hooks),
                }
                for finding in self.findings
            ],
            "passed_checks": self.passed_checks,
            "residualized_failures": self.residualized_failures,
            "support_blocking_failures": self.support_blocking_failures,
            "evidence_refs": self.evidence_refs,
            "provenance": self.provenance,
        }
        if include_digest:
            data["report_digest"] = self.report_digest
        return data

    def to_json(self) -> str:
        self.finalize()
        return json.dumps(self.to_dict(), indent=2, sort_keys=True)

    def to_markdown(self) -> str:
        self.finalize()
        lines = [f"# {self.audit_name}", "", f"Decision: `{self.decision}`", ""]
        if not self.findings:
            lines.append("No findings.")
        for finding in self.findings:
            lines.append(f"- `{finding.code}` {finding.severity}: {finding.message}")
        lines.extend(["", f"Report digest: `{self.report_digest}`"])
        return "\n".join(lines)


class AuditEngine:
    def packet_ecology(self, packets: list[VerifierPacket]) -> AuditReport:
        from verification_ecology_kit.audit.packet_ecology import audit_packet_ecology

        return audit_packet_ecology(packets)

    def residual_metabolism(self, state: VerifierEcologyState) -> AuditReport:
        from verification_ecology_kit.audit.residual_metabolism import audit_residual_metabolism

        return audit_residual_metabolism(state)

    def aperture_regression(self, before: Aperture, after: Aperture) -> AuditReport:
        from verification_ecology_kit.audit.aperture_regression import audit_aperture_regression

        return audit_aperture_regression(before, after)
