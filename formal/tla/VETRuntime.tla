---- MODULE VETRuntime ----
EXTENDS Naturals, Sequences

CONSTANTS Residuals, ExternalPackets

VARIABLES routed, quarantined, internalized, authorityAllowed

Init ==
  /\ routed = {}
  /\ quarantined = {}
  /\ internalized = {}
  /\ authorityAllowed = FALSE

RouteResidual(r) ==
  /\ r \in Residuals
  /\ routed' = routed \cup {r}
  /\ UNCHANGED <<quarantined, internalized, authorityAllowed>>

QuarantineExternal(p) ==
  /\ p \in ExternalPackets
  /\ quarantined' = quarantined \cup {p}
  /\ UNCHANGED <<routed, internalized, authorityAllowed>>

InternalizeExternal(p) ==
  /\ p \in ExternalPackets
  /\ p \in quarantined
  /\ routed = Residuals
  /\ internalized' = internalized \cup {p}
  /\ UNCHANGED <<routed, quarantined, authorityAllowed>>

AllowAuthority ==
  /\ ExternalPackets \subseteq internalized
  /\ routed = Residuals
  /\ authorityAllowed' = TRUE
  /\ UNCHANGED <<routed, quarantined, internalized>>

Next ==
  \/ \E r \in Residuals : RouteResidual(r)
  \/ \E p \in ExternalPackets : QuarantineExternal(p)
  \/ \E p \in ExternalPackets : InternalizeExternal(p)
  \/ AllowAuthority

Spec == Init /\ [][Next]_<<routed, quarantined, internalized, authorityAllowed>>

NoAuthorityBeforeQuarantine ==
  authorityAllowed => ExternalPackets \subseteq quarantined

NoAuthorityBeforeResidualRouting ==
  authorityAllowed => routed = Residuals

====
