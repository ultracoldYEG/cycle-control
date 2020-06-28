# cycle-control

This is  a python-based tool that is used to parameterize and control hardware which outputs digital, arbitrary waveform, and radio frequency signals. It has the following dependencies:
* PyQt5
* numpy
* matplotlib
* spinapi
* DAQmx
* DAQmx python wrapper

# Creating Procedures
* **Cycles** may be defined which are a list of **instructions** to be output by your selected hardware.
* An **instruction** defines an output for every connected piece of hardware and a length of time for that output to be active.
* A **procedure** is a sequence of cycles, in which a selection of variables may be swept through a range of values upon each iteration of a completed **cycle**. Each iteration is called a **step**.
* This structure lends itself well for conducting experiments where a complex setup is required (like creating a Bose-Einstein Condensate), and a single variable needs to be tweaked each time to see how it changes the system
* In an **instruction**, the output is defined by a mathematical function of time (e.g a sine wave, exponential curve, or simply a constant value). Users are encouraged to add their own functions as desired to the code (see `CycleControl/user_functions.py`)
* The arguments of these functions can be literal numbers, or they can be parameterized via user-defined variables. Variables take on two forms in this software:
	* **Static Variables** are variables where the value does not change throughout the entire procedure. It essentially attaches a label to a numerical value of your choice.
	* **Dynamic Variables** are able to change from one cycle to the next as each step is executed in the procedure. To specify how the dynamic variable changes,  some options are available:
		* **Start value**: the beginning value of the variable upon the first cycle of the procedure
		* **End value**: the value the variable will have upon the last desired cycle of the procedure
		* **Default value**: the value the variable will have if the variable is not enabled, or if the procedure has passed the specified number of steps.
		* **Logarithmic**: a boolean value that specifies whether the variable will change logarithmically or linearly from the start value to the end value
	* Note that the step size of dynamic variables ultimately depend on the number of steps defined for the given procedure. More steps in the procedure will generate smaller step sizes for these types of variables.
* All of the variable types may be edited in the **Variables tab** in the software. Here, the number of steps in the procedure may be specified, as well as a delay between cycles, if desired. Another option called **persistent cycling** is found here. Enabling this will cause the system to continue running cycles indefinitely after the specified number of steps with the default values for all the variables. 
* Anytime the variables are edited, the changes will not be reflected in the output of the hardware until the user clicks on the **Update Globals** button in the upper potion of the screen.
* **Procedures** may be saved and loaded from the **File Management tab** in the program. They are saved into a `.json` format, so they are human readable and editable.

# Currently Supported Functions
 * **Constant**:
   Outputs a constant value. If no function is specified it is assumed to be constant.
   *Usage*: `const(x)` or `x`
 * **Ramp**:
   A linear increase from `a` to `b` over the duration of the instruction
   *Usage*: `ramp(a, b)` 
 * **Sinusoid**:
   A sine wave with amplitude `A`, angular frequency `w`,  and phase `p`.
   *Usage*: `sin(A, w, p)`
 * **Exponential**:
   Creates a curve which exponentially changes from `a` to `b` over the duration of the instruction with a time constant `t`
   *Usage*: `exp(a, b, t)` 

# Hardware Management
* An arbitrary number of boards with arbitrary channels may be added to a setup in the **File Management Tab**. Here, pulseblaster boards may be added which output digital waveforms. Individual channels may be enabled/disabled and labelled if desired. Novatech boards  for RF control may also be added here, and the same feature set applies the individual channels for this board. National Instruments arbitrary waveform generator boards may be added for analog signal control. Individual channels can also be enabled, renamed, as well as limited to a certain output range. 
* Changes to the current hardware setup will be reflected in the **Primary Staging** tab. Disabled channels will not show up, and labels will be displayed where applicable.
* Hardware setups can be saved an loaded from the **File Management Tab**.

# Plotting
An output plotter is provided in the **Plotting Tab**. Here, any channel from any board may be added to the current view to see how the output value changes over the course of an entire cycle. There is a a **cycle number** parameter which may be changed to see how stepping through the procedure affects the output of the plotted channels. 

# Acknowledgements:
* **spinapi:**
  Author: Chris Billington
Home Page: https://bitbucket.org/cbillington/spinapi/
License: BSD
Package Index Owner: cbillington
DOAP record: spinapi-3.1.1.xml

* **DAQmx python wrapper:**
Author: Pierre Cladé
Documentation: PyDAQmx package documentation
Home Page: http://pythonhosted.org/PyDAQmx/
Keywords: DAQmx,National Instrument,Data Acquisition,nidaq,nidaqmx
License: This software can be used under one of the following two licenses: (1) The BSD license. (2) Any other license, as long as it is obtained from the original author.
Package Index Owner: clade
DOAP record: PyDAQmx-1.3.2.xml