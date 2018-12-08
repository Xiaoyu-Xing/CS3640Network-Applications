def test_iperf(em_net, traffic_properties):
    source = traffic_properties.get('source')
    destination = traffic_properties.get('destination')
    
    return Mininet.iperf(em_net, hosts=[source,destination],seconds=traffic_properties.get('time'))