import VETCore.WellFormed

namespace VETCore

def ApertureLoss (before after : EcologyState) : Prop :=
  after.aperture.feasibleQuestions < before.aperture.feasibleQuestions ∨
  after.aperture.feasibleCounters < before.aperture.feasibleCounters

def JustifiedBoundaryExclusion (s : EcologyState) : Prop :=
  s.aperture.boundaryExclusionJustified = true

def ApertureDebtRecorded (s : EcologyState) : Prop :=
  s.aperture.debtResidualPresent = true ∨ HasResidualKind s ResidualKind.aperture_debt

def PacketSpam (before after : EcologyState) : Prop :=
  before.packetCount < after.packetCount ∧
  after.frontier.expanded = false ∧
  after.aperture.preserved = false

def VerifierAcceleration (before after : EcologyState) : Prop :=
  before.packetCount < after.packetCount ∧
  after.frontier.expanded = true ∧
  after.aperture.preserved = true

end VETCore
