from verification_ecology_kit import VerifierPacket

packet = VerifierPacket.minimal()
packet.boundary_refs.destructive_boundary_ref = "boundary-destructive-1"
packet.boundary_refs.narrowing_boundary_ref = "boundary-narrowing-1"
packet.counter_packet_refs.append("counter-packet-1")

for result in packet.validate():
    print(result.to_dict())
