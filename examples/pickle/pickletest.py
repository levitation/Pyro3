import Pyro.core
import Pyro.protocol
import Pyro.errors
import Pyro.naming
import Pyro.EventService.Clients
import Pyro.EventService.Server
import Pyro.configuration

import cPickle as pickle

import sys
if sys.version_info < (2,5):
	raise SystemExit("this test only runs on Python 2.5 or newer")

# a list of all classes to be tested for pickleability
classes=[
	Pyro.configuration.Config,
	Pyro.core.ObjBase,
	Pyro.core.CallbackObjBase,
	
	Pyro.core.PyroURI,
	Pyro.core.DynamicProxy,
	Pyro.core.DynamicProxyWithAttrs,
	
	Pyro.errors.PyroError,
	Pyro.errors.NamingError,
	Pyro.errors.PyroExceptionCapsule,
	
	Pyro.naming.NameServerLocator,
	Pyro.naming.NameServerProxy,
	
	Pyro.protocol.PYROAdapter,
	# Pyro.protocol.PYROSSLAdapter,
	Pyro.protocol.DefaultConnValidator,
	Pyro.protocol.BasicSSLValidator,
	Pyro.protocol.LocalStorage,
	
	Pyro.EventService.Server.Event,
	Pyro.EventService.Server.EventService,
]

# various helper constructors follow
def createConfig(clazz):
	c=clazz()
	c.setup(None)
	return c
	
def createNameserverProxy(clazz):
	locator=Pyro.naming.NameServerLocator(identification="identify")
	ns=locator.getNS()
	if isinstance(ns,clazz):
		return ns
	raise TypeError("wrong class")

def createPyroAdapter(clazz):
	a=clazz()
	a.setOneway(["method"])
	a.setTimeout(42)
	a.setIdentification("identify")
	return a

# A table of object constructors for various types.
# If a type isn't present, its base type is tried.
constructors={
	object: lambda c: c(),
	str: lambda c: c("test"),
	int: lambda c: c(42),
	dict: lambda c: c({"test":42}),
	Exception: lambda c: c("errormessage"),
	Pyro.configuration.Config: createConfig,
	Pyro.core.PyroURI: lambda c: c("PYRO://127.0.0.1:9999/objectid"),
	Pyro.core.DynamicProxy: lambda c: c("PYRO://127.0.0.1:9999/objectid"),
	Pyro.errors.PyroExceptionCapsule: lambda c: c(Exception("errormessage"),"some error"),
	Pyro.naming.NameServerProxy: createNameserverProxy,
	Pyro.naming.NameServerLocator: lambda c: c(identification="identify"),
	Pyro.EventService.Server.Event: lambda c: c("subject","message"),
	Pyro.protocol.PYROAdapter: createPyroAdapter,
}

# check if objects are the same according to various attributes
def compareObjects(obj1,obj2):
	if type(obj1) is type(obj2):
		t=type(obj1)
		if t in (str,int,dict,tuple):
			return obj1==obj2
		if t in (Pyro.configuration.Config, Pyro.core.PyroURI):
			return obj1==obj2
		if t in (Pyro.core.ObjBase, Pyro.core.CallbackObjBase):
			return obj1.objectGUID==obj2.objectGUID and \
				   obj1.delegate==obj2.delegate and \
				   obj1.lastUsed==obj2.lastUsed
		if isinstance(obj1, Exception):
			return obj1.args==obj2.args
		if t is Pyro.errors.PyroExceptionCapsule or obj1.__class__==Pyro.errors.PyroExceptionCapsule:
			return type(obj1.excObj)==type(obj2.excObj) and \
				   obj1.__class__==obj2.__class__ and\
				   obj1.excObj.args==obj2.excObj.args and \
				   obj1.args==obj2.args
		if t is Pyro.naming.NameServerLocator:
			return obj1.identification==obj2.identification
		if t in (Pyro.naming.NameServerProxy,Pyro.core.DynamicProxy,Pyro.core.DynamicProxyWithAttrs):
			return obj1.URI==obj2.URI and \
				   obj1.objectID==obj2.objectID and \
				   compareObjects(obj1.adapter,obj2.adapter)
		if t is Pyro.protocol.PYROAdapter:
			return obj1.ident==obj2.ident and \
				   obj1.timeout==obj2.timeout and \
				   obj1.onewayMethods==obj2.onewayMethods
		if t in (Pyro.protocol.LocalStorage, Pyro.protocol.DefaultConnValidator,
				 Pyro.protocol.BasicSSLValidator, Pyro.EventService.Server.Event,
				 Pyro.EventService.Server.EventService, Pyro.EventService.Clients.Publisher):
			return obj1.__dict__==obj2.__dict__
		print "NO COMPARE FOR TYPE",t
	return False
		
# Create a list of objects to be tested for pickleability. 
# An object is created for every class in the class list.
def createTestObjects(classes, verbose=False):
	def createObject(clazz):
		def findConstructor(clazz):
			if not clazz:
				return None,None
			if clazz in constructors:
				return constructors[clazz],clazz
			return findConstructor(clazz.__base__)
		constr,clazz2=findConstructor(clazz)
		return constr(clazz),clazz in constructors,clazz2
	objects=[]
	for clazz in classes:
		obj,specified,clazz2=createObject(clazz)
		objects.append(obj)
		if not specified and verbose:
			print "Warning, no specific constructor for",clazz.__name__,", used:",clazz2.__name__
	return objects

# Do the pickle test!
def pickletest(objects, protocol):
	print "----------------------------"
	print "Pickle test with protocol",protocol
	goodcount=0
	for obj in objects:
		print obj.__class__.__name__,":",
		try:
			p=pickle.dumps(obj,protocol=protocol)
			try:
				obj2=pickle.loads(p)
				try:
					if compareObjects(obj,obj2):
						print "OK"
						goodcount+=1
					else:
						print "COMPARE FAIL, DICT=",obj.__dict__
				except Exception,x:
					print "COMPARE FAIL:",x
			except Exception,x:
				print "LOADS FAIL:",x
		except Exception,x:
			print "DUMPS FAIL:",x
	print
	errorcount=len(objects)-goodcount
	print "FAILURES:",errorcount, "   OK:",goodcount
	print
	return errorcount
	
# We need to check some special cases more thorougly.
def specialcases(protocol):
	print "SPECIAL CASES"
	errorcount=0
	locator=Pyro.naming.NameServerLocator()
	ns=locator.getNS()
	print "PyroAdapter bound to URI:",
	a=createPyroAdapter(Pyro.protocol.PYROAdapter)
	assert not hasattr(a,"URI")
	assert not hasattr(a,"conn")
	a.bindToURI(ns.URI)
	assert isinstance(a.conn, Pyro.protocol.TCPConnection)
	assert isinstance(a.URI, Pyro.core.PyroURI)
	try:
		s=pickle.dumps(a,protocol=protocol)
		a2=pickle.loads(s)
		assert not hasattr(a,"conn"), "original cannot have conn because of release"
		assert not hasattr(a2,"conn"), "pickled obj cannot have conn"
		if compareObjects(a,a2):
			print "OK"
		else:
			errorcount+=1
			print "COMPARE FAIL, DICT=",a.__dict__
	except Exception,x:
		errorcount+=1
		print "ERROR",x
	print "DynamicProxy bound to URI:",
	p=Pyro.core.getProxyForURI(ns.URI)
	assert not hasattr(p.adapter,"conn")
	p.ping()
	assert isinstance(p.adapter.conn, Pyro.protocol.TCPConnection)
	try:
		s=pickle.dumps(p,protocol=protocol)
		p2=pickle.loads(s)
		assert not hasattr(p2.adapter,"conn"), "pickled obj cannot have conn"
		assert p.adapter is not None, "original must still have conn"
		if compareObjects(p,p2):
			print "OK"
		else:
			errorcount+=1
			print "COMPARE FAIL, DICT=",p.__dict__
	except Exception,x:
		errorcount+=1
		print "ERROR",x
	print "DynamicAttrProxy bound to URI:",
	p=Pyro.core.getAttrProxyForURI(ns.URI)
	assert not hasattr(p.adapter,"conn")
	p.ping()
	assert isinstance(p.adapter.conn, Pyro.protocol.TCPConnection)
	try:
		s=pickle.dumps(p,protocol=protocol)
		p2=pickle.loads(s)
		assert not hasattr(p2.adapter,"conn"), "pickled obj cannot have conn"
		assert p.adapter is not None, "original must still have conn"
		if compareObjects(p,p2):
			print "OK"
		else:
			errorcount+=1
			print "COMPARE FAIL, DICT=",p.__dict__
	except Exception,x:
		errorcount+=1
		print "ERROR",x
	return errorcount

# let's go
def main():
	#initNameServer()
	errorcount=0
	objects=createTestObjects(classes, verbose=True)
	for protocol in range(pickle.HIGHEST_PROTOCOL+1):
		errorcount+=pickletest(objects,protocol)
		errorcount+=specialcases(protocol)	
		objects=createTestObjects(classes, verbose=False)  # new set of objects for next cycle
	print
	print "TOTAL ERRORS:",errorcount   # must be zero!
	
if __name__=="__main__":
	main()
