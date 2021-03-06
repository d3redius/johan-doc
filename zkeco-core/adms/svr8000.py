#!/usr/bin/python
# -*- coding: utf-8 -*-
import wsgiserver
import os
import sys
import django.core.handlers.wsgi
import dict4ini

from conf.apacheConf import apacheConf
from conf.nginxConf import nginxConf

def writeRegForPython(path):
        import win32api
        import win32con
        key=win32api.RegOpenKey(win32con.HKEY_LOCAL_MACHINE, "SOFTWARE", 0, win32con.KEY_ALL_ACCESS)
        key2=win32api.RegCreateKey(key, "Python\\PythonCore\\2.5\\PythonPath")
        win32api.RegSetValueEx(key2,'',0,win32con.REG_SZ, path)

class server():
        server_type='Simple'
        def __init__(self, configFile='attsite.ini'):
                os.environ['DJANGO_SETTINGS_MODULE'] = 'mysite.settings'
                p=os.getcwd()
                self.p=p
                os.environ['PATH']="%(p)s\\Apache2\\bin;%(p)s\\Python25;%(p)s\\mssql"%{"p":p}+os.environ['PATH']
                newpath="%INSTALL_PATH%\\mssql;%INSTALL_PATH%\\mssql\\win32;%INSTALL_PATH%\\mssql\\win32\\lib;%INSTALL_PATH%\\Python25;%INSTALL_PATH%\\Python25\\Lib\\site-packages;%INSTALL_PATH%".replace('%INSTALL_PATH%',p).split(";")
                for p in newpath:
                        if p not in sys.path:
                                sys.path.append(p)
#                print "sys.path:", sys.path
                self.address='0.0.0.0:80'
                self.numthreads=10
                self.queue_size=200        
                self.port=80
                self.fcgiPort=10026
                if os.path.exists(p+"/"+configFile+".dev"):
                    configFile+=".dev"
                if os.path.exists(p+"/"+configFile):
                        cfg=dict4ini.DictIni(p+"/"+configFile, values={'Options':
                        {'Port':80, 
                         'IPAddress':'0.0.0.0', 
                         'Type': self.server_type,
                         'NumThreads': 10,
                         'QueueSize': 200,
                         'FcgiPort': 10026,
                        }})
                        self.port=cfg.Options.Port
                        self.address="%s:%s"%(cfg.Options.IPAddress, cfg.Options.Port)
                        self.server_type=cfg.Options.Type
                        self.numthreads=cfg.Options.NumThreads
                        self.queue_size=cfg.Options.QueueSize
                        self.fcgiPort=cfg.Options.FcgiPort

#                print "address=%s,number of threads=%s,queue size=%s"%(self.address,self.numthreads,self.queue_size)
                print "Start Automatic Data Master Server ... ...\nOpen your web browser and go http://%s"%(self.address.replace("0.0.0.0","127.0.0.1"))+"/"

        def runWSGIServer(self):        
#                print "runWSGIServer"
                address=tuple(self.address.split(":"))
                wserver = wsgiserver.CherryPyWSGIServer(
                        (address[0], int(address[1])),
                        django.core.handlers.wsgi.WSGIHandler(),
                        server_name='www.bio-Device.com',
                        numthreads = self.numthreads,
                        request_queue_size=self.queue_size,
                )
                try:
                        wserver.start()
                except KeyboardInterrupt:
                        wserver.stop()

        def runSimpleServer(self):
                '''
                Django 内置服务器运行
                '''
#                print "runSimpleServer"
                from django.core.management import execute_manager
                from mysite import settings 
                execute_manager(settings, [self.p+'/mysite/manage.py', 'runserver', self.address])
        
        def runApacheServer(self):
#                print "runApacheServer"
                writeRegForPython(";".join(sys.path))
                from dbapp.utils import tmpFile
                fn=tmpFile('apache.conf', 
                        apacheConf%{
                                "address":self.address, 
                                "path": self.p.replace("\\","/"),
                                "numthreads":self.numthreads,
                                "request_queue_size":self.queue_size,
                        }, False)
                os.system("%s\\Apache2\\bin\\apache.exe -f \"%s\""%(self.p,fn))

        def runNginxServer(self):
                from django.core.servers.fastcgi import runfastcgi
                from django.core.management import setup_environ
                from mysite import settings
                os.chdir("%s/../../python-support/nginx"%self.p)
                fname="conf/site.conf"
                f=file(fname, "w+")
                confStr=nginxConf%{"PORT":self.port, "FCGI_PORT":self.fcgiPort}
                f.write(confStr)
                f.close()
                if os.name=='posix': 
                        os.system("""./nginx -s stop""")
                        os.system("""./nginx""")
                else: #'nt', windows
                        os.system("""nginx.exe -s stop""")
                        os.system("""start nginx.exe""")
                os.chdir(self.p)
                address=("0.0.0.0",self.fcgiPort)
                wserver = wsgiserver.CherryPyWSGIServer(
                        (address[0], int(address[1])),
                        django.core.handlers.wsgi.WSGIHandler(),
                        server_name='www.bio-Device.com',
                        numthreads = self.numthreads,
                        request_queue_size=self.queue_size,
                )
                try:
                        wserver.start()
                except KeyboardInterrupt:
                        wserver.stop()
                #print "startup fcgi module ..."
                """if os.name=='posix': 
                        setup_environ(settings)
                        runfastcgi(method="threaded", maxrequests=500, protocol="fcgi", host="localhost", port=self.fcgiPort)
                else: #runfcgi method=threaded host=localhost port=10026
                        from django.core.management import execute_manager
                        sys.argv.append("runfcgi") 
                        sys.argv.append("method=thread") 
                        sys.argv.append("host=localhost") 
                        sys.argv.append("port=%s"%self.fcgiPort)
                        execute_manager(settings)
				"""
        def run(self):
                if self.server_type=='Apache': return self.runApacheServer()
                if self.server_type=='WSGI': return self.runWSGIServer()
                if self.server_type=='Nginx': return self.runNginxServer()
                self.runSimpleServer()
                
if __name__ == "__main__":
        config="attsite.ini"
        try:
                config=sys.argv[1]
        except: pass
        server(config).run()
        
