from matplotlib import pyplot as plt
#import sncosmo
from sntd import simulation, fitting
from sntd.plotting import _COLORLIST5
import sys

nsim = 100
dt_fit_list = []
murel_fit_list = []
for isim in range(nsim):
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
        microlensing_params=[10,2,10])
    ifig = 0
    print("Simulated strongly lensed SN %i"%isim)

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
    dt_fit_list.append(t0_s2-t0_s1)
    murel_fit_list.append(A_s2/A_s1)

#plt.plot(dt_fit_list, murel_fit_list,
#         marker='o', color=_COLORLIST5[3], ls=' ')
plt.hist(dt_fit_list, bins=20, normed=True)
plt.show()