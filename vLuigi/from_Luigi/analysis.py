import gammalib
import ctools
import cscripts
import math

# energy bounds for analysis
Emin = 0.03
Emax = 200.
emin = gammalib.GEnergy(Emin,'TeV')
emax = gammalib.GEnergy(Emax,'TeV')

# ROI definition
roi_width = 4.
clon = 26.507
clat = 0.209
bin_width = 0.02


def check_fit_quality(obs,label,spectral=True):
    resmap = cscripts.csresmap(obs)
    resmap['algorithm'] = 'SIGNIFICANCE'
    resmap['emin'] = Emin
    resmap['emax'] = Emax
    resmap['nxpix'] = int(roi_width / bin_width)
    resmap['nypix'] = int(roi_width / bin_width)
    resmap['binsz'] = bin_width
    resmap['proj'] = 'CAR'
    resmap['coordsys'] = 'GAL'
    resmap['xref'] = clon
    resmap['yref'] = clat
    resmap['outmap'] = 'resmap_{}.fits'.format(label)
    resmap['logfile'] = 'resmap_{}.log'.format(label)
    resmap.logFileOpen()
    resmap.execute()

    if spectral:
        resspec = cscripts.csresspec(obs)
        resspec['algorithm'] = 'SIGNIFICANCE'
        resspec['components'] = True
        resmap['outfile'] = 'resspec_{}.fits'.format(label)
        resspec['logfile'] = 'resspec_{}.log'.format(label)
        resspec.logFileOpen()
        resspec.execute()

# Crab flux above 30 GeV
crab_30GeV = 3.72e-9 # cm-2 s-1

# create binned observation
cube = gammalib.GCTAObservation('cntcube_0.03_100_FOV_4.0_binsz_0.02_GAL.fits')
cube.response(gammalib.GCTACubeExposure('expcube_0.03_100_FOV_4.0_binsz_0.02_GAL.fits'),
              gammalib.GCTACubePsf('psfcube_0.03_100_FOV_4.0_binsz_0.02_GAL.fits'),
              gammalib.GCTACubeBackground('bkgcube_0.03_100_FOV_4.0_binsz_0.02_GAL.fits'))

#create observation container and append models
obs = gammalib.GObservations()
obs.append(cube)
inmodels = gammalib.GModels('inmodel.xml')
obs.models(inmodels)

# before running a first fit make sure all parameters are blocked except normalisations
# for backgrounds and normalisation/spectral pars of bright sources > 100 mCrab inside the ROI
# also disable TS calculation for faster execution
for model in obs.models():
    model.tscalc(False)
    for par in model:
        par.fix()
    if model.name() == 'BackgroundModel':
        model['Prefactor'].free()
    elif model.name() == 'IEM':
        model['Normalization'].free()
    else:
        # check source in ROI
        src_dir = model.spatial().dir()
        lon = src_dir.l_deg()
        lat = src_dir.b_deg()
        if abs(clon - lon) < roi_width and abs(clat - lat) < roi_width:
            # check source flux
            flux = model.spectral().flux(emin, emax)
            if flux / crab_30GeV >= 0.1:
                # free normalization and spectral parameters
                model['Prefactor'].free()
                model['Index'].free()
                if model.has_par('CutoffEnergy'):
                    model['CutoffEnergy'].free()
                if model.has_par('Curvature'):
                    model['Curvature'].free()
            else:
                pass
        else:
            pass

# check number of free parameters
n_free = 0
for model in obs.models():
    for par in model:
        if par.is_free():
            n_free += 1

print('Initial model')
print(n_free, 'free parameters')

# first fit
label = 'initial'
like = ctools.ctlike(obs)
like['debug'] = True
like['logfile'] = 'ctlike_{}.log'.format(label)
like.logFileOpen()
like.run()
print(like.opt())
like0 = like.opt().value()
check_fit_quality(like.obs(),label,spectral=False)

# save models to restart analysis from here if needed
like.obs().models().save('models_{}.xml'.format(label))

# freeze IEM which is not well constrained by the data
like.obs().models()['IEM']['Normalization'].fix()

# free spectrum of sources that overlap with the pulsar
for model in obs.models():
    if model.name() == 'BackgroundModel':
        pass
    elif model.name() == 'IEM':
        pass
    else:
        # check source in ROI
        src_dir = model.spatial().dir()
        lon = src_dir.l_deg()
        lat = src_dir.b_deg()
        if abs(clon - lon) < roi_width and abs(clat - lat) < roi_width:
            #find 68% source containement
            rad = 0.
            if model.has_par('Sigma'):
                rad = 1.51 * model['Sigma'].value()
            elif model.has_par('Radius'):
                rad = 0.82 * model['Radius'].value()
            else:
                pass
            # add instrumental PSF 68%, conservative estimate of 0.3 deg at 30 GeV
            rad = math.sqrt(rad**2 + 0.3**2)
            dist = math.sqrt((clon-lon)**2 + (clat - lat)**2)
            if dist <= rad:
                model['Prefactor'].free()
                model['Index'].free()
                if model.has_par('CutoffEnergy'):
                    model['CutoffEnergy'].free()
                if model.has_par('Curvature'):
                    model['Curvature'].free()
        else:
            pass

# check number of free parameters
n_free = 0
for model in obs.models():
    for par in model:
        if par.is_free():
            n_free += 1

print('Background model')
print(n_free, 'free parameters')

# new fit with all background sources
label = 'background'
like['logfile'] = 'ctlike_{}.log'.format(label)
like.logFileOpen()
like.run()
print(like.opt())
like1 = like.opt().value()
check_fit_quality(like.obs(),label,spectral=False)

# save models to restart analysis from here if needed
like.obs().models().save('models_{}.xml'.format(label))

# add source at the position of the pulsar
newpntsrc = gammalib.GModelSky(gammalib.GModelSpatialPointSource(279.7334038845833,-5.619299891666667),
                               gammalib.GModelSpectralPlaw(1.e-15,-3.,gammalib.GEnergy(5.e4,'MeV')),
                               gammalib.GModelTemporalConst(1))
newpntsrc.name('PSR_J1838-0537')
like.obs().models().append(newpntsrc)

# new fit with all background sources
label = 'test'
like['logfile'] = 'ctlike_{}.log'.format(label)
like.logFileOpen()
like.run()
print(like.opt())
like2 = like.opt().value()
# TS of the pulsar
ts    = -2.0 * (like2 - like1)
print('TS PSR_J1838-0537', ts)
check_fit_quality(like.obs(),label,spectral=False)

# save models to restart analysis from here if needed
like.obs().models().save('models_{}.xml'.format(label))

