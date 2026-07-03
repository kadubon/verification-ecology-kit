import VETCore.Invariants

namespace VETCore

theorem residual_preservation_step
    {s s' : EcologyState} {op : PacketOperation}
    (_hInv : EcologyInvariantHolds s)
    (h : Step s op s') :
    ResidualsAccounted s s' := by
  cases h with
  | fork cert => exact cert.residualsAccounted
  | specialize cert => exact cert.residualsAccounted
  | generalize cert _ => exact cert.residualsAccounted
  | compose cert _ _ => exact cert.residualsAccounted
  | contrast cert => exact cert.residualsAccounted
  | repair cert _ => exact cert.residualsAccounted
  | retire cert _ => exact cert.residualsAccounted
  | quarantine cert _ => exact cert.residualsAccounted
  | internalize cert _ => exact cert.residualsAccounted
  | redact cert _ => exact cert.residualsAccounted

theorem active_residual_without_live_route_blocks_authority
    {inputs : AuthInputs} {s s' : EcologyState} {r : Residual}
    (hmem : r ∈ s.ledger.residuals)
    (hactive : r.active = true)
    (hblocking : r.authorityBlocking = true)
    (hnolive : ¬ LiveResidual r) :
    ¬ AuthorityAllowTransition inputs s s' := by
  intro h
  cases h with
  | allow _ _ _ _ _ noBlockingResidual _ =>
      exact hnolive (noBlockingResidual r hmem hactive hblocking)

theorem admissible_operation_preserves_or_residualizes_invariants
    {s s' : EcologyState} {op : PacketOperation}
    (h : Step s op s') :
    EcologyInvariantHolds s' ∨ ResidualizedViolationsLive s' := by
  cases h with
  | fork cert => exact cert.invariantAccounting
  | specialize cert => exact cert.invariantAccounting
  | generalize cert _ => exact cert.invariantAccounting
  | compose cert _ _ => exact cert.invariantAccounting
  | contrast cert => exact cert.invariantAccounting
  | repair cert _ => exact cert.invariantAccounting
  | retire cert _ => exact cert.invariantAccounting
  | quarantine cert _ => exact cert.invariantAccounting
  | internalize cert _ => exact cert.invariantAccounting
  | redact cert _ => exact cert.invariantAccounting

theorem compose_not_automatically_certified
    {s s' : EcologyState}
    (h : Step s PacketOperation.compose s') :
    FreshBoundaryObligation s' ∧ FreshCounterPacketObligation s' := by
  cases h with
  | compose _ freshBoundary freshCounter => exact And.intro freshBoundary freshCounter

theorem redaction_requires_residual
    {s s' : EcologyState}
    (h : Step s PacketOperation.redact s') :
    RedactionResidualPresent s' := by
  cases h with
  | redact _ redaction => exact redaction

theorem generalization_requires_boundary_work
    {s s' : EcologyState}
    (h : Step s PacketOperation.generalize s') :
    BoundaryWorkOrUnexcludedResidual s' := by
  cases h with
  | generalize _ boundaryWork => exact boundaryWork

theorem authority_allow_requires_support_eligibility
    {inputs : AuthInputs} {s s' : EcologyState}
    (h : AuthorityAllowTransition inputs s s') :
    AllRequiredSupportEligible inputs := by
  cases h with
  | allow supportEligible _ _ _ _ _ _ => exact supportEligible

theorem stale_revoked_unknown_support_blocks_authority
    {s s' : EcologyState} {inputs : AuthInputs} {support : SupportRecord}
    (hmem : support ∈ inputs.supportRefs)
    (hbad : BadSupportStatus support)
    (hallows : AuthorityAllowTransition inputs s s') :
    False := by
  cases hallows with
  | allow _ noBadSupport _ _ _ _ _ =>
      exact (noBadSupport support hmem) hbad

theorem migrated_support_requires_witness
    {s s' : EcologyState} {inputs : AuthInputs} {support : SupportRecord}
    (hmem : support ∈ inputs.supportRefs)
    (hmigrated : support.status = Status.migrated)
    (hnoWitness : support.migrationWitnessAccepted = false)
    (hallows : AuthorityAllowTransition inputs s s') :
    False := by
  cases hallows with
  | allow _ _ migratedWitness _ _ _ _ =>
      have hwitness := migratedWitness support hmem hmigrated
      cases hwitness
      contradiction

theorem external_packet_not_authority_before_internalization
    {s s' : EcologyState} {inputs : AuthInputs}
    (hnotReady : inputs.externalPacketReadyForLocalAuthority = false)
    (hallows : AuthorityAllowTransition inputs s s') :
    False := by
  cases hallows with
  | allow _ _ _ _ externalReady _ _ =>
      unfold ExternalCandidatesInternalized at externalReady
      cases externalReady
      contradiction

theorem runtime_preserves_ecological_invariants
    {s s' : EcologyState} {stage : RuntimeStage}
    (_hInv : EcologyInvariantHolds s)
    (h : RuntimeStep s stage s') :
    EcologyInvariantHolds s' ∨ ResidualizedViolationsLive s' := by
  cases h with
  | candidate_generation cert => exact cert.invariantAccounting
  | core_accountability cert => exact cert.invariantAccounting
  | semantic_accountability cert => exact cert.invariantAccounting
  | residual_metabolism cert => exact cert.invariantAccounting
  | packet_generation cert => exact cert.invariantAccounting
  | counter_packet_check cert => exact cert.invariantAccounting
  | boundary_check cert => exact cert.invariantAccounting
  | reachability_check cert => exact cert.invariantAccounting
  | schema_overclosure_check cert => exact cert.invariantAccounting
  | lineage_check cert => exact cert.invariantAccounting
  | authority_check cert => exact cert.invariantAccounting
  | quarantine_decision cert => exact cert.invariantAccounting
  | internalization_decision cert => exact cert.invariantAccounting
  | repair_decision cert => exact cert.invariantAccounting
  | retirement_decision cert => exact cert.invariantAccounting
  | aperture_update cert => exact cert.invariantAccounting
  | frontier_update cert => exact cert.invariantAccounting

theorem packet_spam_not_acceleration
    {before after : EcologyState}
    (hspam : PacketSpam before after) :
    ¬ VerifierAcceleration before after := by
  intro haccel
  exact hspam.right.left haccel.right.left

theorem aperture_loss_requires_debt
    {s s' : EcologyState} {op : PacketOperation}
    (hloss : ApertureLoss s s')
    (hnoBoundary : ¬ JustifiedBoundaryExclusion s')
    (h : Step s op s') :
    ApertureDebtRecorded s' := by
  cases h with
  | fork cert => exact cert.apertureDebtForLoss hloss hnoBoundary
  | specialize cert => exact cert.apertureDebtForLoss hloss hnoBoundary
  | generalize cert _ => exact cert.apertureDebtForLoss hloss hnoBoundary
  | compose cert _ _ => exact cert.apertureDebtForLoss hloss hnoBoundary
  | contrast cert => exact cert.apertureDebtForLoss hloss hnoBoundary
  | repair cert _ => exact cert.apertureDebtForLoss hloss hnoBoundary
  | retire cert _ => exact cert.apertureDebtForLoss hloss hnoBoundary
  | quarantine cert _ => exact cert.apertureDebtForLoss hloss hnoBoundary
  | internalize cert _ => exact cert.apertureDebtForLoss hloss hnoBoundary
  | redact cert _ => exact cert.apertureDebtForLoss hloss hnoBoundary

theorem missing_schema_field_can_residualize
    {s : EcologyState}
    (h : MissingSchemaFieldCanResidualize s) :
    HasResidualKind s ResidualKind.schema_overclosure := by
  exact h.left

theorem anti_overclosure_overclosure_blocked
    {p : VerifierPacket}
    (h : AntiOverclosureRuleSuppressesResiduals p) :
    SchemaRevisabilityViolated p := by
  unfold SchemaRevisabilityViolated
  unfold SchemaRevisable
  intro hrev
  cases hrev with
  | inl hescape => exact h.left hescape
  | inr hschema => exact h.right hschema

end VETCore
