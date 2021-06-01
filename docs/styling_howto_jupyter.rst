=================================================
Datacube-OWS Styling JupyterHub Quick-Start Guide
=================================================

.. contents:: Table of Contents

Introduction
------------

This document assumes you have a working account with a JupyterHub-based ODC installation,
e.g. DEA Sandbox.

Installing Datacube-ows
-----------------------

At the time of writing datacube-ows is not included in the standard DEA Sandbox build.

Simply installing via ``pip install`` in a JupyterHub tab is sufficient, but
will not persist between sessions unless you have already set up a local virtual
environment.

::

     pip install datacube-ows

If you do not already have a local virtual environment set up, check that you have sufficient disk
space available in your home directory (at least 3.5G), using a Jupyter Hub terminal tab:

::

    df -h | awk '/home/{print $6, "has", $4, "of disk space available"}'

If you have sufficient space, you can create a virtual environment using the following commands in the Terminal
tab:

::

    # create new empty env in ~/.envs/odc directory
    EE=odc
    cd $HOME
    mkdir $HOME/.envs
    cd $HOME/.envs
    /usr/bin/python3 -m venv ${EE}

    # transplant modules from default env
    (cd /env/lib; tar c .) | (cd ${EE}/lib; tar x)
    # make sure base libs are up-to-date
    ./${EE}/bin/python3 -m pip install -U pip wheel setuptools

    # Check that modules transplanted ok
    ./${EE}/bin/python3 -m pip list

    # Install new kernel (tell jupyter about it)
    ./${EE}/bin/python3 -m ipykernel install --user --name 'ows' --display-name 'ODC (OWS)'

Now you can simply launch a new terminal tab using the new "ODC (OWS)" environment and install datacube-ows
using ``pip install``, as described above.

Displaying images
-----------------

To display an xarray image in JupyterHub, as returned by the Styling API, the following function is helpful.
Something similar will be included in a future release of the API:

::

    def plot_image(xr_image, x="x", y="y", size=10):
        rgb = xr_image.to_array(dim="color")
        rgb = rgb.transpose(*(rgb.dims[1:] + rgb.dims[:1]))
        rgb = rgb / 255
        rgb.plot.imshow(x=x, y=y, size=size)

