# ctlike_check_psr_j1838-0537

vold3 (35 free pars, stalled):
- spatial model is fixed for all the sources
- spectra:
  - field-of-view sources are free
  - out of field-of-view sources are fixed
- pulsar model is included (Src006)

vold4 (12 free pars, converged): 
- spatial model is fixed for all the sources
- spectra:
  - close field-of-view sources are free
  - far field-of-view sources are fixed
  - out of field-of-view sources are fixed
- pulsar model is not included

vold5 (18 free pars, converged): 
- spatial model is fixed for all the sources
- spectra:
  - close field-of-view sources are free
  - leaving free spectra of R000102_00001_J1837-0636 and R000102_00011_J1838-0621 (with respect to vold4)
  - far field-of-view sources are fixed
  - out of field-of-view sources are fixed
- pulsar model is not included

vold6 (16 free pars, in progress):
- spatial model is fixed for all the sources (except for R000102_00001_J1837-0636 and R000102_00011_J1838-0621)
- leaving free spatial model of R000102_00001_J1837-0636 and R000102_00011_J1838-0621 (with respect to vold5)
- spectra:
  - input model is taken from the output of ctlike_vold5
  - close field-of-view sources are free (except for R000103_00006_J1842-0507, R000103_00003_J1841-0533, R000103_00005_J1839-0557, R000103_00010)
  - far field-of-view sources are fixed
  - out of field-of-view sources are fixed
- pulsar model is not included
