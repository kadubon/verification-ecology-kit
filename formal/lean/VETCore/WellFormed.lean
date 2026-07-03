import VETCore.Residual

namespace VETCore

def OriginTraceable (p : VerifierPacket) : Prop :=
  p.origin.createdFrom ≠ "" ∧ (p.origin.traceRefs ≠ [] ∨ p.origin.parentPackets ≠ [])

def ScopeAccountable (p : VerifierPacket) : Prop :=
  p.scope.unvalidatedAssumptions = []

def ResidualPreserved (p : VerifierPacket) : Prop :=
  ∀ r, r ∈ p.residuals -> WellFormedResidual r

def BoundaryPreserved (p : VerifierPacket) : Prop :=
  p.hasBoundaryWork = true ∨ HasResidualKind
    { packets := [], counterPackets := [], boundaries := [], reachabilityCertificates := [],
      counterexampleChannels := [], authorityRecords := [], ledger := { residuals := p.residuals,
      events := [], traceCertificateAccepted := true }, aperture := { feasibleQuestions := 0,
      feasibleCounters := 0, debtResidualPresent := false, boundaryExclusionJustified := false,
      preserved := true }, frontier := { frontierSize := 0, expanded := false, evidenceRefs := [] },
      packetCount := 0 } ResidualKind.unexcluded

def HasCounterPacketOrResidual (p : VerifierPacket) : Prop :=
  p.counterPacketRefs ≠ [] ∨ ∃ r, r ∈ p.residuals ∧ r.kind = ResidualKind.missing_counter

def RetirementLive (p : VerifierPacket) : Prop :=
  p.hasRetirementCondition = true ∨ ∃ r, r ∈ p.residuals ∧ r.kind = ResidualKind.liveness_debt

def ApertureAccounted (p : VerifierPacket) : Prop :=
  p.hasApertureDebt = true ∨ p.invariants.preserveAperture = true

def SchemaRevisable (p : VerifierPacket) : Prop :=
  p.antiOverclosure.residualEscapeHatch = true ∨ p.antiOverclosure.schemaRevisionPath = true

def LocalSovereigntySatisfied (p : VerifierPacket) : Prop :=
  p.trustStatus = TrustStatus.local ∨
  (p.visibility = Visibility.quarantined ∧ p.hasLocalCounterHook = true)

def WellFormedPacketCore (p : VerifierPacket) : Prop :=
  p.packetId ≠ "" ∧
  p.hasProcedure = true ∧
  p.hasCertificationCondition = true

def CoreAccountablePacket (p : VerifierPacket) : Prop :=
  WellFormedPacketCore p ∨ ∃ r, r ∈ p.residuals ∧ r.kind = ResidualKind.missing

def WellFormedPacket (p : VerifierPacket) : Prop :=
  CoreAccountablePacket p ∧
  OriginTraceable p ∧
  ScopeAccountable p ∧
  ResidualPreserved p ∧
  BoundaryPreserved p ∧
  HasCounterPacketOrResidual p ∧
  RetirementLive p ∧
  ApertureAccounted p ∧
  SchemaRevisable p ∧
  LocalSovereigntySatisfied p

def SupportEligible (support : SupportRecord) : Prop :=
  support.status = Status.active ∧
  support.digestMatches = true ∧
  support.residualGateLive = true ∧
  (support.status ≠ Status.migrated ∨ support.migrationWitnessAccepted = true) ∧
  support.redactionResidualPresent = true

def BadSupportStatus (support : SupportRecord) : Prop :=
  support.status = Status.stale ∨ support.status = Status.revoked ∨ support.status = Status.unknown

def MigratedWithoutWitness (support : SupportRecord) : Prop :=
  support.status = Status.migrated ∧ support.migrationWitnessAccepted = false

def AllRequiredSupportEligible (inputs : AuthInputs) : Prop :=
  ∀ support, support ∈ inputs.supportRefs -> SupportEligible support

def NoBadRequiredSupport (inputs : AuthInputs) : Prop :=
  ∀ support, support ∈ inputs.supportRefs -> ¬ BadSupportStatus support

def MigratedSupportHasWitness (inputs : AuthInputs) : Prop :=
  ∀ support, support ∈ inputs.supportRefs -> support.status = Status.migrated ->
    support.migrationWitnessAccepted = true

def WellFormedAuthority (record : AuthorityRecord) : Prop :=
  record.authorityId ≠ "" ∧
  record.inputs.candidateDigestMatches = true ∧
  record.inputs.absenceCertificatesResolved = true ∧
  record.inputs.soundGapRefsResolved = true ∧
  record.inputs.counterexampleRefsResolved = true ∧
  record.inputs.statusRefsResolved = true ∧
  AllRequiredSupportEligible record.inputs

def ScopeExpansionAccounted (s : EcologyState) : Prop :=
  ∀ p, p ∈ s.packets -> p.hasBoundaryWork = true ∨ HasResidualKind s ResidualKind.unexcluded

def InheritedResidualsAccounted (s : EcologyState) : Prop :=
  ∀ p, p ∈ s.packets -> ResidualPreserved p

def InheritedBoundariesAccounted (s : EcologyState) : Prop :=
  ∀ p, p ∈ s.packets -> BoundaryPreserved p

def CounterPacketsAccounted (s : EcologyState) : Prop :=
  ∀ p, p ∈ s.packets -> HasCounterPacketOrResidual p

def RetirementLivenessAccounted (s : EcologyState) : Prop :=
  ∀ p, p ∈ s.packets -> RetirementLive p

def ApertureLossAccounted (s : EcologyState) : Prop :=
  s.aperture.preserved = true ∨ s.aperture.debtResidualPresent = true ∨
  s.aperture.boundaryExclusionJustified = true ∨ HasResidualKind s ResidualKind.aperture_debt

def SchemaUnknownsAccounted (s : EcologyState) : Prop :=
  ∀ p, p ∈ s.packets ->
    p.antiOverclosure.unknownsToPreserve ≠ [] ∨ HasResidualKind s ResidualKind.schema_overclosure

def EcologyInvariantHolds (s : EcologyState) : Prop :=
  (∀ p, p ∈ s.packets -> OriginTraceable p) ∧
  ScopeExpansionAccounted s ∧
  InheritedResidualsAccounted s ∧
  InheritedBoundariesAccounted s ∧
  CounterPacketsAccounted s ∧
  RetirementLivenessAccounted s ∧
  ApertureLossAccounted s ∧
  SchemaUnknownsAccounted s

def ResidualizedViolationsLive (s : EcologyState) : Prop :=
  HasLiveResidualKind s ResidualKind.unresolved ∨
  HasLiveResidualKind s ResidualKind.unexcluded ∨
  HasLiveResidualKind s ResidualKind.aperture_debt ∨
  HasLiveResidualKind s ResidualKind.liveness_debt ∨
  HasLiveResidualKind s ResidualKind.schema_overclosure ∨
  HasLiveResidualKind s ResidualKind.missing_counter

def WellFormedEcologyState (s : EcologyState) : Prop :=
  (∀ p, p ∈ s.packets -> WellFormedPacket p) ∧
  (∀ record, record ∈ s.authorityRecords -> WellFormedAuthority record) ∧
  TraceOK s.ledger

end VETCore
