import os
from pathlib import Path
import re

geopath = Path( '../Geometries/' )

def return_places_list():
    mylist = os.listdir( geopath )
    ll = []
    for myf in mylist:
        ii = re.findall('(\w+).geojson$', myf )
        if len(ii):
          ll.append( ii[0] )

    return ll

