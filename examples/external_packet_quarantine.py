from verification_ecology_kit.model.circulation import ExternalPacket, LocalSovereignty
from verification_ecology_kit.model.packets import VerifierPacket

packet = VerifierPacket.from_external_candidate()
external = ExternalPacket(packet, source_ecology="partner", received_at="logical-clock-1")
print(LocalSovereignty().quarantine_external(external).to_dict())
