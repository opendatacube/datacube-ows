=================
OWS Configuration
=================

.. toctree::
   :maxdepth: 2
   :hidden:
   :glob:

   configuration
   cfg_global
   cfg_wms
   cfg_wmts
   cfg_wcs
   cfg_functions
   cfg_masks
   cfg_layers
   cfg_styling
   cfg_component_styles
   cfg_colourramp_styles
   cfg_colourmap_styles
   cfg_hybrid_styles
   cfg_style_api
   cfg_style_api_examples

.. contents:: Table of Contents

.. _introduction:

Introduction
------------

The behaviour of a datacube_ows server instance can be controlled, customised and extended by configuration files.

Datacube OWS configuration files can be written in Python (as a static serialisable python dictionary) or as JSON.
All examples in this documentation will always be presented in Python syntax.  JSON syntax is almost identical, but
note that there are some important differences:

1. JSON string literals must always be delimited with double quotes - so no Python-style single quote strings!
2. JSON boolean literals are all lowercase (``true``, ``false``) and Python boolean literals are title case (e.g.
   ``True``, ``False``)
3. JSON does not allow commas after the last element of lists and objects (dictionaries in Python terms).
4. JSON does not support comments of any kind.

`This general introductory stuff is boring.  Take me straight to the description of the
configuration file. <#general-config-structure>`_

.. _location:

Where is Configuration Read From?
---------------------------------

Configuration is read by default from the ``ows_cfg object`` in ``datacube_ows/ows_cfg.py``
but this can be overridden by setting the ``$DATACUBE_OWS_CFG`` environment variable.

Configuration can be read from a python file, a json file, or a collection of python
and/or json files.

A json file can optionally also be fetched from AWS S3 if access to S3 is configured correctly for datacube_ows
and the environment variable ``$DATACUBE_OWS_CFG_ALLOW_S3`` is set to ``YES``. Please note that this is not
possible for configurations as python file.

.. _DATACUBE_OWS_CFG:

The DATACUBE_OWS_CFG Environment Variable
=========================================

The environment variable ``$DATACUBE_OWS_CFG`` is interpreted as follows (first matching
alternative applies):

1. Has a leading slash, e.g. ``/opt/odc_ows_cfg/odc_ows_cfg_prod.json``

   Config loaded as **json** from absolute file path.

2. Contains a slash, e.g. ``configs/prod.json``

   Config loaded as **json** from relative file path.

3. Begins with an open brace "{", e.g. ``{...}``

   Config loaded directly from the environment variable as **json** (not recommended)

4. Ends in ".json", e.g. ``cfg_prod.json``

   Config loaded from **json** file in working directory.

5. Has a valid ``s3://`` URL and a ``.json`` extension

   The configuration is fetched from AWS S3 in json format.

   N.B. Configuration can only be loaded from S3 if the environment variable ``$DATACUBE_OWS_CFG_ALLOW_S3``
   is set to ``yes``, otherwise a ``ConfigurationException`` will be raised.

6. Contains a dot (.), e.g. ``package.sub_package.module.cfg_object_name``

   Imported as python object (expected to be a dictionary).

   N.B. It is up to you to ensure that the Python file in question is in your Python path and
   that all package directories have a ``__init__.py`` file, etc.

7. Valid python object name, e.g. ``cfg_prod``

   Imported as **python** from named object in ``datacube_ows/ows_cfg.py``

8. Blank or not set

   Default to import ows_cfg object in ``datacube_ows/ows_cfg.py`` as described above.

.. _inclusion:

Inclusion: Breaking Up Config Into Multiple Files
-------------------------------------------------

The root configuration can include configuration content from other Python or JSON files,
allowing cleaner organisation of configuration and facilitating reuse of common configuration
elements across different layers within the one configuration and between different
configurations or deployment environments.

N.B. The examples here illustrate the inclusion directives only, and are not valid Datacube OWS configuration!

If you are simply loading config as a Python object, this can be directly achieved by normal programmatic techniques,
e.g.:

::

  handy_config = {
     "desc": "This is a piece of config that might want to use in multiple places",
     "handy": True,
     "reusable": True,
     "difficulty": 3
  }

  "layers": [
    {
       "name": "first_layer",
       "handyness": handy_config,
    },
    {
       "name": "second_layer",
       "handyness": handy_config,
    }
  ]


If you want to reuse chunks of config in json, or wish to combine json with and python in your configuration,
the following convention applies in both Python and JSON:

Any JSON or Python element that forms the full configuration tree or a subset of it,
can be supplied in any of the following ways:

1. Directly embed the config content.

   Don't use inclusion at all, simply provide the config:

   ::

       {
           "a_cfg_entry": 1,
           "another_entry": "llama"
       }

2. Include a python object (by FQN - fully qualified name):

   ::

      {
           "include": "path.to.module.object",
           "type": "python"
      }

   Where  the object named ``object`` in the Python file ``path/to/module.py`` contains the code in example 1.

   The path must be fully qualified.  Relative Python imports are not supported.

   N.B. It is up to you to ensure that the Python file in question is in your Python path and
   that all package directories have a ``__init__.py`` file, etc.


3. Include a JSON file (by absolute or relative file path):

   ::

       {
           "include": "path/to/file.json",
           "type": "json"
       }

   N.B. Resolution of relative file paths is done in the following order:

   a) Relative to the working directory of the web app.

   b) If a JSON file is being included from another JSON file, relative to
      directory in which the including file resides.

Note that this does not just apply when the included python or json entity is a dictionary/object.
Any of the above include directives could expand to an array, or even to single integer or string.

Configuration Inheritance
-------------------------

Sometimes you want to *almost* reuse a piece of configuration - e.g. you want a layer
that is almost the same as an existing layer but with a handful of minor differences.
Configuration inheritance addresses this use-case.

Given a fully defined named configuration object that supports inheritance:

::

    parent_obj = {
        "name": "obj1",
        "foo": "bar",
        "zing": "blat",
    }

You can easily define a new almost identical named object by inheriting from parent_obj,
either directly:

::

    direct_child_obj = {
        "inherits": parent_obj,
        "name": "obj2",
        "foo": "pow",
    }

Or by name:

::

    byname_child_obj = {
        "inherits": {
            "obj": "obj1",
        },
        "name": "obj3",
        "foo": "pow",
    }

Direct inheritance can also be achieved via inclusion, as described above.
Note that this is the only way to achieve direct inheritance in json. E.g.:

::

    include_direct_child_obj = {
        "inherits": {
            "include": "path.to.module.obj1",
            "type": "python"
        },
        "name": "obj4",
        "foo": "pow"
    }

In all three cases, the child object:

1. creates a new unique name for itself,
2. overrides the value of "foo" to "pow", and
3. inherits the parent value of "zing" (by not explicitly overriding it).

The child objects can also be used in turn as the parents of subsequent layers,
as long as cyclic dependencies are avoided.

There are two types of named configuration object that support inheritance:
named `Layers <https://datacube-ows.readthedocs.io/en/latest/cfg_layers.html>`_ and
`styles <https://datacube-ows.readthedocs.io/en/latest/cfg_styling.html>`_.
The exact way to inherit by name differs depending on the object type so
`see <https://datacube-ows.readthedocs.io/en/latest/cfg_layers.html#inheritance>`_
the
`relevant <https://datacube-ows.readthedocs.io/en/latest/cfg_styling.html#inheritance>`_
sections for details.

The copying and updating of the parent configuration object is recursive

Note that a layer or style can only inherit by name from a parent layer or style that has already
been parsed by the config parser - i.e. it must appear earlier in the definition of the layers section.
This restriction can be avoided using direct inheritance.

Behaviour of Lists
++++++++++++++++++

Care should be taken of the special handling of lists in configuration:

1. If the child entry is an empty list, this will replace the parent entry, resulting in an empty list.
2. If the child entry is a non-empty list, the values in the child list are appended to the parent entry, resulting
   in a merged list.

This can result in unexpected behaviour.  E.g. the following example does NOT replace
the color_ramp, but rather appends the "all new" color ramp on to the end of
the "original" color ramp - which will almost certainly result in a ramp-order error.

::

    original_style = {
        "name": "original",
        "title": "Original Style",
        "abstract": "The original. Accept no substitute!",
        ... # Stuff that is shared
        "color_ramp": [ ... ], # Original Color Ramp
    }

    inherited_style = {
        "inherits": original_style,
        "name": "all_new",
        "title": "All New Style",
        "abstract": "Just like Original Style, but with a hip new twist!",
        "color_ramp": [ ... ], # All New Color Ramp
    }

To replace the color ramp you can either inherit through an intermediate style
that explicitly sets the colour ramp to an empty list, or inherit both styles from
a common abstract base style that has an empty list for the color ramp.  Eg.

::

    original_style = {
        "name": "original",
        "title": "Original Style",
        "abstract": "The original. Accept no substitute!",
        ... # Stuff that is shared
        "color_ramp": [ ... ], # Original Color Ramp
    }

    intermediate_style = {
        "inherits": original_style,
        "abstract": "I am an ugly hack. I make people feel dirty just by existing.",
        "color_ramp": [], # Empty Color Ramp
    }

    inherited_style = {
        "inherits": intermediate_style,
        "name": "all_new",
        "title": "All New Style",
        "abstract": "Just like Original Style, but with a hip new twist!",
        "color_ramp": [ ... ], # All New Color Ramp
    }

Or:

::

    abstract_base_style = {
        "abstract": """
            I am an elegant abstract base class.
            I am beloved by all for my transcendent utility and beauty.
        """,
        ... # Stuff that is shared
        "color_ramp": [], # Empty Color Ramp
    }

    original_style = {
        "inherits": abstract_base_style,
        "name": "original",
        "title": "Original Style",
        "abstract": "The original. Accept no substitute!",
        "color_ramp": [ ... ], # Original Color Ramp
    }

    inherited_style = {
        "inherits": abstract_base_style,
        "name": "all_new",
        "title": "All New Style",
        "abstract": "Just like Original Style, but with a hip new twist!",
        "color_ramp": [ ... ], # All New Color Ramp
    }



Metadata Separation and Internationalisation
--------------------------------------------

Human-readable metadata can simply be embedded directly in the configuration.  However in order to support
use-cases like multi-language internationalisation and integrating metadata with external
content management systems, all human-readable metadata in the OWS configuration can be extracted
into a separate file and managed independently.

Metadata Separation
+++++++++++++++++++

To separate your metadata from config (either as an end in itself, or as preparation for internationalisation/translation):

1. Add a unique ``label`` to each of your folder layers.

   This step is optional, but strongly recommended. OWS will autogenerate
   a unique but non-obvious label for each folder if you do not supply one.

2. Run ``datacube-ows-cfg extract -m messages.po``

   This extracts all the translatable/human-readable text from your config file, and writes it to the
   named file in gettext "po" file format.

3. Add ``"message_file": "/path/to/messages.po"`` to the global section of your OWS config file.

   Subsequently, text in messages.po will over-ride text in the config file. Update as needed, restart
   wsgi process to take effect. Any field not included in the message file will be loaded directly
   from the config, as previously.

The msgid's in the message file are symbolic. E.g.

* ``global.title``: The title for the whole service.
* ``layer.<label>.title``: The title for a folder, identified by label.
* ``layer.<name>.title``: The title for a named layer, identified by name.
* ``layer.<name>.bands.<band_name>``: The default name for a band.
* ``style.<layer_name>.<style_name>.title``: The title for a style, identified by layer name and style name.
* ``style.<layer_name>.<style_name>.legend.1.title``: The title for a style legend (single date form),
  identified by layer name, style name, and the lowest date count the legend supports.

The msgstr's in the message file are the text used by OWS for global/layer/style metadata, in preference
to the values in the config file.

Fields that can be included in the message file are:

*    Titles (global, folder, layer, style, colour-ramp legends, colour-map legends)
*    Abstracts (global, folder, layer, style)
*    Units (colour-ramp legends only)
*    Tick labels (colour-ramp legends only) [#tlt]_
*    Default band names (layer only)
*    Keywords (global, folder, layer)
*    Attribution titles (global, folder, layer)
*    Fees (global only)
*    Access Constraints (global only)
*    Contact Info Organisation (global only)
*    Contact Info Position (global only)

.. [#tlt] Prefixes, suffixes and labels are pre-combined for translation purposes, and only combined tick_labels
   that contain at least one alphabetic character are recognised by the translation engine.  E.g. a label of "0.0"
   with a prefix of "<" will not be picked up by the translation engine, but if the prefix is changed to "less than ",
   then the resulting combined value "less than 0.0" WILL be picked up the translation engine.

Internationalisation/Translation of Metadata
++++++++++++++++++++++++++++++++++++++++++++

Once you have extracted your metadata into a single file, separate from the main body of configuration,
as described `above <#metadata-separation>`_, generate a translation catalog for every language you want
translations for - including the "native" language that your messages file is already in:

::

    # Create new translation catalogs for English (en), German (de), French (Fr) and Swahili (Sw).

    datacube-ows-cfg translation -n -D my_ows_project -d /config/translations -m /config/messages.po en de fr sw

This will create the following files:

::

   /config/translations/en/LC_MESSAGES/my_ows_project.po
   /config/translations/de/LC_MESSAGES/my_ows_project.po
   /config/translations/fr/LC_MESSAGES/my_ows_project.po
   /config/translations/sw/LC_MESSAGES/my_ows_project.po


These files are currently identical, apart from the language in the header.  These files should be distributed to
translators for the respective languages.  The translators keep the file in the same format, but replace
the ``msg_str`` sections with the translated text in their language and return the translated message
file to you.  Then you keep then save them into the directory structure above, replacing the untranslated
templates.

Once the translations have been placed in translations directory, they must be compiled:

::

    datacube-ows-cfg compile -D my_ows_project -d /config/translations en de fr sw

This creates the following machine-readable message (.mo) files:

::

   /config/translations/en/LC_MESSAGES/my_ows_project.mo
   /config/translations/de/LC_MESSAGES/my_ows_project.mo
   /config/translations/fr/LC_MESSAGES/my_ows_project.mo
   /config/translations/sw/LC_MESSAGES/my_ows_project.mo

You can now update the
`global section of your OWS Configuration <https://datacube-ows.readthedocs.io/en/latest/cfg_global.html#metadata-separation-and-internationalisation>`_
section and restart the web service and
you are serving multi-lingually!  (Adjust your client's "Accept-Language" header to test.)

General Config Structure
------------------------

At the top level, the Datacube OWS configuration is a single dictionary with the following elements:

::

  ows_cfg = {
     "global": {
         # Configuration to the whole server across all supported services goes here.
     },
     "wms": {
         # Configuration specific to the WMS and WMTS services goes here.
     },
     "wmts": {
         # Configuration specific to the WMTS service goes here.
     },
     "wcs": {
         # Configuration specific to the WCS service goes here.
     },
     "layers: [
         # A list of configurations for layers (WMS/WMTS) (or coverages (WCS)) to be served.
     ]
  }

The `global <https://datacube-ows.readthedocs.io/en/latest/cfg_global.html>`_ section contains configuration that
applies to the whole server across all services and layers.
The `global <https://datacube-ows.readthedocs.io/en/latest/cfg_global.html>`_ section is always required.

The `wms <https://datacube-ows.readthedocs.io/en/latest/cfg_wms.html>`_ section contains configuration that applies to the WMS/WMTS
services aross all layers.
The `wmts <https://datacube-ows.readthedocs.io/en/latest/cfg_wmts.html>`_ section contains configuration that applies to the WMTS
services aross all layers.
The `wms <https://datacube-ows.readthedocs.io/en/latest/cfg_wms.html>`_ section can be omitted if only the WCS service is
activated (specified in the `global services <https://datacube-ows.readthedocs.io/en/latest/cfg_global.html#service-selection-services>`_
section), or if the default values for all entries are acceptable.

The `wmts <https://datacube-ows.readthedocs.io/en/latest/cfg_wmts.html>`_ section is optional.

The `wcs <https://datacube-ows.readthedocs.io/en/latest/cfg_wcs.html>`_ section must be supplied if the WCS service is
activated (specified in the `global services <https://datacube-ows.readthedocs.io/en/latest/cfg_global.html#service-selection-services>`_
section).

WMTS is implemented as a thin wrapper around the WMS implementation. Therefore configuration in the
WMS section generally applies equally to WMTS.

The `layers <https://datacube-ows.readthedocs.io/en/latest/cfg_layers.html>`_ section
contains a list of layer configurations.  The configured layers define the
layers (in WMS and WMTS) and coverages (in WCS) that the instance serves, and their behaviour. The layers section
is always required.
