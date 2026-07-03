import VETCore.Theorems

namespace VETCore

def sampleResidual : Residual :=
  { residualId := "res-sample",
    kind := ResidualKind.unresolved,
    origin := "obj",
    scope := ["sample"],
    active := true,
    authorityBlocking := true,
    routeLive := true,
    reasonedPreservation := false,
    retiredWithReason := false,
    quarantined := false,
    redactedWithResidual := false,
    mergedWithWitness := false,
    disposedWithWitness := false }

def sampleLedger : ResidualLedger :=
  { residuals := [sampleResidual], events := [], traceCertificateAccepted := true }

def sampleAperture : Aperture :=
  { feasibleQuestions := 1, feasibleCounters := 1, debtResidualPresent := false,
    boundaryExclusionJustified := false, preserved := true }

def sampleFrontier : Frontier :=
  { frontierSize := 1, expanded := true, evidenceRefs := ["frontier"] }

def emptyState : EcologyState :=
  { packets := [], counterPackets := [], boundaries := [], reachabilityCertificates := [],
    counterexampleChannels := [], authorityRecords := [], ledger := sampleLedger,
    aperture := sampleAperture, frontier := sampleFrontier, packetCount := 0 }

example : HasResidualKind emptyState ResidualKind.unresolved := by
  unfold HasResidualKind
  exact Exists.intro sampleResidual (And.intro (by simp [emptyState, sampleLedger]) rfl)

end VETCore
