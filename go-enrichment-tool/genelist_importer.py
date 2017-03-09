#!/usr/bin/env python3
# -*- coding: utf-8 -*-
'''
@author: Pieter Moris
'''

import os


def importGeneList(path):
    """
    Imports the interest/background set of genes (uniprot AC).

    Parameters
    ----------
    path : str
        The path to the file.

    Returns
    -------
    set of str
        A set of background uniprot AC's.

    Notes: Gene lists should not contain a header. One gene per line.
    
    Possible improvements: check for file structure and allow headers, comma separated lists, etc.
    """

    listPath = os.path.abspath(path)
    
    with open(listPath, 'r') as inGenes:
        geneSet = set([line.rstrip() for line in inGenes])
        
    print('Retrieved', len(geneSet), 'uniprot AC\'s from', listPath)

    return geneSet

def isValidSubset(subset, background):
    """
    Checks if the gene subset of interest contains genes not present in the background set.
    If there are additional genes they are removed.

    Parameters
    ----------
    subset : set of str
        A subset of uniprot ACs of interest.
    background : set of str
        A set of uniprot ACs to be used as the background.

    Returns
    -------
    set of str
        A cleaned subset of uniprot ACs of interest.
    """

    if subset.issubset(background):
        return subset
    else:
        missing = [AC for AC in subset if AC not in background]
        print('WARNING! The subset of interest contained genes not present in the background list.')
        print(missing)
        print('Removing these genes from the set of interest...\n')
        return subset.difference(missing)

def reportMissingGenes(set, gafDict, indicator):
    """
    Finds and reports Uniprot AC's in the provided background/interest gene sets which
    are not present in the gene association file (most likely obsolete entries).
    #Also returns a new set where these missing genes are removed.

    Parameters
    ----------
    set : set of str
        A set of Uniprot ACs.
        Generated by importSubset() or importBackground().
    gafDict : dict of str mapping to set
        A dictionary mapping gene Uniprot AC's (str) to a set GO ID's.
        Generated by importGAF().
    indicator : str
        A string signifying whether the set is the background or interest set of genes.

    Returns
    -------
    set : set of str
        The set after removal of Uniprot AC's not present in provided gene lists.
    """

    if len(set) != len(gafDict):
        obsoleteGenes = [AC for AC in set if AC not in gafDict]
        print('WARNING! The', indicator, 'gene set contained genes not present in the gene association file.')
        print(obsoleteGenes)
        print('Removing these genes from the', indicator, 'set...\n')
        return set.difference(obsoleteGenes)
    else:
        return set