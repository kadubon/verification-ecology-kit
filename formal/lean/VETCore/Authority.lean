import VETCore.Aperture

namespace VETCore

def ExternalCandidatesInternalized (inputs : AuthInputs) : Prop :=
  inputs.externalPacketReadyForLocalAuthority = true

def AuthorityInputsResolved (inputs : AuthInputs) : Prop :=
  inputs.candidateDigestMatches = true ∧
  inputs.absenceCertificatesResolved = true ∧
  inputs.soundGapRefsResolved = true ∧
  inputs.counterexampleRefsResolved = true ∧
  inputs.statusRefsResolved = true ∧
  inputs.rollbackHookPresent = true ∧
  inputs.assessmentRolePresent = true ∧
  inputs.sandboxPresent = true

inductive AuthorityAllowTransition : AuthInputs -> EcologyState -> EcologyState -> Prop where
  | allow
      {inputs : AuthInputs}
      {s s' : EcologyState}
      (supportEligible : AllRequiredSupportEligible inputs)
      (noBadSupport : NoBadRequiredSupport inputs)
      (migratedWitness : MigratedSupportHasWitness inputs)
      (inputsResolved : AuthorityInputsResolved inputs)
      (externalReady : ExternalCandidatesInternalized inputs)
      (noBlockingResidual : NoBlockingActiveNonLiveResidual s)
      (trace : TraceOK s.ledger)
      : AuthorityAllowTransition inputs s s'

end VETCore
