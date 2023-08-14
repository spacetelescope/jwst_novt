JWST NIRSpec Observation Visualization Tool (NOVT)
==================================================

.. image:: https://github.com/spacetelescope/jwst_novt/workflows/CI/badge.svg
    :target: https://github.com/spacetelescope/jwst_novt/actions
    :alt: GitHub Actions CI Status
.. image:: https://codecov.io/gh/spacetelescope/jwst_novt/branch/main/graph/badge.svg
    :target: https://codecov.io/gh/spacetelescope/jwst_novt
    :alt: Coverage Status
.. image:: https://readthedocs.org/projects/jwst_novt/badge/?version=latest
    :target: https://jwst-novt.readthedocs.io/en/latest/?badge=latest
    :alt: Documentation Status
.. image:: http://img.shields.io/badge/powered%20by-AstroPy-orange.svg?style=flat
   :target: http://www.astropy.org
   :alt: Powered by Astropy Badge


The NIRSpec Observation Visualization Tool (NOVT) visualizes projected footprints
for the NIRSpec and NIRCam instruments on the James Webb Space Telescope (JWST).
It is intended to aid in planning NIRCam pre-imaging for NIRSpec MOS observations,
by allowing simultaneous display and configuration of the NIRSpec and NIRCam
fields of view for a given sky position.

Available modules
-----------------

The NOVT package includes tools for calculating footprints and visibility timelines
and tools for interactively configuring and displaying them.  The dependencies for
the interactive tools are much more extensive than the core tools require, so the
package allows installation of the core tools without the optional dependencies
required by the interactive tools.

See the `online documentation <https://jwst-novt.readthedocs.io/en/latest/>`__
for more information on the contents of the software modules.

Core tools: jwst_novt
~~~~~~~~~~~~~~~~~~~~~
The top-level package (`jwst_novt`) contains lightweight interfaces to the
`pysiaf <https://github.com/spacetelescope/pysiaf>`__ and
`jwst_gtvt <https://github.com/spacetelescope/jwst_gtvt>`__
tools to compute aperture projections by target position and
target visibility and position angle by date, respectively. This package may
be installed and used directly to create inputs for preferred visualization
tools (e.g.
`SAO DS9 <https://sites.google.com/cfa.harvard.edu/saoimageds9>`__ or
`Imviz <https://jdaviz.readthedocs.io/en/latest/imviz/index.html>`__).

See the `novt_tools` notebook in the `notebooks` directory of the source
distribution for an example of this usage.

Display and interactive tools: jwst_novt.interact
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
The `jwst_novt.interact` package contains tools to configure, visualize, and interact
with the instrument apertures and visibility timeline in a Jupyter notebook
context. A default application is provided that can be run in a local notebook
server, or as a remote web application.  STScI plans to serves this application for the
public soon.  In the meantime, the default application can be run locally by following the
installation instructions below, then running the command::

    $ novt

See also the `novt_interact` notebook in the `notebooks` directory of the source
distribution for an example of using NOVT tools with the Imviz display tool in
a custom notebook.

See the `NOVT JDox article <https://jwst-docs.stsci.edu/jwst-other-tools/nirspec-observation-visualization-tool-help>`__
for usage information for the web application.

Installation
------------

It is highly recommended that the user install the NOVT package into a virtual
environment.  For example, use conda to create and activate a virtual environment
before following the installation steps::

    $ conda create -n jwst_novt python
    $ conda activate jwst_novt

Core tools only
~~~~~~~~~~~~~~~

To install the top-level package from source via GitHub::

    $ git clone https://github.com/spacetelescope/jwst_novt
    $ pip install -e jwst_novt


To install via pip::

    $ pip install jwst_novt

Either method will also download and install the required software dependencies.

Core tools + display and interactive tools
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To install the display and interactive tools along with the base package from
source via GitHub::

    $ git clone https://github.com/spacetelescope/jwst_novt
    $ pip install -e jwst_novt[interact]


Or via pip::

    $ pip install jwst_novt[interact]

Either method will download and install the additional required software dependencies
for the interact module.

License
-------
See `LICENSE.rst` in the `source distribution <https://github.com/spacetelescope/jwst_novt>`__ for more information.


Contributing
------------
See `CONTRIBUTING.md` in the `source distribution <https://github.com/spacetelescope/jwst_novt>`__ for more information.
