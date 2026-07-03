import VETCore.Authority

namespace VETCore

structure StepCertificate (s s' : EcologyState) where
  preconditions : Prop
  packetChangesRecorded : Prop
  residualAdditionsRecorded : Prop
  ledgerEventsRecorded : Prop
  boundaryConsequencesRecorded : Prop
  authorityConsequencesRecorded : Prop
  apertureConsequencesRecorded : Prop
  lineageConsequencesRecorded : Prop
  residualsAccounted : ResidualsAccounted s s'
  invariantAccounting : EcologyInvariantHolds s' ∨ ResidualizedViolationsLive s'
  apertureDebtForLoss :
    ApertureLoss s s' -> ¬ JustifiedBoundaryExclusion s' -> ApertureDebtRecorded s'

def FreshBoundaryObligation (s : EcologyState) : Prop :=
  HasResidualKind s ResidualKind.unexcluded ∨
  ∃ c, c ∈ s.reachabilityCertificates ∧ c.freshForComposition = true

def FreshCounterPacketObligation (s : EcologyState) : Prop :=
  HasResidualKind s ResidualKind.missing_counter ∨ s.counterPackets ≠ []

def RedactionResidualPresent (s : EcologyState) : Prop :=
  HasResidualKind s ResidualKind.redaction_residual

def BoundaryWorkOrUnexcludedResidual (s : EcologyState) : Prop :=
  (∃ p, p ∈ s.packets ∧ p.hasBoundaryWork = true) ∨ HasResidualKind s ResidualKind.unexcluded

def ExternalInternalizationWitness (s : EcologyState) : Prop :=
  ∃ p, p ∈ s.packets ∧
    p.trustStatus = TrustStatus.local ∧
    p.visibility ≠ Visibility.quarantined ∧
    p.hasBoundaryWork = true ∧
    p.hasLocalCounterHook = true ∧
    HasResidualKind s ResidualKind.translation_residual

def RepairDispositionWitness (s : EcologyState) : Prop :=
  ∃ event, event ∈ s.ledger.events ∧ event.hasDispositionWitness = true

def RetirementWitness (s : EcologyState) : Prop :=
  ∃ event, event ∈ s.ledger.events ∧ event.kind = "retire" ∧
    event.hasReinspectionCondition = true

def QuarantineWitness (s : EcologyState) : Prop :=
  ∃ event, event ∈ s.ledger.events ∧ event.kind = "quarantine" ∧
    event.hasDispositionWitness = true

inductive Step : EcologyState -> PacketOperation -> EcologyState -> Prop where
  | fork
      {s s' : EcologyState}
      (cert : StepCertificate s s')
      : Step s PacketOperation.fork s'
  | specialize
      {s s' : EcologyState}
      (cert : StepCertificate s s')
      : Step s PacketOperation.specialize s'
  | generalize
      {s s' : EcologyState}
      (cert : StepCertificate s s')
      (boundaryWork : BoundaryWorkOrUnexcludedResidual s')
      : Step s PacketOperation.generalize s'
  | compose
      {s s' : EcologyState}
      (cert : StepCertificate s s')
      (freshBoundary : FreshBoundaryObligation s')
      (freshCounter : FreshCounterPacketObligation s')
      : Step s PacketOperation.compose s'
  | contrast
      {s s' : EcologyState}
      (cert : StepCertificate s s')
      : Step s PacketOperation.contrast s'
  | repair
      {s s' : EcologyState}
      (cert : StepCertificate s s')
      (disposition : RepairDispositionWitness s')
      : Step s PacketOperation.repair s'
  | retire
      {s s' : EcologyState}
      (cert : StepCertificate s s')
      (retired : RetirementWitness s')
      : Step s PacketOperation.retire s'
  | quarantine
      {s s' : EcologyState}
      (cert : StepCertificate s s')
      (quarantined : QuarantineWitness s')
      : Step s PacketOperation.quarantine s'
  | internalize
      {s s' : EcologyState}
      (cert : StepCertificate s s')
      (witness : ExternalInternalizationWitness s')
      : Step s PacketOperation.internalize s'
  | redact
      {s s' : EcologyState}
      (cert : StepCertificate s s')
      (redaction : RedactionResidualPresent s')
      : Step s PacketOperation.redact s'

end VETCore
