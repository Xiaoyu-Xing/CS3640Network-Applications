from mininet.topo import Topo
from mininet.net import Mininet
from mininet.node import OVSKernelSwitch, Switch, Controller
from mininet.link import TCLink
from mininet.log import setLogLevel

#setLogLevel('debug')

def create_new_topology(topology_vector):
	# vector is constructed as: 
	# there are n switches (s[0], ..., s[n-1]), where n is the length of topology_vector.
	# the  ith  switch s[i-1] is connected to topology_vector[i-1] end-hosts (h[i-1][0], ..., h[i-1][topology[i-1]-1]).
    newTopo = Topo()
    if topology_vector: # Verifies there are values in topology_vector before doing any work.
        for ind, switch in enumerate(topology_vector):
            if ind == 0: # Creates 1st switch of the network.
                newSwitch = 's'+str(ind)
                newTopo.addSwitch(newSwitch)
                i = 0
                while i < int(switch): # Creates hosts & links to switch per topology_vector value.
                    newHost = 'h'+str(ind)+str(i)
                    newTopo.addHost(newHost)
                    newTopo.addLink(newSwitch,newHost)
                    i += 1
            else:
                newSwitch = 's'+str(ind)
                prevSwitch = 's'+str(ind-1)
                newTopo.addSwitch(newSwitch)
                newTopo.addLink(newSwitch,prevSwitch)
                i = 0
                while i < int(switch):
                    newHost = 'h'+str(ind)+str(i)
                    newTopo.addHost(newHost)
                    newTopo.addLink(newSwitch,newHost)
                    i += 1
    
    return newTopo

def test_pingall(topology):

    Network = Mininet()
    Network.buildFromTopo(topology)
    Network.start()
    result = Network.pingAll()
    Network.stop()
    if result == 0:
        return True
    else:
        return False
        

if "__name__" == "__main__":
	test_pingall(create_new_topology([1, 2, 1]))