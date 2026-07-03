from verification_ecology_kit.audit.schema_overclosure import audit_schema_overclosure

report = audit_schema_overclosure(
    schema_rejected_unknown=True,
    suppressed_residuals=("schema-incompatible-residual",),
)
print(report.to_json())
