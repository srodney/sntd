import sntd
import sncosmo
import numpy as np
from matplotlib import pyplot as plt
from sntd import plotting, lightcurves, simulation, fitting

# Part 1 : simulate a doubly-imaged Type Ib SN and fit for time delays
modname = 'snana-2004gv'
snType = 'Ib'
#bandlist = ['bessellb', 'bessellv', 'bessellr']
bandlist = ['F125W']
lcs1 = simulation.createMultiplyImagedSN(
    modname, snType, 1.3, bands=bandlist,
    zp=30., cadence=2., epochs=25., mjdRange=[0,100.], time_delays=[0., 15.],
    magnifications=[10.,20.], objectName='Test'+snType, telescopename='HST',
    z_lens=0.5, microlensing_type='AchromaticSplineMicrolensing',
    microlensing_params=[10,1,20])


lcs2 = simulation.createMultiplyImagedSN(
    modname, snType, 1.3, bands=bandlist,
    zp=27., cadence=10., epochs=10., mjdRange=[0,100.], time_delays=[0., 15.],
    magnifications=[10.,20.], objectName='Test'+snType, telescopename='HST',
    z_lens=0.5, microlensing_type='AchromaticSplineMicrolensing',
    microlensing_params=[10,1,20])

# Plot the simulated lightcurves, showing each separate image as observed
lcs1.plot_lightcurve(bands=bandlist, color="#004949",
                     combined=False, showmodel='sim',
                     showmicrolensing='sim', showfig=True)
fig = plt.gcf()
axlist = fig.axes
lcs2.plot_lightcurve(bands=bandlist, color='darkorange',
                     combined=False, showmodel='sim',
                     showmicrolensing='sim', showfig=True,
                     axlist=axlist)

'''
from matplotlib import pyplot as plt
#import sncosmo
from sntd import simulation, fitting
import sys

# Part 1 : simulate a doubly-imaged Type Ib SN and fit for time delays
modname = 'snana-2004gv'
snType = 'Ib'
#bandlist = ['bessellb', 'bessellv', 'bessellr']
bandlist = ['F125W']
lcs = simulation.createMultiplyImagedSN(
    modname, snType, 1.3, bands=bandlist,
    zp=30., cadence=2., epochs=25., mjdRange=[0,100.], time_delays=[0., 15.],
    magnifications=[10.,20.], objectName='Test'+snType, telescopename='HST',
    z_lens=0.5, microlensing_type='AchromaticSplineMicrolensing',
    microlensing_params=[10,1,20])
ifig = 0
print("Simulated strongly lensed SN \n")

# Plot the simulated lightcurves, showing each separate image as observed
lcs.plot_lightcurve(bands=bandlist, combined=False, showmodel='sim',
                    showmicrolensing='sim', showfig=True)
for k in lcs.images.keys():
    print("image {} t0={}".format(k, lcs.images[k].simMeta['t0']))

# Part 2: fit each light curve separately to determine lensing parameters
lcs_tdfit=fitting.fit_data(lcs, snType='Ib', models=['snana-2004gv'],
                            params=['amplitude','t0'],
                            combined_or_separate='separate',
                            method='minuit')

# TODO: make this more general, i.e. use keywords list instead of s1 and s2.
t0_s1 = lcs_tdfit.images['S1'].fits.model.get('t0')
t0_s2 = lcs_tdfit.images['S2'].fits.model.get('t0')
A_s1 = lcs_tdfit.images['S1'].fits.model.get('amplitude')
A_s2 = lcs_tdfit.images['S2'].fits.model.get('amplitude')
lcs_tdfit.combine_curves(tds={'S1':1,'S2':t0_s2-t0_s1},
                         mus={'S1':1,'S2':A_s2/A_s1})

# Plot the lightcurve again, showing the composite light curve after correcting
# for magnification and time delay, using the best-fit lensing parameters. Also
# overlay the best fit model. Note that since we have set the magnification
# and time delays for combine_curves using S1 as the reference image, we use
# the best fit model as stored in the S1 image object.
bestfitmodel = lcs_tdfit.images['S1'].fits.model
lcs_tdfit.plot_lightcurve(bands=bandlist,  combined=True,
                          showmodel=bestfitmodel, showmicrolensing='sim',
                          showfig=True)

plt.savefig("/Users/rodney/sim_and_fit_lightcurve.pdf")


# TODO:  Part 3 : make 100 simulations with variations on microlensing
# and find time delays from each.
# Set initial guesses for the t0 and mu values, and a grid of mu,dt values to
# explore.
#lcs_tdfit=fitting.fit_data(lcs, snType='Ib', models=['snana-2004gv'],
#                            params=['amplitude','t0'],
#                            combined_or_separate='combined',
#                           method='minuit')
'''