namespace VETCore

abbrev ObjectId := String
abbrev ObjectRef := String
abbrev DigestValue := String
abbrev ResidualId := String
abbrev PacketId := String
abbrev BoundaryId := String
abbrev CertificateId := String
abbrev AuthorityId := String
abbrev StageId := String

inductive Status where
  | active
  | stale
  | revoked
  | migrated
  | unknown
  deriving DecidableEq, Repr

inductive ResidualKind where
  | unresolved
  | untranslated
  | unexcluded
  | missing
  | deliberately_preserved
  | schema_overclosure
  | aperture_debt
  | liveness_debt
  | soundness_gap
  | redaction_residual
  | translation_residual
  | migration_residual
  | conflict_residual
  | missing_counter
  deriving DecidableEq, Repr

inductive ResidualRouteKind where
  | question_formation
  | counterexample_search
  | boundary_revision
  | repair
  | retirement
  | translation
  | counter_packet_generation
  | schema_revision
  | redaction_review
  | migration_review
  | reasoned_preservation
  | quarantine
  deriving DecidableEq, Repr

inductive AuthorityDecision where
  | allow
  | deny
  | quarantine
  | residualize
  deriving DecidableEq, Repr

inductive Visibility where
  | private_
  | shared
  | public
  | redacted
  | quarantined
  | retired
  deriving DecidableEq, Repr

inductive TrustStatus where
  | local
  | external_candidate
  | low_trust
  | adversarial
  | unknown
  deriving DecidableEq, Repr

inductive PacketOperation where
  | fork
  | specialize
  | generalize
  | compose
  | contrast
  | repair
  | retire
  | quarantine
  | internalize
  | redact
  deriving DecidableEq, Repr

inductive RuntimeStage where
  | candidate_generation
  | core_accountability
  | semantic_accountability
  | residual_metabolism
  | packet_generation
  | counter_packet_check
  | boundary_check
  | reachability_check
  | schema_overclosure_check
  | lineage_check
  | authority_check
  | quarantine_decision
  | internalization_decision
  | repair_decision
  | retirement_decision
  | aperture_update
  | frontier_update
  deriving DecidableEq, Repr

structure DigestRecord where
  algorithm : String
  value : DigestValue
  deriving Repr

structure ResidualRoute where
  route : ResidualRouteKind
  live : Bool
  owner : String
  trigger : String
  reason : String
  deriving Repr

structure Residual where
  residualId : ResidualId
  kind : ResidualKind
  origin : ObjectRef
  scope : List String
  active : Bool
  authorityBlocking : Bool
  routeLive : Bool
  reasonedPreservation : Bool
  retiredWithReason : Bool
  quarantined : Bool
  redactedWithResidual : Bool
  mergedWithWitness : Bool
  disposedWithWitness : Bool
  deriving Repr

structure LedgerEvent where
  eventId : String
  kind : String
  sourceResiduals : List ResidualId
  targetResiduals : List ResidualId
  hasDeltaWitness : Bool
  hasDispositionWitness : Bool
  hasReinspectionCondition : Bool
  hasRedactionConsequence : Bool
  deriving Repr

structure ResidualLedger where
  residuals : List Residual
  events : List LedgerEvent
  traceCertificateAccepted : Bool
  deriving Repr

structure PacketOrigin where
  createdFrom : String
  traceRefs : List ObjectRef
  parentPackets : List PacketId
  lineageRefs : List PacketId
  deriving Repr

structure PacketScope where
  appliesTo : List String
  excludes : List String
  assumptions : List String
  unvalidatedAssumptions : List String
  deriving Repr

structure BoundaryRefs where
  destructiveBoundaryRef : Option BoundaryId
  narrowingBoundaryRef : Option BoundaryId
  reachabilityCertificateRefs : List CertificateId
  inheritedBoundaryRefs : List BoundaryId
  deriving Repr

structure AntiOverclosure where
  unknownsToPreserve : List String
  futureCandidatesMayNarrow : Bool
  residualEscapeHatch : Bool
  schemaRevisionPath : Bool
  deriving Repr

structure EcologicalInvariants where
  preserveOrigin : Bool
  preserveScope : Bool
  preserveResiduals : Bool
  preserveBoundaries : Bool
  preserveCounterPacketRoute : Bool
  preserveAperture : Bool
  deriving Repr

structure VerifierPacket where
  packetId : PacketId
  origin : PacketOrigin
  scope : PacketScope
  boundaryRefs : BoundaryRefs
  residuals : List Residual
  counterPacketRefs : List PacketId
  antiOverclosure : AntiOverclosure
  invariants : EcologicalInvariants
  visibility : Visibility
  trustStatus : TrustStatus
  certification : Bool
  hasProcedure : Bool
  hasCertificationCondition : Bool
  hasRepairCondition : Bool
  hasRetirementCondition : Bool
  hasLocalCounterHook : Bool
  hasBoundaryWork : Bool
  hasApertureDebt : Bool
  lineageVisible : Bool
  deriving Repr

structure CounterPacket where
  packet : VerifierPacket
  targetPacketId : PacketId
  inspectionRoles : List String
  deriving Repr

structure BoundaryRecord where
  boundaryId : BoundaryId
  destructiveChecked : Bool
  narrowingChecked : Bool
  deriving Repr

structure ReachabilityCertificate where
  certificateId : CertificateId
  freshForComposition : Bool
  excludesDestructiveReachability : Bool
  excludesNarrowingReachability : Bool
  deriving Repr

structure CounterexampleChannel where
  channelId : String
  live : Bool
  targetPacketId : PacketId
  deriving Repr

structure SoundGapResidual where
  residual : Residual
  blocksAuthority : Bool
  deriving Repr

structure CertificationRecord where
  certificateId : String
  packetId : PacketId
  freshForOperation : Bool
  status : Status
  deriving Repr

structure SupportRecord where
  supportRef : ObjectRef
  status : Status
  digestMatches : Bool
  migrationWitnessAccepted : Bool
  redactionResidualPresent : Bool
  residualGateLive : Bool
  deriving Repr

structure AuthInputs where
  candidateRef : ObjectRef
  candidateDigestMatches : Bool
  supportRefs : List SupportRecord
  absenceCertificatesResolved : Bool
  soundGapRefsResolved : Bool
  counterexampleRefsResolved : Bool
  statusRefsResolved : Bool
  externalPacketReadyForLocalAuthority : Bool
  rollbackHookPresent : Bool
  assessmentRolePresent : Bool
  sandboxPresent : Bool
  deriving Repr

structure AuthorityRecord where
  authorityId : AuthorityId
  decision : AuthorityDecision
  inputs : AuthInputs
  deriving Repr

structure Aperture where
  feasibleQuestions : Nat
  feasibleCounters : Nat
  debtResidualPresent : Bool
  boundaryExclusionJustified : Bool
  preserved : Bool
  deriving Repr

structure Frontier where
  frontierSize : Nat
  expanded : Bool
  evidenceRefs : List ObjectRef
  deriving Repr

structure EcologyState where
  packets : List VerifierPacket
  counterPackets : List CounterPacket
  boundaries : List BoundaryRecord
  reachabilityCertificates : List ReachabilityCertificate
  counterexampleChannels : List CounterexampleChannel
  authorityRecords : List AuthorityRecord
  ledger : ResidualLedger
  aperture : Aperture
  frontier : Frontier
  packetCount : Nat
  deriving Repr

structure RuntimeTrace where
  beforeState : EcologyState
  stage : RuntimeStage
  afterState : EcologyState
  residualDeltaRecorded : Bool
  boundaryDeltaRecorded : Bool
  authorityDeltaRecorded : Bool
  apertureDeltaRecorded : Bool
  frontierDeltaRecorded : Bool
  deriving Repr

end VETCore
