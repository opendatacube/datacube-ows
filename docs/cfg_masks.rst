===========================
OWS Configuration - Masking
===========================

.. contents:: Table of Contents

------------------------
Masking in Configuration
------------------------

OWS uses masks in three distinct contexts.  Both use the same basic syntax to define mask rules,
but the semantics of how they are applied differs between contexts, and some contexts have
extend the basic syntax.

This page discusses the common syntax only.

Mask Rule Definition
====================

A mask rule defines a pixel test against one or more bands in an image dataset, selecting a set of
pixels for further processing (e.g. for transparency masking or colour coding)

This can be done either by treating the band as a bit-flag (
with the `flags <#bitflag-rules-flags>`_ entry) or as an enumeration (
with the `values <#enumeration-rules-values>`_ entry).

A mask rule will always be associated with a particular measurement band, but the details of how
this association is determined varies by context.

Bitflag Rules (flags)
+++++++++++++++++++++

For bitflag bands, the actual logic of the Value Rule is contained in the "flags" entry.

The flags entry is a dictionary with one of three possible formats.  Note
that formats cannot be combined.  In particular ``and`` and ``or`` logic cannot
be combined in a single rule.

Refer to the OpenDataCube metadata for the underlying product for the
valid bitflag names.

Simple Rules
&&&&&&&&&&&&

A simple rule allows matching a single bitflag value.
The ``flags`` dictionary contains a single entry, the key is a valid bitflag
for the band, and the value is boolean.

E.g.::

        {
            ..., # Other values, as required by context.
            "flags": {
                # matches all pixels that have the "open_forest" bit flag set to True.
               "open_forest": True,
            }
        }

And Rules
&&&&&&&&&

And Rules allow a pixel match if all the specified comparisons match. The flags
entry contains an "and" dictionary that in turn contains the individual comparisons.

E.g.::

    {
        ..., # Other values, as required by context.
        "flags": {
            "and": {
                # matches all pixels that have the "open_forest" bit flag set to True
                # AND the "underwater" bit flag set to False.
               "open_forest": True,
               "underwater": False,
            }
        }
    }

Or Rules
&&&&&&&&

Or Rules allow a pixel match if any of the specified comparisons match. The flags
entry contains an "or" dictionary that in turn contains the individual comparisons.

E.g.::

    {
        ..., # Other values, as required by context.
        "flags": {
            "or": {
                # matches all pixels that have not already matched a previous rule
                # and have either the "open_forest" or the "closed_forest" bit flag set
                # to True.
               "open_forest": True,
               "closed_forest": True,
            }
        }
    }

Enumeration Rules (values)
++++++++++++++++++++++++++

For non-bitflag bands, the actual logic of the Value Rule is contained in the "values" entry.

The "values" entry is a list of integers.  Pixels whose exact value is in this list satisfy
the rule.

E.g.

::

    {
        ..., # Other values, as required by context.
        # Matches pixels whose value is exactly either 2, 3, 7 or 15.
        "values": [2, 3, 7, 15],
    }

Inverse Logic (invert)
++++++++++++++++++++++

Any mask rule can be inverted with the ``invert`` flag. The ``invert`` flag is a boolean and
defaults to False if not set.

When ``invert`` is True, the mask is inverted, so it matches pixels that do not match the
uninverted pixels.

E.g.
::

    {
        ...,
        "invert": True,
        # With the invert flag applied, this rule matches all pixels that do NOT
        # have the open_forest bit set.
        "flags": {
           "open_forest": True,
        }
    }


    {
        ...,
        "invert": True,
        # With the invert flag applied, this rule matches all pixels that do NOT
        # have BOTH the open_forest bit and underwater bit set.
        # (The "and" operates as a "nand")
        "flags": {
            "and": {
                # matches all pixels that have the "open_forest" bit flag set to True
                # AND the "underwater" bit flag set to False.
               "open_forest": True,
               "underwater": False,
            }
        }
    }

    {
        ...,
        "invert": True,
        # With the invert flag applied, this rule matches all pixels that are neither open_forest
        # nor closed_forest.
        # (The "and" operates as a "nor")
        "flags": {
            "or": {
                # matches all pixels that have not already matched a previous rule
                # and have either the "open_forest" or the "closed_forest" bit flag set
                # to True.
               "open_forest": True,
               "closed_forest": True,
            }
        }
    }

    {
        ...,
        "invert": True,
        # Matches pixels whose value is any value EXCEPT 2, 3, 7 or 15.
        "values": [2, 3, 7, 15],
    }
