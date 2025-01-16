import numpy as np
import pandas as pd
from datetime import timedelta
import xarray as xr
from glob import glob
import sys, os
from parcels import FieldSet, Field, ParticleSet, JITParticle, AdvectionRK4

sys.path.insert(0, os.path.abspath(os.path.join(".")))
from virtualargofleet import Velocity, VirtualFleet, FloatConfiguration, VelocityField

files = '/home1/scratch/kbalem/test_concat_gigatl_6month.nc'

variables = {'U': 'u', 'V': 'v', 'depth_rho':'depth_rho'}

dimensions = {'U': {'lon': 'lon_u', 'lat': 'lat_u', 'depth': 'depth_rho', 'time': 'time'},
              'V': {'lon': 'lon_u', 'lat': 'lat_u', 'depth': 'depth_rho', 'time': 'time'},
              'depth_rho' : {'lon': 'lon_rho', 'lat': 'lat_rho', 'depth': 'depth_rho', 'time': 'time'}}

fieldset = FieldSet.from_c_grid_dataset(files, variables, dimensions, allow_time_extrapolation=True)

mask=xr.open_dataset('/home1/scratch/kbalem/mask_for_vf_gigatl_2.nc')
fieldset.add_field(Field('bathy',mask['depth_rho'].values,lon=fieldset.U.lon,lat=fieldset.U.lat,interp_method='nearest'))

# Set min/max depth for float conf, this is to make sure Parcels doesn't struggle 
min_depth = 2.5 
max_depth = int(fieldset.gridset.grids[0].depth.max() / 100)*100
fieldset.add_constant("vf_surface",min_depth)
fieldset.add_constant("vf_bottom", max_depth)

# Number of float we want to simulate
nfloats = 20

# Then we must define numpy array (size nfloats) for lat, lon, depth and time
lon0, lat0 = -12, 41  # Center of the box
Lx, Ly = 3.5, 6.0 # Size of the box
lon = np.random.uniform(lon0-Lx/2, lon0+Lx/2, size=nfloats)
lat = np.random.uniform(lat0-Ly/2, lat0+Ly/2, size=nfloats)
tim = np.array(['2008-03-14T12:00:00.00' for i in range(nfloats)],dtype='datetime64')
depth = np.array([min_depth for i in range(nfloats)])

# Define the deployment plan as a dictionary:
my_plan = {'lat': lat, 'lon': lon, 'time': tim, 'depth':depth}

# Float config
cfg = FloatConfiguration('default')
cfg.update('cycle_duration',24*10)
cfg.update('profile_depth',2000)
cfg.update('parking_depth',1000)

VFleet = VirtualFleet(plan=my_plan, fieldset=fieldset, mission=cfg, verbose_events=False)
VFleet.simulate(
            duration=timedelta(days=90),
            step=timedelta(minutes=5),
            record=timedelta(minutes=30),
            output_folder="/home1/scratch/kbalem/",
        )

