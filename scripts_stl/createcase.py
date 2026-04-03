from osm2json import geojson2json
from osm2stl import json2stls
from joinstls import fullstl

if __name__ == "__main__":

    cityname = "shenzhen"
    # Create a json to be used to generate the stl
    output_json = geojson2json( f"{cityname}.geojson" )

    # Domain:
    y_offset = 400
    #x_offsets = ( y_offset, 1200 )
    x_offsets = ( 1200, 0 )

    # Create all the buildings and the box
    json2stls( output_json, cityname, x_offsets, y_offset, z_offset=300, 
              domain='cylinder' )

    # Create the flow volume
    #stl_name = f"{cityname}_x{x_offsets[0]+x_offsets[1]}_y{2*y_offset}_dummy"
    stl_name = f"{cityname}_r{x_offsets[0]}_dummy"
    fullstl( cityname, stl_name )




