import unittest
from host_supervisor import validate_allocation
import host_supervisor as h
from pathlib import Path
from unittest.mock import patch
class Alloc(unittest.TestCase):
 def setUp(self):
  self.f={'JobId':'12','JobState':'RUNNING','UserId':'user(55)','Account':'cis260361p','QOS':'rm','Partition':'RM-shared','NumNodes':'1','NumCPUs':'26','CPUs/Task':'26','Requeue':'0','Restarts':'0','TimeLimit':'00:45:00','WorkDir':'/physical/runtime','BatchHost':'r1','AllocTRES':'cpu=26,mem=48G,node=1'}
  self.e={'SLURM_JOB_ID':'12','SLURM_CLUSTER_NAME':'bridges2','SLURM_CPUS_PER_TASK':'26'}
 def test_valid(self):self.assertEqual(validate_allocation(self.f,self.e,55,'r1','/physical/runtime')['cpu'],'26')
 def test_reject_wrong_facts(self):
  for k,v in [('Account','other'),('QOS','gpu'),('Partition','GPU-shared'),('NumCPUs','4'),('WorkDir','/virtual/runtime'),('BatchHost','r2'),('TimeLimit','01:00:00'),('AllocTRES','cpu=26,mem=48G,gres/gpu=1'),('AllocTRES','cpu=26,mem=47G')]:
   with self.subTest(key=k,value=v):
    f=dict(self.f);f[k]=v
    with self.assertRaises((AssertionError,KeyError,ValueError)):validate_allocation(f,self.e,55,'r1','/physical/runtime')
 def test_reject_faked_cluster(self):
  e=dict(self.e,SLURM_CLUSTER_NAME='delta')
  with self.assertRaises(AssertionError):validate_allocation(self.f,e,55,'r1','/physical/runtime')
class Relocation(unittest.TestCase):
 def test_physical_packet_maps_to_virtual_path(self):
  with patch.object(h,'PHYS',Path('/physical')),patch.object(h,'VIRT',Path('/virtual')),patch.object(h,'R',Path('/virtual/runtime')),patch.dict(h.os.environ,{'SLURM_JOB_ID':'12'},clear=True):
   argv=h.container_command(Path('/physical/packet'),Path('/physical/output'),'abc',42)
  self.assertIn('/virtual/packet/inner.sh',argv);self.assertIn('/physical:/virtual:ro',argv);self.assertIn('/physical/output:/virtual/output:rw',argv);self.assertNotIn('--nv',argv)
if __name__=='__main__':unittest.main()
