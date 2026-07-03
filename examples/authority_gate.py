from verification_ecology_kit.digest import Digest
from verification_ecology_kit.model.authority import AuthorityDecision, AuthorityEngine
from verification_ecology_kit.model.records import (
    AuthorityAction,
    AuthorityDecisionValue,
    LifecycleStatus,
)

decision = AuthorityDecision(
    authority_decision_id="auth-deploy",
    object_id="packet-1",
    schema_version="1.0",
    canonical_digest=Digest("sha256", "example"),
    lifecycle_status=LifecycleStatus.ACTIVE,
    policy_id="local-policy",
    action=AuthorityAction.DEPLOYMENT,
    decision=AuthorityDecisionValue.ALLOW,
    required_support_refs=("support-judgment",),
    support_judgment_refs=("support-judgment",),
)

value, result = AuthorityEngine().aggregate(
    AuthorityAction.DEPLOYMENT,
    [decision],
    required_support_refs=("support-judgment",),
)
print({"decision": value.value, "check": result.to_dict()})
