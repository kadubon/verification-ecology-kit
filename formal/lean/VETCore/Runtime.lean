import VETCore.Semantics

namespace VETCore

structure RuntimeCertificate (s s' : EcologyState) where
  stagePreconditions : Prop
  checkerResultRecorded : Prop
  residualDeltaRecorded : Prop
  boundaryDeltaRecorded : Prop
  authorityDeltaRecorded : Prop
  apertureDeltaRecorded : Prop
  frontierDeltaRecorded : Prop
  invariantAccounting : EcologyInvariantHolds s' ∨ ResidualizedViolationsLive s'

inductive RuntimeStep : EcologyState -> RuntimeStage -> EcologyState -> Prop where
  | candidate_generation {s s'} (cert : RuntimeCertificate s s') :
      RuntimeStep s RuntimeStage.candidate_generation s'
  | core_accountability {s s'} (cert : RuntimeCertificate s s') :
      RuntimeStep s RuntimeStage.core_accountability s'
  | semantic_accountability {s s'} (cert : RuntimeCertificate s s') :
      RuntimeStep s RuntimeStage.semantic_accountability s'
  | residual_metabolism {s s'} (cert : RuntimeCertificate s s') :
      RuntimeStep s RuntimeStage.residual_metabolism s'
  | packet_generation {s s'} (cert : RuntimeCertificate s s') :
      RuntimeStep s RuntimeStage.packet_generation s'
  | counter_packet_check {s s'} (cert : RuntimeCertificate s s') :
      RuntimeStep s RuntimeStage.counter_packet_check s'
  | boundary_check {s s'} (cert : RuntimeCertificate s s') :
      RuntimeStep s RuntimeStage.boundary_check s'
  | reachability_check {s s'} (cert : RuntimeCertificate s s') :
      RuntimeStep s RuntimeStage.reachability_check s'
  | schema_overclosure_check {s s'} (cert : RuntimeCertificate s s') :
      RuntimeStep s RuntimeStage.schema_overclosure_check s'
  | lineage_check {s s'} (cert : RuntimeCertificate s s') :
      RuntimeStep s RuntimeStage.lineage_check s'
  | authority_check {s s'} (cert : RuntimeCertificate s s') :
      RuntimeStep s RuntimeStage.authority_check s'
  | quarantine_decision {s s'} (cert : RuntimeCertificate s s') :
      RuntimeStep s RuntimeStage.quarantine_decision s'
  | internalization_decision {s s'} (cert : RuntimeCertificate s s') :
      RuntimeStep s RuntimeStage.internalization_decision s'
  | repair_decision {s s'} (cert : RuntimeCertificate s s') :
      RuntimeStep s RuntimeStage.repair_decision s'
  | retirement_decision {s s'} (cert : RuntimeCertificate s s') :
      RuntimeStep s RuntimeStage.retirement_decision s'
  | aperture_update {s s'} (cert : RuntimeCertificate s s') :
      RuntimeStep s RuntimeStage.aperture_update s'
  | frontier_update {s s'} (cert : RuntimeCertificate s s') :
      RuntimeStep s RuntimeStage.frontier_update s'

end VETCore
