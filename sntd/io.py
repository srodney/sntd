#!/Users/jpierel/anaconda3/envs/astro2/bin python2
import string
from collections import OrderedDict as odict

import numpy as np
import os
import pycs
import sncosmo
from astropy.table import Table,vstack,Column
#from pycs.gen.lc import lightcurve
from scipy.stats import mode
from sncosmo import get_magsystem
from copy import deepcopy
import matplotlib.pyplot as plt
from .plotting import plot_lc, testplot, _COLORLIST15, _COLORLIST5

from .util import *

#from.util import _get_default_prop_name

__all__=['curve','curveDict','read_data','write_data','table_factory','factory']

_comment_char={'#'}
_meta__={'@','$','%','!','&'}


class curveDict(dict):
    #todo document this class
    def __init__(self,telescopename="Unknown",object="Unknown"):
        """
        Constructor for curveDict class. Inherits from the dictionary class,
        and is the main object of organization used by SNTD.
        :param telescopename: Name of the telescope that the data were
        gathered from
        :param object: Name of the object (i.e., the supernova ID)
        """
        super(curveDict, self).__init__() #init for the super class
        self.meta = {'info': ''}
        """@type: dict
            @ivar: The metadata for the curveDict object, intialized with an empty "info" key value pair. It's
            populated by added _metachar__ characters into the header of your data file.
        """
        self.bands=set()
        """
        @type: list
        @ivar: The list of bands contained inside this curveDict
        """
        self.table=None
        """
        @type:~astropy.table.Table
        @ivar: The astropy table containing all of the data in your data file
        """
        self.telescopename=telescopename
        """
        @type: str
        @ivar: Name of the telescope that the data were gathered from
        """
        self.object=object
        """
        @type: str
        @ivar: Object of interest
        """
        self.images=dict([])

        self.combined=curve()



    #these three functions allow you to access the curveDict via "dot" notation
    __setattr__ = dict.__setitem__
    __delattr__ = dict.__delitem__
    __getattr__ = dict.__getitem__


    def __getstate__(self):
        """
        A function necessary for pickling
        :return: self
        """
        return self

    def __setstate__(self, d):
        """
        A function necessary for pickling
        :param d: A value
        :return: self.__dict__
        """
        self.__dict__ = d

    def __str__(self):
        """
        A replacement for the print method of the class, so that when you run print(curveDict()), this is how it shows
        up.
        """
        print('Telescope: %s'%self.telescopename)
        print('Object: %s'%self.object)
        print('Number of bands: %d' %len(self.bands))
        print('')
        print('Metadata:')
        print('\n'.join('{}:{}'.format(*t) for t in zip(self.meta.keys(),self.meta.values())))
        print('')
        for c in np.sort(list(self.images.keys())):
            print('------------------')
            print('Image: %s:'%c)
            print('Bands: {}'.format(self.images[c].bands))
            print('Date Range: %.5f->%.5f' % (
            min(self.images[c].table[_get_default_prop_name('time')]),
            max(self.images[c].table[_get_default_prop_name('time')])))
            print('Number of points: %d' %len(self.images[c].table))
        return '------------------'

    def add_curve(self,myCurve):

        self.bands.update([x for x in myCurve.bands if x not in self.bands])
        im='S'+str(len(self.images)+1)
        myCurve.table.add_column(Column([im for i in range(len(myCurve.table))],name='object'))

        if not myCurve.zpsys:
            myCurve.zpsys=myCurve.table['zpsys'][0]
        if not myCurve.zp:
            print('Assuming standard curve...')
            myCurve.zp=myCurve.table['zp'][0]
        #myCurve.fluxes


        tempCurve=deepcopy(myCurve)


        self.images[im]=myCurve

        if self.table:
            for row in tempCurve.table:
                self.table.add_row(row)
        else:
            self.table=tempCurve.table
        return(self)

    def combine_curves(self,tds=None,mus=None):
        if len(self.images) <2:
            print("Not enough curves to combine!")
            return(self)
        if not tds:
            tds=_guess_time_delays(self)
        if not mus:
            mus=_guess_magnifications(self)
        #print(tds)
        #print(mus)
        self.combined.table=Table(names=self.table.colnames,dtype=[self.table.dtype[x] for x in self.table.colnames])
        for k in np.sort(list(self.images.keys())):
            #print('True mu:'+str(self.images[k].simMeta['mu']/self.images['S3'].simMeta['mu']))
            #print('True td: '+str(self.images[k].simMeta['td']-self.images['S3'].simMeta['td']))
            temp=deepcopy(self.images[k].table)
            temp['time']-=tds[k]
            temp['flux']/=mus[k]

            self.combined.table=vstack([self.combined.table,temp])
        #print(self.combinedCurve)
        self.combined.bands=self.bands
        self.combined.meta['td']=tds
        self.combined.meta['mu']=mus
        return(self)


    def plot_lightcurve(self, bands='all', showfig=False,
                        orientation='horizontal',
                        showmodel=False, combined=False,
                        **kwargs):
        """Plot the multiply-imaged SN light curve.
        Each subplot shows a single-band light curve, with each image of the SN
        plotted with a different color and marker.
        :param bands: 'all' = plot all bands; or provide a list of strings
        :param orientation: 'horizontal' = all subplots are in a single row
            'vertical' = all subplots are in a single column
        :param showmodel: str,
        'sim'= for a simulated SN, overplot the model used to generate it
        'fit'= overplot the best-fit model
        None = show no model curves

        :param combined: bool;  True=plot the combined data set, after shifting
         to account for the best-fit time delay and magnification.
        """
        if bands=='all':
            bands = self.bands

        if len(self.images.keys())>5:
            colorlist = _COLORLIST15
        else:
            colorlist = _COLORLIST5
        markerlist = ['o', '^', 's', 'd', '*', '8', 's', '+', 'D', '.']
        fig, axlist = plt.subplots(nrows=1, ncols=3,
                                   sharex='all', sharey='all')
        for imname,marker,color in zip(self.images.keys(),markerlist,colorlist):
            if combined:
                ithisim = np.where(self.combined.table['object'] == imname)
                thisim_table = self.combined.table[ithisim]
                # TODO : either make the user provide a model object, or /
                # allow more specificity of which model to show with 'fit'
                if showmodel=='fit':
                    model = self.model
                elif showmodel=='sim':
                    model = self.images[imname].simMeta['model']
                elif showmodel:
                    model = showmodel
                else:
                    model = None
            else:
                thisim_table = self.images[imname].table
                if showmodel=='sim':
                    model = self.images[imname].simMeta['model']
                elif showmodel=='fit':
                    model = self.images[imname].model
                elif showmodel:
                    model = showmodel
                else:
                    model = None
            plot_lc(thisim_table, bands=bands, marker=marker,
                    color=color,
                    axlist=axlist, showfig=False, savefig=False,
                    filename=None, orientation=orientation,
                    model=model, zp=self.zpDict, zpsys=self.zpsys,
                    **kwargs)
        if showfig:
            plt.show()
        return


#class curve(lightcurve,object):
class curve(object):
    """
    A class that has an
    astropy.table.Table version of the data file for SNCosmo commands and flux/fluxerr
    arrays.
    """
    def __init__(self,zp=None,zpsys=None):
        #todo: implement more general read and write functions
        """
        Constructor for curve class, which inherits from the PyCS lightcurve
        superclass. Following their format, we initialize a small lightcurve with
        only 5 points, etc. See pycs.gen.lc module for more info on the inherited properties.

        :param band, zp, zpsys
        """
        #todo populate param documentation
        super(curve,self).__init__()
        self.meta = {'info': ''}
        """@type: dict
            @ivar: The metadata for the curveDict object, intialized with an empty "info" key value pair. It's
            populated by added _metachar__ characters into the header of your data file.
        """
        self.table=None
        """@type: ~astropy.table.Table
        @ivar: A table containing the data, used for SNCosmo functions, etc.
        """
        #We just start with default test values for flux/fluxerr
        self.fluxes=np.array([0.0,0.25,0.5,0.75,1.0])
        """@type: 1D float array
        @ivar: Fluxes, preferably connected to magnitudes that exist in the superclass
        """
        self.fluxerrs=np.array([0.1,0.1,0.15,0.05,0.2])

        """@type: 1D float array
        @ivar: Errors of fluxes, as floats
        """
        self.zp=zp
        """@type: float
        @ivar: zero-point for flux scale
        """
        self.bands=[]
        """@type: string
        @ivar: band names, used
        """
        self.zpsys=zpsys
        """@type: string
        @ivar: zero-point system
        """
        if self.zpsys:
            self.system=get_magsystem(self.zpsys)
        else:
            self.system=None
        """@type: class sncosmo.MagSystem
        @ivar: Used to convert between mag and flux, none if no zpsys is defined at construction
        """
        self.simMeta=dict([])

        self.fits=None

    def calcmagshiftfluxes(self,inverse=False):
        """
        Returns an array of fluxes that you have to add to the curve.fluxes if you want to take into account for the magshift.
        Be careful with the order of things ! Always take into account this magshift *before* the magshift / microlensing.

        :param inverse: Returns the fluxes to subtract from magshiftedfluxes to get back the original fluxes.
        :return: A 1-D float array of length len(self), containing the shifts in flux from self.magshift
        """
        if self.magshift != 0.0:
            # We need to include a check :
            if inverse:
                shift = self.system.band_mag_to_flux(self.magshift,self.band)
            else:
                shift = -self.system.band_mag_to_flux(self.magshift,self.band)
            return shift
        else:
            return 0


    def getfluxes(self,noml=False):
        #TODO: More advanced mag_to_flux integration or add ml.calcmlfluxes
        """
        A getter method returning fluxes, but taking magshift, fluxshift, and microlensing into consideration ("copy" of
        lightcurve.getmags()

        :param noml: to ignore microlensing effects while calculating the flux with fluxshift/magshift
        :return: 1-D float array of length len(self), a copy of shifted fluxes (doesn't effect self.fluxes)
        """
        if self.magshift != 0.0:
            if (self.ml != None) and (noml == False):
                return self.fluxes + self.calcmagshiftfluxes() + self.fluxshift + np.array([self.system.band_mag_to_flux(x,self.band) for x in self.ml.calcmlmags(self)])
            else:
                return self.fluxes + self.calcmagshiftfluxes() + self.fluxshift
        else:
            if (self.ml != None) and (noml == False):
                return self.fluxes + self.fluxshift + np.array(self.system.band_mag_to_flux(self.ml.calcmlmags(self),self.band))
            else:
                return self.fluxes + self.fluxshift


    def getfluxerrs(self):
        #TODO: Figure out if magshift/ml effect fluxerrs

        """
        A getter method returning fluxerrs

        :return: 1-D float array copy of self.fluxerrs
        """
        return self.fluxerrs.copy()


    def getzp(self):
        """
        A getter method returning zero-point

        :return: float, self.zp
        """
        return self.zp


    def getzpsys(self):
        """
        A getter method returning the zero-point system

        :return: string, self.zpsys
        """
        return self.zpsys


    def gettable(self):
        """
        A getter method to return the associated astropy table, but with all of the potential shifts taken into consideration.

        :return: astropy Table, copy of self.table with shifts considered
        """
        temp=self.table.copy()
        temp[_get_default_prop_name('jds')]=self.getjds()
        temp[_get_default_prop_name('mags')] = self.getmags()
        temp[_get_default_prop_name('magerrs')] = self.getmagerrs()
        temp[_get_default_prop_name('flux')] = self.getfluxes()
        temp[_get_default_prop_name('fluxerr')] = self.getfluxerrs()
        temp[_get_default_prop_name('zp')] = self.getzp()
        temp[_get_default_prop_name('zpsys')] = self.getzpsys()
        for key in [x for x in self.table.keys() if x not in _props.keys()]:
            temp[_get_default_prop_name(key)]=self.table[_get_default_prop_name(key)].copy()
        return temp


    def applyml(self):
        """
        Simply extends the superclass version of applyml to add the ml effect to the fluxes as well as the mags

        :return: None, but changes self.mags,self.fluxes, and removes current microlensing
        """
        if self.ml == None:
            raise(RuntimeError, "Hey, there is no ml associated to this lightcurve !")

        #if self.fluxshift != 0.0:
        #    raise(RuntimeError, "Apply the fluxshift before applying the ML !")
        #self.fluxes+=np.array([self.system.band_mag_to_flux(x,self.band) for x in self.ml.calcmlmags(self)])

        super(curve,self).applyml()


    def cutmask(self):
        """
        Simply extends the superclass version of cutmask to include flux

        :return: None, but changes self.jds, self.mags, self.magerrs, self.labels, self.properties, self.mask, and
        removes microlensing if it exists
        """
        self.fluxes=self.fluxes[self.mask]
        self.fluxerrs=self.fluxerrs[self.mask]
        super(curve,self).cutmask()


    def validate(self, verbose=False):
        """
        Simply extends the superclass version of validate to include flux
        :param verbose: Default=False -> won't print "Validation done!"

        :return: None
        """
        ndates=len(self)
        if len(self.fluxes) != ndates or len(self.fluxerrs) != ndates or len(self.table)!=ndates:
            raise(RuntimeError, "The length of your flux/fluxerr arrays are inconsistent with rest of curve!")
        if not self.zp or not self.zpsys:
            raise(RuntimeError, "No zero-point or zero-point system defined")
        if not self.system:
            self.system=get_magsystem(self.zpsys)
        super(curve,self).validate(verbose)


    def sort(self):
        """
        Simply extends the superclass version of sort to include flux and the table

        :return: None, but changes self.jds, self.mags, self.magerrs, self.labels, self.properties, self.mask, and
        removes microlensing if it exists
        """
        sortedindices=np.argsort(self.jds)
        self.fluxes=self.fluxes[sortedindices]
        self.fluxerrs=self.fluxerrs[sortedindices]
        self.table.sort(_get_default_prop_name('time'))
        super(curve,self).sort()


    def montecarlofluxes(self,f=1.0,seed=None):
        self.commentlist.append("Monte Carlo on fluxes !")  # to avoid confusions.
        rs = np.random.RandomState(seed)  # we create a random state object, to control the seed.
        self.fluxes += rs.standard_normal(self.fluxes.shape) * f * self.fluxerrs  # and here we do the actual bootstrapping !


    def merge(self,otherlc):
        #todo: make sure we actually care about these things that currently error

        """
        This is just an extension of the existing merge function in the lightcurve
        class, which just merges the new features (i.e. Table and flux data) as well and checks for matching band/zp/zpsys

        :param otherlc: The other curve object you're merging
        :return: A single merged curve object
        """
        if self.band!=otherlc.band:
            raise(RuntimeError,"You're merging two lightcurves with different bands!")
        if self.zp!=otherlc.zp:
            print("You're merging lightcurves with different zero-points, careful if you care about absolute data and use the normalize function.")
        if self.zpsys != otherlc.zpsys:
            print("You're merging lightcurves with different zero-point systems, careful if you care about absolute data and use the normalize function.")

        concfluxes=np.concatenate([self.getfluxes(),otherlc.getfluxes()])
        concfluxerrs=np.concatenate([self.getfluxerrs(),otherlc.getfluxerrs()])
        concTable=vstack(self.gettable(),otherlc.gettable())
        self.fluxes=concfluxes
        self.fluxerrs=concfluxerrs
        self.table=concTable
        super(curve,self).merge(otherlc)


    def applymagshift(self):
        """
        It adds the magshift-float to the present flux, then puts this magshift-float to 0. So that "nothing" changes as seen from
        the outside. "Copy" of pycs.gen.lc.applyfluxshift

        :return: None, but changes fluxes and magshift
        """

        self.fluxes += self.calcmagshiftfluxes()
        self.commentlist.append("CAUTION : magshift of %f APPLIED" % (self.magshift))
        self.magshift = 0.0  # as this is now applied.




    def rdbexport(self, filename=None, separator="\t", writeheader=True, rdbunderline=True, properties=None):
        """
        Updated copy of pycs.gen.lc.rdbexport
        ***
        Writes the lightcurve into an "rdb" file, that is tab-separeted columns and a header.
        Note that any shifts/ML are taken into account. So it's a bit like if you would apply the
        shifts before writing the file.

        Includes mask column only if required (if there is a mask)
        ***

        :param filename: where to write the file
        :type filename: string or path
        :param separator: how to separate the collumns
        :type separator: string
        :param writeheader: include rdb header ?
        :type writeheader: boolean
        :param properties: properties of the lightcurves to be include in the file.
        :type properties: list of strings, e.g. ["fwhm", "ellipticity"]

        :return: None, but creates rdb file
        """

        import csv

        self.validate()  # Good idea to keep this here, as the code below is so ugly ...

        if filename == None:
            filename = "%s_%s.rdb" % (self.telescopename, self.object)

        # We include a "mask" column only if mask is not True for all points
        if False in self.mask:
            colnames = ["mhjd", "mag", "magerr", "flux","fluxerr","zp","zpsys","mask"]
            data = [self.getjds(), self.getmags(), self.getmagerrs(), self.fluxes, self.fluxerrs,
                    np.asarray(self.table[_get_default_prop_name('zp')]),
                    np.asarray(self.table[_get_default_prop_name('zpsys')]), self.mask]

        else:
            colnames = ["mhjd", "mag", "magerr","flux","fluxerr","zp","zpsys"]
            data = [self.getjds(), self.getmags(), self.getmagerrs(), self.fluxes, self.fluxerrs,
                    np.asarray(self.table[_get_default_prop_name('zp')]),
                    np.asarray(self.table[_get_default_prop_name('zpsys')])]

        # Now we do some special formatting for the cols mhjd, mag, magerr, flux, fluxerr
        data[0] = map(lambda mhjd: "%.8f" % (mhjd), data[0])  # formatting of mhjd
        data[1] = map(lambda mhjd: "%.8f" % (mhjd), data[1])  # formatting of mhjd
        data[2] = map(lambda mhjd: "%.8f" % (mhjd), data[2])  # formatting of mhjd
        data[3] = map(lambda mhjd: "%.8f" % (mhjd), data[3])  # formatting of mhjd
        data[4] = map(lambda mhjd: "%.8f" % (mhjd), data[4])  # formatting of mhjd

        data = map(list, list(zip(*data)))  # list to make it mutable

        # We add further columns
        if properties == None:
            properties = []
        colnames.extend(properties)
        for i in range(len(self.jds)):
            for property in properties:
                data[i].append(self.properties[i][property])

        underline = ["=" * n for n in map(len, colnames)]

        outfile = open(filename, "wb")  # b needed for csv
        writer = csv.writer(outfile, delimiter=separator)

        if writeheader:
            writer.writerow(colnames)
            if rdbunderline:
                writer.writerow(underline)
        writer.writerows(data)

        outfile.close()
        print("Wrote %s into %s." % (str(self), filename))

def table_factory(table,band,telescopename="Unknown",object="Unknown",verbose=False):
    #todo finish documenting this function
    """
    This function will create a new curve object using an astropy table.
    :param table: ~astropy.table.Table() with all of your data from your data file.
    :param band:
    :param telescopename:
    :param object:
    :param verbose:
    :return:
    """
    newlc=curve()

    newlc.jds = np.asarray(table[_get_default_prop_name('time')])
    newlc.mags = np.asarray(table[_get_default_prop_name('mag')])
    newlc.magerrs = np.asarray(table[_get_default_prop_name('magerr')])
    newlc.fluxes = np.asarray(table[_get_default_prop_name('flux')])
    newlc.fluxerrs = np.asarray(table[_get_default_prop_name('fluxerr')])
    newlc.zp = {x for x in table[_get_default_prop_name('zp')]}
    newlc.zpsys={x for x in table[_get_default_prop_name('zpsys')]}
    if len(newlc.zp)>1:
        raise(RuntimeError,"zero point not consistent across band: %s"%band)
    if len(newlc.zpsys)>1:
        raise(RuntimeError,"zero point system not consistent across band: %s"%band)
    newlc.zpsys=newlc.zpsys.pop()
    newlc.zp = newlc.zp.pop()

    newlc.band=band

    if len(newlc.jds) != len(newlc.mags) or len(newlc.jds) != len(newlc.magerrs) or len(newlc.jds) != len(
            newlc.fluxes) or len(newlc.jds) != len(newlc.fluxerrs):
        raise (RuntimeError, "lightcurve factory called with arrays of incoherent lengths")

    newlc.mask = newlc.magerrs >= 0.0  # This should be true for all !
    newlc.mask = newlc.fluxes >= 0.0  # This should be true for all !    newlc.table=table

    newlc.table=table

    newlc.properties = [{}] * len(newlc.jds)

    newlc.telescopename = telescopename
    newlc.object = object

    newlc.setindexlabels()
    newlc.commentlist = []

    newlc.sort()  # not sure if this is needed / should be there

    newlc.validate()

    if verbose: print("New lightcurve %s with %i points" % (str(newlc), len(newlc.jds)))

    return newlc


def factory(jds, mags,fluxes,band,zp,zpsys,magerrs=None, fluxerrs=None, telescopename="Unknown", object="Unknown", verbose=False):
    #todo: improve it and use this in file importing functions
    """
    "COPY" of pycs.gen.lc.factory, but for fluxes
    Returns a valid lightcurve object from the provided arrays.
    The numpy arrays jds and mags are mandatory. If you do not specify a third array containing the magerrs,
    we will calculate them "automatically" (all the same value), to avoid having 0.0 errors.

    @type	jds: 1D numpy array
    @param	jds: julian dates
    @type	mags: 1D numpy array
    @param	mags: flux data
    @type	magerrs: 1D numpy array
    @param	magerrs: optional mag errors
    @type	fluxes: 1D numpy array
    @param	fluxes: flux data
    @type	fluxerrs: 1D numpy array
    @param	fluxerrs: optional flux errors

    """
    # Make a brand new lightcurve object :
    newlc = curve()

    # Of couse we can/should check a lot of things, but let's be naive :

    newlc.jds = np.asarray(jds)
    newlc.mags=np.asarray(mags)
    newlc.fluxes = np.asarray(fluxes)
    newlc.zp=zp
    newlc.zpsys=zpsys
    if _isfloat(band[0]):
        band = 'band_' + band
    newlc.band=band

    if fluxerrs is not None:
        newlc.fluxerrs = np.zeros(len(newlc.jds)) + 0.1
    else:
        newlc.fluxerrs = np.asarray(fluxerrs)
    if magerrs is not None:
        newlc.magerrs = np.zeros(len(newlc.jds)) + 0.1
    else:
        newlc.magerrs = np.asarray(magerrs)

    if len(newlc.jds) != len(newlc.mags) or len(newlc.jds) != len(newlc.magerrs) or len(newlc.jds) != len(
            newlc.fluxes) or len(newlc.jds) != len(newlc.fluxerrs):
        raise(RuntimeError, "lightcurve factory called with arrays of incoherent lengths")

    newlc.mask = newlc.magerrs >= 0.0  # This should be true for all !
    newlc.mask = newlc.fluxerrs >= 0.0  # This should be true for all !

    colnames = [_get_default_prop_name(x) for x in ["time", "mag", "magerr", "flux", "fluxerr", "zp", "zpsys"]]
    newlc.table = Table([jds, mags, magerrs, fluxes, fluxerrs, [zp for i in range(len(newlc.jds))],
                         [zpsys for i in range(len(newlc.jds))]], names=colnames)
    newlc.properties = [{}] * len(newlc.jds)

    newlc.telescopename = telescopename
    newlc.object = object

    newlc.setindexlabels()
    newlc.commentlist = []

    newlc.sort()  # not sure if this is needed / should be there

    newlc.validate()

    if verbose: print("New lightcurve %s with %i points" % (str(newlc), len(newlc.jds)))

    return newlc


def _switch(ext):
    switcher = {
        '.pkl': _read_pickle,
        #'rdb': pycs.gen.lc.rdbimport
    }
    return switcher.get(ext, _read_data)


def lc_to_curve(lc):
    #todo write this function that takes a pycs lc and turns it into an sntd curve
    pass


def write_data(curves,filename=None,type='pkl',verbose=True,protocol=-1):
    if not filename:
        filename=curves.object
    if type!='pkl':
        return _write_data()
    else:
        return pycs.gen.util.writepickle(curves,filename,verbose=verbose,protocol=protocol)
    pass


def _write_data():
    pass


def read_data(filename,telescopename="Unknown",object=None,**kwargs):
    #todo document this function and maybe add other file types (I suspect pickles will be the answer)
    return(_switch(os.path.splitext(filename)[1])(filename,telescopename,object,**kwargs))
    #spline=None
    #if not isinstance(lc,curve):
    #    lc=lc_to_curve(lc)
    #if isinstance(lc,list):
    #    curves = curveDict()
    #    for x in range(len(lc)):
    #        curves[lc[x].band]=lc[x]
    #    curves.spline=spline
    #try:
    #    getattr(lc,'table')
    #except:
    #    print('made it here')
    #    sys.exit()
    #    pass


def _read_pickle(filename,telescopename="Unknown",object="Unknown",**kwargs):
    return pycs.gen.util.readpickle(filename,verbose=True)


def _write_pickle(curves):
    pycs.gen.util.writepickle(curves,'myData.pkl',verbose=False)


def _col_check(colnames):
    colnames=set(colnames)
    flux_to_mag=False
    mag_to_flux=False
    if len(colnames & set(_props.keys())) != len(_props.keys()):
        temp_missing=[x for x in _props.keys() if x not in [_get_default_prop_name(y) for y in ['flux','fluxerr','mag','magerr']] and x not in colnames]
        if len(temp_missing) !=0:
            raise RuntimeError("Missing required data, or else column name is not in default list: {0}".format(', '.join(temp_missing)))
        temp_flux = {_get_default_prop_name(x) for x in ['flux', 'fluxerr']}
        temp_mag = {_get_default_prop_name(x) for x in ['mag', 'magerr']}
        if len(temp_flux & colnames) != len(temp_flux):
            if len(temp_mag & colnames) != len(temp_mag):
                raise RuntimeError("You need mag and/or flux data with error, missing: {0}".format(
                    ', '.join([x for x in list(temp_flux) + list(temp_mag) if x not in colnames])))
            mag_to_flux = True
        elif len(temp_mag & colnames) != len(temp_mag):
            flux_to_mag = True
    return flux_to_mag,mag_to_flux


def _read_data(filename,telescopename,object,**kwargs):
    if not object:
        try:
            object=filename[:filename.rfind('.')]
        except:
            object='Unknown'
    try:
        table = sncosmo.read_lc(filename, masked=True,**kwargs)
        for col in table.colnames:
            if col != _get_default_prop_name(col.lower()):
                table.rename_column(col, _get_default_prop_name(col.lower()))
    except:
        table = Table(masked=True)

    delim = kwargs.get('delim', None)
    #curves=curveDict()
    myCurve=curve()
    with anyOpen(filename) as f:
        lines=f.readlines()
        length=mode([len(l.split()) for l in lines])[0][0]#uses the most common line length as the correct length
        for i,line in enumerate(lines):
            if line[0] in _comment_char:
                continue
            line = line.strip(delim)
            if len(line)==0:
                continue
            if line[0] in _meta__:
                pos = line.find(' ')
                if (lines[i + 1][0] in _meta__ or lines[i + 1][0] in _comment_char or len(
                        line) != length):  # just making sure we're not about to put the col names into meta
                    if (pos == -1 or not any([_isfloat(x) for x in line.split()])):
                        if line[-1] not in string.punctuation:
                            line=line+'.'
                        #myCurve.meta['info']=curves.meta['info']+' '+ line[1:]
                        myCurve.meta['info']=myCurve.meta['info']+' '+ line[1:]
                    else:
                        myCurve.meta[line[1:pos]] = _cast_str(line[pos:])
                continue
            line=line.split()
            if len(line)!= length:
                raise(RuntimeError,"Make sure your data are in a square matrix.")
            if table.colnames:
                colnames=table.colnames
            else:
                colnames = odict.fromkeys([_get_default_prop_name(x.lower()) for x in line])
                if len(colnames) != len(line):
                    raise (RuntimeError, "Do you have duplicate column names?")
                colnames=odict(zip(colnames,range(len(colnames))))
            startLine=i
            break
    f.close()
    if not table:
        lines = [x.strip().split() for x in lines[startLine + 1:]]
        for col in colnames:
            table[col]=np.asarray([_cast_str(x[colnames[col]]) for x in lines])
        colnames=colnames.keys()

    flux_to_mag, mag_to_flux = _col_check(colnames)
    '''
    #todo: don't get rid of negative flux
    if flux_to_mag:
        table=table[table[_get_default_prop_name('flux')]>=0]
        table=_flux_to_mag(table)
    elif mag_to_flux:
        table=table[table[_get_default_prop_name('magerr')] >= 0]
        table=_mag_to_flux(table)
    else:
        table = table[table[_get_default_prop_name('flux')] >= 0]
        table = table[table[_get_default_prop_name('magerr')] >= 0]
    '''
    bnds = {x for x in table[_get_default_prop_name('band')]}
    table=_norm_flux_mag(table, bnds)
    for band in bnds:
        if _isfloat(band[0]):
            band='band_'+band
        try:
            if band[0:5]=='band_':
                sncosmo.get_bandpass(band[5:])
            else:
                sncosmo.get_bandpass(band)
        except:
            print('Skipping band %s, not in registry.' %band)
            table.mask[table[_get_default_prop_name('band')]==band]=True
            continue
        myCurve.bands.append(band)

        #curves[band]=table_factory(table[table[_get_default_prop_name('band')]==band],band=band,telescopename=curves.meta.get('telescopename',telescopename),object=curves.meta.get('object',object))
        #curves[band].spline=None
    myCurve.table=table
    #curves.telescopename=curves.meta.get('telescopename',telescopename)
    #curves.object=curves.get('object',object)
    #myCurve.bands=bnds
    #myCurve.fits=sntd.fitting.fits()
    #curves.curves=table
    return myCurve

def _norm_flux_mag(table,bands):
    #todo make sure that by changing the zero-point i'm not messing with the errors
    for band in bands:
        zp = round(mode(table[table[_get_default_prop_name('band')]==band][_get_default_prop_name('zp')])[0][0],4)
        table[table[_get_default_prop_name('band')] == band][_get_default_prop_name('mag')] = np.asarray(
            map(lambda x, y: x + (y - zp),
                table[table[_get_default_prop_name('band')] == band][_get_default_prop_name('mag')],
                table[table[_get_default_prop_name('band')] == band][_get_default_prop_name('zp')]))
        table[table[_get_default_prop_name('band')] == band][_get_default_prop_name('flux')] = np.asarray(
            map(lambda x, y: x * y / (2.5 * np.log10(np.e)),
                table[table[_get_default_prop_name('band')] == band][_get_default_prop_name('magerr')],
                table[table[_get_default_prop_name('band')] == band][_get_default_prop_name('flux')]))
        table[_get_default_prop_name('zp')][table[_get_default_prop_name('band')] == band]=zp
    return table


def _flux_to_mag(table):
    table[_get_default_prop_name('mag')] = np.asarray(map(lambda x, y: -2.5 * np.log10(x) + y, table[_get_default_prop_name('flux')],
                                  table[_get_default_prop_name('zp')]))
    table[_get_default_prop_name('magerr')] = np.asarray(map(lambda x, y: 2.5 * np.log10(np.e) * y / x, table[_get_default_prop_name('flux')],
                                     table[_get_default_prop_name('fluxerr')]))
    return table


def _mag_to_flux(table):
    table[_get_default_prop_name('flux')] = np.asarray(
        map(lambda x, y: 10 ** (-.4 * (x -y)), table[_get_default_prop_name('mag')],
            table[_get_default_prop_name('zp')]))
    table[_get_default_prop_name('fluxerr')] = np.asarray(
        map(lambda x, y: x * y / (2.5 * np.log10(np.e)), table[_get_default_prop_name('magerr')],
            table[_get_default_prop_name('flux')]))
    return table



