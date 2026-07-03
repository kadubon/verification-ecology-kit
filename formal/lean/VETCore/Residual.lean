import VETCore.Syntax

namespace VETCore

def ResidualPresentById (residualId : ResidualId) (residuals : List Residual) : Prop :=
  ∃ r, r ∈ residuals ∧ r.residualId = residualId

def LiveResidual (r : Residual) : Prop :=
  r.active = true ∧ (r.routeLive = true ∨ r.reasonedPreservation = true)

def ResidualClassLive (r : Residual) : Prop :=
  match r.kind with
  | ResidualKind.unresolved => LiveResidual r
  | ResidualKind.untranslated => LiveResidual r
  | ResidualKind.unexcluded => LiveResidual r
  | ResidualKind.missing => LiveResidual r
  | ResidualKind.deliberately_preserved => r.reasonedPreservation = true
  | ResidualKind.schema_overclosure => LiveResidual r
  | ResidualKind.aperture_debt => LiveResidual r
  | ResidualKind.liveness_debt => LiveResidual r
  | ResidualKind.soundness_gap => LiveResidual r
  | ResidualKind.redaction_residual => LiveResidual r
  | ResidualKind.translation_residual => LiveResidual r
  | ResidualKind.migration_residual => LiveResidual r
  | ResidualKind.conflict_residual => LiveResidual r
  | ResidualKind.missing_counter => LiveResidual r

def WellFormedResidual (r : Residual) : Prop :=
  r.residualId ≠ "" ∧
  r.origin ≠ "" ∧
  (r.active = false ∨ ResidualClassLive r ∨ r.authorityBlocking = false)

def ResidualAccounted (r : Residual) (s' : EcologyState) : Prop :=
  ResidualPresentById r.residualId s'.ledger.residuals ∨
  r.retiredWithReason = true ∨
  r.quarantined = true ∨
  r.redactedWithResidual = true ∨
  r.mergedWithWitness = true ∨
  r.disposedWithWitness = true

def ResidualsAccounted (s s' : EcologyState) : Prop :=
  ∀ r, r ∈ s.ledger.residuals -> ResidualAccounted r s'

def HasResidualKind (s : EcologyState) (kind : ResidualKind) : Prop :=
  ∃ r, r ∈ s.ledger.residuals ∧ r.kind = kind

def HasLiveResidualKind (s : EcologyState) (kind : ResidualKind) : Prop :=
  ∃ r, r ∈ s.ledger.residuals ∧ r.kind = kind ∧ LiveResidual r

def NoBlockingActiveNonLiveResidual (s : EcologyState) : Prop :=
  ∀ r,
    r ∈ s.ledger.residuals ->
    r.active = true ->
    r.authorityBlocking = true ->
    LiveResidual r

def WellFormedLedger (ledger : ResidualLedger) : Prop :=
  (∀ r, r ∈ ledger.residuals -> WellFormedResidual r) ∧
  ledger.traceCertificateAccepted = true ∧
  (∀ event, event ∈ ledger.events -> event.hasDeltaWitness = true)

def TraceOK (ledger : ResidualLedger) : Prop :=
  WellFormedLedger ledger ∧
  ∀ event,
    event ∈ ledger.events ->
    event.hasDispositionWitness = true ∧
    (event.kind ≠ "redact" ∨ event.hasRedactionConsequence = true) ∧
    (event.kind ≠ "retire" ∨ event.hasReinspectionCondition = true)

end VETCore
