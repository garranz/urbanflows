from osm2json import geojson2json
from osm2stl import json2stls
from joinstls import fullstl

import os
if __name__ == "__main__":

    cityname = "osaka"
    # Create a jsonto be used to generate the stl
    output_json = geojson2json( f"../Geometries/{cityname}.geojson" )

    # Domain:
    y_offset = 1200
    x_offsets = ( y_offset, y_offset )

    # Create all the buildings and the box
    json2stls( output_json, cityname, x_offsets, y_offset, z_offset=300,
               domain = 'cylinder', export_buildings=True)

    # Create the flow volume
    stl_name = f"{cityname}_r{y_offset}"
    fullstl( cityname, stl_name )



