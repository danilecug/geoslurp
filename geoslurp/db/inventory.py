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

#contains a class to work with  the geoslurp inventory table
from sqlalchemy import Column,Integer,String,Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.dialects.postgresql import TIMESTAMP, ARRAY,JSONB
from sqlalchemy.ext.mutable import MutableDict
from sqlalchemy import MetaData

GSBase=declarative_base(metadata=MetaData(schema='admin'))

class InventTable(GSBase):
    """Defines the GEOSLURP POSTGRESQL inventory table"""
    __tablename__='inventory'
    id=Column(Integer, primary_key=True)
    scheme=Column(String)
    dataset=Column(String,unique=True)
    pgfunc=Column(String,unique=True)
    owner=Column(String)
    lastupdate=Column(TIMESTAMP)
    updatefreq=Column(Integer)
    version=Column(ARRAY(Integer,as_tuple=True))
    cache=Column(String)
    datadir=Column(String)
    data=Column(MutableDict.as_mutable(JSONB))
        
class Inventory:
    """Class which provides read/write access to the postgresql inventory table"""
    table=InventTable
    def __init__(self,geoslurpConn):
        """

        :type geoslurpConn: geoslurp database connector
        """
        self.db=geoslurpConn
        self._ses=self.db.Session()

        #creates the inventory table if it doesn't exists
        # if not geoslurpConn.dbeng.has_table(self.table.__tablename__):
            # GSBase.metadata.create_all(geoslurpConn.dbeng)
            # #also grant geoslurp all privileges
            # self.db.dbeng.execute('GRANT ALL PRIVILEGES ON admin.%s to geoslurp'%(self.table.__tablename__))


    def __iter__(self):
        """Query the Inventory table and returns a generator"""
        for entry in self._ses.query(InventTable):
            yield entry

    def __getitem__(self, dataset):
        """Retrieves the entry from the inventory table corresponding to the dataset"""
        #we need to open up a small sqlalcheny session here
        # note  this will raise a NoResultsFound exception if none was found (should be treated by caller)
        inventEntry=self._ses.query(InventTable).filter(InventTable.dataset == dataset).one()

        return inventEntry


