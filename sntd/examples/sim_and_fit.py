#from matplotlib import pyplot as plt
#import sncosmo
from sntd import simulation, fitting

# Part 1 : simulate a doubly-imaged Type Ib SN and fit for time delays
modname = 'snana-2004gv'
snType = 'Ib'
bandlist = ['bessellb', 'bessellv', 'bessellr']
lcs = simulation.createMultiplyImagedSN(
    modname, snType, 0.1, bands=bandlist,
    zp=30., cadence=2., epochs=25., mjdRange=[0,100.], time_delays=[0., 15.],
    magnifications=[10.,20.], objectName='Test'+snType, telescopename='HST',
    z_lens=0.05, microlensing_type='AchromaticSplineMicrolensing',
    microlensing_params=[10,2,10])
ifig = 0
print("Simulated strongly lensed SN \n")

# Plot the simulated lightcurves, showing each separate image as observed
lcs.plot_lightcurve(bands=bandlist, combined=False, showmodel='sim',
                    showfig=True)
for k in lcs.images.keys():
    print("image {} t0={}".format(k, lcs.images[k].simMeta['t0']))


# Part 2: fit the light curve data to determine lensing parameters
lcs_tdfit=fitting.fit_data(lcs, snType='Ib', models=['snana-2004gv'],
                            params=['amplitude','t0'],
                            combined_or_separate='separate',
                            method='minuit')

# TODO: make this more general, i.e. use keywords list instead of s1 and s2.
t0_s1 = lcs_tdfit.images['S1'].fits.model.get('t0')
t0_s2 = lcs_tdfit.images['S2'].fits.model.get('t0')
A_s1 = lcs_tdfit.images['S1'].fits.model.get('amplitude')
A_s2 = lcs_tdfit.images['S2'].fits.model.get('amplitude')
bestfitmodel = lcs_tdfit.images['S1'].fits.model
lcs_tdfit.combine_curves(tds={'S1':1,'S2':t0_s2-t0_s1},
                         mus={'S1':1,'S2':A_s2/A_s1})

# Plot the lightcurve again, showing the composite light curve after correcting
# for magnification and time delay, using the best-fit lensing parameters.
lcs_tdfit.plot_lightcurve(bands=bandlist,  combined=True,
                          showmodel=bestfitmodel, showfig=True)
