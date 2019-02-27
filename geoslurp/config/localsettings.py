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
# License along with geoslurp; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301  USA

# Author Roelof Rietbroek (roelof@geod.uni-bonn.de), 2018
import os
import sys
import yaml
from datetime import datetime
import keyring
import getpass
def readLocalSettings(args):
    """Retrieves/updates last used settings from the local settings file .geoslurp_lastused.yaml"""
    settingsFile=os.path.join(os.path.expanduser('~'),'.geoslurp_lastused.yaml')
    #read last used settings
    if os.path.exists(settingsFile):
        #Read parameters from yaml file
        with open(settingsFile, 'r') as fid:
            lastOpts=yaml.safe_load(fid)
    else:
        lastOpts={}

    isUpdated=False

    #update dict with provided options from args
    if args.host:
        lastOpts["host"]=args.host
        isUpdated=True
    else:
        #take data from file options
        try:
            args.host=lastOpts["host"]
        except KeyError:
            print("--host option is needed for initialization",file=sys.stderr)
            sys.exit(1)

    if args.user:
        lastOpts["user"]=args.user
        isUpdated=True
    else:
        try:
            args.user=lastOpts["user"]
        except KeyError:
            print("--user option is needed for initialization",file=sys.stderr)
            sys.exit(1)

    if args.usekeyring:
        lastOpts["useKeyring"]=True
        isUpdated=True
    else:
        try:
            args.usekeyring=lastOpts["useKeyring"]
        except KeyError:
            #don't use the keyring
            pass

    #write out  options to file to store these settings
    if isUpdated:
        lastOpts["lastupdate"]=datetime.now()
        with open(settingsFile,'w') as fid:
            yaml.dump(lastOpts, fid, default_flow_style=False)


    # we take a different strategy for the password as we don't want to store this unencrypted in a file
    if not args.password:
        if args.usekeyring:
            args.password=keyring.get_password("geoslurp",args.user)
            if not args.password:
                args.password=getpass.getpass(prompt='Please enter password: ')
        else:
            #try checking the environment variable GEOSLURP_PGPASS
            try:
                args.password=os.environ["GEOSLURP_PGPASS"]
            except KeyError:
                args.password=getpass.getpass(prompt='Please enter password: ')
    else:
        #update keyring
        if args.usekeyring:
            keyring.set_password("geoslurp",args.user,args.password)
