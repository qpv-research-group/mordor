.. Mordor documentation master file, created by sphinx-quickstart on Sat Mar  7 20:33:18 2015. You can adapt this file completely to your liking, but it should at least contain the root `toctree` directive.

Welcome to Mordor's documentation!
==================================

Mordor is a hardware manager and data adquisition software developed at the Quantum Photovoltaics Group (QPV) to simplify the execution of common experiments and the implementation of new ones. It is also designed to be simple to mantain and to expand by any user with some knowledge of Python. The idea is that, if the main developer leaves the group, the software will be easy to maintain and update acording to the group needs and the inevitable upgrades of computers and operative systems.

Currently supported features are:

#. **Spectroscopy measurements**
    Single scan measurements or in batch mode.

    -  Versus voltage or current

#. **IV measurements**
    Single scan measurements versus voltage or current.

For the sake of simplicity, *Mordor* does not control all options of the hardware it can use, just those that:

- are esential to automate the measuring process, such as changing the wavelength of a monochromator or getting the measured data from a spectrometer,
- are too obscure to change directly in the aparatus, as the integration time of a SMU,
- can not be modified otherwise, like changing the grating of a monochromator, which can only be done by means of software.

Of course, nothing prevents future developers to add all the missing options, but that is not the spirit of *Mordor*.

Using *Mordor* is quite straigth forward, so this documentation is more focused on describing how it works internally and how to expand it with new hardware or new experiments.


Contents:
---------

.. toctree::
    :maxdepth: 3

    Experiments
    Devices



Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

