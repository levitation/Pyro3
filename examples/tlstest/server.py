import threading
import sys
import Pyro.core
try:
    import win32com.client, pythoncom
    has_com=True
except ImportError:
    has_com=False
    
class TestServer(Pyro.core.ObjBase):
    def ping(self):
        threadid=threading.currentThread().ident
        tls=self.getLocalStorage()
        output="server: ping, tls=%s, threadid=%s, TLS threadid=%s\n" % (id(tls), threadid, tls.threadid)
        sys.stdout.write(output)
        sys.stdout.flush()
        if tls.threadid!=threadid:
            sys.stdout.write("!!!!! ERROR: threadids aren't identical !!!!!\n")
            sys.stdout.flush()
    def oneway(self):
        threadid=threading.currentThread().ident
        tls=self.getLocalStorage()
        output="server: oneway, tls=%s, threadid=%s, TLS threadid=%s\n" % (id(tls), threadid, tls.threadid)
        sys.stdout.write(output)
        sys.stdout.flush()
        if tls.threadid!=threadid:
            sys.stdout.write("!!!!! ERROR: threadids aren't identical !!!!!\n")
            sys.stdout.flush()
    def comcall(self):
        if not has_com:
            print "server: no com, doing nothing"
            return
        else:
            locator=win32com.client.Dispatch("WbemScripting.SwbemLocator")
            top = locator.ConnectServer(".", r"\\.\root\cimv2")
            users = top.InstancesOf("Win32_UserAccount")
            names=[]
            for u in users:
                names.append(u.name)
            return names


def initTLS(tls):
    threadid=threading.currentThread().ident
    if has_com:
        pythoncom.CoInitialize()   # initialize COM for this thread
    sys.stdout.write("server: initTLS, tls=%s, threadid=%s\n" % (id(tls),threadid))
    sys.stdout.flush()
    tls.threadid=threadid

daemon=Pyro.core.Daemon()
obj=TestServer()
uri=daemon.connect(obj)
daemon.setInitTLS(initTLS)
print "URI=",uri
print "server running"
daemon.requestLoop()
