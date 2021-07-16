import colibri.constants as const
import numpy as np
import scipy.special as ss
import scipy.integrate as sint
import scipy.interpolate as si
import scipy.misc as sm
import colibri.useful_functions as UF
import sys
import warnings
from six.moves import xrange
from six import iteritems
try:                from classy import Class
except ImportError: pass
try:                import camb
except ImportError: pass


class cosmo:
    """
    The class ``cosmo`` takes as arguments a set of cosmological parameters and returns a ``cosmo`` instance,
    which contains several methods to compute useful cosmological quantities, such as distances, ages,
    scales, power spectra and evolution of cosmological parameters.
    This class supports :math:`\\Lambda\mathrm{CDM}` cosmologies as well as massive neutrinos,
    evolving dark energy models and non-flat geometries.
    It accepts the following arguments, with the default values specified:

    :param Omega_m: Matter density parameter today (including massive neutrinos), :math:`\Omega_m`.
    :type Omega_m: float, default = 0.3089

    :param Omega_b: Baryon density parameter today, :math:`\Omega_b`.
    :type Omega_b: float, default = 0.0486

    :param Omega_K: Curvature density parameter today, :math:`\Omega_K`.
    :type Omega_K: float, default = 0
        
    :param N_nu: Number of active neutrino species.
    :type N_nu: int, default = 3

    :param M_nu: Neutrino masses expressed in eV. Its size must be <= ``N_nu``. When ``cosmo`` is called, this quantity will be transformed to an array (``self.M_nu``) of length ``N_nu`` containing the non-vanishing neutrino masses assigned here padded with zeros in order to reach ``N_nu``. E.g.: if ``M_nu = [0.2, 0.1]`` and ``N_nu = 3``, then ``self.M_nu`` will become ``[0.2, 0.1, 0.0]``.
    :type M_nu: float or list of floats, default = 0.

    :param N_eff: Effective number of neutrinos. This number should be greater than ``N_nu``.
    :type N_eff: float, default = 3.046

    :param As: Amplitude of primordial scaled perturbations. At least one between this and `sigma_8` must be different from None. If ``As`` is not None, it will be the parameter used to compute the amplitude of the power spectrum.
    :type As: float, default = 2.14e-9

    :param sigma_8: Root mean square amplitude fluctuation on scales of 8 :math:`\mathrm{Mpc}/h`. At least one between this and ``As`` must be different from None. If ``sigma_8`` is not None, and ``As`` is None, the former will be the parameter used to compute the amplitude of the power spectrum.
    :type sigma_8: float, default = ``None``

    :param ns: Spectral index of scalar primordial perturbations.
    :type ns: float, default = 0.9667

    :param h: Hubble constant in units of 100 km/s/Mpc.
    :type h: float, default = 0.6774

    :param w0: Dark energy parameter of state today.
    :type w0: float, default = -1

    :param wa: Evolution of dark energy parameter of state.
    :type wa: float, default = 0

    :param tau: Optical depth to reionization.
    :type tau: float, default = 0.06

    :param T_cmb: CMB temperature today.
    :type T_cmb: float, default = 2.7255


    After initialization, the following quantities will be stored

    :param H0: Hubble constant in km/s/Mpc, i.e. :math:`100 h`.
    :param Omega_lambda: Dark energy/cosmological constant density parameter, :math:`\Omega_\Lambda`.
    :param Omega_nu: Neutrino density parameters, :math:`\Omega_\\nu`.
    :param Omega_cdm: Cold dark matter density parameter today, :math:`\Omega_{cdm}`.
    :param Omega_cb: Cold dark matter + baryons density parameter today, :math:`\Omega_{cb}`.
    :param Omega_gamma: Photon density parameter today, :math:`\Omega_\gamma`.
    :param omega_m: Reduced matter density parameter today, :math:`\Omega_m h^2`.
    :param omega_cdm: Reduced cold dark matter density parameter today, :math:`\Omega_{cdm} h^2`.
    :param omega_cb: Reduced cold dark matter density parameter today, :math:`\Omega_{cb} h^2`.
    :param omega_b: Reduced baryon parameter today, :math:`\Omega_{b} h^2`.
    :param omega_nu: Reduced neutrino parameter today, :math:`\Omega_\\nu h^2`.
    :param omega_gamma: Reduced photon density parameter today, :math:`\Omega_\gamma h^2`.
    :param omega_K: Reduced curvature parameter today, :math:`\Omega_K h^2`.
    :param massive_nu: Number of massive neutrinos.
    :param massless_nu: Number of massless neutrinos, :math:`N_{eff} - N_{massive \ \\nu}`
    :param Omega_massive_nu: Massive neutrino density parameters today.
    :param Omega_massless_nu: Massless neutrino density parameters today.
    :param log10_As: If ``As`` is not None, base-10 logarithm of initial scalar amplitude.
    :param f_nu: Neutrino fractions, in units of :math:`\Omega_m`.
    :param f_nu_tot: Sum of neutrino fractions.
    :param f_b: Baryon fraction in units of :math:`\Omega_m`.
    :param f_c: Cold dark matter fraction in units of :math:`\Omega_m`.
    :param f_cb: Cold dark matter plus baryon fraction in units of :math:`\Omega_m`.
    :param Gamma_nu: Neutrino-to-photon temperature ratio.
    :param T_nu: Neutrino temperature today.
    :param M: Array of masses, used to sample (e.g.) mass functions
    :type M: array of 512 equally-spaced logarithmic bins from :math:`10^2` to :math:`10^{18} \ M_\odot/h`.
    :param delta_sc: Critical overdensity for spherical collapse (linear theory extrapolation), :math:`\delta_{sc} = \\frac{3}{20} \left(12\pi\\right)^{2/3} \\approx 1.686`.
    :param eta_sc: Time of shell-crossing (radians), :math:`\eta_{sc} \\approx 3.488`.
    :param delta_v: Critical underdensity for voids (linear theory extrapolation), :math:`\delta_v = - \\frac{3}{20} \left[6 (\sinh \eta_{sc}-\eta_{sc})\\right]^{2/3} \\approx -2.717`.
    """

    def __init__(self,
                 Omega_m      = 0.3089,
                 Omega_b      = 0.0486,
                 Omega_K      = 0.,
                 N_nu         = 3,
                 M_nu         = 0.,
                 N_eff        = 3.046,
                 As           = 2.14e-9,
                 ns           = 0.9667,
                 sigma_8      = None,
                 h            = 0.6774,
                 w0           = -1.,
                 wa           = 0.,
                 tau          = 0.06,
                 T_cmb        = 2.7255):

        #-------------------------------------        
        # Check neutrinos
        #-------------------------------------
        assert N_nu <= N_eff, "Number of active neutrinos must be smaller than N_eff"
        assert len(np.atleast_1d(M_nu))<=N_nu, "Provided a number of neutrino masses greater than the actual number of neutrinos. Set N_nu to be at least equal to the length of M_nu"

        #-------------------------------------        
        # Check that at least one between As and sigma_8 is given
        #-------------------------------------
        if As is None and sigma_8 is None:
            raise AssertionError("At least one between As and sigma_8 must be different from None.")


        #---------------------------------------------------
        # Calling the functions related to initialization
        #---------------------------------------------------
        self.Omega_m      = Omega_m
        self.Omega_b      = Omega_b
        self.Omega_K      = Omega_K
        self.N_nu         = N_nu
        self.M_nu         = np.pad(np.atleast_1d(M_nu), (0,self.N_nu-len(np.atleast_1d(M_nu))), 'constant')
        self.N_eff        = N_eff
        self.Gamma_nu     = (4./11.)**(1./3.)*(N_eff/self.N_nu)**0.25
        self.massive_nu   = np.count_nonzero(self.M_nu)
        self.massless_nu  = self.N_eff - self.massive_nu
        self.As           = As
        if As is not None:
            self.log10_As = np.log10(As)
        self.sigma_8      = sigma_8
        self.ns           = ns
        self.w0           = w0
        self.wa           = wa
        self.tau          = tau
        self.T_cmb        = T_cmb
        self.T_nu         = T_cmb*self.Gamma_nu
        self.theta        = T_cmb/2.7
        self.h            = h
        self.H0           = 100.*self.h
        self.K            = -self.Omega_K*(self.H0/self.h/const.c)**2.    # (h/Mpc)^2

        #-------------------------------------
        # Quantities for halo mass function and void size function
        #-------------------------------------
        self.delta_sc     = 3./20.*(12.*const.PI)**(2./3.)
        self.eta_sc       = 3.48752242
        self.delta_v      = - 3./20.*(6.*(np.sinh(self.eta_sc)-self.eta_sc))**(2./3.)
        self.M            = np.logspace(2.1, 17.9, 512)

        #-------------------------------------
        # Other cosmological parameters
        #-------------------------------------
        self.Omega_gamma       = const.alpha_BB*self.T_cmb**4./(const.c*1.e3)**2./const.Msun*1.e3*const.Mpc_to_m**3./const.rhoch2/self.h**2.
        self.Omega_nu          = 15./const.PI**4.*self.Gamma_nu**4.*self.Omega_gamma*np.array([self.FermiDirac_integral(x/(const.kB*self.T_nu)) for x in self.M_nu])
        self.Omega_cdm         = self.Omega_m - self.Omega_b - np.sum(self.Omega_nu)
        self.Omega_cb          = self.Omega_cdm + Omega_b
        self.Omega_lambda      = 1. - self.Omega_cb - np.sum(self.Omega_nu) - self.Omega_K - self.Omega_gamma
        self.Omega_massive_nu  = self.Omega_nu[np.where(self.M_nu != 0.)]
        self.Omega_massless_nu = self.Omega_nu[np.where(self.M_nu == 0.)]

        self.omega_m      = Omega_m*h**2.
        self.omega_b      = Omega_b*h**2.
        self.omega_K      = Omega_K*h**2.
        self.omega_cdm    = self.Omega_cdm*h**2.
        self.omega_cb     = self.Omega_cb*h**2.
        self.omega_nu     = self.Omega_nu*h**2.
        self.omega_gamma  = self.Omega_gamma*h**2.

        #-------------------------------------
        # Density fractions
        #-------------------------------------
        self.f_nu     = self.Omega_nu/self.Omega_m
        self.f_nu_tot = np.sum(self.f_nu)
        self.f_cb     = self.Omega_cb/self.Omega_m
        self.f_b      = self.Omega_b/self.Omega_m
        self.f_c      = self.Omega_cdm/self.Omega_m


    #-------------------------------------------------------------------------------
    # SCALE FACTOR FROM REDSHIFT
    #-------------------------------------------------------------------------------
    def scale_factor(self, z = 0.):
        """
        Returns the scale factor given the redshift.

        :param z: Redshift.
        :type z: float, default = 0.0

        :return: float
        """
        return 1./(1.+z)

    #-------------------------------------------------------------------------------
    # REDSHIFT FROM SCALE FACTOR
    #-------------------------------------------------------------------------------
    def redshift(self, a = 1.):
        """
        Returns the redshift given the scale factor.

        :param a: Scale factor.
        :type a: float, default = 1.0

        :return: float
        """
        return 1./a-1.

    #-------------------------------------------------------------------------------
    # AGE OF THE UNIVERSE
    #-------------------------------------------------------------------------------
    def age(self, z = 0.):
        """
        Cosmic time from Big Bang in :math:`\mathrm{Myr}`.

        :param z: Redshift.
        :type z: float, default = 0.0

        :return: float
        """
        integrand = lambda x: const.Mpc_to_km/(self.H(x)*(1.+x))/const.Myr_to_s
        age, _ = sint.quad(integrand, z, np.inf)
        return age

    #-------------------------------------------------------------------------------
    # LOOKBACK TIME
    #-------------------------------------------------------------------------------
    def lookback_time(self, z = 1.):
        """
        Cosmic time from today to a given redshift in Myr.

        :param z: Redshift.
        :type z: float, default = 1.0

        :return: float
        """
        integrand = lambda x: const.Mpc_to_km/(self.H(x)*(1.+x))/const.Myr_to_s
        lookback, _ = sint.quad(integrand, 0., z)
        return lookback

    #-------------------------------------------------------------------------------
    # OMEGA COLD DARK MATTER (as function of z)
    #-------------------------------------------------------------------------------
    def Omega_cdm_z(self, z):
        """
        Cold dark matter density parameter at a given redshift

        :param z: Redshifts.
        :type z: array

        :return: array with :math:`\Omega_{cdm}(z)`.
        """
        return self.Omega_cdm*(1.+z)**3.*(self.H0/self.H(z))**2.

    #-------------------------------------------------------------------------------
    # OMEGA BARYON (as function of z)
    #-------------------------------------------------------------------------------
    def Omega_b_z(self, z):
        """
        Baryon density parameter at a given redshift

        :param z: Redshifts.
        :type z: array

        :return: array with :math:`\Omega_{b}(z)`.
        """
        return self.Omega_b*(1.+z)**3.*(self.H0/self.H(z))**2.

    #-------------------------------------------------------------------------------
    # OMEGA CDM + BARYON (as function of z)
    #-------------------------------------------------------------------------------
    def Omega_cb_z(self, z):
        """
        Cold dark matter plus baryon density parameter at a given redshift

        :param z: Redshifts.
        :type z: array

        :return: array with :math:`\Omega_{cb}(z)`.
        """
        return self.Omega_cb*(1.+z)**3.*(self.H0/self.H(z))**2.


    #-------------------------------------------------------------------------------
    # FERMI-DIRAC INTEGRAL
    #-------------------------------------------------------------------------------
    def FermiDirac_integral(self, y):
        """
        It computes the integral

        .. math::

            \mathcal F(y) = \int_0^\infty dx \ x^2 \ \\frac{(x^2+y^2)^{1/2}}{e^x+1},

        useful to compute the neutrino parameter of state
        :math:`w_\\nu = \\frac{1}{3}\left[1-\\frac{\mathrm{d}\ln\mathcal F}{\mathrm{d} \ln y}\\right]`


        :param y: Quantity related to neutrino mass, namely :math:`\\frac{M_\\nu}{(1+z) k_B T_\\nu}`.
        :type y: float

        :return: float
        """
        return sint.quad_vec(lambda x: x**2.*np.sqrt(x**2.+y**2.)/(np.exp(x)+1.), 0., 100.)[0]

    #-------------------------------------------------------------------------------
    # OMEGA NEUTRINO (as function of z)
    #-------------------------------------------------------------------------------
    def Omega_nu_z(self, z):
        """
        Neutrino density parameters at a given redshift.


        :param z: Redshifts.
        :type z: array

        :return: array of shape ``(self.N_nu, len(z))`` containing :math:`\Omega_\\nu(z)`.
        
        """
        mnu  = np.atleast_1d(self.M_nu)
        zz   = np.atleast_1d(np.array(z))
        onuz = np.zeros((len(mnu),len(zz)))
        for i in xrange(len(mnu)):
            y = mnu[i]/((1.+zz)*const.kB*self.T_nu)
            F = np.array(list(map(self.FermiDirac_integral,y)))
            onuz[i] = 15./const.PI**4.*self.Omega_gamma*F*self.Gamma_nu**4.*(1.+zz)**4.*self.H0**2./self.H(zz)**2.
        return onuz

    #-------------------------------------------------------------------------------
    # WARM DARK MATTER TEMPERATURE
    #-------------------------------------------------------------------------------
    def T_wdm(self, Omega_wdm, M_wdm):
        """
        Temperature of any warm dark matter component (also neutrinos).

        :param Omega_wdm: WDM density parameter today.
        :type Omega_wdm: float

        :param M_wdm: WDM mass in keV.
        :type M_wdm: float

        :return: float.
        
        """
        M_wdm *= 1e3 # switch to eV
        denominator = np.pi**4.*const.kB*self.T_cmb / (15*self.Gamma_nu**3.*self.omega_gamma*1.5*ss.zeta(3))*self.h**2
        return self.Gamma_nu*(Omega_wdm*denominator/M_wdm)**(1./3.)*self.T_cmb

    #-------------------------------------------------------------------------------
    # OMEGA MATTER (as function of z)
    #-------------------------------------------------------------------------------
    def Omega_m_z(self, z):
        """
        Matter density parameter at a given redshift.

        :param z: Redshifts.
        :type z: array

        :return: array with :math:`\Omega_{m}(z)`.
        """
        return self.Omega_cdm_z(z) + self.Omega_b_z(z) + np.sum(self.Omega_nu_z(z), axis = 0)

    #-------------------------------------------------------------------------------
    # OMEGA LAMBDA (as function of z)
    #-------------------------------------------------------------------------------
    def Omega_lambda_z(self, z):
        """
        Dark energy density parameter at a given redshift.

        :param z: Redshifts.
        :type z: array

        :return: array with :math:`\Omega_{\Lambda}(z)`.
        """
        w_DE = self.w0+self.wa*z/(1.+z)
        return self.Omega_lambda*(1.+z)**(3.*(1.+w_DE))*(self.H0/self.H(z))**2.


    #-------------------------------------------------------------------------------
    # OMEGA K (as function of z)
    #-------------------------------------------------------------------------------
    def Omega_K_z(self, z):
        """
        Curvature density parameter at a given redshift.

        :param z: Redshifts.
        :type z: array

        :return: array with :math:`\Omega_{K}(z)`.
        """
        return self.Omega_K*(1.+z)**2.*(self.H0/self.H(z))**2.


    #-------------------------------------------------------------------------------
    # OMEGA GAMMA (as function of z)
    #-------------------------------------------------------------------------------
    def Omega_gamma_z(self, z):
        """
        Photon density parameter at a given redshift.

        :param z: Redshifts.
        :type z: array

        :return: array with :math:`\Omega_{\gamma}(z)`.
        """
        return self.Omega_gamma*(1.+z)**4.*(self.H0/self.H(z))**2.


    #-------------------------------------------------------------------------------
    # OMEGA GAMMA (as function of z)
    #-------------------------------------------------------------------------------
    def w_DE(self, z):
        """
        Dark energy parameter of state ad function of redshift.

        :param z: Redshifts.
        :type z: array

        :return: array with :math:`w_{de}(z)`.
        """
        return self.w0+self.wa*z/(1.+z)

    #-------------------------------------------------------------------------------
    # HUBBLE PARAMETER
    #-------------------------------------------------------------------------------
    def H(self, z):
        """
        Hubble function in km/s/Mpc. 

        :param z: Redshifts.
        :type z: array

        :return: array with :math:`H(z)` in units of km/s/Mpc.
        """
        # Dark energy parameter of state
        wde = self.w0+self.wa*(z/(1.+z))
        # Neutrino contribution
        y = np.outer(self.M_nu/(const.kB*self.T_nu), 1./(1.+z))
        F = np.zeros_like(y)
        for i in xrange(len(np.atleast_1d(y))):
            F[i] = np.array(list(map(self.FermiDirac_integral, np.atleast_1d(y[i]))))
        neutrino_contribution = 15./const.PI**4.*self.Gamma_nu**4.*self.Omega_gamma*F*(1.+z)**4.
        # H(z)
        return self.H0*(self.Omega_cb*(1.+z)**3. +
                    self.Omega_gamma*(1.+z)**4. + 
                    self.Omega_lambda*(1.+z)**(3.*(1.+wde)) +
                    self.Omega_K*(1.+z)**2. +
                    np.sum(neutrino_contribution, axis = 0))**0.5


    def H_massive(self, z):
        """
        Hubble function in km/s/Mpc. It assumes that all neutrinos are pure matter and therefore
        :math:`w_\\nu = 0`.
        For the minimum neutrino masses allowed by particle physics, assuming normal hierarchy
        and the correct differences of square masses, the error committed is about 0.01% at :math:`z=0`,
        0.5% at :math:`z = 100`, 5% at :math:`z = 1000` and 30% at :math:`z = \infty`. 

        :param z: Redshifts.
        :type z: array

        :return: array with :math:`H(z)` in units of km/s/Mpc.

        """
        return self.H0*(self.Omega_cb*(1.+z)**3. +
               np.sum(self.Omega_nu)*(1.+z)**3. +
               self.Omega_lambda*(1.+z)**(3.*(1.+self.w0+self.wa*(z/(1.+z)))) +
               self.Omega_gamma*(1.+z)**4. +
               self.Omega_K*(1.+z)**2.)**0.5


    #-------------------------------------------------------------------------------
    # ACCELERATION PARAMETER 
    #-------------------------------------------------------------------------------
    def q_acc(self, z):
        """
        Acceleration parameter at a given redshift.

        :param z: Redshifts.
        :type z: array

        :return: array.
        """
        return self.Omega_gamma_z(z) + self.Omega_m_z(z)/2. - self.Omega_lambda_z(z)

    #-------------------------------------------------------------------------------
    # CRITICAL DENSITY
    #-------------------------------------------------------------------------------
    def rho_crit(self, z):
        """
        Critical density of the Universe at a given redshift in units of :math:`h^2 M_\odot \mathrm{Mpc}^{-3}`.

        :param z: Redshifts.
        :type z: array

        :return: array.
        """
        return 3.*self.H(z)**2./(8.*const.PI*const.G)/self.h**2.

    #-------------------------------------------------------------------------------
    # MATTER DENSITY (as function of z)
    #-------------------------------------------------------------------------------
    def rho(self, z):
        """
        Matter density of the Universe at a given redshift in units of :math:`h^2 M_\odot \mathrm{Mpc}^{-3}`.

        :param z: Redshifts.
        :type z: array

        :return: array.
        """
        return self.rho_crit(z)*self.Omega_m_z(z)

    #-------------------------------------------------------------------------------
    # REDSHIFT OF EQUALITY
    #-------------------------------------------------------------------------------
    def z_eq(self):
        """
        Redshift at which radiation and matter had the same density.

        :return: float.
        """
        theta = self.T_cmb/2.7
        return 25000.*self.Omega_m*self.h**2.*theta**-4.

    #-------------------------------------------------------------------------------
    # SCALE OF EQUALITY
    #-------------------------------------------------------------------------------
    def k_eq(self):
        """
        Scale corresponding to epoch of equality (peak of matter power spectrum) in :math:`h/\mathrm{Mpc}`.

        :return: float.
        """
        z_eq = self.z_eq()
        H_eq = 100.*(2.*self.Omega_m_z(0.)*(1.+z_eq)**3.)**0.5
        return H_eq/const.c/(1.+z_eq)


    #-------------------------------------------------------------------------------
    # WINDOW FUNCTIONS
    #-------------------------------------------------------------------------------
    def TopHat_window(self, x):
        """
        Top-hat window function in Fourier space.

        :param x: Abscissa.
        :type x: array

        :return: array.
        """
        return 3./(x)**3*(np.sin(x)-x*np.cos(x))

    def Gaussian_window(self, x):
        """
        Gaussian window function.

        :param x: Abscissa.
        :type x: array

        :return: array.
        """
        return np.exp(-x**2./2.)

    def Sharp_k_window(self, x, step=1e-2):
        """
        Sharp window function in Fourier space.

        :param x: Abscissa.
        :type x: array

        :param step: Transition width from 0 to 1.
        :type step: float, default = 1e-2

        :return: array.
        """
        return 0.5*(1.+2./np.pi*np.arctan((1.-x)/step))

    def Smooth_k_window(self, x, beta):
        """
        Smooth window function in Fourier space.

        :param x: Abscissa.
        :type x: array

        :param beta: Transition width from 0 to 1.
        :type beta: float, default = 1e-2

        :return: array.
        """
        return 1./(1.+x**beta)


    #-------------------------------------------------------------------------------
    # COMOVING DISTANCE
    #-------------------------------------------------------------------------------
    def comoving_distance(self, z, massive_nu_approx = False):
        """
        Comoving distance to a given redshift in :math:`\mathrm{Mpc}/h`.

        :param z: Redshifts.
        :type z: array

        :param massive_nu_approx: Whether to use ``self.H_massive()`` or ``self.H()`` to compute Hubble expansion, i.e. whether to consider massive neutrinos as matter or do the expensive computation.
        :type massive_nu_approx: boolean, default = False

        :return: array.
        """
        z = np.atleast_1d(z)
        if massive_nu_approx:
            result = np.array([sint.quad(lambda x: const.c*1./(self.H_massive(x)/self.h), 0., z[i], epsabs = 1e-8)[0] for i in range(len(np.atleast_1d(z)))])
        else:
            result = np.array([sint.quad(lambda x: const.c*1./(self.H(x)/self.h), 0., z[i], epsabs = 1e-8)[0] for i in range(len(np.atleast_1d(z)))])

        return result


    #-------------------------------------------------------------------------------
    # GEOMETRIC FACTOR
    #-------------------------------------------------------------------------------
    def f_K(self, z, massive_nu_approx = False):
        """
        Geometric factor to a given redshift in :math:`\mathrm{Mpc}/h`. If :math:`\chi(z)` is the comoving distance and :math:`k` is the curvature, then

        .. math::
            
            f_K(z) =\left\{\\begin{array}{ll}
                    \chi(z) & \\text{for } K=0 \\

                    \\frac{1}{\sqrt{K}} \ \sin[\sqrt{K}\chi(z)] & \\text{for } K>0

                    \\frac{1}{\sqrt{|K|}} \ \sinh[\sqrt{|K|}\chi(z)] & \\text{for } K<0

                    \end{array}.\\right.

        :param z: Redshifts.
        :type z: array

        :param massive_nu_approx: Whether to use ``self.H_massive()`` or ``self.H()`` to compute Hubble expansion, i.e. whether to consider massive neutrinos as matter or do the expensive computation.
        :type massive_nu_approx: boolean, default = False

        :return: array.
        """
        # Curvature in (h/Mpc)^2 units. Then I will take the sqrt and it will
        # go away with comoving_distance(z), giving a final result in units of Mpc/h
        K = self.K
        # Change function according to sign of K
        if K == 0.:
            return self.comoving_distance(z, massive_nu_approx) #Mpc/h
        elif K > 0.:
            return 1./K**0.5*np.sin(K**0.5*self.comoving_distance(z, massive_nu_approx)) #Mpc/h
        else:
            return 1./np.abs(K)**0.5*np.sinh(np.abs(K)**0.5*self.comoving_distance(z, massive_nu_approx)) #Mpc/h

    #-------------------------------------------------------------------------------
    # DIFFERENTIAL GEOMETRIC FACTOR (FOR WINDOW FUNCTION)
    #-------------------------------------------------------------------------------
    def delta_f_K(self, z_1, z_2, massive_nu_approx = False):
        """
        Difference in geometric factor (distance) between two redshifts in :math:`\mathrm{Mpc}/h`.

        :param z_1: Redshift number 1.
        :type z_1: float

        :param z_2: Redshift number 2.
        :type z_2: float


        :param massive_nu_approx: Whether to use ``self.H_massive()`` or ``self.H()`` to compute Hubble expansion, i.e. whether to consider massive neutrinos as matter or do the expensive computation.
        :type massive_nu_approx: boolean, default = False

        :return: array.
        """
        # Curvature in (h/Mpc)^2 units. Then I will take the sqrt and it will
        # go away with comoving_distance(z), giving a final result in units of Mpc/h
        K = self.K
        # Change function according to sign of K
        delta_chi = self.comoving_distance(z_1, massive_nu_approx) - self.comoving_distance(z_2, massive_nu_approx) #Mpc/h
        if K == 0.:
            return delta_chi
        elif K > 0.:
            return 1./K**0.5*np.sin(K**0.5*delta_chi) #Mpc/h
        else:
            return 1./np.abs(K)**0.5*np.sinh(np.abs(K)**0.5*delta_chi) #Mpc/h

    #-------------------------------------------------------------------------------
    # LUMINOSITY DISTANCE
    #-------------------------------------------------------------------------------
    def luminosity_distance(self, z, massive_nu_approx = False):
        """
        Luminosity distance to a given redshift in :math:`\mathrm{Mpc}/h`.

        :param z: Redshifts.
        :type z: array

        :param massive_nu_approx: Whether to use ``self.H_massive()`` or ``self.H()`` to compute Hubble expansion, i.e. whether to consider massive neutrinos as matter or do the expensive computation.
        :type massive_nu_approx: boolean, default = False

        :return: array.
        """
        com = self.f_K(z, massive_nu_approx)
        return com*(1.+z)

    #-------------------------------------------------------------------------------
    # ANGULAR DIAMETER DISTANCE
    #-------------------------------------------------------------------------------
    def angular_diameter_distance(self, z, massive_nu_approx = False):
        """
        Angular diameter distance to a given redshift in :math:`\mathrm{Mpc}/h`.

        :param z: Redshifts.
        :type z: array

        :param massive_nu_approx: Whether to use ``self.H_massive()`` or ``self.H()`` to compute Hubble expansion, i.e. whether to consider massive neutrinos as matter or do the expensive computation.
        :type massive_nu_approx: boolean, default = False

        :return: array.
        """
        com = self.f_K(z, massive_nu_approx)
        return com/(1.+z)

    #-------------------------------------------------------------------------------
    # ISOTROPIC VOLUME DISTANCE
    #-------------------------------------------------------------------------------
    def isotropic_volume_distance(self, z, massive_nu_approx = False):
        """
        Isotropic volume distance to a given redshift in :math:`\mathrm{Mpc}/h`.

        :param z: Redshifts.
        :type z: array

        :param massive_nu_approx: Whether to use ``self.H_massive()`` or ``self.H()`` to compute Hubble expansion, i.e. whether to consider massive neutrinos as matter or do the expensive computation.
        :type massive_nu_approx: boolean, default = False

        :return: array.
        """
        return ((1.+z)**2.*self.angular_diameter_distance(z, massive_nu_approx)**2.*const.c*z*self.h/self.H(z))**(1./3.)


    #-------------------------------------------------------------------------------
    # RECESSION VELOCITY
    #-------------------------------------------------------------------------------
    def v_rec(self, z, massive_nu_approx = False):
        """
        Recession velocity of galaxies at a given redshift in km/s.

        :param z: Redshifts.
        :type z: array

        :param massive_nu_approx: Whether to use ``self.H_massive()`` or ``self.H()`` to compute Hubble expansion, i.e. whether to consider massive neutrinos as matter or do the expensive computation.
        :type massive_nu_approx: boolean, default = False

        :return: array.
        """
        return self.H(z)/self.h*self.comoving_distance(z, massive_nu_approx)/(1.+z)


    #-------------------------------------------------------------------------------
    # L TO K
    #-------------------------------------------------------------------------------
    def l_to_k(self, l, z, massive_nu_approx = False):
        """
        Conversion factor from multipoles to scales given the redshift

        :param l: Multipoles
        :type l: array

        :param z: Redshifts.
        :type z: array

        :param massive_nu_approx: Whether to use ``self.H_massive()`` or ``self.H()`` to compute Hubble expansion, i.e. whether to consider massive neutrinos as matter or do the expensive computation.
        :type massive_nu_approx: boolean, default = False

        :return: array.
        """
        inv_dist = 1./self.f_K(z, massive_nu_approx = False)
        scale = np.outer(l,inv_dist)
        return scale

    #-------------------------------------------------------------------------------
    # R_bg
    #-------------------------------------------------------------------------------
    def R_bg(self, z):
        """
        Weigthed ratio :math:`\\frac{3 \\rho_b}{4 \\rho_\gamma}` as a function of redshift

        :param z: Redshifts.
        :type z: array

        :return: array.
        """
        rho_b           = self.Omega_b*self.rho_crit(0.)*(1.+z)**3.
        rho_gamma       = self.Omega_gamma*self.rho_crit(0.)*(1.+z)**4.
        rho_massless_nu = rho_gamma*7./8*(4./11.)**(4./3.)*self.massless_nu
        
        return 3.*rho_b/(4.*(rho_gamma + rho_massless_nu))


    #-------------------------------------------------------------------------------
    # SOUND SPEED
    #-------------------------------------------------------------------------------
    def c_s(self, z):
        """
        Speed of sound at a given redshift, in km/s.
        Approximation valid only before recombination, say :math:`z > 1200`.

        :param z: Redshifts.
        :type z: array

        :return: array.
        """
        R = self.R_bg(z)
        return const.c/np.sqrt(3.*(1.+R))

    #-------------------------------------------------------------------------------
    # NEUTRINO THERMAL VELOCITY
    #-------------------------------------------------------------------------------
    def neutrino_thermal_velocity(self, z):
        """
        Thermal velocity in km/s of each neutrino species at a given redshift.
        Approximation valid only at :math:`z \ll z_\mathrm{nr}`

        :param z: Redshifts.
        :type z: array

        :return: array.
        """
        vel = np.zeros(self.N_nu)
        for i in xrange(self.N_nu):
            if self.M_nu[i] == 0. :
                vel[i] = const.c
            else:
                fac    = 5./3.*5.*ss.zeta(5.)/ss.zeta(3.)
                vel[i] = fac**.5*(const.kB*self.T_nu/self.M_nu[i])*(1.+z)*const.c
        return vel


    #-------------------------------------------------------------------------------
    # DRAG EPOCH
    #-------------------------------------------------------------------------------
    def z_d(self):
        """
        Drag epoch redshift according to Eisenstein & Hu approximation

        :return: float.
        """
        # Approximation for drag epoch redshift
        om_m = self.Omega_m-np.sum(self.Omega_nu)
        om_b = self.Omega_b
        h    = self.h
        b1   = 0.313*(om_m*h*h)**(-0.419)*(1+0.607*(om_m*h*h)**0.674)
        b2   = 0.238*(om_m*h*h)**0.223
        z_d  = 1291.*(1+b1*(om_b*h*h)**b2)*(om_m*h*h)**0.251/(1.+0.659*(om_m*h*h)**0.828)
        return z_d


    #-------------------------------------------------------------------------------
    # SOUND HORIZON AT DRAG EPOCH (BAO SCALE)
    #-------------------------------------------------------------------------------
    def r_s(self):
        """
        Sound horizon at drag epoch.

        :return: float.
        """
        if 'classy' not in sys.modules:
            warnings.warn("Class not installed, using a custom function to compute sound horizon (not precise)")
            return self.r_s_drag()
        else:
            params = {
                'A_s':       self.As,
                'n_s':       self.ns, 
                'h':         self.h,
                'omega_b':   self.Omega_b*self.h**2.,
                'omega_cdm': self.Omega_cdm*self.h**2.,
                'Omega_k':   self.Omega_K,
                'N_ur':      self.massless_nu,
                'N_ncdm':    self.massive_nu}
            if self.massive_nu != 0:
                params['m_ncdm'] = ', '.join(str(x) for x in self.M_nu[self.M_nu != 0.])

            cosmo = Class()
            cosmo.set(params)
            cosmo.compute()

            rs = cosmo.rs_drag()*cosmo.h()

            cosmo.struct_cleanup()
            cosmo.empty()

            return rs

    def r_s_drag(self):
        rs, _ = sint.quad(lambda x: self.c_s(x)/self.H(x), self.z_d(), np.inf)
        return rs*self.h

    #-----------------------------------------------------------------------------------------
    # MASS VARIANCE
    #-----------------------------------------------------------------------------------------
    def mass_variance(self, logM, k = [], pk = [], var = 'cb', window = 'th', **kwargs):
        """
        Mass variance in spheres as a function of mass.

        :param logM: logarithm (base 10!) of the masses at which to compute the variance, in units of :math:`M_\odot/h`. To compute these masses from radii, use :func:`colibri.cosmology.cosmo.mass_in_radius()`
        :type logM: array

        :param k: Scales of power spectrum in units of :math:`h/\mathrm{Mpc}`.
        :type k: array, default = []

        :param pk: Power spectrum in redshifts and scales in units of :math:`(\mathrm{Mpc}/h)^3`.
        :type pk: 2D array, one for each redshift, default = []

        :param var: component with respect to which to compute the variance.

         - 'cb' : cold dark matter + baryons
         - 'cdm': cold dark matter
         - 'b'  : baryons
         - 'nu' : neutrinos
         - 'tot': total matter
        :type var: string, default = 'cb'

        :param window: Window function used to filter.

         - `'th'`,`'th'`,`'tophat'`,`'top-hat'` for top-hat filter
         - `'gauss'`, `'Gaussian'`, `'Gauss'`, `'gaussian'`, `'g'`, for Gaussian
         - `'sharp'`, `'heaviside'`, `'s'` for sharp-k filter

        :type window: string, default = 'th'

        :return: An interpolated function that gives :math:`\\sigma^2(\log_{10}(M))`, evaluable between 2 and 18 (therefore between :math:`M = 10^2` and :math:`10^{18} \ M_\odot/h`).
        """
        return self.mass_variance_multipoles(logM = logM, k = k, pk = pk, var = var, window = window, **kwargs)

    #-----------------------------------------------------------------------------------------
    # SIGMA^2_j
    #-----------------------------------------------------------------------------------------
    def mass_variance_multipoles(self,
                                 logM,
                                 k      = [],
                                 pk     = [],
                                 var    = 'cb',
                                 window = 'th',
                                 j      = 0,
                                 smooth = False,
                                 R_sm   = 5.5,
                                 beta   = 2.,
                                 **kwargs):
        """
        Multipoles of the mass variance as function of mass, namely:

        .. math::

            \sigma^2_j(M) = \int_0^\infty \\frac{dk \ k^{2+2j}}{2\pi^2} P(k) \ W^2[kR(M)],

        where :math:`W` is a window function, :math:`R` is a radius in :math:`\mathrm{Mpc}/h` and :math:`M` is the mass enclosed in such radius according to the window function.

        :param logM: logarithm (base 10!) of the masses at which to compute the variance, in units of :math:`M_\odot/h`. To compute these masses from radii, use :func:`colibri.cosmology.cosmo.mass_in_radius()`
        :type logM: array

        :param k: Scales of power spectrum in units of :math:`h/\mathrm{Mpc}`.
        :type k: array, default = []

        :param pk: Power spectrum in redshifts and scales in units of :math:`(\mathrm{Mpc}/h)^3`.
        :type pk: 2D array, one for each redshift, default = []

        :param var: component with respect to which to compute the variance.

         - 'cb' : cold dark matter + baryons
         - 'cdm': cold dark matter
         - 'b'  : baryons
         - 'nu' : neutrinos
         - 'tot': total matter
        :type var: string, default = 'cb'

        :param window: Window function used to filter.

         - `'th'`,`'th'`,`'tophat'`,`'top-hat'` for top-hat filter
         - `'gauss'`, `'Gaussian'`, `'Gauss'`, `'gaussian'`, `'g'`, for Gaussian
         - `'sharp'`, `'heaviside'`, `'s'` for sharp-k filter
         - `'smooth'`, `'smoothk'`, `'sm'` for smooth-k filter

        :type window: string, default = 'th'

        :param beta: slope of the smooth-k window (used only if `window==smooth`)
        :type beta: float, default = 2

        :param j: Order of multipole.
        :type j: even integer, default = 0

        :param smooth: Further smoothing of the density field with a Gaussian filter (useful for void size function).
        :type smooth: boolean, default = True

        :param R_sm: Size of second Gaussian filter in :math:`\mathrm{Mpc}/h.`
        :type R_sm: float, default = 5.5

        :return: 2D array containing :math:`\\sigma^2_j(\log_{10}M,z)`
        """

        # Checks
        pk=np.atleast_2d(pk)
        assert len(pk[0])==len(k), "Length of scales is different from power spectra"
        nz = len(pk)
        pk = np.atleast_2d(pk)

        # Assertions on scales, lengths and intervals
        assert np.max(k)>=10.,    "Maximum k of power spectrum is too low to obtain a convergent result. Use k_max>=10 h/Mpc."
        assert np.min(k)<=0.001,  "Minimum k of power spectrum is too high to obtain a convergent result. Use k_min<=0.001 h/Mpc."
        assert len(k)>=100,       "size of 'k' too low to obtain a convergent result. At least 100 points."
        assert np.all([np.isclose(np.log(k[ind+1]/k[ind]), np.log(k[ind+2]/k[ind+1]),
                atol = 1e-4, rtol = 1e-2) for ind in xrange(len(k[:-2]))]),"k are not regularly log-spaced"

        P_kappa = []
        for iz in range(nz):
            k_ext, p_tmp = UF.extrapolate_log(k, pk[iz], 1e-6, 1e8)
            P_kappa.append(p_tmp)
        kappa   = np.expand_dims(np.atleast_2d(k_ext),axis=1)
        P_kappa = np.expand_dims(P_kappa, axis = 1)

        # Scales and power
        dlnk    = np.log(k_ext[1]/k_ext[0])

        # Smoothing radii
        if   var == 'cb':   omega = self.Omega_cb
        elif var == 'cdm':  omega = self.Omega_cdm
        elif var == 'b':    omega = self.Omega_b
        elif var == 'nu':   omega = np.sum(self.Omega_nu)
        elif var == 'tot':  omega = self.Omega_m
        else:               raise NameError("Component unknown, use 'cb', 'cdm', 'b', 'nu', 'tot'")
        rho = self.rho_crit(0.)*omega
        #M   = self.M
        M   = 10.**logM
        R   = self.radius_of_mass(M, var = var, window = window, **kwargs)

        # Window function
        k,r = np.meshgrid(kappa,R)        
        if window in ['TH','th','tophat', 'top-hat']:
            W = self.TopHat_window(k*r)
        elif window in ['gauss', 'Gaussian', 'Gauss', 'gaussian', 'g']:
            W = self.Gaussian_window(k*r)
        elif window in ['sharp', 'heaviside', 's']:
            W = self.Sharp_k_window(k*r)
        elif window in ['smooth', 'smoothk', 'sm']:
            W = self.Smooth_k_window(k*r,beta=beta)
        else:
            raise NameError("Window not known")
        W = np.expand_dims(W,axis=0)

        # Second smoothing
        if smooth:
            sm = np.exp(-k**2.*(r/R_sm)**2./2.)
            sm = np.expand_dims(sm,axis=0)
        else:
            sm = 1.

        # Integration in log-bins (with numpy)
        sigma2 = sint.simps(kappa**(3.+2.*j)*P_kappa/(2.*const.PI**2.)*W**2.*sm**2.,dx=dlnk,axis=-1)
        return sigma2


    #-----------------------------------------------------------------------------------------
    # MASS IN SPHERE
    #-----------------------------------------------------------------------------------------
    def mass_in_radius(self, R, var = 'cb', window = 'th', prop_const = 2.5):
        """
        Mass contained in a sphere of radius R in :math:`M_\odot/h`.

        :param R: Radii in :math:`\mathrm{Mpc}/h`.
        :type R: array

        :param var: component with respect to which to compute the variance.

         - 'cb' : cold dark matter + baryons
         - 'cdm': cold dark matter
         - 'b'  : baryons
         - 'nu' : neutrinos
         - 'tot': total matter
        :type var: string, default = 'cb'

        :param window: Window function used to filter.

         - `'th'`,`'th'`,`'tophat'`,`'top-hat'` for top-hat filter
         - `'gauss'`, `'Gaussian'`, `'Gauss'`, `'gaussian'`, `'g'`, for Gaussian
         - `'sharp'`, `'heaviside'`, `'s'` for sharp-k filter
         - `'smooth'`, `'smoothk'`, `'sm'` for smooth-k filter
        :type window: string, default = 'th'

        :param prop_const: proportional constant of radius to mass (used only if `window==sharp`)
        :type prop_const: float, default = 2.5.

        :return: array.
        """

        if   var == 'cb':  omega = self.Omega_cb
        elif var == 'cdm': omega = self.Omega_cdm
        elif var == 'b':   omega = self.Omega_b
        elif var == 'nu':  omega = np.sum(self.Omega_nu)
        elif var == 'tot': omega = self.Omega_m
        else:              raise NameError("Component unknown, use 'cb', 'cdm', 'b', 'nu', 'tot'")

        rho_bg = self.rho_crit(0.)*omega

        # Window function
        if window in ['TH','th','tophat', 'top-hat']:
            return 4./3.*const.PI*rho_bg*R**3.
        elif window in ['gauss', 'Gaussian', 'Gauss', 'gaussian', 'g']:
            return rho_bg*(2.*const.PI*R**2.)**(3./2.)
        elif window in ['sharp', 'heaviside', 's', 'smooth', 'smoothk', 'sm']:
            return 4./3.*const.PI*rho_bg*(prop_const*R)**3.
        else:
            raise NameError("window not known")
        

    #-----------------------------------------------------------------------------------------
    # RADIUS OF MASS
    #-----------------------------------------------------------------------------------------
    def radius_of_mass(self, M, var = 'cb', window = 'th', prop_const = 2.5):
        """
        Radius that contains a certain amount of mass in :math:`\mathrm{Mpc}/h`.


        :param M: Masses in :math:`M_\odot/h`.
        :type M: array

        :param var: component with respect to which to compute the variance.

         - 'cb' : cold dark matter + baryons
         - 'cdm': cold dark matter
         - 'b'  : baryons
         - 'nu' : neutrinos
         - 'tot': total matter
        :type var: string, default = 'cb'

        :param window: Window function used to filter.

         - `'th'`,`'th'`,`'tophat'`,`'top-hat'` for top-hat filter
         - `'gauss'`, `'Gaussian'`, `'Gauss'`, `'gaussian'`, `'g'`, for Gaussian
         - `'sharp'`, `'heaviside'`, `'s'` for sharp-k filter
         - `'smooth'`, `'smoothk'`, `'sm'` for smooth-k filter
        :type window: string, default = 'th'

        :param prop_const: proportional constant of radius to mass (used only if `window==sharp`)
        :type prop_const: float, default = 2.5.


        :return: array.
        """
        if   var == 'cb':  omega = self.Omega_cb
        elif var == 'cdm': omega = self.Omega_cdm
        elif var == 'b':   omega = self.Omega_b
        elif var == 'nu':  omega = np.sum(self.Omega_nu)
        elif var == 'tot': omega = self.Omega_m
        else:              raise NameError("Component unknown, use 'cb', 'cdm', 'b', 'nu', 'tot'")

        rho_bg = self.rho_crit(0.)*omega

        # Window function
        if window in ['TH','th','tophat', 'top-hat']:
            return (3.*M/(4.*const.PI*rho_bg))**(1./3.)
        elif window in ['gauss', 'Gaussian', 'Gauss', 'gaussian', 'g']:
            return (M/rho_bg)**(1./3.)/(2.*const.PI)**0.5
        elif window in ['sharp', 'heaviside', 's', 'smooth', 'smoothk', 'sm']:
            return (3.*M/(4.*const.PI*rho_bg))**(1./3.)/prop_const
        else:
            raise NameError("window not known")

    #-----------------------------------------------------------------------------------------
    # VOLUME OF RADIUS
    #-----------------------------------------------------------------------------------------
    def volume_of_radius(self, R, window = 'th', prop_const = 2.5):
        """
        Volume of a window function of a given radius in :math:`(\mathrm{Mpc}/h)^3`.

        :param R: Radii in :math:`\mathrm{Mpc}/h`.
        :type R: array

        :param var: component with respect to which to compute the variance.

         - 'cb' : cold dark matter + baryons
         - 'cdm': cold dark matter
         - 'b'  : baryons
         - 'nu' : neutrinos
         - 'tot': total matter
        :type var: string, default = 'cb'

        :param window: Window function used to filter.

         - `'th'`,`'th'`,`'tophat'`,`'top-hat'` for top-hat filter
         - `'gauss'`, `'Gaussian'`, `'Gauss'`, `'gaussian'`, `'g'`, for Gaussian
         - `'sharp'`, `'heaviside'`, `'s'` for sharp-k filter
         - `'smooth'`, `'smoothk'`, `'sm'` for smooth-k filter
        :type window: string, default = 'th'

        :param prop_const: proportional constant of radius to mass (used only if `window==sharp`)
        :type prop_const: float, default = 2.5.


        :return: array.
        """

        # Window function
        if window in ['TH','th','tophat', 'top-hat']:
            return 4./3.*const.PI*R**3.
        elif window in ['gauss', 'Gaussian', 'Gauss', 'gaussian', 'g']:
            return (2.*const.PI*R**2.)**1.5
        elif window in ['sharp', 'heaviside', 's', 'smooth', 'smoothk', 'sm']:
            return 4./3.*const.PI*(prop_const*R)**3.
        else:
            raise NameError("window not known, use 'TH' or 'gauss'")

    #-----------------------------------------------------------------------------------------
    # VOLUME OF MASS
    #-----------------------------------------------------------------------------------------
    def volume_of_mass(self, M, var = 'cb', window = 'th', prop_const = 2.5):
        """
        Volume of a window function of a given mass in :math:`(\mathrm{Mpc}/h)^3`.

        :param M: Masses in :math:`M_\odot/h`.
        :type M: array

        :param var: component with respect to which to compute the variance.

         - 'cb' : cold dark matter + baryons
         - 'cdm': cold dark matter
         - 'b'  : baryons
         - 'nu' : neutrinos
         - 'tot': total matter
        :type var: string, default = 'cb'

        :param window: Window function used to filter.

         - `'th'`,`'th'`,`'tophat'`,`'top-hat'` for top-hat filter
         - `'gauss'`, `'Gaussian'`, `'Gauss'`, `'gaussian'`, `'g'`, for Gaussian
         - `'sharp'`, `'heaviside'`, `'s'` for sharp-k filter
         - `'smooth'`, `'smoothk'`, `'sm'` for smooth-k filter
        :type window: string, default = 'th'

        :param prop_const: proportional constant of radius to mass (used only if `window==sharp`)
        :type prop_const: float, default = 2.5.


        :return: array.
        """
        R = self.radius_of_mass(M, var = var, window = window, prop_const = prop_const)
        return self.volume_of_radius(R, window = window, prop_const = prop_const)


    #-----------------------------------------------------------------------------------------
    # LAGRANGE TO EULER
    #-----------------------------------------------------------------------------------------
    def lagrange_to_euler(self, z = 0., delta_v = None, delta_c = None):
        """
        Mapping between Eulerian and Lagrangian radii in :math:`\mathrm{Mpc}/h`.

        :param z: Redshift
        :type z: float

        :param delta_v: Critical underdensity in linear theory.
        :type delta_v: float

        :param delta_c: Critical overdensity in linear theory.
        :type delta_c: float


        :return: array.
        """
        z = np.array(z)
        if delta_v == None: delta_v = self.delta_v
        if delta_c == None: delta_c = self.delta_sc
        return (1.-self.D_1(z)*delta_v/delta_c)**(delta_c/3.0)

    #-----------------------------------------------------------------------------------------
    # PEAK-BACKGROUND SPLIT
    #-----------------------------------------------------------------------------------------
    def peak_height(self, logM, k = [], pk = []):
        """
        Peak height as a function of log10(M).

        :param logM: logarithm (base 10!) of the masses at which to compute the variance, in units of :math:`M_\odot/h`. To compute these masses from radii, use :func:`colibri.cosmology.cosmo.mass_in_radius()`
        :type logM: array

        :param k: Scales of power spectrum in units of :math:`h/\mathrm{Mpc}`.
        :type k: array, default = []

        :param pk: Power spectrum in redshifts and scales in units of :math:`(\mathrm{Mpc}/h)^3`.
        :type pk: 2D array, one for each redshift, default = []

        :return: 2D array containing :math:`\delta_c/\\sigma(\log_{10}M,z)`
        """
        # Checks
        pk=np.atleast_2d(pk)
        assert len(pk[0])==len(k), "Length of scales is different from power spectra"
        sigma2   = self.mass_variance(logM,k,pk)
        nu       = self.delta_sc/sigma2**.5
        return nu

    #-----------------------------------------------------------------------------------------
    # SHETH-TORMEN MASS FUNCTION
    #-----------------------------------------------------------------------------------------
    def ShethTormen_mass_function(self, sigma, a = 0.707, p = 0.3, delta_th = None):
        """
        Universal mass function by Sheth-Tormen as function of the RMS mass fluctuation in spheres :math:`\sigma(M)`.

        :param sigma: RMS mass fluctuation.
        :type sigma: array

        :param a: Sheth-Tormen mass function parameter.
        :type a: float, default = 0.707

        :param p: Sheth-Tormen mass function parameter.
        :type p: float<0.5, default = 0.3

        :param delta_th': Threshold for collapse.
        :type delta_th': float, default = None

        :return: array
        """
        if delta_th == None: delta_th = self.delta_sc
        nu = np.abs(delta_th)/sigma
        n = nu**2.
        A = 1./(1. + 2.**(-p)*ss.gamma(0.5-p)/np.sqrt(const.PI))
        ST = A * np.sqrt(2.*a*n/const.PI) * (1.+1./(a*n)**p) * np.exp(-a*n/2.)
        return ST

    #-----------------------------------------------------------------------------------------
    # SHETH-TORMEN MASS FUNCTION
    #-----------------------------------------------------------------------------------------
    def Despali_mass_function(self, sigma, a = 0.794, p = 0.247, A = 0.3333, delta_th = None):
        """
        Universal mass function by Despali as function of the RMS mass fluctuation in spheres :math:`\sigma(M)`.

        :param sigma: RMS mass fluctuation.
        :type sigma: array

        :param a: Sheth-Tormen mass function parameter.
        :type a: float, default = 0.707

        :param p: Sheth-Tormen mass function parameter.
        :type p: float<0.5, default = 0.3

        :param A: Amplitude of .
        :type A: float, default = 0.3333.

        :param delta_th': Threshold for collapse.
        :type delta_th': float, default = None

        :return: array
        """
        if delta_th == None: delta_th = self.delta_sc
        nu = np.abs(delta_th)/sigma
        n = nu**2.
        ST = A * np.sqrt(2.*a*n/const.PI) * (1.+1./(a*n)**p) * np.exp(-a*n/2.)
        return ST


    #-----------------------------------------------------------------------------------------
    # PRESS-SCHECHTER MASS FUNCTION
    #-----------------------------------------------------------------------------------------
    def PressSchechter_mass_function(self, sigma, delta_th = None):
        """
        Universal mass function by Press-Schechter as function of the RMS mass fluctuation in spheres :math:`\sigma(M)`.

        :param sigma: RMS mass fluctuation.
        :type sigma: array

        :param delta_th: Threshold for collapse.
        :type delta_th: float, default = None

        :return: array
        """
        return self.ShethTormen_mass_function(sigma, a = 1., p = 0., delta_th = delta_th)


    #-----------------------------------------------------------------------------------------
    # TINKER MASS FUNCTION
    #-----------------------------------------------------------------------------------------
    def Tinker_mass_function(self, sigma, z = 0., Delta = 200.):
        """
        Universal mass function by Tinker as function of the RMS mass fluctuation in spheres :math:`\sigma(M)`.

        :param sigma: RMS mass fluctuation.
        :type sigma: array

        :param z: Redshift.
        :type z: array, default = 0

        :param Delta: Overdensity of collapsed objects.
        :type Delta: 200<=float<=3200, default = 200

        :return: array
        """

        z = np.array(z)
        assert len(np.atleast_2d(sigma))==len(np.atleast_1d(z)), "First dimension of 'sigma' must correspond to number of redshifts"

        # Exponent for redshift evolution of parameters
        alpha = 10.**(-(0.75/np.log10(Delta/75.))**1.2)
        # Log of overdensity
        logDelta = np.log10(Delta)

        # Interpolation of parameters of mass function
        delta_array = [  200.,  300.,  400.,  600.,  800., 1200., 1600., 2400., 3200.]
        A_array     = [ 1.858659e-01, 1.995973e-01, 2.115659e-01, 2.184113e-01,
                        2.480968e-01, 2.546053e-01, 2.600000e-01, 2.600000e-01, 2.600000e-01]
        a_array     = [ 1.466904, 1.521782, 1.559186, 1.614585,
                        1.869936, 2.128056, 2.301275, 2.529241, 2.661983,]
        b_array     = [ 2.571104, 2.254217, 2.048674, 1.869559,
                        1.588649, 1.507134, 1.464374, 1.436827, 1.405210]
        c_array     = [ 1.193958, 1.270316, 1.335191, 1.446266,
                        1.581345, 1.795050, 1.965613, 2.237466, 2.439729]

        A_d = si.interp1d(delta_array, A_array, 'cubic')
        a_d = si.interp1d(delta_array, a_array, 'cubic')
        b_d = si.interp1d(delta_array, b_array, 'cubic')
        c_d = si.interp1d(delta_array, c_array, 'cubic')
        A = np.expand_dims(A_d(Delta)*(1.+z)**(-0.14), axis = 0).T
        a = np.expand_dims(a_d(Delta)*(1.+z)**(-0.06), axis = 0).T
        b = np.expand_dims(b_d(Delta)*(1.+z)**(-alpha), axis = 0).T
        c = np.expand_dims(c_d(Delta), axis = 0).T

        return A*((sigma/b)**(-a) + 1.)*np.exp(-c/sigma**2.)


    #-----------------------------------------------------------------------------------------
    # MICE MASS FUNCTION
    #-----------------------------------------------------------------------------------------
    def MICE_mass_function(self, sigma, z = 0.):
        """
        Universal mass function by Crocce et al. (2010) as function of the RMS mass fluctuation in spheres :math:`\sigma(M)`.

        :param sigma: RMS mass fluctuation.
        :type sigma: 2D array

        :param z: Redshift.
        :type z: array, default = 0

        :return: array
        """
        z = np.array(z)
        assert len(np.atleast_2d(sigma))==len(np.atleast_1d(z)), "First dimension of 'sigma' must correspond to number of redshifts"

        A = np.expand_dims(0.580*(1.+z)**-0.130, axis = 0).T
        a = np.expand_dims(1.370*(1.+z)**-0.150, axis = 0).T
        b = np.expand_dims(0.300*(1.+z)**-0.084, axis = 0).T
        c = np.expand_dims(1.036*(1.+z)**-0.024, axis = 0).T

        return A*(sigma**(-a)+b)*np.exp(-c/sigma**2.)


    #-----------------------------------------------------------------------------------------
    # SHETH-TORMEN BIAS
    #-----------------------------------------------------------------------------------------
    def ShethTormen_bias(self, sigma, a = 0.707, p = 0.3, delta_th = None):
        """
        Eulerian bias for the Sheth-Tormen mass function as function of the RMS mass fluctuation in spheres :math:`\sigma(M)`.

        :param sigma: RMS mass fluctuation.
        :type sigma: array

        :param a: Sheth-Tormen mass function parameter.
        :type a': float, default = 0.707

        :param p: Sheth-Tormen mass function parameter.
        :type p: float<0.5, default = 0.3

        :param delta_th: Threshold for collapse.
        :type delta_th: float, default = None

        :return: array
        """
        if delta_th == None: delta_th = self.delta_sc
        nu = np.abs(delta_th)/sigma
        b = 1. + (a*nu**2.-1.)/self.delta_sc + 2.*p/self.delta_sc/(1.+(a*nu**2.)**p)
        return b


    #-----------------------------------------------------------------------------------------
    # PRESS-SCHECHTER BIAS
    #-----------------------------------------------------------------------------------------
    def PressSchechter_bias(self, sigma):
        """
        Eulerian bias for the Press-Schechter mass function as function of the RMS mass fluctuation in spheres :math:`\sigma(M)`.

        :param sigma: RMS mass fluctuation.
        :type sigma: array

        :param delta_th: Threshold for collapse.
        :type delta_th: float, default = None

        :return: array
        """
        return self.ShethTormen_bias(sigma, a = 1., p = 0.)


    #-----------------------------------------------------------------------------------------
    # TINKER BIAS
    #-----------------------------------------------------------------------------------------
    def Tinker_bias(self, sigma, z = 0., Delta = 200.):
        """
        Eulerian bias for the Tinker mass function as function of the RMS mass fluctuation in spheres :math:`\sigma(M)`.

        :param sigma: RMS mass fluctuation.
        :type sigma: array

        :param z: Redshift.
        :type z: array, default = 0

        :param Delta: Overdensity of collapsed objects.
        :type Delta: 200<=float<=3200, default = 200

        :return: array
        """

        z = np.array(z)
        assert len(np.atleast_2d(sigma))==len(np.atleast_1d(z)), "First dimension of 'sigma' must correspond to number of redshifts"      

        y = np.log10(Delta)
        A = 1. + 0.24*y*np.exp(-(4./y)**4.)
        a = 0.44*y - 0.88
        C = 0.019 + 0.107*y + 0.19*np.exp(-(4./y)**4.)
        B, b, c = 0.183, 1.5, 2.4

        nu = self.delta_sc/sigma

        return 1. - A*nu**a/(nu**a+self.delta_sc**a) + B*nu**b + C*nu**c

    #-----------------------------------------------------------------------------------------
    # HALO BIAS
    #-----------------------------------------------------------------------------------------
    def halo_bias(self, sigma, mass_fun = 'ST', **kwargs):
        """
        Eulerian bias for the a given halo mass function as function of the RMS mass fluctuation in spheres :math:`\sigma(M)`.

        :param sigma: RMS mass fluctuation.
        :type sigma: array

        :param mass_fun: Kind of halo mass function.

         - 'Sheth-Tormen','ST','ShethTormen' for Sheth-Tormen
         - 'Press-Schechter', 'PS', 'PressSchechter' for Press-Schechter
         - 'Tinker', 'T', 'T08' for Tinker et al. (2008)

        :type mass_fun: string, default = `'ST'`

        :param kwargs: Keyword arguments to pass to `'mass_fun'`.

        :return: array
        """
        # Choose according the mass function
        if mass_fun in ['Sheth-Tormen','ST','ShethTormen','Despali','D']:
            return self.ShethTormen_bias(sigma = sigma, **kwargs)
        elif mass_fun in ['Press-Schechter', 'PS', 'PressSchechter']:
            return self.PressSchechter_bias(sigma = sigma)
        elif mass_fun in ['Tinker', 'T', 'T08']:
            return self.Tinker_bias(sigma = sigma, **kwargs)
        else:
            raise NameError("Unknown mass function, use 'Sheth-Tormen','ST','ShethTormen' / 'Press-Schechter', 'PS', 'PressSchechter' / 'Tinker', 'T', 'T08'")

    #-----------------------------------------------------------------------------------------
    # EFFECTIVE BIAS
    #-----------------------------------------------------------------------------------------
    def effective_bias(self, z = 0., M_min = 1e10, M_max = 1e17, k = [], pk = [], mass_fun = 'ST', **kwargs):
        """
        It computes the effective halo bias as

        .. math::

            b_\mathrm{eff} = \\frac{\int_{M_{min}}^{M_{max}} dM \ b(M) \ \\frac{dn}{dM}}{\int_{M_{min}}^{M_{max}} dM \ \\frac{dn}{dM}}

        where :math:`b(M)` is the linear halo bias given the kind of mass function.

        :param z: Redshift, used only for Tinker and Crocce mass functions
        :type z: array, default = 0

        :param M_min: Minimum halo mass in :math:`M_\odot/h`.
        :type M_min: float>1e2, default = 1e10

        :param M_min: Maximum halo mass in :math:`M_\odot/h`.
        :type M_max: float<1e18, default = 1e17

        :param k: Scales of power spectrum in units of :math:`h/\mathrm{Mpc}`.
        :type k: array, default = []

        :param pk: Power spectrum in units of :math:`(\mathrm{Mpc}/h)^3`.
        :type pk: array, default = []

        :param mass_fun: Kind of halo mass function.

         - 'Sheth-Tormen','ST','ShethTormen' for Sheth-Tormen
         - 'Press-Schechter', 'PS', 'PressSchechter' for Press-Schechter
         - 'Tinker', 'T', 'T08' for Tinker et al. (2008)

        :type mass_fun: string, default = `'ST'`

        :param kwargs: Keyword arguments to pass to `'mass_fun'`.

        :return: array, same length as ``z``
        """

        # mass quantities
        logM   = np.log10(self.M)
        conv   = np.log(10.)

        # halo mass function
        HMF    = self.halo_mass_function(logM = logM, z = z, k = k, pk = pk, mass_fun = mass_fun, **kwargs)

        # mass variance in spheres
        sigma2 = self.mass_variance(logM = logM, k = k, pk = pk)

        # compute bias and interpolate in log10(mass)
        bias_eff = np.zeros(len(pk))
        for iz in range(len(pk)):
            bias           = np.array(self.halo_bias(sigma2[iz]**.5, mass_fun = mass_fun, **kwargs))
            bias_interp    = si.interp1d(logM, bias, kind = 'cubic')
            HMF_int        = si.interp1d(logM, HMF[iz], 'cubic')
            numerator, _   = sint.quad(lambda m: HMF_int(m)*bias_interp(m)*conv*10.**m, np.log10(M_min), np.log10(M_max))
            denominator, _ = sint.quad(lambda m: HMF_int(m)*conv*10.**m,                np.log10(M_min), np.log10(M_max))
            bias_eff[iz]   = numerator/denominator
        return bias_eff


    #-----------------------------------------------------------------------------------------
    # HALO MASS FUNCTION
    #-----------------------------------------------------------------------------------------
    def halo_mass_function(self, logM, z = 0., k = [], pk = [], window = 'th', mass_fun = 'Sheth-Tormen', beta = 2., prop_const = 2.5, **kwargs):
        """
        Halo mass function, i.e. number of halos per unit volume per unit mass.

        :param logM: logarithm (base 10!) of the masses at which to compute the variance, in units of :math:`M_\odot/h`. To compute these masses from radii, use :func:`colibri.cosmology.cosmo.mass_in_radius()`.
        :type logM: array

        :param z: Redshift, used only if Tinker and MICE/Crocce mass functions are requested. Must be of same length as ``pk``.
        :type z: array, default = 0

        :param k: Scales of power spectrum in units of :math:`h/\mathrm{Mpc}`.
        :type k: array, default = []

        :param pk: Power spectrum in units of :math:`(\mathrm{Mpc}/h)^3`.
        :type pk: array, default = []

        :param mass_fun: Kind of halo mass function.

         - 'Sheth-Tormen','ST','ShethTormen' for Sheth-Tormen
         - 'Press-Schechter', 'PS', 'PressSchechter' for Press-Schechter
         - 'Despali', 'D' for Despali et al. (2015)
         - 'Tinker', 'T', 'T08' for Tinker et al. (2008)
         - 'MICE', 'Crocce', 'C' for Crocce et al. (2010)

        :type mass_fun: string, default = `'ST'`

        :param beta: slope of the smooth-k window (used only if `window==smooth`)
        :type beta: float, default = 2

        :param prop_const: proportional constant of radius to mass (used only if `window==sharp`)
        :type prop_const: float, default = 2.5.

        :param kwargs: Keyword arguments to pass to `'mass_fun'`.

        :return: 2D array containing :math:`\\frac{dn}{dM}` in :math:`h^4 \ \mathrm{Mpc}^{-3} \ M_\odot^{-1}`
        """
        # Set number of redshifts
        pk=np.atleast_2d(pk)
        # Check dimensions (only if MICE or Tinker are asked)
        if mass_fun in ['Tinker', 'T', 'T08','MICE', 'Crocce', 'C']:
            assert len(np.atleast_1d(z))==len(pk), "Redshifts are not of the same length as power spectra"
        # Check mass values
        if logM.min()<2.1: raise ValueError("Minimum logM value must be > 2.1, found %.1f" %logM.min())
        if logM.max()>17.9: raise ValueError("Maximum logM value must be < 17.9, found %.1f" %logM.max())

        # CDM density today
        rho = self.rho_crit(0.)*self.Omega_cb
        # masses
        Mtmp     = self.M[1:-1]
        logM_tmp = np.log10(Mtmp)
        # sigma^2
        sigma2 = self.mass_variance(logM_tmp,k,pk,'cb',window,prop_const=prop_const,beta=beta)
        sigma  = sigma2**.5
        # log-derivative
        log_der = []
        for iz in range(len(pk)):
            s2_interp  = si.interp1d(logM_tmp, sigma2[iz], 'cubic',fill_value='extrapolate',bounds_error=False)
            derivative = sm.derivative(s2_interp, logM_tmp, dx = 1e-3, n = 1, order = 3) # d(sigma^2)/dlog10 M ---> factor of log10(e)
            log_der.append(derivative*(-1.)/2./sigma2[iz]*np.log10(np.e))                # Factor of 1/2 because of sigma^2
        log_der = np.array(log_der)

        # Choose according the mass function
        if mass_fun in ['Sheth-Tormen','ST','ShethTormen']:
            f_nu = self.ShethTormen_mass_function(sigma = sigma, **kwargs)
        elif mass_fun in ['Despali', 'D']:
            f_nu = self.Despali_mass_function(sigma = sigma, **kwargs)
        elif mass_fun in ['Tinker', 'T', 'T08']:
            f_nu = self.Tinker_mass_function(sigma = sigma, z = z, **kwargs)
        elif mass_fun in ['MICE', 'Crocce', 'C']:
            f_nu = self.MICE_mass_function(sigma = sigma, z = z)
        elif mass_fun in ['Press-Schechter', 'PS', 'PressSchechter']:
            f_nu = self.PressSchechter_mass_function(sigma = sigma)
        else:
            raise NameError("Unknown mass function, use 'Sheth-Tormen','ST','ShethTormen' / 'MICE', 'Crocce', 'C' / 'Press-Schechter', 'PS', 'PressSchechter' / 'Tinker', 'T', 'T08'")    

        # Halo mass function
        hmf_base = rho/Mtmp**2.*log_der*f_nu
        # Interpolation and evaluation
        hmf = np.array([si.interp1d(logM_tmp, hmf_base[iz], 'cubic',fill_value='extrapolate',bounds_error=False)(logM) for iz in range(len(pk))])
        return hmf

    #-------------------------------------------------------------------------------
    # VOID SIZE FUNCTION EXCURSION SET
    #-------------------------------------------------------------------------------
    def F_BBKS(self, x):
        num1 = (x**3.-3.*x)/2.*(ss.erf(x*np.sqrt(5./2.)) + ss.erf(x*np.sqrt(5./8.)))
        num2 = np.sqrt(2./(5.*const.PI))*(31.*x**2./4. + 8./5.)*np.exp(-5.*x**2./8.)
        num3 = np.sqrt(2./(5.*const.PI))*(x**2./2. - 8./5.)*np.exp(-5.*x**2./2.)
        return (num1 + num2 + num3)

    def Gauss(self, x, mean, var):
        return np.exp(-(x-mean)**2./(2.*var))/np.sqrt(2.*const.PI*var)

    def G_n_BBKS(self, n, gamma_p, nu):
        var  = 1.-np.array(gamma_p)**2.
        mean = np.array(gamma_p*nu)
        G    = np.array(list(map(lambda m, v: sint.quad(lambda x: x**n*self.F_BBKS(x)*self.Gauss(x,m,v), 0., np.inf)[0], mean, var)))
        # To avoid problems with integration, substitute high mass approximation for nu>>1 (nu>10)
        indices = np.where(nu>10.)
        G[indices] = gamma_p[indices]*nu[indices]*((nu[indices]**3.-3*nu[indices])*gamma_p[indices]**3.)
        return G

    def void_size_function(self, R, z, k, pk, delta_v = None, a = 1., p = 0.):
        """
        This routine returns the void size function, i.e. the number of voids per
        unit volume per unit (Lagrangian) radius, according ot the Excursion Set of Troughs theory.
        It returns two 2D arrays containing the Lagrangian radii as function of redshift and the void size 
        function in units of :math:`(h/\mathrm{Mpc})^4`.

        :param R: (Eulerian) radii of voids, in :math:`\mathrm{Mpc}/h`.
        :type R: array

        :param z: Redshifts.
        :type z: array

        :param k: Scales of power spectrum in units of :math:`h/\mathrm{Mpc}`.
        :type k: array

        :param pk: Power spectrum in redshifts and scales in units of :math:`(\mathrm{Mpc}/h)^3`.
        :type pk: 2D array, first dimension must match ``len(z)``

        :param delta_v: Critical underdensity in linear theory. If None, it is substituted by -1.76.
        :type delta_v: float, default = None

        :param a: Sheth-Tormen-like parameter
        :type a: float

        :param p: Sheth-Tormen-like parameter
        :type p: float

        Returns
        -------

        RL: 2D array
            Lagrangian radii corresponding, at each redshift, to the comoving ones in input.

        dndR: 2D array
            Containing :math:`\\frac{dn}{dR}` in :math:`h^4 \ \mathrm{Mpc}^{-4}`
        """
        if delta_v == None: delta_v = -1.76
        # Set number of redshifts
        pk=np.atleast_2d(pk)
        # Check dimensions
        assert len(np.atleast_1d(z))==len(pk), "Redshifts are not of the same length as power spectra"
        nz = len(pk)
        nR = len(np.atleast_1d(R))

        # Set minimum/maximum radii and masses
        Rmin,Rmax = 0.01, 200. # Mpc/h
        Mmin,Mmax = self.mass_in_radius(Rmin),self.mass_in_radius(Rmax)

        # Temporary radii and masses
        Rtmp = self.radius_of_mass(self.M)
        Mtmp = self.M[np.where((Rtmp>Rmin) & (Rtmp<Rmax))]
        Rtmp = Rtmp  [np.where((Rtmp>Rmin) & (Rtmp<Rmax))]
        logMtmp = np.log10(Mtmp)

        # sigma_j^2
        s0 = self.mass_variance_multipoles(logM=logMtmp,k=k,pk=pk,j=0,smooth=True ,window='th')
        s1 = self.mass_variance_multipoles(logM=logMtmp,k=k,pk=pk,j=1,smooth=True ,window='th')
        s2 = self.mass_variance_multipoles(logM=logMtmp,k=k,pk=pk,j=2,smooth=True ,window='th')

        # Useful quantities
        gamma_p = s1/np.sqrt(s0*s2) # gamma parameter
        R_star  = np.sqrt(3.*s1/s2) # R_* parameter
        dv      = np.abs(delta_v)   # Use -1.76!!!!
        nu      = dv/s0**.5         # Peak height
        RLtmp   = np.outer(self.lagrange_to_euler(z = z, delta_v = delta_v),Rtmp)
        RL      = np.outer(self.lagrange_to_euler(z = z, delta_v = delta_v),R)

        # Excursion Set Troughs
        G1   = np.array([self.G_n_BBKS(1, gamma_p[iz], nu[iz]) for iz in range(nz)])
        f_ST = self.ShethTormen_mass_function(s0**.5,delta_th=dv,a=a,p=p)/(2.*nu)
        f_nu = self.volume_of_radius(Rtmp, 'th')/(2.*np.pi*R_star**2.)**(3./2.)*(f_ST)*G1/(gamma_p*nu)

        # VSF
        dndR = np.zeros((nz,nR))
        loge = np.log10(np.e)
        for iz in range(nz):
            s0_int   = si.interp1d(logMtmp, s0[iz],'cubic',bounds_error=False,fill_value='extrapolate')
            log_der  = sm.derivative(s0_int, logMtmp, dx = 1e-3, n = 1, order = 3)
            dnu_dr   = -3./2.*nu[iz]/Rtmp*loge/s0[iz]*log_der
            V        = self.volume_of_radius(Rtmp, 'th')
            dndR_tmp = f_nu[iz]/V*dnu_dr
            dndR[iz] = si.interp1d(RLtmp[iz],dndR_tmp,'cubic')(RL[iz])
        return RL,dndR

    #-------------------------------------------------------------------------------
    # VOID SIZE FUNCTION SPHERICAL EVOLUTION
    #-------------------------------------------------------------------------------
    def f_ln_sigma(self, sigma, delta_c = None, delta_v = None, max_index = 200):
        if max_index<200: raise ValueError("max_index for sum must be at least 200 for convergence")
        dc   = self.delta_sc if delta_c is None else delta_c
        dv   = np.abs(self.delta_v) if delta_c is None else delta_v
        D    = dv/(dc+dv)
        x    = D/dv*sigma
        jpi  = np.array([j*np.pi for j in range(max_index)])
        X, JPI = np.meshgrid(x,jpi,indexing='ij')
        return 2.*np.sum(np.exp(-(JPI*X)**2./2.)*JPI*X**2.*np.sin(JPI*D),axis=1)

    def linear_underdensity_collapse_voids(self,Delta_NL,z):
        assert Delta_NL < 0., "Non-linear underdensity for collapsed voids must be lower than 0"
        assert Delta_NL > -1., "Non-linear underdensity for collapsed voids must be larger than -1"
        D1 = self.D_1(z)
        return ((1.+Delta_NL)**(-1/self.delta_sc)-1.)*self.delta_sc/D1

    def void_size_function_new(self, R, z, k, pk, model, Delta_NL, delta_c = None, **kwargs):
        """
        This routine returns the void size function, i.e. the number of voids per
        unit volume per unit radius, following three different recipes which can all be
        found listed in Jennings, Li, Hu (2013).
        
        :param R: (Eulerian) radii of voids, in :math:`\mathrm{Mpc}/h`.
        :type R: array

        :param z: Redshifts.
        :type z: array

        :param k: Scales of power spectrum in units of :math:`h/\mathrm{Mpc}`.
        :type k: array

        :param pk: Power spectrum in redshifts and scales in units of :math:`(\mathrm{Mpc}/h)^3`.
        :type pk: 2D array, first dimension must match ``len(z)``

        :param model: Model to use, choose among 'linear', 'SvdW', 'Vdn'
        :type model: string

        :param Delta_NL: Critical (non-linear) underdensity for collapse of voids.
        :type Delta_NL: float between 0 and -1

        :param delta_c: Critical overdensity for collapse. If ``None`` the standard value 1.686 is used
        :type delta_c: float, default None

        :param kwargs: keyword arguments


        Returns
        -------

        R: 2D array
            Lagrangian radii corresponding, at each redshift, to the comoving ones in input.

        VSF: 2D array
            Containing :math:`\\frac{dn}{d\ln R}` in :math:`h^3 \ \mathrm{Mpc}^{-3}`
        """
        # Checks
        z           = np.atleast_1d(z)
        assert model in ['linear','SvdW','Vdn'], "Model for VSF not recognized"
        # Fixed parameters
        window      = 'th'
        delta_v     = np.abs(self.linear_underdensity_collapse_voids(Delta_NL,z))
        if delta_c is None: delta_c = self.delta_sc
        ratio_radii = 1. if model == 'linear' else (1+Delta_NL)**(-1/3)
        # Masses and radii
        logM_tmp    = np.log10(self.M)
        R_tmp       = self.radius_of_mass(self.M,'cb',window)*ratio_radii
        # Mass variance
        sigma       = self.mass_variance(logM_tmp,k,pk,'cb',window)**0.5
        # Universal function
        flns        = np.array([self.f_ln_sigma(sigma[iv], delta_c, delta_v[iv], **kwargs) for iv in range(len(delta_v))])
        # Derivative of sigma
        deriv = np.zeros_like(sigma)
        for iz in range(len(pk)):
            sig_interp = si.interp1d(np.log(R_tmp),np.log(1./sigma[iz]),'cubic',fill_value='extrapolate',bounds_error=False)
            deriv[iz]  = sm.derivative(sig_interp,np.log(R_tmp),dx=1e-3,n=1,order=3)
        # Void size function
        if model == 'Vdn':
            Volume_tmp = 4./3.*np.pi*(R_tmp)**3.
        else:
            Volume_tmp = 4./3.*np.pi*(R_tmp/ratio_radii)**3.
        VSF_tmp = flns/Volume_tmp*deriv
        # Interpolate
        VSF = np.array([si.interp1d(R_tmp,VSF_tmp[iz],'cubic')(R) for iz in range(len(z))])
        return R,VSF


    #-------------------------------------------------------------------------------
    # FREE STREAMING
    #-------------------------------------------------------------------------------
    def y_fs(self, k):
        """
        Quantity related to free-streaming scale.

        :param k: Scales of power spectrum in units of :math:`h/\mathrm{Mpc}`.
        :type k: array

        :return: array
        """
        theta = self.T_cmb/2.7
        chi   = k*theta**2./(self.Omega_m)    # k in h/Mpc (it is right! Don't worry)
        f_nu  = np.sum(np.atleast_1d(self.f_nu))
        f_cb  = self.f_cb
        
        y_fs  = 17.2*f_nu*(1.+0.488*f_nu**(-7./6.))*(self.massive_nu*chi/f_nu)**2.
        
        return y_fs

    #-------------------------------------------------------------------------------
    # FREE STREAMING SCALE
    #-------------------------------------------------------------------------------
    def k_FS(self, z):
        """
        Free-streaming scale in :math:`h/\mathrm{Mpc}`.

        :param z: Redshifts.
        :type z: array

        :return: array
        """
        E = self.H_massive(z)/self.H0
        return 0.82*np.sum(np.atleast_1d(self.M_nu))*E/(1.+z)**2. #h/Mpc

    #-------------------------------------------------------------------------------
    # GROWTH FACTOR LCDM: 
    #-------------------------------------------------------------------------------
    def D_1(self, z):
        """
        Matter growth factor for a LCDM cosmology (i.e. scale-independent) at a
        given redshift, normalized to 1 today.

        :param z: Redshifts.
        :type z: array

        :return: array
        """
        nz = len(np.atleast_1d(z))
        d1 = np.zeros(nz)
        if nz == 1:
            z = [z]
        for i in xrange(nz):
            LCDM, _  = sint.quad(lambda x: (1+x)*(self.H0/self.H_massive(x))**3., z[i], np.inf)
            d1[i] = LCDM*self.H_massive(z[i])/self.H0
        LCDM0, _ = sint.quad(lambda x: (1+x)*(self.H0/self.H_massive(x))**3., 0., np.inf)
        d1 *= 1./LCDM0
        return d1

    #-------------------------------------------------------------------------------
    # GROWTH FACTOR CDM+BARYONS:
    #-------------------------------------------------------------------------------
    def growth_cb(self, k, z):
        """
        Non normalized scale-dependent growth factor for cdm+baryons.
        See :func:`colibri.cosmology.cosmo.D_cb()` for further information
        """
        LCDM = self.D_1(z)

        # Same of LCDM if no massive neutrinos
        if np.sum(np.atleast_1d(self.M_nu)) == 0.:
            LCDM = np.array([LCDM for i in xrange(len(np.atleast_1d(k)))])
            return np.transpose(LCDM)
        else:
            K, Z = np.meshgrid(k,z)
            f_cb = self.f_cb
            f_nu = np.sum(np.atleast_1d(self.f_nu))
            
            # Normalize at z initial
            LCDM = np.transpose([LCDM for i in xrange(len(np.atleast_1d(k)))])/self.D_1(self.z_d())
            
            # exponent
            p_cb = 1./4.*(5.-np.sqrt(1.+24.*f_cb))

            # Growth rate for TOTAL MATTER (cdm+b+nu) for nuLCDM Universe (approx!)
            growth_cb = (1. + (LCDM/(1. + self.y_fs(K)))**0.7)**(p_cb/0.7)*LCDM**(1.-p_cb)

            return growth_cb

    def D_cb(self, k, z):
        """
        Cold dark matter + baryon scale-dependent growth factor at a given redshift,
        normalized to 1 today.

        :param k: Scales in units of :math:`h/\mathrm{Mpc}`.
        :type k: array

        :param z: Redshifts.
        :type z: array

        :return: 2D array of shape ``(len(z), len(k))``
        """
        return self.growth_cb(k, z)/self.growth_cb(k, 0.)

    #-------------------------------------------------------------------------------
    # GROWTH FACTOR nuLCDM
    #-------------------------------------------------------------------------------
    def growth_cbnu(self, k, z):
        """
        Unnormalized scale-dependent growth factor for matter.
        See :func:`colibri.cosmology.cosmo.D_cb()` for further information
        """
        LCDM = self.D_1(z)
        
        # Same of LCDM if no massive neutrinos
        if np.sum(self.M_nu) == 0.:
            LCDM = np.array([LCDM for i in xrange(len(np.atleast_1d(k)))])
            return np.transpose(LCDM)
        else:
            K, Z = np.meshgrid(k,z)
            f_cb = self.f_cb
            f_nu = np.sum(np.atleast_1d(self.f_nu))

            # Normalize at z initial
            LCDM = np.transpose([LCDM for i in xrange(len(np.atleast_1d(k)))])/self.D_1(self.z_d())

            # exponent
            p_cb = 1./4.*(5.-np.sqrt(1.+24.*f_cb))

            # Growth rate for TOTAL MATTER (cdm+b+nu) for nuLCDM Universe (approx!)
            growth_cbnu = (f_cb**(0.7/p_cb) + (LCDM/(1. + self.y_fs(K)))**0.7)**(p_cb/0.7)*LCDM**(1.-p_cb)

            return growth_cbnu

    def D_cbnu(self, k, z):
        """
        Total matter (i.e. cold dark matter + baryon + neutrino) scale-dependent growth factor
        at a given redshift, normalized to 1 today.

        :param k: Scales in units of :math:`h/\mathrm{Mpc}`.
        :type k: array

        :param z: Redshifts.
        :type z: array

        :return: 2D array of shape ``(len(z), len(k))``
        """
        return self.growth_cbnu(k, z)/self.growth_cbnu(k, 0.)

    #-----------------------------------------------------------------------------------------
    # MASS OF A PARTICLE IN N-BODY SIMULATIONS
    #-----------------------------------------------------------------------------------------
    def M_p(self, L, N, kind = 'cb'):
        """
        Mass of a single particle (in :math:`M_\odot/h`) in a simulation box, given the length L of the box
        itself (in :math:`\mathrm{Mpc}/h`) and the number of particles N per side.

        :param L: Boxsize in :math:`\mathrm{Mpc}/h`.
        :type L: array

        :param N: Number of particles per side.
        :type N: array

        :param kind:

         - 'cb' : cold dark matter + baryons
         - 'cdm': cold dark matter
         - 'b'  : baryons
         - 'nu' : neutrinos
         - 'tot': total matter
        :type kind: string, default = `'cb'`

        :return: 2D array of shape ``(len(N), len(L))``
        """
        
        L = np.array(L)
        N = np.array(N)
        L_over_N = np.outer(L,1./N)

        if   kind == 'cdm': omega = self.Omega_cdm
        elif kind == 'cb':  omega = self.Omega_cb
        elif kind == 'nu':  omega = self.Omega_nu
        elif kind == 'b':   omega = self.Omega_b
        else:               raise NameError("unknown kind of particle, use 'cb', 'cdm', 'b', 'nu'")

        return L_over_N**3.*omega*self.rho_crit(0.)

    #-----------------------------------------------------------------------------------------
    # BARYON FEEDBACK
    #-----------------------------------------------------------------------------------------
    def feedback_suppression(self, k, z, log_Mc, eta_b, z_c):
        """
        Suppression of the matter power spectrum according to the Baryon Correction Model
        (Schneider et al., 2015).

        :param k: Scales in units of :math:`h/\mathrm{Mpc}`.
        :type k: array

        :param z: Redshifts.
        :type z: array

        :param log_Mc: Feedback mass: all halos below the mass of 10.**log_Mc are stripped of their gas.
        :type log_Mc: float>12.1

        :param eta_b: Ratio between the thermal velocity of the gas and the escape velocity from the halo.
        :type eta_b: float

        :param z_c: Scale redshift of feedback.
        :type z_c: float


        :return: 2D array of shape ``(len(z), len(k))``
        """
        K,Z = np.meshgrid(k,z)

        # Model is valid only for eta_b > 0
        if eta_b <= 0.: raise ValueError("eta_b must be grater than 0.")

        # Stellar component
        ks = 55.
        stellar = 1. + (K/ks)**2.
        
        # Baryon suppression
        B0 = 0.105*log_Mc - 1.27
        assert B0>0., "log_Mc must be grater than 12.096"
        B = B0*1./(1.+(Z/z_c)**2.5)

        k_g = 0.7*((1.-B)**4.)*eta_b**(-1.6)
        scale_ratio = K/k_g

        suppression = B/(1.+scale_ratio**3.)+(1.-B)

        return suppression*stellar

    #-------------------------------------------------------------------------------
    # WDM suppression
    #-------------------------------------------------------------------------------
    def WDM_suppression(self, k, z, M_wdm, nonlinear = False):
        """
        Suppression of the matter power spectrum due to (thermal) warm dark matter. In the linear
        case, the formula by https://arxiv.org/pdf/astro-ph/0501562.pdf is followed;
        otherwise the formula by https://arxiv.org/pdf/1107.4094.pdf is used.
        The linear formula is an approximation strictly valid only at :math:`k < 5-10 \ h/\mathrm{Mpc}`.
        The nonlinear formula has an accuracy of 2% level at :math:`z < 3` and for masses larger than 0.5 keV.

        .. warning::

         This function returns the total suppression in power. To obtain the suppression in the transfer function, take the square root of the output.

        :param k: Scales in units of :math:`h/\mathrm{Mpc}`.
        :type k: array

        :param z: Redshifts.
        :type z: array

        :param M_wdm: Mass of the warm dark matter particle in keV.
        :type M_wdm: float

        :param nonlinear: Whether to return non-linear transfer function.
        :type nonlinear: boolean, default = False

        :return: 2D array of shape ``(len(z), len(k))``
        """
        K,Z = np.meshgrid(k,z)
        if not nonlinear:
            alpha_linear = 0.049*M_wdm**(-1.11)*(self.Omega_cdm/0.25)**0.11*(self.h/0.7)**1.22 # Mpc/h
            nu           = 1.12
            return (1.+(alpha_linear*K)**(2.*nu))**(-10./nu)

        else:
            nu, l, s = 3., 0.6, 0.4
            alpha    = 0.0476*(1./M_wdm)**1.85*((1.+Z)/2.)**1.3 # Mpc/h
            return (1.+(alpha*K)**(nu*l))**(-s/nu)

    #-------------------------------------------------------------------------------
    # DDM suppression
    #-------------------------------------------------------------------------------
    def decaying_dark_matter_suppression(self, k, z, tau, f_ddm):
        """
        Suppression of the matter power spectrum due to decaying dark matter (DDM), according to Hubert et al., 2021. It predicts the correct shape at up to :math:`k>10 h/\mathrm{Mpc}` and :math:`z<2.35`.

        .. warning::

         This function returns the total suppression in power. To obtain the suppression in the transfer function, take the square root of the output.

        :param k: Scales in units of :math:`h/\mathrm{Mpc}`.
        :type k: array

        :param z: Redshifts.
        :type z: array

        :param tau: Half-life time of the particle in Gyr
        :type tau: float

        :param f_ddm: fraction of DDM.
        :type f_ddm: float between 0 and 1

        :return: 2D array of shape ``(len(z), len(k))``
        """
        K,Z = np.meshgrid(k*self.h,z)
        a = 0.7208+2.027/tau+3.0310/(1+1.1*Z)-0.180
        b = 0.0120+2.786/tau+0.6699/(1+1.1*Z)-0.090
        p = 1.0450+1.225/tau+0.2207/(1+1.1*Z)-0.099
        q = 0.9922+1.735/tau+0.2154/(1+1.1*Z)-0.056
        u,v,w = self.omega_b/0.0216,self.h/0.6776,self.omega_m/0.14116
        alpha = (5.323-1.4644*u-1.391*v)+(-2.055+1.329*u+0.8672*v)*w+(0.2682-0.3509*u)*w**2
        beta  = 0.9260 + (0.05735-0.02690*v)*w + (-0.01373+0.006713*v)*w**2
        gamma = (9.553-0.7860*v)+(0.4884+0.1754*v)*w+(-0.2512+0.07558*v)*w**2
        eps_lin    = alpha/tau**beta*(1+0.105*Z)**(-gamma)
        eps_nonlin = eps_lin*(1.+a*K**p)/(1.+b*K**q)*f_ddm
        return 1.-eps_nonlin

    #-------------------------------------------------------------------------------
    # f(R) enhancement
    #-------------------------------------------------------------------------------
    def fR_correction(self, k, z, f_R0, nonlinear = True):
        """
        Enhancement of the matter power spectrum due to f(R) gravity. The formula used is from Winther et al. (2019)

        .. warning::

         This function returns the total suppression in power. To obtain the suppression in the transfer function, take the square root of the output.

        :param k: Scales in units of :math:`h/\mathrm{Mpc}`.
        :type k: array

        :param z: Redshifts.
        :type z: array

        :param f_R0: modified gravity amplitude
        :type f_R0: float

        :param nonlinear: whether to return the linear or nonlinear enhancement
        :type nonlinear: boolean, default = True

        :return: 2D array of shape ``(len(z), len(k))``
        """
        # k,z arrays
        Z,K      = np.meshgrid(z,k,indexing='ij')
        a        = 1./(1.+Z)

        # Non-linear enhancement
        if nonlinear:
            # Low values of f(R) and relative table
            fR0_low    = 5e-6
            param_low  = [ 0.768779  , -0.405375   ,  0.0075176,  0.0288574 , -0.0638224 , -0.401206  , 
                           0.369507  ,  0.109392   , -0.342089 ,  0.226376  , -0.107105  ,  0.0484649 ,
                          -0.024377  , -0.051962   , -0.0351849,  0.147194  ,  0.061761  , -0.131382  ,
                           0.00759035, -0.00101884 ,  0.0118011, -0.0296267 ,  0.025968  ,  0.076885  ,
                           0.0312734 ,  0.0293253  , -0.0141899,  0.109011  ,  0.0818948 , -0.0568241 ,
                           0.120272  ,  0.0249235  , -0.0298492,  0.0354401 , -0.262769  ,  0.230278  ,
                          -0.139116  , -0.132313   ,  0.13132  , -0.0565551 , -0.0338864 ,  0.0712653 ,
                           0.20246   , -0.116113   ,  0.102453 ,  0.0632254 ,  0.0694305 ,  0.00296431,
                           0.0522931 ,  0.0780708  , -0.0977045]
            # Medium values of f(R) and relative table
            fR0_mid    = 1e-5
            param_mid  = [ 0.936496   , -0.545832  ,  0.634804 , -0.0290649 , -0.0954373 , -0.342491  ,
                           0.491066   ,  0.297816  , -0.287142 , -0.0399919 ,  0.3037    ,  0.360959  ,
                           0.000615209, -0.00941931, -0.0181341,  0.376297  ,  0.486358  ,  0.0349385 ,
                           0.240066   ,  0.188202  ,  0.665834 ,  0.0122249 , -0.0343399 , -0.0520361 ,
                           0.261006   ,  0.525633  ,  0.266255 ,  0.393546  ,  0.29088   , -0.411491  ,
                           0.776609   ,  0.470777  , -0.681923 , -0.079589  , -0.282388  ,  0.53954   ,
                          -0.0930797  ,  0.0783781 ,  0.194957 ,  0.270378  ,  0.370288  ,  0.194857  ,
                           0.318637   ,  0.0457011 ,  0.139237 ,  0.033403  ,  0.0762982 , -0.0001047 , 
                          -0.00275824 ,  0.0461644 ,  0.189897 ]

            # High values of f(R) and relative table
            fR0_high   = 5e-5
            param_high = [ 0.572477   ,  0.254686  ,  1.21637  ,  0.00046274, -0.0901242 , -0.355849  ,
                           2.31154    ,  2.29822   , -0.483186 ,  0.4988    ,  0.36089   ,  0.0703424 ,
                           0.0257389  ,  0.0168936 , -0.030697 , -0.206992  ,  0.266084  ,  0.603357  ,
                           0.574264   , -0.30799   ,  0.831644 , -0.0093644 ,  0.00221153,  0.0076829 ,
                          -0.650381   ,  0.0179215 ,  0.927038 ,  0.77903   ,  0.919643  , -0.936328  ,
                           1.26756    ,  1.44477   , -1.44129  ,  0.219594  ,  0.353883  ,  1.02533   ,
                          -0.251705   ,  0.124875  ,  0.345995 , -0.146438  ,  0.0200251 ,  0.0892343 ,
                           0.284755   , -0.158286  ,  0.541178 , -0.0471913 ,  0.139772  , -0.134888  ,
                           0.0959162  ,  0.368186  , -0.157828 ]

            # r \propto log(f_R0)
            r_low  = np.log(f_R0/fR0_low)
            r_mid  = np.log(f_R0/fR0_mid)
            r_high = np.log(f_R0/fR0_high)

            # Find ratios
            ratio_low  = self.ratio_by_param(r_low , a, K, param_low )  # 1e-7 < fR0 < 5e-6
            ratio_mid  = self.ratio_by_param(r_mid , a, K, param_mid )  # 5e-6 < fR0 < 5e-5
            ratio_high = self.ratio_by_param(r_high, a, K, param_high)  # 1e-5 < fR0 < 1e-4

            # Return
            if   f_R0>5e-5:
                enhancement = ratio_high
            elif f_R0<5e-6:
                enhancement = ratio_low
            elif f_R0>1e-5:
                enhancement = ratio_mid + (ratio_high - ratio_mid) * (f_R0 - 1e-5)/(5e-5 - 1e-5)
            else: 
                enhancement = ratio_low + (ratio_mid  - ratio_low) * (f_R0 - 5e-6)/(1e-5 - 5e-6)

        # Linear enhancement
        else:
            r   = np.log(f_R0/1e-5)
            K  *= np.sqrt(f_R0/1e-5)
            b_Z =  3.10000+ 2.34466*(a-1.)- 1.86362*(a-1.)**2.
            c_Z = 34.49510+28.86370*(a-1.)-13.13020*(a-1.)**2.
            d_Z =  0.14654- 0.01000*(a-1.)- 0.14944*(a-1.)**2.
            e_Z =  1.62807+ 0.71291*(a-1.)- 1.41003*(a-1.)**2.
            enhancement = 1. + (b_Z*K)**2./(1.+c_Z*K**2.) + d_Z*np.abs(np.log(K)*K/(K-1.))*np.arctan(e_Z*K)

        return enhancement

    def ratio_by_param(self,r,a,k,param):

        aminusone  = a-1.
        aminusone2 = aminusone**2.
        r2         = r**2.

        b0 = (param[ 0]) + (param[ 9])*r + (param[18])*r2 
        b1 = (param[ 1]) + (param[10])*r + (param[19])*r2
        b2 = (param[ 2]) + (param[11])*r + (param[20])*r2
        c0 = (param[ 3]) + (param[12])*r + (param[21])*r2 
        c1 = (param[ 4]) + (param[13])*r + (param[22])*r2
        c2 = (param[ 5]) + (param[14])*r + (param[23])*r2
        d0 = (param[ 6]) + (param[15])*r + (param[24])*r2 
        d1 = (param[ 7]) + (param[16])*r + (param[25])*r2
        d2 = (param[ 8]) + (param[17])*r + (param[26])*r2
        e0 = (1.0      ) + (param[27])*r + (param[30])*r2
        e1 = (0.0      ) + (param[28])*r + (param[31])*r2
        e2 = (0.0      ) + (param[29])*r + (param[32])*r2
        f0 = (param[33]) + (param[36])*r + (param[39])*r2 
        f1 = (param[34]) + (param[37])*r + (param[40])*r2
        f2 = (param[35]) + (param[38])*r + (param[41])*r2
        g0 = (param[42]) + (param[45])*r + (param[48])*r2 
        g1 = (param[43]) + (param[46])*r + (param[49])*r2
        g2 = (param[44]) + (param[47])*r + (param[50])*r2
      
        b = b0 + b1*aminusone + b2*aminusone2
        c = c0 + c1*aminusone + c2*aminusone2
        d = d0 + d1*aminusone + d2*aminusone2
        e = e0 + e1*aminusone + e2*aminusone2
        f = f0 + f1*aminusone + f2*aminusone2
        g = g0 + g1*aminusone + g2*aminusone2

        return 1.+b*(1.+c*k)/(1.+e*k)*np.abs(np.arctan(d*k))**(1.+f+g*k)


    #-------------------------------------------------------------------------------
    # CAMB_Pk
    #-------------------------------------------------------------------------------
    def camb_Pk(self,
                z = 0.,
                k = np.logspace(-4., 2., 1001),
                nonlinear = False,
                halofit = 'mead2015',
                var_1 = 'tot',
                var_2 = 'tot',
                share_delta_neff = True,
                **kwargs
                ):
        """
        This routine uses the CAMB Boltzmann solver to return power spectra for the chosen cosmology.
        Depending on the value of 'nonlinear', the power spectrum is linear or non-linear; the 'halofit'
        argument chooses the non-linear model.

        :param z: Redshifts.
        :type z: array, default = 0

        :param k: Scales in units of :math:`h/\mathrm{Mpc}`.
        :type k: array, default = ``np.logspace(-4., 2., 1001)``

        :param nonlinear: Whether to return non-linear power spectra.
        :type nonlinear: boolean, default = False

        :type halofit: string, default = 'mead'
        :param halofit: Which version of Halofit to use. See CAMB documentation for further info.

        :param var_1: Density field for the first component of the power spectrum.
        :type var_1: string, default = 'tot'

        :param var_2: Density field for the second component of the power spectrum.

         - `'tot'`   : total matter 
         - `'cdm'`   : cold dark matter
         - `'b'`     : baryons
         - `'nu'`    : neutrinos
         - `'cb'`    : cold dark matter + baryons
         - `'rad'`   : radiation
         - `'v_cdm'` : cdm velocity
         - `'v_b'`   : baryon velocity
         - `'Phi'`   : Weyl potential
        :type var_2: string, default = `'tot'`


        :param kwargs: Keyword arguments to be passed to ``camb.set_params``. See CAMB documentation for further info: https://camb.readthedocs.io/en/latest/

        Returns
        -------

        k: array
            Scales in :math:`h/\mathrm{Mpc}`. Basically the same 'k' of the input.

        pk: 2D array of shape ``(len(z), len(k))``
            Power spectrum in units of :math:`(\mathrm{Mpc}/h)^3`.
        """
        # Neutrino part
        #num_nu_massless – (float64) Effective number of massless neutrinos
        #num_nu_massive – (integer) Total physical (integer) number of massive neutrino species
        #nu_mass_eigenstates – (integer) Number of non-degenerate mass eigenstates
        #nu_mass_degeneracies – (float64 array) Degeneracy of each distinct eigenstate
        #nu_mass_fractions – (float64 array) Mass fraction in each distinct eigenstate
        #nu_mass_numbers – (integer array) Number of physical neutrinos per distinct eigenstate
        nu_mass_eigen   = len(np.unique([mm for mm in self.M_nu[np.where(self.M_nu!=0.)]])) if np.any(self.M_nu!=0.) else 0
        nu_mass_numbers = [list(self.M_nu[np.where(self.M_nu!=0.)]).count(x) for x in set(list(self.M_nu[np.where(self.M_nu!=0.)]))]
        nu_mass_numbers = sorted(nu_mass_numbers,reverse=True) if np.any(self.M_nu!=0.) else [0]
        # Set parameters
        cambparams = {
                      'num_nu_massive': self.massive_nu,
                      'num_nu_massless': self.massless_nu,
                      'nu_mass_eigenstates': nu_mass_eigen, 
                      'nu_mass_numbers': nu_mass_numbers,
                      'nnu': self.N_eff,
                      'omnuh2': np.sum(self.omega_nu[np.where(self.M_nu!=0.)]),
                      'ombh2': self.omega_b,
                      'omch2': self.omega_cdm+np.sum(self.omega_nu[np.where(self.M_nu==0.)]),
                      'omk': self.Omega_K,
                      'H0': 100.*self.h,
                      'As': self.As,
                      'ns': self.ns,
                      'w': self.w0,
                      'wa': self.wa,
                      'TCMB': self.T_cmb,
                      'tau': self.tau,
                      'share_delta_neff':True,
                      'dark_energy_model':'DarkEnergyPPF'}
        # kwargs
        for key, value in kwargs.items():
            if not key in cambparams: cambparams[key] = value
        params = camb.set_params(**cambparams)

        # Redshifts
        z  = np.atleast_1d(z)
        nz = len(z)

        # Possible components to use
        components = {'tot'  : 'delta_tot',
                      'cdm'  : 'delta_cdm',
                      'b'    : 'delta_baryon',
                      'nu'   : 'delta_nu',
                      'cb'   : 'delta_nonu',
                      'rad'  : 'delta_photon',
                      'v_cdm': 'v_newtonian_cdm',
                      'v_b'  : 'v_newtonian_baryon',
                      'Phi'  : 'Weyl'}            # Weyl: (phi+psi)/2 is proportional to lensing potential

        # Number of points (according to logint)
        logint  = 100
        npoints = int(logint*np.log10(k.max()/k.min()))
        dlogk   = 2.*np.log10(k.max()/k.min())/npoints

        # Halofit version
        if nonlinear == True:
            params.NonLinearModel.set_params(halofit_version=halofit)
            params.NonLinear = camb.model.NonLinear_both

        # Computing spectra
        params.set_matter_power(redshifts=z,kmax=k.max()*10**dlogk,silent=True,k_per_logint=0,accurate_massive_neutrino_transfers=True)
        results = camb.get_results(params)
        kh, z, pkh = results.get_matter_power_spectrum(minkh = k.min()*10.**-dlogk, maxkh = k.max()*10**dlogk, npoints = npoints, var1 = components[var_1], var2 = components[var_2])

        # Interpolation to the required scales k's
        # I use UnivariateSpline because it makes good extrapolation
        pk = np.zeros((nz,len(np.atleast_1d(k))))
        for iz in range(nz):
            lnpower = si.InterpolatedUnivariateSpline(kh, np.log(pkh[iz]), k=3, ext=0, check_finite=False)
            pk[iz] = np.exp(lnpower(k))

        return k, pk


    #-------------------------------------------------------------------------------
    # CAMB_XPk
    #-------------------------------------------------------------------------------
    def camb_XPk(self,
            z = 0.,
            k = np.logspace(-4., 2., 1001),
            nonlinear = False,
            halofit = 'mead2015',
            var_1 = ['tot'],
            var_2 = ['tot'],
            share_delta_neff = True,
            **kwargs
            ):
        """
        The function CAMB_XPk() runs the Python wrapper of CAMB and returns auto- and 
        cross-spectra for all the quantities specified in 'var_1' and 'var_2'.
        Depending on the value of 'nonlinear', the power spectrum is linear or non-linear.
        It returns scales in units of :math:`h/\mathrm{Mpc}` and power spectra in units of (:math:`(\mathrm{Mpc}/h)^3`.

        :param z: Redshifts.
        :type z: array, default = 0

        :param k: Scales in units of :math:`h/\mathrm{Mpc}`.
        :type k: array, default = ``np.logspace(-4., 2., 1001)``

        :param nonlinear: Whether to return non-linear power spectra.
        :type nonlinear: boolean, default = False

        :type halofit: string, default = 'mead'
        :param halofit: Which version of Halofit to use. See CAMB documentation for further info.

        :param var_1: Density field for the first component of the power spectrum.
        :type var_1: list of strings, default = ['tot']

        :param var_2: Density field for the second component of the power spectrum.

         - `'tot'`   : total matter 
         - `'cdm'`   : cold dark matter
         - `'b'`     : baryons
         - `'nu'`    : neutrinos
         - `'cb'`    : cold dark matter + baryons
         - `'rad'`   : radiation
         - `'v_cdm'` : cdm velocity
         - `'v_b'`   : baryon velocity
         - `'Phi'`   : Weyl potential
        :type var_2: list of strings, default = ['tot']


        :param kwargs: Keyword arguments to be passed to ``camb.set_params``. See CAMB documentation for further info: https://camb.readthedocs.io/en/latest/

        Returns
        -------

        k: array
            Scales in :math:`h/\mathrm{Mpc}`. Basically the same 'k' of the input.

        pk: dictionary
            Keys are given by `'var_1-var_2'`. Each of these is a 2D array of shape ``(len(z), len(k))`` containing :math:`P_\mathrm{var_1-var_2}(z,k)` in units of :math:`(\mathrm{Mpc}/h)^3`.

        """

        # Neutrino part
        nu_mass_eigen   = len(np.unique([mm for mm in self.M_nu[np.where(self.M_nu!=0.)]])) if np.any(self.M_nu!=0.) else 0
        nu_mass_numbers = [list(self.M_nu[np.where(self.M_nu!=0.)]).count(x) for x in set(list(self.M_nu[np.where(self.M_nu!=0.)]))]
        nu_mass_numbers = sorted(nu_mass_numbers,reverse=True) if np.any(self.M_nu!=0.) else [0]
        # Set parameters
        cambparams = {
                      'num_nu_massive': self.massive_nu,
                      'num_nu_massless': self.massless_nu,
                      'nu_mass_eigenstates': nu_mass_eigen, 
                      'nu_mass_numbers': nu_mass_numbers,
                      'nnu': self.N_eff,
                      'omnuh2': np.sum(self.omega_nu[np.where(self.M_nu!=0.)]),
                      'ombh2': self.omega_b,
                      'omch2': self.omega_cdm+np.sum(self.omega_nu[np.where(self.M_nu==0.)]),
                      'omk': self.Omega_K,
                      'H0': 100.*self.h,
                      'As': self.As,
                      'ns': self.ns,
                      'w': self.w0,
                      'wa': self.wa,
                      'TCMB': self.T_cmb,
                      'tau': self.tau,
                      'share_delta_neff':True,
                      'dark_energy_model':'DarkEnergyPPF'}
        # kwargs
        for key, value in kwargs.items():
            if not key in cambparams: cambparams[key] = value
        params = camb.set_params(**cambparams)

        # Redshifts and scales
        k  = np.atleast_1d(k)
        nk = len(k)
        z  = np.atleast_1d(z)
        nz = len(z)
        if nz > 3: spline = 'cubic'
        else:      spline = 'linear'

        # Possible components to use
        components = {'tot'  : 'delta_tot',
                      'cdm'  : 'delta_cdm',
                      'b'    : 'delta_baryon',
                      'nu'   : 'delta_nu',
                      'cb'   : 'delta_nonu',
                      'rad'  : 'delta_photon',
                      'v_cdm': 'v_newtonian_cdm',
                      'v_b'  : 'v_newtonian_baryon',
                      'Phi'  : 'Weyl'}

        # Number of points (according to logint)
        npoints = int(100*np.log10(k.max()/k.min()))
        dlogk   = 2.*np.log10(k.max()/k.min())/npoints

        # Halofit version
        if nonlinear == True:
            #camb.nonlinear.Halofit(halofit_version = halofit)
            params.NonLinearModel.set_params(halofit_version=halofit)
            params.NonLinear = camb.model.NonLinear_both

        # Initialize power spectrum as a dictionary and compute it
        pk = {}
        params.set_matter_power(redshifts = z, kmax = k.max()*10**dlogk, silent = True,accurate_massive_neutrino_transfers=True)
        results = camb.get_results(params)

        # Fill the power spectrum array
        for c1 in var_1:
            for c2 in var_2:
                string = c1+'-'+c2
                kh, zz, ppkk = results.get_matter_power_spectrum(minkh = k.min()*10.**-dlogk,
                                                                 maxkh = k.max()*10**dlogk,
                                                                 npoints = npoints,
                                                                 var1 = components[c1],
                                                                 var2 = components[c2])

                pk[string] = np.zeros((nz,nk))
                for iz in range(nz):
                    lnpower = si.InterpolatedUnivariateSpline(kh,np.log(ppkk[iz]),k=3,ext=0, check_finite=False)
                    pk[string][iz] = np.exp(lnpower(k))
                
                #if nz != 1:
                #    power = si.interp2d(kh, zz, ppkk, kind = spline)
                #    pk[string] = power(k, z)
                #    pk[string] = np.nan_to_num(pk[string])
                #else:
                #    power = si.interp1d(kh, ppkk, kind = spline)
                #    pk[string] = power(k)
                #    pk[string] = np.nan_to_num(pk[string])

        return k, pk


    #-------------------------------------------------------------------------------
    # CLASS_Pk
    #-------------------------------------------------------------------------------
    def class_Pk(self,
                 z = 0.,
                 k = np.logspace(-4., 2., 1001),
                 nonlinear = False,
                 halofit = 'halofit',
                 **kwargs):
        """
        This routine uses CLASS to return power spectra for the chosen cosmology. Depending
        on the value of 'nonlinear', the power spectrum is linear or non-linear.

        :param z: Redshifts.
        :type z: array, default = 0

        :param k: Scales in units of :math:`h/\mathrm{Mpc}`.
        :type k: array, default = ``np.logspace(-4., 2., 1001)``

        :param nonlinear: Whether to return non-linear power spectra.
        :type nonlinear: boolean, default = False

        :param kwargs: Keyword arguments of ``classy.pyx`` (see the file `explanatory.ini` in Class or https://github.com/lesgourg/class_public/blob/master/python/classy.pyx)

        Returns
        -------

        k: array
            Scales in :math:`h/\mathrm{Mpc}`. Basically the same 'k' of the input.

        pk: 2D array of shape ``(len(z), len(k))``
            Power spectrum in units of :math:`(\mathrm{Mpc}/h)^3`.
        """

        # Set halofit for non-linear computation
        if nonlinear == True:
                halofit = halofit
        else: halofit = 'none'

        # Setting lengths
        nk = len(np.atleast_1d(k))
        nz = len(np.atleast_1d(z))
        if nz == 1.: z = np.array([z])
        else:        z = np.array(z)
        kmax = max(k[-1],500.)
        zmax = max(z[-1],101.)
        tau = self.tau
        params = {
            'output': 'mPk dTk',
            'n_s': self.ns, 
            'h': self.h,
            'omega_b': self.Omega_b*self.h**2.,
            'omega_cdm': self.Omega_cdm*self.h**2.,
            'Omega_k': self.Omega_K,
            'tau_reio': self.tau,
            'T_cmb': self.T_cmb,
            'P_k_max_h/Mpc': kmax,
            'z_max_pk': zmax,
            'non_linear': halofit}
        # Set initial conditions
        if self.sigma_8 is not None:
            params['sigma8'] = self.sigma_8            
        else:
            params['A_s'] = self.As            
        # Set dark energy
        if self.w0 != -1. or self.wa != 0.:
            params['Omega_fld'] = self.Omega_lambda
            params['w0_fld'] = self.w0
            params['wa_fld'] = self.wa

        # Set neutrino masses
        # If all masses are zero, then no m_ncdm
        params['N_ur']   = self.massless_nu
        params['N_ncdm'] = self.massive_nu
        if self.massive_nu != 0:
            params['m_ncdm'] = ', '.join(str(x) for x in self.M_nu[self.M_nu != 0.])

        # Add the keyword arguments
        for key, value in kwargs.items():
            if not key in params: params[key] = value
            else: raise KeyError("Parameter %s already exists in the dictionary, impossible to substitute it." %key)

        # Compute
        cosmo = Class()
        cosmo.set(params)
        cosmo.compute()

        # I change to k/h since CLASS uses k in units of 1/Mpc
        k *= self.h

        # Storing Pk
        pk = np.zeros((nz,nk))
        for i in xrange(nk):
            for j in xrange(nz):
                pk[j,i] = cosmo.pk(k[i],z[j])*self.h**3.
        # Re-switching to (Mpc/h) units
        k /= self.h

        cosmo.struct_cleanup()
        cosmo.empty()

        return k, pk

    #-------------------------------------------------------------------------------
    # CLASS_XPk
    #-------------------------------------------------------------------------------
    def class_XPk(self,
                  z = 0.,
                  k = np.logspace(-4., 2., 1001),
                  nonlinear = False,
                  halofit = 'halofit',
                  var_1 = ['tot'],
                  var_2 = ['tot'],
                  **kwargs
                  ):
        """
        The function class_XPk() runs the Python wrapper of CLASS and returns auto- and 
        cross-spectra for all the quantities specified in 'var_1' and 'var_2'.
        Depending on the value of 'nonlinear', the power spectrum is linear or non-linear.
        Halofit by Takahashi is empoyed.

        :param z: Redshifts.
        :type z: array, default = 0

        :param k: Scales in units of :math:`h/\mathrm{Mpc}`.
        :type k: array, default = ``np.logspace(-4., 2., 1001)``

        :param nonlinear: Whether to return non-linear power spectra.
        :type nonlinear: boolean, default = False

        :param var_1: Density field for the first component of the power spectrum.
        :type var_1: list of strings, default = ['tot']

        :param var_2: Density field for the second component of the power spectrum.

         - `'tot'`   : total matter 
         - `'cdm'`   : cold dark matter
         - `'b'`     : baryons
         - `'nu'`    : massive neutrinos
         - `'ur'`    : massless neutrinos
         - `'cb'`    : cold dark matter + baryons
         - `'rad'`   : radiation
         - `'Phi'`   : Weyl potential
         - `'Psi'`   : Weyl potential
        :type var_2: list of strings, default = ['tot']


        :param kwargs: Keyword arguments of ``classy.pyx`` (see the file `explanatory.ini` in Class or https://github.com/lesgourg/class_public/blob/master/python/classy.pyx)

        Returns
        -------

        k: array
            Scales in :math:`h/\mathrm{Mpc}`. Basically the same 'k' of the input.

        pk: dictionary
            Keys are given by `'var_1-var_2'`. Each of these is a 2D array of shape ``(len(z), len(k))`` containing :math:`P_\mathrm{var_1-var_2}(z,k)` in units of :math:`(\mathrm{Mpc}/h)^3`.
        """
        components = {'tot': 'd_tot',
                      'cdm': 'd_cdm',
                      'b'  : 'd_b',
                      'nu' : 'd_nu',
                      'ur' : 'd_ur',
                      'cb' : 'd_cb',
                      'rad': 'd_g',
                      'Phi': 'phi',
                      'Psi': 'psi'}


        # Set halofit for non-linear computation
        if nonlinear == True:
                halofit = halofit
        else: halofit = 'none'

        # Setting lengths
        nk = len(np.atleast_1d(k))
        nz = len(np.atleast_1d(z))
        if nz == 1.: z = np.array([z])
        else:        z = np.array(z)
        kmax = max(k[-1],500.)
        zmax = max(z[-1],101.)
        tau = self.tau
        params = {
            'output': 'mPk dTk',
            'n_s': self.ns, 
            'h': self.h,
            'omega_b': self.Omega_b*self.h**2.,
            'omega_cdm': self.Omega_cdm*self.h**2.,
            'Omega_k': self.Omega_K,
            'tau_reio': self.tau,
            'T_cmb': self.T_cmb,
            'P_k_max_h/Mpc': kmax,
            'z_max_pk': zmax,
            'non_linear': halofit}
        # Set initial conditions
        if self.sigma_8 is not None:
            params['sigma8'] = self.sigma_8            
        else:
            params['A_s'] = self.As        
        # Set dark energy
        if self.w0 != -1. or self.wa != 0.:
            params['Omega_fld'] = self.Omega_lambda
            params['w0_fld'] = self.w0
            params['wa_fld'] = self.wa

        # Set neutrino masses
        # If all masses are zero, then no m_ncdm
        #if np.count_nonzero(np.atleast_1d(self.M_nu))!=len(np.atleast_1d(self.M_nu)):
        params['N_ur']   = self.massless_nu
        params['N_ncdm'] = self.massive_nu
        if self.massive_nu != 0:
            params['m_ncdm'] = ', '.join(str(x) for x in self.M_nu[self.M_nu != 0.])

        # Add the keyword arguments
        for key, value in kwargs.items():
            if not key in params: params[key] = value
            else: raise KeyError("Parameter %s already exists in the dictionary, impossible to substitute it." %key)

        # Compute
        cosmo = Class()
        cosmo.set(params)
        cosmo.compute()

        # Setting lengths
        nk = len(np.atleast_1d(k))
        nz = len(np.atleast_1d(z))
        n1 = len(var_1)
        n2 = len(var_2)
        if nz == 1.: z = np.array([z])
        else:        z = np.array(z)

        # I change to k/h since CLASS uses k in units of 1/Mpc
        k *= self.h
        
        # Storing Pk
        pk_m = np.zeros((nz,nk))
        for i in xrange(nk):
            for j in xrange(nz):
                pk_m[j,i] = cosmo.pk(k[i],z[j])*self.h**3.

        # Re-switching to (Mpc/h) units
        k /= self.h

        # Get transfer functions and rescale the power spectrum
        #pk = np.zeros((n1,n2,nz,nk))
        pk = {}
        # Loop over variables
        for c1 in var_1:
            for c2 in var_2:
                string = c1+'-'+c2
                pk[string] = np.zeros((len(np.atleast_1d(z)),len(k)))
                # Loop over redshifts
                for ind_z in xrange(len(np.atleast_1d(z))):
                    # Get transfer functions at z
                    TF         = cosmo.get_transfer(z = z[ind_z])
                    k_T        = TF['k (h/Mpc)']
                    T_m        = TF['d_tot']
                    T_cdm      = TF['d_cdm']
                    T_b        = TF['d_b']
                    T_phi      = TF['phi']
                    T_psi      = TF['psi']
                    T_rad      = TF['d_g']
                    T_ur       = TF['d_ur']
                    TF['d_cb'] = (self.Omega_cdm * T_cdm + self.Omega_b * T_b)/self.Omega_cb
                    T_nu       = np.array([el[1] for el in list(filter(lambda item: item[0].startswith('d_ncdm'), TF.items()))])
                    try:                 TF['d_nu'] = np.sum(self.M_nu[self.M_nu!=0.]*T_nu.T, axis = 1)/np.sum(self.M_nu)
                    except np.AxisError: TF['d_nu'] = np.zeros(len(k_T))
                    # Interpolation of matter T(k)
                    tm_int   = si.interp1d(k_T, T_m, kind = 'cubic', fill_value = "extrapolate")
                    transf_m = tm_int(k)            
                    # Interpolate them to required k
                    t1_int = si.interp1d(k_T, TF[components[c1]], kind = 'cubic', fill_value = "extrapolate")
                    t2_int = si.interp1d(k_T, TF[components[c2]], kind = 'cubic', fill_value = "extrapolate")
                    transf_1 = t1_int(k)
                    transf_2 = t2_int(k)
                    # Rescaling
                    pk[string][ind_z] = pk_m[ind_z]*transf_1*transf_2/transf_m**2.
        cosmo.struct_cleanup()
        cosmo.empty()
        
        return k, pk

    #-------------------------------------------------------------------------------
    # EISENSTEIN-HU_Pk
    #-------------------------------------------------------------------------------
    def EisensteinHu_Pk(self,
        z = 0.,
        k = np.logspace(-4., 2., 1001),
        sigma_8 = 0.83):
        """
        It returns the linear power spectrum in the Eisenstein & Hu approximation.

        .. warning::

         This function does not allow to use non-flat FRW universes! ``Omega_K`` will be therefore
         set to 0 and its value devolved to ``Omega_m``.

        .. warning::

         This function does not reproduce massive neutrinos! Therefore ``Omega_nu`` will be set to 0 and its value transferred to ``Omega_m``.

        .. warning::

         This function only uses :math:`w_{de} = -1`.

        .. warning::

         This code uses :math:`\sigma_8` as a normalization. :math:`A_s` will not have any impact.

        :param z: Redshifts.
        :type z: array, default = 0

        :param k: Scales in units of :math:`h/\mathrm{Mpc}`.
        :type k: array, default = ``np.logspace(-4., 2., 1001)``

        :param sigma_8: RMS mass fluctuation in spheres of 8 :math:`\mathrm{Mpc}/h` of radius.
        :type sigma_8: float, default = 0.83

        Returns
        -------

        k: array
            Scales in :math:`h/\mathrm{Mpc}`. Basically the same 'k' of the input.

        pk: 2D array of shape ``(len(z), len(k))``
            Power spectrum in units of :math:`(\mathrm{Mpc}/h)^3`.

        """

        om_m  = self.Omega_m
        om_b  = self.Omega_b
        n_tld = self.ns - 1.
        h     = self.h
        theta = self.T_cmb/2.7
        
        if np.sum(np.atleast_1d(self.M_nu)) != 0.:
            warnings.warn("EisensteinHu_Pk is not able to reproduce massive neutrinos as it uses the Eisenstein & Hu approximation (1998) for the linear power spectrum. The Omega_nu parameter will be transferred to Omega_lambda such that Omega_lambda -> (Omega_lambda + Omega_nu)")
            om_m -= np.sum(self.Omega_nu)
        if self.w0 != -1. or self.wa != 0.:
            warnings.warn("nw_Pk is not able to reproduce non-static dark energy with w0 != -1. The dark enerdy parameters will be set to w0 = -1, wa = 0")
        if self.Omega_K != 0.:
            warnings.warn("EisensteinHu_Pk is not able to reproduce non-flat FRW metric! The Omega_K parameter will be transferred to Omega_lambda such that Omega_lambda -> (Omega_lambda + Omega_K)")
            om_m -= self.Omega_K

        rk = k*h
        e = np.exp(1.)

        # Recombination and equality
        thet = 2.728/2.7
        b1   = 0.313*(om_m*h*h)**(-0.419)*(1+0.607*(om_m*h*h)**0.674)
        b2   = 0.238*(om_m*h*h)**0.223
        zd   = 1291.*(1+b1*(om_b*h*h)**b2)*(om_m*h*h)**0.251/(1.+0.659*(om_m*h*h)**0.828)
        ze   = 2.50e4*om_m*h*h/thet**4.
        rd   = 31500.*om_b*h*h/thet**4./zd
        re   = 31500.*om_b*h*h/thet**4./ze
        rke  = 7.46e-2*om_m*h*h/thet**2.
        s    = (2./3./rke)*np.sqrt(6./re)*np.log((np.sqrt(1.+rd)+np.sqrt(rd+re))/(1+np.sqrt(re)))
        rks  = 1.6*( (om_b*h*h)**0.52 ) * ( (om_m*h*h)**0.73 ) * (1.+(10.4*om_m*h*h)**(-0.95))
        q    = rk/13.41/rke
        y    = (1.+ze)/(1.+zd)
        g    = y*(-6.*np.sqrt(1+y)+(2.+3.*y)*np.log((np.sqrt(1.+y)+1.)/(np.sqrt(1.+y)-1.)))

        # Master function
        ab   = g*2.07*rke*s/(1.+rd)**(0.75)
        a1   = (46.9*om_m*h*h)**0.670*(1+(32.1*om_m*h*h)**(-0.532))
        a2   = (12.0*om_m*h*h)**0.424*(1+(45.0*om_m*h*h)**(-0.582))
        ac   = (a1**(-om_b/om_m)) * (a2**(-(om_b/om_m)**3.))
        B1   = 0.944/(1+(458.*om_m*h*h)**(-0.708))
        B2   = (0.395*om_m*h*h)**(-0.0266)
        bc   = 1./(1.+B1*((1.-om_b/om_m)**B2-1.))

        # CDM transfer function
        f    = 1./(1.+(rk*s/5.4)**4.)
        c1   = 14.2 + 386./(1.+69.9*q**1.08)
        c2   = 14.2/ac + 386./(1.+69.9*q**1.08)
        tc   = f*np.log(e+1.8*bc*q)/(np.log(e+1.8*bc*q)+c1*q*q) +(1.-f)*np.log(e+1.8*bc*q)/(np.log(e+1.8*bc*q)+c2*q*q)
        
        # Baryon transfer function
        bb   = 0.5+(om_b/om_m) + (3.-2.*om_b/om_m)*np.sqrt((17.2*om_m*h*h)**2.+1.)
        bn   = 8.41*(om_m*h*h)**0.435
        ss   = s/(1.+(bn/rk/s)**3.)**(1./3.)
        tb   = np.log(e+1.8*q)/(np.log(e+1.8*q)+c1*q*q)/(1+(rk*s/5.2)**2.)
        fac  = np.exp(-(rk/rks)**1.4)
        tb   = (tb+ab*fac/(1.+(bb/rk/s)**3.))*np.sin(rk*ss)/rk/ss

        # Total transfer function
        T = (om_b/om_m)*tb+(1-om_b/om_m)*tc

        # Power spectrum and normalization
        #delta_H = 1.94e-5*om_m**(-0.785-0.05*np.log(om_m))*np.exp(-0.95*n_tld-0.169*n_tld**2.)
        #power_tmp = delta_H**2.*(const.c*rk/self.H0)**(3.+self.ns)/rk**3.*(2.*const.PI**2.)*T**2.
        power_tmp = k**self.ns*(2.*const.PI**2.)*T**2.
        norm = sigma_8/self.compute_sigma_8(k = k, pk = power_tmp)
        power_tmp *= norm**(2.)
        
        # Different redshifts
        nz = len(np.atleast_1d(z))
        if nz == 1:
            z = np.array([z])
        nk = len(np.atleast_1d(k))
        Pk = np.zeros((nz,nk))
        for i in xrange(nz):
            Pk[i] = power_tmp*(self.D_1(z[i])/self.D_1(0.))**2.

        return k, Pk

    #-------------------------------------------------------------------------------
    # REMOVE_BAO
    #-------------------------------------------------------------------------------
    def remove_bao(self, k_in, pk_in, k_low = 2.8e-2, k_high = 4.5e-1):
        """
        This routine removes the BAOs from the input power spectrum and returns
        the no-wiggle power spectrum in :math:`(\mathrm{Mpc}/h)^3`.
        Originally written by Mario Ballardini (you can find it in `the montepython repository <https://github.com/brinckmann/montepython_public/blob/master/montepython/likelihood_class.py>`_ .
        )

        :param k_in: Scales in units of :math:`h/\mathrm{Mpc}`.
        :type k_in: array

        :param pk_in: Power spectrum in units of :math:`(\mathrm{Mpc}/h)^3`.
        :type pk_in: array

        :param k_low: Lowest scale to spline in :math:`h/\mathrm{Mpc}`.
        :type k_low: float, default = 2.8e-2

        :param k_high: Highest scale to spline in :math:`h/\mathrm{Mpc}`.
        :type k_high: float, default = 4.5e-1

        :return: array, power spectrum without BAO.
        """

        # This k range has to contain the BAO features:
        k_ref = [k_low, k_high]

        # Get interpolating function for input P(k) in log-log space:
        _interp_pk = si.interp1d(np.log(k_in), np.log(pk_in),
                                                kind='quadratic', bounds_error=False )
        interp_pk = lambda x: np.exp(_interp_pk(np.log(x)))

        # Spline all (log-log) points outside k_ref range:
        idxs = np.where(np.logical_or(k_in <= k_ref[0], k_in >= k_ref[1]))
        _pk_smooth = si.UnivariateSpline( np.log(k_in[idxs]),
                                                         np.log(pk_in[idxs]), k = 3, s = 0 )
        pk_smooth = lambda x: np.exp(_pk_smooth(np.log(x)))

        # Find second derivative of each spline:
        fwiggle = si.UnivariateSpline(k_in, pk_in / pk_smooth(k_in), k = 3, s = 0)
        derivs  = np.array([fwiggle.derivatives(_k) for _k in k_in]).T
        d2      = si.UnivariateSpline(k_in, derivs[2], k = 3, s = 1.0)

        # Find maxima and minima of the gradient (zeros of 2nd deriv.), then put a
        # low-order spline through zeros to subtract smooth trend from wiggles fn.
        wzeros = d2.roots()
        wzeros = wzeros[np.where(np.logical_and(wzeros >= k_ref[0], wzeros <= k_ref[1]))]
        wzeros = np.concatenate((wzeros, [k_ref[1],]))
        try:
            wtrend = si.UnivariateSpline(wzeros, fwiggle(wzeros), k = 3, s = None, ext = 'extrapolate')
        except:
            wtrend = si.UnivariateSpline(k_in, fwiggle(k_in), k = 3, s = None, ext = 'extrapolate')

        # Construct smooth no-BAO:
        idxs = np.where(np.logical_and(k_in > k_ref[0], k_in < k_ref[1]))
        pk_nobao = pk_smooth(k_in)
        pk_nobao[idxs] *= wtrend(k_in[idxs])

        # Construct interpolating functions:
        ipk = si.interp1d( k_in, pk_nobao, kind='cubic',
                           bounds_error=False, fill_value=0. )

        pk_nobao = ipk(k_in)

        return pk_nobao

    #-----------------------------------------------------------------------------------------
    # SIGMA 8
    #-----------------------------------------------------------------------------------------
    def compute_sigma_8(self, k = [], pk = [], var = 'tot'):
        """
        This routine computes :math:`sigma_8`.

        :param k: Scales in units of :math:`h/\mathrm{Mpc}`.
        :type k: array, default = []

        :param pk: Power spectrum in units of :math:`(\mathrm{Mpc}/h)^3`.
        :type pk: array, default = []

        :param var: component with respect to which to compute the variance.

            - 'tot'   : total matter 
            - 'cdm'   : cold dark matter
            - 'b'     : baryons
            - 'nu'    : neutrinos
            - 'cb'    : cold dark matter + baryons
            - 'rad'   : radiation
            - 'v_cdm' : cdm velocity
            - 'v_b'   : baryon velocity
            - 'Phi'   : Weyl potential
        :type var: string, default = 'tot'

        :return: float
        """

        # Smoothing radius of 8 Mpc/h
        R = 8.
        # Assertions on scales, lengths and intervals
        assert np.max(k)>=np.pi/R*2., "k_max too low to obtain a convergent result. Use k_max >= pi/4 h/Mpc to obtain covergent results."
        assert np.min(k)<=0.001,      "k_min too high to obtain a convergent result. Use k_min <= 0.001 h/Mpc to obtain covergent results."
        assert len(k)>=100,           "size of 'k' too low to obtain a convergent result. Use at least 100 points."
        # Make 'k' 2D
        k2d = np.atleast_2d(k)
        # Top-hat window function
        W_kR = self.TopHat_window(k2d*R)
        # Integration in log-bins
        integral = sint.simps(k2d**3.*pk/(2.*const.PI**2.)*W_kR**2.,x=np.log(k),axis=1)
        return integral**.5

    #-----------------------------------------------------------------------------------------
    # NORMALIZE P(k)
    #-----------------------------------------------------------------------------------------
    def normalize_Pk(self, k, pk, new_sigma8):
        """
        This routine normalizes the input power spectrum to the required :math:`sigma_8`.

        :param k: Scales in units of :math:`h/\mathrm{Mpc}`.
        :type k: array, default = []

        :param pk: Power spectrum in units of :math:`(\mathrm{Mpc}/h)^3`.
        :type pk: array, default = []

        :param new_sigma_8: Value to which normalize.
        :type new_sigma8: float

        :return: array of normalized power spectrum in :math:`(\mathrm{Mpc}/h)^3`.
        """
        s8_in = self.compute_sigma_8(k = k, pk = pk)
        return pk*(new_sigma8/s8_in)**2.

    #-------------------------------------------------------------------------------
    # CLASS_Cl
    #-------------------------------------------------------------------------------
    def class_Cl(self,
                 l_max = 3000,
                 lensing = True,
                 do_tensors = True,
                 l_max_tensors = 500,
                 r = 0.07,
                 **kwargs):
        """
        Computation of the CMB angular power spectrum for the chosen cosmology.


        :param l_max: Maximum multipole to compute.
        :type l_max: integer, default = 3000

        :param lensing: Compute lensed components.
        :type lensing: boolean, default = True

        :param do_tensors: Compute tensors components.
        :type do_tensors: boolean, default = True

        :param l_max_tensors: Maximum multipole for computation of tensor components.
        :type l_max_tensors: int, default = 3000

        :param r: Tensor-to-scalar ratio.
        :type r: float, default = 0.07

        :param kwargs: Keyword arguments of Class (see the file `explanatory.ini` in Class for a list of them)

        Returns
        -------

        l: array
            Array of integers that goes from 2 to ``l_max``

        Cl: dictionary
            Contains the CMB angular power spectrum.

            - `'TT'`, `'TE'`, `'EE'`, `'BB'` are the unlensed components
            - `'TT-lensed', `'TE-lensed'`, `'EE-lensed'`, `'BB-lensed'` are the lensed components

        """
        # tCl = transfer (density)
        # pCl = polarization
        # lCl = lensed

        # Setting params
        params = {
            'output': 'tCl, pCl',
            'r': r,
            'YHe': 0.249,
            'l_max_scalars': l_max,
            'A_s': self.As,
            'n_s': self.ns, 
            'h': self.h,
            'omega_b': self.Omega_b*self.h**2.,
            'omega_cdm': self.Omega_cdm*self.h**2.,
            'Omega_k': self.Omega_K,
            'tau_reio': self.tau,
            'T_cmb': self.T_cmb}
        # Set dark energy
        if self.w0 != -1. or self.wa != 0.:
            params['Omega_fld'] = self.Omega_lambda
            params['w0_fld'] = self.w0
            params['wa_fld'] = self.wa

        # Set neutrino masses
        # If all masses are zero, then no m_ncdm
        #if np.count_nonzero(np.atleast_1d(self.M_nu))!=len(np.atleast_1d(self.M_nu)):
        params['N_ur']   = self.massless_nu
        params['N_ncdm'] = self.massive_nu
        if self.massive_nu != 0:
            params['m_ncdm'] = ', '.join(str(x) for x in self.M_nu[self.M_nu != 0.])

        # Setting tensors
        if do_tensors:
            params['modes'] = 's,t'
            params['l_max_tensors'] = l_max_tensors
        else:
            params['modes'] = 's'

        # Setting lensing    
        if lensing:
            params['output'] += ', lCl'
            params['lensing'] = 'yes'

        # Add the keyword arguments
        for key, value in kwargs.items():
            if not key in params: params[key] = value
            else: raise KeyError("Parameter %s already exists in the dictionary, impossible to substitute it." %key)

        # Compute
        cosmo = Class()
        cosmo.set(params)
        cosmo.compute()

        # Access the raw cl
        cl_dict = cosmo.raw_cl(l_max)

        # Create new dictionary
        l  = cl_dict['ell']
        Cl = {}

        # Fill new dictionary
        Cl['TT'] = cl_dict['tt']
        Cl['TE'] = cl_dict['te']
        Cl['EE'] = cl_dict['ee']
        if do_tensors:
            Cl['BB'] = cl_dict['bb']
        if lensing:
            cl_dict_lens = cosmo.lensed_cl(l_max)
            Cl['TT-lensed'] = cl_dict_lens['tt']
            Cl['TE-lensed'] = cl_dict_lens['te']
            Cl['EE-lensed'] = cl_dict_lens['ee']
            if do_tensors:
                Cl['BB-lensed'] = cl_dict_lens['bb']

        return l, Cl


