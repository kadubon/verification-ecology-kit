import Std

namespace CapacityCore

structure State where
  unfinished : Nat
  completed : Nat
  available : Nat
  reserved : Nat
  consumed : Nat
  authority : Nat
  residuals : List Nat
  seen : List Nat
  deriving DecidableEq, Repr

def reserve (s : State) (amount : Nat) : Option State :=
  if amount ≤ s.available then
    some { s with available := s.available - amount, reserved := s.reserved + amount }
  else none

def ready (s : State) (predecessors : List Nat) : Bool :=
  predecessors.all (fun p => s.seen.contains p)

def finish (s : State) (id units cost : Nat) (predecessors : List Nat) : Option State :=
  if s.seen.contains id then some s
  else if ready s predecessors && decide (units ≤ s.unfinished) && decide (cost ≤ s.reserved) then
    some { s with unfinished := s.unfinished - units, completed := s.completed + units,
                  reserved := s.reserved - cost, consumed := s.consumed + cost,
                  seen := id :: s.seen }
  else none

def followup (s : State) (units : Nat) : State :=
  { s with unfinished := s.unfinished + units }

def activateModel (s : State) : State := s

def releaseUnused (s : State) (amount : Nat) : Option State :=
  if amount ≤ s.reserved then
    some { s with reserved := s.reserved - amount, available := s.available + amount }
  else none

theorem release_conserves (s t : State) (n : Nat) (h : releaseUnused s n = some t) :
    t.available + t.reserved = s.available + s.reserved := by
  unfold releaseUnused at h
  split at h
  · simp only [Option.some.injEq] at h
    subst t
    simp only
    omega
  · contradiction

theorem reservation_no_completion (s t : State) (n : Nat) (h : reserve s n = some t) :
    t.completed = s.completed ∧ t.authority = s.authority := by
  unfold reserve at h
  split at h
  · cases Option.some.inj h
    exact ⟨rfl, rfl⟩
  · contradiction

theorem reservation_conserves (s t : State) (n : Nat) (h : reserve s n = some t) :
    t.available + t.reserved = s.available + s.reserved := by
  unfold reserve at h
  split at h
  · simp only [Option.some.injEq] at h
    subst t
    simp only
    omega
  · contradiction

theorem shared_pool_bounded (s t : State) (n : Nat) (h : reserve s n = some t) :
    t.reserved ≤ s.available + s.reserved := by
  have := reservation_conserves s t n h
  omega

theorem completion_conserves (s t : State) (id units cost : Nat) (ps : List Nat)
    (h : finish s id units cost ps = some t) :
    t.unfinished + t.completed = s.unfinished + s.completed ∧
    t.reserved + t.consumed = s.reserved + s.consumed := by
  unfold finish at h
  split at h
  · cases Option.some.inj h
    exact ⟨rfl, rfl⟩
  · split at h
    · simp only [Option.some.injEq] at h
      subst t
      simp_all only [Bool.and_eq_true, decide_eq_true_eq]
      omega
    · contradiction

theorem nonnegative_remaining (s : State) : 0 ≤ s.unfinished := Nat.zero_le _

theorem no_completion_before_predecessors (s t : State) (id units cost : Nat) (ps : List Nat)
    (h : finish s id units cost ps = some t) (fresh : s.seen.contains id = false) :
    ready s ps = true := by
  unfold finish at h
  simp only [fresh, Bool.false_eq_true, ↓reduceIte] at h
  split at h
  · simp_all
  · contradiction

theorem completion_preserves_authority_residuals (s t : State) (id units cost : Nat)
    (ps : List Nat) (h : finish s id units cost ps = some t) :
    t.authority = s.authority ∧ t.residuals = s.residuals := by
  unfold finish at h
  split at h
  · cases Option.some.inj h
    exact ⟨rfl, rfl⟩
  · split at h
    · cases Option.some.inj h
      exact ⟨rfl, rfl⟩
    · contradiction

theorem duplicate_result_no_credit (s : State) (id units cost : Nat) (ps : List Nat)
    (h : s.seen.contains id = true) : finish s id units cost ps = some s := by
  simp only [finish, h, ite_true]

theorem followup_preserves_source (s : State) (n : Nat) :
    (followup s n).residuals = s.residuals ∧ (followup s n).authority = s.authority := by
  simp [followup]

theorem model_activation_no_authority (s : State) :
    (activateModel s).authority = s.authority := rfl

end CapacityCore
