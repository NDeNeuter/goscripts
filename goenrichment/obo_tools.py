#!/usr/bin/env python3
# -*- coding: utf-8 -*-
'''
@author: Pieter Moris
'''

import os
import re


class goTerm:
    """
    GO term object.

    Stores the ID, name and domain of the GO term and contains dictionaries for child and parent nodes.

    Attributes
    ----------
    id : str
        The identifier of the GO term.
    altid : str
        Optional tag for an alternative id.
    name : str
        The GO term name.
    namespace : str
        The domain of the GO term (Cellular Component, Molecular Function or Biological Process).
    parents : set of str
        The parent terms of the GO term, as indicated by the `is_a` relationship.
    childs : set of str
        The child terms of the GO term, derived from other GO terms after a complete OBO file is processed initially.

    not necessary... Methods
    -------
    returnID
        Returns the ID of the GO term.
    gamma(n=1.0)
        Change the photo's gamma exposure.  
    # https://stackoverflow.com/questions/1336791/dictionary-vs-object-which-is-more-efficient-and-why

    '''
    https://stackoverflow.com/questions/3489071/in-python-when-to-use-a-dictionary-list-or-set
    When you want to store some values which you'll be iterating over, 
    Python's list constructs are slightly faster. 
    However, if you'll be storing (unique) values in order to check for their existence, 
    then sets are significantly faster.
    '''
    """

    goCount = 0

    __slots__ = ('id', 'name', 'altid', 'namespace', 'childs', 'parents')

    def __init__(self, GOid):
        self.id = GOid
        self.altid = []
        self.name = ''
        self.namespace = ''
        self.childs = set()
        self.parents = set()

        goTerm.goCount += 1

    def returnID(self):
        return self.id


def importOBO(path):
    """
    Imports an OBO file and generates a dictionary containing an OBO object for each GO term.

    Parameters
    ----------
    path : str
        The path to the file.

    Returns
    -------
    dict of OBO objects
        Keys are of the format `GO-0000001` and map to OBO objects.

    Possible improvements:
        Check for `is_obsolete` and `replaced_by`, although the replacement term should be in OBO file as an entry.
    """

    GOdict = {}

    path = os.path.abspath(path)
    with open(path, 'r') as oboFile:
        # find re pattern to match '[Entry]'
        entryPattern = re.compile('^\[.+\]')
        validEntry = False

        for line in oboFile:

            # Only parse entries preceded by [Entry], not [Typedef]
            if entryPattern.search(line):
                if 'Term' in line:
                    validEntry = True
                else:
                    validEntry = False

            # if [Entry] was encountered previously, parse annotation
            elif validEntry:
                # and hierarchy from subsequent lines
                if line.startswith('id'):
                    # Store ID for lookup of other attributes in next lines
                    GOid = line.split(': ')[1].rstrip()

                    if not GOid in GOdict:               # check if id is already stored as a key in dictionary
                        # if not, create new GOid object as the value for this
                        # key
                        GOdict[GOid] = goTerm(GOid)

                elif line.startswith('name'):
                    GOdict[GOid].name = line.split(': ')[1].rstrip()
                elif line.startswith('namespace'):
                    GOdict[GOid].namespace = line.split(': ')[1].rstrip()
                elif line.startswith('alt_id'):
                    GOdict[GOid].altid.append(line.split(': ')[1].rstrip())
                elif line.startswith('is_a'):
                    GOdict[GOid].parents.add(line.split()[1].rstrip())
    return GOdict


def buildGOtree(GOdict):
    """
    Generates the entire GO tree's parent structure by walking through the parent hierarchy of each GO entry.

    Parameters
    ----------
    GOdict : dict
        A dictionary of GO objects generated by importOBO().
        Keys are of the format `GO-0000001` and map to OBO objects.

    Returns
    -------
    None
        The input GO dictionary will be updated.
        Parent attributes now trace back over the full tree hierarchy.
    """

    # Process each GO term in the GO dictionary
    for GOid, GOobj in GOdict.items():
        # Define new set to store higher order parents
        parentSet = set()
        # Call helper function to propagate through parents
        propagateParents(GOid, GOid, GOdict, parentSet)
        # Update GO term's parents attribute to include all higher order
        # parents
        GOobj.parents.update(parentSet)

    # After all parents have been found, for each ID, add it as a child for
    # all its parents
    completeChildHierarchy(GOdict)

    return None


def propagateParents(currentTerm, baseGOid, GOdict, parentSet):
    """
    Propagates through the parent hierarchy of a provided GO term.

    Parameters
    ----------
    GOdict : dict
        A dictionary of GO objects generated by importOBO().
        Keys are of the format `GO-0000001` and map to OBO objects.
    baseGOid : str
        d
   parentSet : set
        An, initially, empty set that gets passed through the recursion.
        It tracks the entire group of parent terms of the GO id.

    Returns
    -------
    dict of OBO objects
        Updated GO dict where parent attributes trace back over the full tree hierarchy.
        Keys are of the format `GO-0000001` and map to OBO objects.
    """

    # If current term is not present in GO dictionary, print warning and end
    # recursion
    if currentTerm not in GOdict:
        print('WARNING!\n' + currentTerm, 'was defined as a parent for',
              baseGOid, ', but was not found in the OBO file.')
        parentSet.pop(currentTerm)      # remove missing value
        return

    # If current term has no further parents the recursion will end and move
    # back up the stack, since there are no parents to iterate over
    parents = GOdict.get(currentTerm).parents
    for parent in parents:

        # # Check if parent is present in GO dictionary
        # if parent not in GOdict:
        #     print('WARNING!\n' + parent, 'was defined as a parent for',
        #           baseGOid, ', but was not found in the OBO file.')

        # Add current term's parents to growing set
        parentSet.add(parent)
        # NOTE: better to do this at the start of the function, by adding current term
        #       otherwise a term that is not present in the OBO dict will be added
        #       since the check happens later, i.e. in the next function call

        # and recurse function for each parent
        propagateParents(parent, baseGOid, GOdict, parentSet)

    return None


def completeChildHierarchy(GOdict):
    """
    Generates the entire GO tree's child structure by iterating over the parents
    of each GO object.

    NOTE: completeParentsHierarchy() must be run prior to this function.

    Parameters
    ----------
    GOdict : dict
        A dictionary of GO objects generated by importOBO().
        Keys are of the format `GO-0000001` and map to OBO objects.

    Returns
    -------
    dict of OBO objects
        Updated GO dict where child attributes trace back over the full tree hierarchy.
        Keys are of the format `GO-0000001` and map to OBO objects.
    """
    for GOid, GOobj in GOdict.items():
        [GOdict[parent].childs.add(GOid) for parent in GOobj.parents]

    return None
