import Pyro.core
import Pyro.naming
import Pyro.errors
import pprint

class MyPyroObj(Pyro.core.ObjBase):
	def __init__(self):
		Pyro.core.ObjBase.__init__(self)
	def method(self, arg):
		return arg*2

daemon=Pyro.core.Daemon()
ns=Pyro.naming.NameServerLocator().getNS()
daemon.useNameServer(ns)

try:
	ns.deleteGroup(":disconnect")
except Pyro.errors.NamingError:
	pass
ns.createGroup(":disconnect")

obj1=MyPyroObj()
obj2=MyPyroObj()
obj3=MyPyroObj()
obj4=MyPyroObj()
uri1=daemon.connect(obj1,":disconnect.testobject1")
uri2=daemon.connect(obj2,":disconnect.testobject2")
uri3=daemon.connect(obj3,":disconnect.testobject3")
uri4=daemon.connect(obj4,":disconnect.testobject4")

print "registered objects:"
pprint.pprint(daemon.getRegistered())
print "objects in name server:"
pprint.pprint(ns.list(":disconnect"))

print
print "Removing object 1 by calling daemon.disconnect(obj)"
daemon.disconnect(obj1)
print "registered objects:"
pprint.pprint(daemon.getRegistered())
print "objects in name server:"
pprint.pprint(ns.list(":disconnect"))

print
print "Removing object 2 by calling daemon.disconnect(uri2.objectID)"
daemon.disconnect(uri2.objectID)
print "registered objects:"
pprint.pprint(daemon.getRegistered())
print "objects in name server:"
pprint.pprint(ns.list(":disconnect"))

print
print "Removing all other objects by looping over the registered object ids"
for objectID in daemon.getRegistered().keys():
	daemon.disconnect(objectID)
print "registered objects:"
pprint.pprint(daemon.getRegistered())
print "objects in name server:"
pprint.pprint(ns.list(":disconnect"))


daemon.shutdown()

