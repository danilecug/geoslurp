# This file is part of geoslurp.
# geoslurp is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 3 of the License, or (at your option) any later version.

# geoslurp is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.

# You should have received a copy of the GNU Lesser General Public
# License along with Frommle; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301  USA

# Author Roelof Rietbroek (roelof@geod.uni-bonn.de), 2018

from .slurpconf import slurpconf
from .geoslurpClient import geoslurpClient
from .PluginManager import PluginManager
from sqlalchemy.orm import load_only
from geoslurp.geoslurpClient import Invent
from sqlalchemy.schema import CreateSchema
class taskScheduler():
    """Manages and schedules geoslurp tasks"""
    def __init__(self,conffile):
        """Gathers all the necessary components to have a working geoslurp instance"""
        
       #read configuration stuff
        self.conf=slurpconf(conffile)
        #set up a database connector 
        self.db=geoslurpClient(self.conf["dburl"])

        #load available plugins
        self.plugman=PluginManager(self.conf['PluginDir'])
        
    
    def addArgs(self,parser):
        """Add top level command line arguments (and request arguments from the plugins)"""
        
        parser.add_argument('--printconfig',action='store_true',help='Prints out default configuration (default file is ~/.geoslurp.yaml)')
        parser.add_argument('--cleancache',action='store_true',help="Clean up the cache directory")
        parser.add_argument('-l','--list',action='store_true',help="list registered datasources from the inventory")
        parser.add_argument('--purge',action='store_true',help="Purge selected datasource from the database (both entries and data)") 
        #also add datasource options
        subparsers = parser.add_subparsers(help='Datasource to select (type geoslurpd.py DATASOURCE --help for detailed options)',dest='datasource')
        for key,cl in self.plugman.plugins.items():
            cl.addParserArgs(subparsers)
    
    
    def execTasks(self,args):
        """execute tasks as requested by the arguments"""
        if args.printconfig:
            self.conf.printDefault()
        
        if args.cleancache:
            self.cleancache()
        
        if args.list:
            #retrieve the entries from the inventory table
            ses=self.db.Session()
            dbinvent=ses.query(Invent).options(load_only('datasource','lastupdate'))
            for ds in dbinvent:
                print("Datasource:",ds.datasource,", last updated:",ds.lastupdate)
        if not args.datasource:
            return
        
        if args.purge:
            self.purge(args.datasource)
            return
        #iextract datasource specific configuration
        confds=self.conf.getDataSource(args.datasource)    

        #if we land here we pass the arguments to the plugin calss itself
        self.plugman.plugins[args.datasource](self.db,confds).parseAndExec(args)


    def cleancache(self):
        """cleans the Cache directory entirely"""
        for f in  os.listdir(self.conf['CacheDir']):
            filep=os.path.join(self.conf['CacheDir'],f)
            if os.path.isfile(f):
                #print(filep)
                os.unlink(filep)
            elif os.path.isdir(filep):
                shutil.rmtree(filep)
    
    
    def purge(self,datasource):
        """purge selected datasource (db tables and data files)"""
        #remove the datadir and it's content
        try:
            ddir=self.conf[datasource]['DataDir']
            if os.path.isdir(ddir):
                shutil.rmtree(ddir)
        except KeyError:
            pass

        #now also remove the scheme and all tables/indexes
        self.db.dropSchema(datasource,cascade=True)
        #remove entry in the inventory
        ses=self.db.Session()
        ses.query(Invent).filter(Invent.datasource == datasource).delete()
        ses.commit() 

        
