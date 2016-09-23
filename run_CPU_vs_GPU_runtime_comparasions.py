import time
import numpy as np
import pysb
import pysb.integrate as integrate
from pysb.bng import generate_equations
from pysb.simulator.cupsoda import set_cupsoda_path, CupSodaSolver

ATOL = 1e-6
RTOL = 1e-6
mxstep = 20000

card = 'gtx-980-ti'
CPU = 'cpu'
GHZ = 'speed'

# mem = 0
# global 0
# shared 1
# sharedconstant 2
mem_dict = {0: 'global', 1: 'shared', 2: 'sharedconstant'}


def main(tspan, model, simulations, vol, name, run, mem):
    set_cupsoda_path("/home/pinojc/git/cupSODA")
    solver = CupSodaSolver(model, tspan, atol=ATOL, rtol=RTOL)
    scipy_solver = pysb.integrate.Solver(model, tspan, rtol=RTOL, atol=ATOL,
                                         integrator='lsoda', )
    output = "model,nsims,tpb,mem,cupsodatime,cupsoda_io_time,pythontime,rtol,atol,mxsteps,t_end,n_steps,vol,card\n"
    scipy_output = "model,nsims,scipytime,rtol,atol,mxsteps,t_end,n_steps,cpu,GHz\n"
    generate_equations(model)
    nominal_values = np.array([p.value for p in model.parameters])
    for num_particles in simulations:

        if run == "cupSODA":
            c_matrix = np.zeros((num_particles, len(nominal_values)))
            c_matrix[:, :] = nominal_values
            y0 = np.zeros((num_particles, len(model.species)))
            for ic in model.initial_conditions:
                for j in range(len(model.species)):
                    if str(ic[0]) == str(model.species[j]):
                        y0[:, j] = ic[1].value
                        break

            tpb = 16
            i = int(np.ceil(1. * num_particles / tpb))
            start_time = time.time()
            solver.run(param_values=c_matrix,
                       y0=y0,
                       gpu=0,
                       max_steps=mxstep,
                       vol=vol,
                       n_blocks=i,
                       # outdir='.',
                       obs_species_only=True,
                       memory_usage=mem_dict[mem])
            end_time = time.time()
            new_line = '%s,%s,%s,%s,%s,%s,%s,%s,%s,' \
                       '%s,%s,%s,%s,%s\n' % (name,
                                             num_particles,
                                             str(tpb),
                                             mem,
                                             solver._cupsoda_time,
                                             solver._total_time,
                                             end_time - start_time,
                                             str(RTOL),
                                             str(ATOL),
                                             len(tspan),
                                             mxstep,
                                             np.max(tspan),
                                             vol,
                                             card)
            output += new_line
            print(new_line)
            print('out==')
            print(solver.concs_observables(squeeze=False)[0][0])
            print(solver.concs_observables(squeeze=False)[0][-1])
            print('==out\n')

        if run == 'scipy':
            start_time = time.time()
            for i in xrange(num_particles):
                scipy_solver.run()
            total_time = time.time() - start_time
            print('sim = %s , time = %s sec' % (num_particles, total_time))
            new_line = '%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,\n' % (name,
                                                             num_particles,
                                                             total_time,
                                                             RTOL,
                                                             ATOL,
                                                             mxstep,
                                                             np.max(tspan),
                                                             len(tspan),
                                                             CPU,
                                                             GHZ,)
            scipy_output += new_line
    if run == 'scipy':
        with open('%s_scipy_timing_%s.csv' % (name, str(mem)), 'w') as f:
            f.write(scipy_output)
    if run == 'cupSODA':
        with open('%s_cupsoda_timing_%s.csv' % (name, str(mem)), 'w') as f:
            f.write(output)


def run_tyson(run, mem):
    from models.tyson_oscillator_in_situ import model
    name = 'tyson'
    tspan = np.linspace(0, 100, 100)
    simulations = [10, 100, 1000, 10000, 100000]
    vol = 1e-19
    main(tspan, model, simulations, vol, name, run, mem)


def run_ras(run, mem):
    from models.ras_camp_pka import model
    name = 'ras'
    tspan = np.linspace(0, 1500, 100)
    simulations = [10, 100, 1000, 10000, 100000]
    vol = 1e-19
    main(tspan, model, simulations, vol, name, run, mem)


def run_earm(run, mem):
    from models.earm_lopez_embedded_flat import model
    name = 'earm'
    tspan = np.linspace(0, 20000, 100)
    simulations = [10, 100, 1000, 10000]
    vol = 1.661e-19
    main(tspan, model, simulations, vol, name, run, mem)


if __name__ == '__main__':
    # Run all the cupsoda timing
    run_tyson('cupSODA', 0)
    run_tyson('cupSODA', 1)
    run_tyson('cupSODA', 2)
    run_earm('cupSODA', 0)
    run_earm('cupSODA', 1)
    run_earm('cupSODA', 2)
    run_ras('cupSODA', 0)
    run_ras('cupSODA', 1)
    run_ras('cupSODA', 2)
    # Run all the scipy timing
    # run_tyson("scipy")
    # run_ras("scipy")
    # run_earm("scipy",0)
