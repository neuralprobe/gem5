# Import the compiled m5 library and all SimObjects
import m5
from m5.objects import *
from caches import *

# arg options
import argparse

parser = argparse.ArgumentParser(
    description="A simple system with 2-level cache."
)
parser.add_argument(
    "binary",
    default="",
    nargs="?",
    type=str,
    help="Path to the binary to execute.",
)
parser.add_argument(
    "--l1i_size", help=f"L1 instruction cache size. Default: 16kB."
)
parser.add_argument(
    "--l1d_size", help="L1 data cache size. Default: Default: 64kB."
)
parser.add_argument("--l2_size", help="L2 cache size. Default: 256kB.")

options = parser.parse_args()


# system: the parent of all the other objects
system = System()

# Set the clock on the system
# 1. Create a clock domain,
# 2. Set the clock frequency on that domain,
# 3. Specify a voltage domain for this clock domain (default unless you care about power)
system.clk_domain = SrcClockDomain()
system.clk_domain.clock = "1GHz"
system.clk_domain.voltage_domain = VoltageDomain()  # Use default options

# Set memory
# 1. Timing mode
# 2. Set memory range
system.mem_mode = "timing"
system.mem_ranges = [AddrRange("512MB")]

# Create CPU
# The most simple timing-based CPU in gem5 for ...
# 1. X86 ISA: X86TimingSimpleCPU
# 2. RISC-V ISA: RiscvTimingSimpleCPU
# 3. ARM ISA: ArmTimingSimpleCPU
system.cpu = X86TimingSimpleCPU()

# Create the system-wide memory bus
system.membus = SystemXBar()

# L1 Cache & connection
system.cpu.icache = L1ICache(options)
system.cpu.dcache = L1DCache(options)
system.cpu.icache.connectCPU(system.cpu)
system.cpu.dcache.connectCPU(system.cpu)

# L2bus
system.l2bus = L2XBar()

system.cpu.icache.connectBus(system.l2bus)
system.cpu.dcache.connectBus(system.l2bus)

# L2 Cache & connection
system.l2cache = L2Cache(options)
system.l2cache.connectCPUSideBus(system.l2bus)
system.membus = SystemXBar()
system.l2cache.connectMemSideBus(system.membus)

# Connect PIO and interrupt ports
# Functional-only ports!
# <= Requirement of X86 architecture
system.cpu.createInterruptController()
system.cpu.interrupts[
    0
].pio = system.membus.mem_side_ports  # No need for ARM and other ISA
system.cpu.interrupts[
    0
].int_requestor = system.membus.cpu_side_ports  # No need for ARM and other ISA
system.cpu.interrupts[
    0
].int_responder = system.membus.mem_side_ports  # No need for ARM and other ISA

system.system_port = system.membus.cpu_side_ports

# Set memory controller
# Connect to membus
system.mem_ctrl = MemCtrl()
system.mem_ctrl.dram = DDR3_1600_8x8()
system.mem_ctrl.dram.range = system.mem_ranges[0]
system.mem_ctrl.port = system.membus.mem_side_ports

# Process (another SimObject) as the workload of the CPU
# SE: syscall emulation (good for user-only mode)
# FS: full system (good for high fidelity modeling of system or OS interaction like page table walks)
options.binary = "tests/test-progs/hello/bin/x86/linux/hello"
system.workload = SEWorkload.init_compatible(
    options.binary
)  # for gem5 V21 and beyond
process = Process()
process.cmd = [options.binary]
system.cpu.workload = process
system.cpu.createThreads()

# Finally,
# 1. Create Root object
# 2. Instantiate the simulation

root = Root(full_system=False, system=system)
m5.instantiate()

# Kick off the actual simulation!
print("Beginning simulation!")
exit_event = m5.simulate()

# Once simulation finishes,
# Inspect the state of the system.

print(
    "Exiting @ tick {} because {}".format(m5.curTick(), exit_event.getCause())
)

# Same full code in configs/learning_gem5/part1/simple.py

# Now go to run gem5
# In root gem5 directory,
# build/X86/gem5.opt configs/tutorial/part1/two_level.py --l2_size='1MB' --l1d_size='128kB'


# Output
# jonghoon@NXZT:~/Codes/gem5$ build/X86/gem5.opt configs/tutorial/part1/two_level.py --l2_size='1MB' --l1d_size='128kB'
# gem5 Simulator System.  https://www.gem5.org
# gem5 is copyrighted software; use the --copyright option for details.

# gem5 version 23.0.1.0
# gem5 compiled Aug 16 2023 22:04:34
# gem5 started Aug 19 2023 17:48:16
# gem5 executing on NXZT, pid 7724
# command line: build/X86/gem5.opt configs/tutorial/part1/two_level.py --l2_size=1MB --l1d_size=128kB

# Global frequency set at 1000000000000 ticks per second
# warn: No dot file generated. Please install pydot to generate the dot file and pdf.
# src/mem/dram_interface.cc:690: warn: DRAM device capacity (8192 Mbytes) does not match the address range assigned (512 Mbytes)
# src/base/statistics.hh:279: warn: One of the stats is a legacy stat. Legacy stat is a stat that does not belong to any statistics::Group. Legacy stat is deprecated.
# system.remote_gdb: Listening for connections on port 7000
# Beginning simulation!
# src/sim/simulate.cc:194: info: Entering event queue @ 0.  Starting simulation...
# Hello world!
# Exiting @ tick 56435000 because exiting with last active thread context


# The full scripts can be found in the gem5 source at configs/learning_gem5/part1/caches.py and configs/learning_gem5/part1/two_level.py.
