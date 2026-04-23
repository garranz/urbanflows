import numpy as np

from common import datapath
from CTGlibD import ngpost

if __name__ == "__main__":

    ngpost.splitProbes( datapath / 'geo3_l6' / 'run' , 'points_device', 
                varlist = ['P', 'U-X', 'U-Y', 'U-Z' ] )

    tt,Ux = [],[]
    Nxyz = (18,20,15)

    for k in range(26):
        print( k )
        pp = ngpost.Probe( datapath / 'geo3_l6' / 'run' / f'run{k}', 'points_device')

        # sort points by x-coordinate
        #coords = np.array( [pp.coords[i+1].reshape( 18, 20, 15 ) for i in range(3) ] )

        # the three first data are: step, time, nbins
        #p = pp.readvar( 'P' )[3:]

        ux_ = pp.readvar( 'U-X' )
        t, ux = ux_[1], ux_[3:]
        #uy = pp.readvar( 'U-Y' )[3:]
        #uz = pp.readvar( 'U-Z' )[3:]


        #P  = p .reshape( *Nxyz, -1 )
        Ux.append( ux.reshape( *Nxyz, -1 )[11,11,3] )
        tt.append( t )
       #Uy = uy.reshape( *Nxyz, -1 )
       #Uz = uz.reshape( *Nxyz, -1 )

