#!/usr/bin/env python3
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

#Command line program to Download and manage Earth science data

import sys
import argparse
from geoslurp.db import Inventory
from geoslurp.db import GeoslurpConnector
import json
import logging
from geoslurp.db import Settings
from geoslurp.config.localsettings import readLocalSettings
from geoslurp.config.register import geoslurpregistry
import geoslurp.dataset
import getpass
import re

def main(argv):
    usage=" Program to download and manage Earth Science data"
    parser = argparse.ArgumentParser(description=usage,add_help=False)


    # add various arguments to the program
    addCommandLineArgs(parser)

    args = parser.parse_args(argv[1:])
    check_args(args,parser)


    # We need a point of contact to communicate with the database
    try:

        DbConn=GeoslurpConnector(args.host,args.user,args.password)
    except Exception as e:
        print(e)
        print("Cannot connect to postgresql database, quitting")
        sys.exit(1)


    # # Process common options

    #Add a new user
    if args.add_user:
        passw1=getpass.getpass(prompt='Please enter new password: ')
        passwcheck=getpass.getpass(prompt='Reenter password: ')
        if passw1 != passwcheck:
            print("Passwords do not match, please try again")
            sys.exit(1)
        else:
            DbConn.addUser(args.add_user,passw1)

    #print registered datasets (i.e. tables)
    if args.info:
        slurpInvent=Inventory(DbConn)
        print("Registered datasets (scheme.dataseti, owner, lastupdate):")
        if args.dset:
            #print a summary of the inventory
            dsetpat=re.compile(args.dset)
            for entry in slurpInvent:
                if dsetpat.search(entry.scheme+'.'+entry.dataset):
                    print("%s.%s %s %s"%(entry.scheme,entry.dataset,entry.owner,entry.lastupdate.isoformat()))
        else:
            #print a summary of the inventory
            for entry in slurpInvent:
                print("%s.%s %s %s"%(entry.scheme,entry.dataset,entry.owner,entry.lastupdate.isoformat()))
    
    
    #change settings in the database
    
    # Initializes an object which holds the current settings
    conf=Settings(DbConn)

    if args.config:
        #register user settings in the database
        conf.update(args.config)

    if args.admin_config:
        #register admin/default settings in the database
        conf.defaultupdate(args.admin_config)

    if args.auth_config:
        conf.updateAuth(args.auth_config)

    datasets=geoslurpregistry.getDatasets(conf,args.dset)
    
    if args.list:
        # show available schemes and datasets
        print("Available datasets (SCHEME.DATASET):")
        for ds in datasets:
            print("\t%s.%s"%(ds.scheme,ds.__name__))
    

    if args.pull or args.update:
        if type(args.pull) == dict:
            pullopts=args.pull
        elif type(args.update) == dict:
            pullopts=args.update
        else:
            pullopts={}
        args.pull=True

    if args.register or args.update:
        if type(args.register) == dict:
            regopts=args.register
        elif type(args.update) == dict:
            regopts=args.update
        else:
            regopts={}
        args.register=True
    
    if not (args.pull or args.register or args.purge_cache or args.purge_data or args.purge_entry):
        sys.exit(0)
    
    for dsclass in datasets:
        ds=dsclass(DbConn)

        if args.data_dir:
            ds.setDataDir(args.data_dir)
        
        if args.cache_dir:
            ds.setCacheDir(args.cache_dir)

        # import pdb;pdb.set_trace()
        if args.purge_cache:
            ds.purgecache(args.purge_cache)

        if args.purge_data:
            ds.purgedata(args.purge_data)
        # import pdb;pdb.set_trace()
        if args.purge_entry:
            ds.purgeentry(args.purge_entry)

        if args.pull:
            try:
                ds.pull(**pullopts)
            except KeyboardInterrupt:
                ds.halt()

        if args.register:
            try:
                ds.register(**regopts)
            except KeyboardInterrupt:
                ds.halt()
        #We need to explicitly delete the dataset instance or else the database QueuePool gets exhausted 
        del ds

class JsonParseAction(argparse.Action):
    """Parse Arguments provided as JSON into dictionaries"""
    def __init__(self, option_strings, dest, nargs, **kwargs):
        super(JsonParseAction, self).__init__(option_strings, dest,nargs, **kwargs)
    def __call__(self, parser=None, namespace=None, values=None, option_string=None):
        if values:
            dct=json.loads(values)
        else:
            dct=True
        setattr(namespace, self.dest, dct)

class increaseVerboseAction(argparse.Action):
    """Parse multiple v's to increase the level of the verbosity"""
    def __init__(self, option_strings, dest, nargs, **kwargs):
        super(increaseVerboseAction, self).__init__(option_strings, dest,nargs, **kwargs)
    def __call__(self, parser=None, namespace=None, values=None, option_string=None):
        setattr(namespace,self.dest,namespace.verbose+values.count('v'))
        levels=[logging.CRITICAL, logging.ERROR, logging.WARNING, logging.INFO,logging.DEBUG]
        logging.basicConfig(level=levels[min(namespace.verbose,4)])

def addCommandLineArgs(parser):
        """Add top level command line arguments (and request arguments from the loaded schema)"""
        parser.add_argument('-h','--help',action='store_true',
                             help="Prints detailed help (may be used in combination with --dset for detailed JSON options)")
        parser.add_argument('-i','--info',action='store_true',
                            help="Show information about selected datasets")

        parser.add_argument('-l','--list',action='store_true',
                            help="List datasets which are available to use")

        # parser.add_argument('--purge-scheme',action='store_true',
        #                     help="Purge selected scheme (This deletes all related datasets as well!")

        parser.add_argument('--purge-cache',type=str, metavar='filter',const='*',nargs='?',
                            help="Purge the cache of the selected dataset. while optionally applying a filter for the files")

        parser.add_argument('--purge-data',type=str, metavar='filter',const='*',nargs='?',
                            help="Purge the data of the selected dataset. while optionally applying a filter for the files")

        parser.add_argument('--purge-entry',type=str, metavar='filter',const='*',nargs='?',
                            help="Purge the database entry of the selected dataset. Optionally applying a filter for the files")

        parser.add_argument("--pull", metavar="JSON",action=JsonParseAction, nargs="?",const=False,default=False,
                            help="Pull data from online resource (possibly pass on options as a JSON dict")

        parser.add_argument("--register", metavar="JSON",action=JsonParseAction, nargs="?",const=False, default=False,
                            help="Register data in the database (possibly pass on options as a JSON dict)")

        parser.add_argument("--update", metavar="JSON", action=JsonParseAction, nargs="?",const=False,default=False,
                            help="Implies both --pull and --register, but applies only to the updated data (accepts JSON options)")


        parser.add_argument("--config", metavar="JSON",action=JsonParseAction, nargs="?",const=False, default=False,
                            help="Register user settings  (pass as a JSON dict, e.g. {\"DataDir\":\"path/\"})")


        parser.add_argument("--auth-config", metavar="JSON",action=JsonParseAction, nargs="?",const=False, default=False,
                            help="Register (and encrypt on a user basis in the database) authentification services "
                                 "(pass as a JSON dict, e.g. {\"servicename\":{\"user\":..,\"passw\":...}})")
        
        parser.add_argument("--admin-config", metavar="JSON",action=JsonParseAction, nargs="?",const=False, default=False,
                            help="Register admin/default settings  (pass as a JSON dict, e.g. {\"DataDir\":\"path/\"})")
       
        parser.add_argument("--host",metavar="hostname",type=str,
                            help='Select host where the PostgreSQL/PostGIS server is running')

        parser.add_argument("--user",metavar="user",type=str,
                            help='Select postgresql user')

        parser.add_argument("--add-user",metavar="username",type=str,
                            help='Add a new postgresql user (you will be prompted for a password)')


        parser.add_argument("--password",metavar="password",type=str,
                            help='Select password for the postgresql user')

        parser.add_argument("--usekeyring",action='store_true',
                            help='Set and get the system keyring to store the database password (alternatives are '
                                 'using --password or the environment variable GEOSLURP_PGPASS')

        parser.add_argument("-v","--verbose", action=increaseVerboseAction, nargs="?",const='',default=3,
                            help="Increase verbosity of the output one cvan use multiple v's after another (e.g. -vv) "
                                 "to increase verbosity. The default prints errors only")

        parser.add_argument('--data-dir',type=str,metavar='DIR',nargs=1,
                help="Specify (and register) a dataset specific data directory DIR")
        
        parser.add_argument('--cache-dir',type=str,metavar='DIR',nargs=1,
                help="Specify (and register) a dataset specific cache directory DIR")
        #also look for datasets 
        parser.add_argument("-d","--dset",metavar="PATTERN",nargs="?",type=str,
                help='Select datasets or all datasets in a scheme (PATTERN is treated as a regular expression applied to the string SCHEME.DATASET)')



def check_args(args,parser):
    """Sanity check for input arguments and possibly supply detailed help"""

    if not any(vars(args).values()):
        print(__file__+' Error: no arguments provided, try --help', file=sys.stderr)
        sys.exit(1)

    if args.help:
        if not args.dset:
            parser.print_help()
        else:
            datasets=geoslurpregistry.getDatasets(None,args.dset)
            for ds in datasets:
                print("Detailed info on %s options which may be provided as JSON dictionaries"%(ds.__name__))
                print("\t%s.pull:\n\t\t %s"%(ds.__name__,ds.pull.__doc__))
                print("\t%s.register:\n\t%s"%(ds.__name__,ds.register.__doc__))

        sys.exit(0)
    #also fillout last options with defaults from the last call
    readLocalSettings(args)


if __name__ == "__main__":
    main(sys.argv)
