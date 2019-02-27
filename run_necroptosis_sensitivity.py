import numpy as np
from pysb.simulator.scipyode import ScipyOdeSimulator
from pysb.simulator.cupsoda import CupSodaSimulator
from pysb.tools.sensitivity_analysis4 import InitialsSensitivity
from models.necro import model
import logging
from pysb.util import update_param_vals, load_params
from pysb.logging import setup_logger
setup_logger(logging.INFO, file_output='necro_run.log', console_output=True)
import matplotlib
import os
matplotlib.use('Agg')

def run():

    tspan = np.linspace(0, 720, 13)
    observable = 'MLKLa_obs'

    def normalize(trajectories):
        """Rescale a matrix of model trajectories to 0-1"""
        ymin = trajectories.min(0)
        ymax = trajectories.max(0)
        return (trajectories - ymin) / (ymax - ymin)

    # t = np.linspace(0, 720, 13)
    # solver1 = ScipyOdeSimulator(model, tspan=t)

    wtx = np.array([0., 1., 2., 3., 4., 5., 6., 7., 8., 9., 10., 11., 12.])
    wty = np.array([0., 0., 0., 0.10, 0.25, 0.5, 0.75, 1., 1., 1., 1., 1., 1.])
    ydata_norm = wty

    mtx = np.array([0., 1., 2., 3., 4., 5., 6., 7., 8., 9., 10., 11., 12.])
    mty = np.array([0.00000000e+00, 2.25604804e-07, 8.07101135e-04, 6.20809831e-02,
                    1.06088474e+00, 8.21767829e+00, 3.93069650e+01, 1.36335330e+02,
                    3.76498798e+02, 8.77789805e+02, 1.79557808e+03, 3.30512082e+03,
                    5.54847820e+03])
    ysim_norm = normalize(mty)

    def likelihood(ysim_norm):
        # result = solver1.run()
        #
        # ysim_array1 = result.observables['MLKLa_obs'][:]
        #
        # ysim_norm1 = normalize(ysim_array1)

        mlkl_wt = np.array([0.05, 0.05, 0.05, 0.05, 0.05, 0.2, 0.05, 0.05, 0.05, 0.05, 0.05, 0.05, 0.05])

        e1 = np.sum((ydata_norm - ysim_norm) ** 2 / (mlkl_wt))

        return e1

    # values to sample over
    vals = np.linspace(.8, 1.2, 21)
    vol = 1e-19
    directory = 'SensitivityData'
    savename = 'tyson_sensitivity_new'
    integrator_opt = {'rtol': 1e-6, 'atol': 1e-6, 'max_steps': 20000, 'memory_usage': 'global', 'vol': vol}
    integrator_opt_scipy = {'rtol': 1e-6, 'atol': 1e-6, 'mxstep': 20000}

    # integrator_opt = {'rtol': 1e-6, 'atol': 1e-6, 'mxsteps': 20000}
    # integrator_opt_scipy = {'rtol': 1e-6, 'atol': 1e-6, 'mxstep': 20000}


    new_params1 = load_params(os.path.join('Params',
                                          'params_necro_new_uncal.txt'))
    savename = 'local_necro_parameters_1'
    update_param_vals(model, new_params1)

    cupsoda_solver = CupSodaSimulator(model, tspan, verbose=True, gpu=0, integrator_options=integrator_opt)

    scipy_solver = ScipyOdeSimulator(model, tspan=tspan, integrator='lsoda',
                                     integrator_options=integrator_opt_scipy)

    sens = InitialsSensitivity(
            cupsoda_solver,
            #scipy_solver,
            values_to_sample=vals,
            observable=observable,
            objective_function=likelihood, sens_type='initials')

    sens.run(save_name=savename, out_dir=directory)

    sens.create_boxplot_and_heatplot(save_name='necro_sensitivity_set_1_uncal', show=True)
    # sens.create_individual_pairwise_plots(save_name='tyson_pairwise')
    # sens.create_plot_p_h_pprime('tyson_phprime')
    #
    #
    # new_params2 = load_params(os.path.join('Params',
    #                                       'params_necro_new_cal.txt'))
    # savename = 'local_necro_parameters_2'
    # update_param_vals(model, new_params2)
    # # cupsoda_solver = CupSodaSimulator(model, tspan, verbose=False, gpu=0,
    # #                                   #memory_usage='sharedconstant', vol=vol,
    # #                                   integrator_options=integrator_opt)
    # scipy_solver = ScipyOdeSimulator(model, tspan=tspan, integrator='lsoda',
    #                                  integrator_options=integrator_opt_scipy)
    #
    # sens = InitialsSensitivity(scipy_solver,
    #                            values_to_sample=vals,
    #                            observable=observable,
    #                            objective_function=likelihood, sens_type='initials')
    #
    # sens.run(save_name=savename, out_dir=directory)
    # sens.create_boxplot_and_heatplot(save_name='necro_sensitivity_set_2_cal')


if __name__ == '__main__':
    run()
