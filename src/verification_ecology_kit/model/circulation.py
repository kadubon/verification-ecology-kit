"""External packet circulation and local sovereignty checks."""

from __future__ import annotations

from dataclasses import dataclass

from verification_ecology_kit.model.packets import VerifierPacket
from verification_ecology_kit.model.records import ResidualKind, TrustStatus, Visibility
from verification_ecology_kit.model.residuals import ResidualRecord
from verification_ecology_kit.result import CheckResult, FailureCode, pass_result, residual_result


@dataclass(frozen=True)
class ExternalPacket:
    packet: VerifierPacket
    source_ecology: str
    received_at: str
    trust_basis: tuple[str, ...] = ()


@dataclass(frozen=True)
class LocalInternalizationResult:
    packet_id: str
    quarantine_first: bool
    translated: bool
    boundary_checked: bool
    residuals_handled: bool
    local_counter_packet_hook: bool
    local_scope_profiled: bool
    authority_not_blocked: bool
    internalized: bool
    residual_refs: tuple[str, ...] = ()


@dataclass(frozen=True)
class LocalInternalizationPipeline:
    quarantine_first: bool
    translated: bool
    boundary_checked: bool
    residuals_handled: bool
    local_counter_packet_hook: bool
    local_scope_profiled: bool = False
    authority_not_blocked: bool = False

    def admissible(self) -> bool:
        return (
            self.quarantine_first
            and self.translated
            and self.boundary_checked
            and self.residuals_handled
            and self.local_counter_packet_hook
            and self.local_scope_profiled
            and self.authority_not_blocked
        )


class LocalSovereignty:
    def quarantine_external(self, external: ExternalPacket) -> CheckResult:
        if external.packet.circulation_status is None:
            return residual_result("LocalSovereignty", FailureCode.MISSING_REQUIRED_CORE)
        external.packet.circulation_status.visibility = Visibility.QUARANTINED
        external.packet.circulation_status.trust_status = TrustStatus.EXTERNAL_CANDIDATE
        external.packet.circulation_status.local_internalization_status = "quarantined"
        return pass_result("LocalSovereignty", evidence_refs=(external.packet.packet_id,))

    def internalize(
        self,
        packet: VerifierPacket,
        *,
        translated: bool,
        boundary_checked: bool,
        residuals_handled: bool = False,
        local_counter_packet_hook: bool = False,
        local_scope_profiled: bool = True,
        authority_not_blocked: bool = True,
    ) -> LocalInternalizationResult:
        if packet.circulation_status is None:
            return LocalInternalizationResult(
                packet.packet_id,
                False,
                translated,
                boundary_checked,
                residuals_handled,
                local_counter_packet_hook,
                local_scope_profiled,
                authority_not_blocked,
                False,
            )
        redaction_ambiguous = (
            packet.circulation_status.visibility == Visibility.REDACTED
            and not packet.circulation_status.redaction_residual_refs
        )
        destructive_or_narrowing_boundary = bool(
            packet.boundary_refs
            and (
                packet.boundary_refs.destructive_boundary_ref
                or packet.boundary_refs.narrowing_boundary_ref
                or packet.boundary_refs.reachability_certificate_refs
            )
        )
        boundary_admissible = boundary_checked
        quarantine_first = (
            packet.circulation_status.visibility == Visibility.QUARANTINED
            or packet.circulation_status.local_internalization_status.startswith("quarantined")
        )
        pipeline = LocalInternalizationPipeline(
            quarantine_first=quarantine_first,
            translated=translated,
            boundary_checked=boundary_admissible,
            residuals_handled=residuals_handled and not redaction_ambiguous,
            local_counter_packet_hook=local_counter_packet_hook,
            local_scope_profiled=local_scope_profiled,
            authority_not_blocked=authority_not_blocked,
        )
        if not pipeline.admissible():
            packet.circulation_status.visibility = Visibility.QUARANTINED
            residual = ResidualRecord(
                kind=ResidualKind.TRANSLATION_RESIDUAL,
                origin=packet.packet_id,
                scope=("local_internalization",),
                obligation=(
                    "External packet requires quarantine, translation, boundary checks, "
                    "residual handling, local scope profile, authority clearance, "
                    "and local counter-packet hook before internalization"
                ),
                exposure="blocks_support",
                payload={
                    "redaction_ambiguous": redaction_ambiguous,
                    "destructive_or_narrowing_boundary": destructive_or_narrowing_boundary,
                },
            )
            packet.residual_obligations.append(residual)
            packet.circulation_status.translation_residual_refs.append(residual.residual_id)
            return LocalInternalizationResult(
                packet.packet_id,
                quarantine_first,
                translated,
                boundary_admissible,
                residuals_handled and not redaction_ambiguous,
                local_counter_packet_hook,
                local_scope_profiled,
                authority_not_blocked,
                False,
                (residual.residual_id,),
            )
        packet.circulation_status.trust_status = TrustStatus.LOCAL
        packet.circulation_status.visibility = Visibility.PRIVATE
        packet.circulation_status.local_internalization_status = "internalized"
        return LocalInternalizationResult(
            packet.packet_id,
            True,
            True,
            True,
            True,
            True,
            True,
            True,
            True,
        )
