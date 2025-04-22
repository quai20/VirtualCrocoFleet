import numpy as np
import pandas as pd
from datetime import timedelta
import xarray as xr
from glob import glob
import itertools
import sys, os
from parcels import FieldSet, Field, ParticleSet, JITParticle, AdvectionRK4
sys.path.insert(0, os.path.abspath(os.path.join("/home1/datahome/kbalem/VirtualCrocoFleet")))
from virtualargofleet import Velocity, VirtualFleet, FloatConfiguration, VelocityField

files = glob('/home/shom_simurep/public_no_ftp/PROJETS/IberArgo/GIGATL/NEW_DOMAIN_WITH_DEPTHS/*2008-0*.nc')
files.sort()

variables = {'U': 'u', 'V': 'v', 'depth_rho':'depth_rho'}
dimensions = {'U': {'lon': 'lon_rho', 'lat': 'lat_rho', 'depth': 'not_yet_set', 'time': 'time'},
              'V': {'lon': 'lon_rho', 'lat': 'lat_rho', 'depth': 'not_yet_set', 'time': 'time'},
              'depth_rho' : {'lon': 'lon_rho', 'lat': 'lat_rho', 'depth': 'not_yet_set', 'time': 'time'}        
             }
fieldset = FieldSet.from_c_grid_dataset(files,variables,dimensions,allow_time_extrapolation=True)
fieldset.U.set_depth_from_field(fieldset.depth_rho)
fieldset.V.set_depth_from_field(fieldset.depth_rho)
# I prefer add the bathy like that, then I'm sure that the bathy value is when there's no data (I'm not sure of that with the bathy var in the gigatl file)
df = xr.open_dataset(files[0]) 
mask = df.isel(time=0)['depth_rho'].max(['sig_rho']) - 50
fieldset.add_field(Field('bathy',mask.values,lon=fieldset.U.lon,lat=fieldset.U.lat,interp_method='nearest'))

# Set min/max depth for float conf, this is to make sure Parcels doesn't struggle 
min_depth = 2.5 #np.ceil(ds['depth_rho'].max(['sig_rho']).min().values)
max_depth = 6200 #int(fieldset.gridset.grids[0].depth.max() / 100)*100
fieldset.add_constant("vf_surface",min_depth)
fieldset.add_constant("vf_bottom", max_depth)

fbox = [-17,32,-10,42]
coords=np.array(list(itertools.product(np.arange(fbox[0],fbox[2],.5),np.arange(fbox[1],fbox[3],.5))))
lon = coords[:,0]
lat = coords[:,1]
nfloats=len(lon)
tim = np.array(['2008-04-01T12:00:00.00' for i in range(nfloats)],dtype='datetime64')
depth = np.array([min_depth for i in range(nfloats)])
# Define the deployment plan as a dictionary:
my_plan = {'lat': lat, 
           'lon': lon, 
           'time': tim, 
           'depth':depth}
cfg = FloatConfiguration('default')
VFleet = VirtualFleet(plan=my_plan, fieldset=fieldset, mission=cfg, verbose_events=False)
VFleet.simulate(
    duration=timedelta(days=100),
    step=timedelta(minutes=5),
    record=timedelta(minutes=30),
    output_folder="/home1/scratch/kbalem/",
)

