import VETCore.Runtime

namespace VETCore

def OperationResidualizesInvariantLoss (s : EcologyState) : Prop :=
  EcologyInvariantHolds s ∨ ResidualizedViolationsLive s

def MissingSchemaFieldCanResidualize (s : EcologyState) : Prop :=
  HasResidualKind s ResidualKind.schema_overclosure ∧
  ∃ p, p ∈ s.packets ∧ p.antiOverclosure.residualEscapeHatch = true

def AntiOverclosureRuleSuppressesResiduals (p : VerifierPacket) : Prop :=
  p.antiOverclosure.residualEscapeHatch = false ∧
  p.antiOverclosure.schemaRevisionPath = false

def SchemaRevisabilityViolated (p : VerifierPacket) : Prop :=
  ¬ SchemaRevisable p

end VETCore
