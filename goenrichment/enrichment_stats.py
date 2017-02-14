#!/usr/bin/env python3
# -*- coding: utf-8 -*-
'''
@author: Pieter Moris
'''

import numpy as np
import statsmodels.sandbox.stats.multicomp

from scipy.stats import hypergeom


# def enrichmentOneSided(GOid, background, subset, GOdict, gafDict, gafSubset, minGenes):
#     """
#     Performs a one-sided hypergeometric test for a given GO term.

#     Parameters
#     ----------
#     GOid : str
#         A GO identifier (key to the GO dictionary).
#     background : set of str
#         A set of background uniprot AC's.
#     subset : set of str
#         A subset of uniprot AC's of interest.
#     GOdict : dict
#         A dictionary of GO objects generated by importOBO().
#         Keys are of the format `GO-0000001` and map to OBO objects.
#     gafDict : dict
#         A dictionary mapping the background's gene uniprot AC's to GO ID's.
#     gafDict : dict
#         A dictionary mapping the subset's gene uniprot AC's to GO ID's.

#     Returns
#     -------
#     float
#         The p-value of the one-sided hypergeometric test.
#     """

#     backgroundTotal = len(background)
#     subsetTotal = len(subset)

#     validTerms = set([GOid])
#     validTerms.update(GOdict['GOid'].childs)

#     backgroundGO = countGOassociations(validTerms, gafDict)
#     subsetGO = countGOassociations(validTerms, gafDict)

#     # If the number of genes for the current GO category is too low, return 1
#     if backgroundGO < minGenes:
#         return None

#     # k or more successes (= GO associations = subsetGO) in N draws (= subsetTotal)
#     # from a population of size M (backgroundTotal) containing n successes (backgroundGO)
#     # k or more is the sum of the probability mass functions of k up to N successes
#     # since cdf gives the cumulative probability up and including input (less or equal to k successes),
#     # and we want P(k or more), we need to calculate 1 - P(less than k) =  1 - P(k-1 or less)
#     # .sf is the survival function (1-cdf).
#     pVal = hypergeom.sf(subsetGO - 1, backgroundTotal,
#                         backgroundGO, subsetTotal)

#     return pVal


def enrichmentOneSided(subsetGO, backgroundTotal, backgroundGO, subsetTotal):
    """
    Performs a one-sided hypergeometric test for a given GO term.

    k or more successes (= GO associations = subsetGO) in N draws (= subsetTotal)
    from a population of size M (backgroundTotal) containing n successes (backgroundGO)
    k or more is the sum of the probability mass functions of k up to N successes
    since cdf gives the cumulative probability up and including input (less or equal to k successes),
    and we want P(k or more), we need to calculate 1 - P(less than k) =  1 - P(k-1 or less)
    sf is the survival function (1-cdf).

    Parameters
    ----------
    GOid : str
        A GO identifier (key to the GO dictionary).
    backgroundTotal : int
        The total number of background uniprot AC's.
    subsetTotal : int
        The total number of subset uniprot AC's of interest.
    GOdict : dict
        A dictionary of GO objects generated by importOBO().
        Keys are of the format `GO-0000001` and map to OBO objects.
    gafDict : dict
        A dictionary mapping the background's gene uniprot AC's to GO ID's.        
    gafSubset : dict
        A dictionary mapping the subset's gene uniprot AC's to GO ID's.

    Returns
    -------
    float
        The p-value of the one-sided hypergeometric test.
    """

    pVal = hypergeom.sf(subsetGO - 1, backgroundTotal,
                        backgroundGO, subsetTotal)

    return pVal


def countGOassociations(validTerms, gafDict):
    """
     Counts the number of genes associated with at least one of the provided GO terms.

     Parameters
     ----------
     validTerms : set
         A set of GO terms. Should include the GO id of interest and all of its childs.
     gafDict : dict
         A dictionary mapping gene uniprot AC's to GO ID's.        

     Returns
     -------
     int
         The number of associated genes.
     """

    GOcounter = 0

    # For each gene:GO id set pair in the GAF dictionary
    for gene, GOids in gafDict.items():
        # Increment the GO counter if the valid terms set shares a member
        # with the GO id set of the current gene
        if not validTerms.isdisjoint(GOids):
            GOcounter += 1

    return GOcounter


def enrichmentAnalysis(background, subset, GOdict, gafDict, gafSubset,
                       minGenes=3, threshold=0.05):
    """
    Performs a GO enrichment analysis.

    First, all GO id's associated with the genes in the subset of interest,
    i.e. those defined in the gafSubset dictionary, will be tested
    using a onesided hypergeometric test.

    If the test is not significant at the chosen threshold, the test will
    recursively be performed for all of the GO id's parents.
    If the test is significant, the recursive call will stop here.

    NOTE: At the moment, this means the test will be propagated until the top level,
    but after a certain point it is probably not worth testing anymore.
    NOTE: Isn't this cherry picking / p-value manipulation?
    C) NICOLAS: set maken van termen vanaf wanneer (dus propageer vanaf onder) er
    genoeg genen geassocieerd zijn, die opslaan en enkel deze testen.

    If the number of genes associated with a GO id is lower than minGenes,
    the test will be skipped for this id, but its parents will recursively be tested.

    For each test, the number of genes associated with the GO id is found
    by counting the number of genes associated with the GO id itself or 
    with any of its child terms.

    In the end, a dictionary containing the tested GO id's mapped to p-values.
    Any term that was not tested will be absent.

    Parameters
    ----------
    background : set
        A set of background gene uniprot AC's.
    subset : set
        A subset of gene uniprot AC's of interest.
    GOdict : dict
        A dictionary of GO objects generated by importOBO().
        Keys are of the format `GO-0000001` and map to OBO objects.
    gafDict : dict
        A dictionary mapping the background's gene uniprot AC's to GO ID's.        
    gafSubset : dict
        A dictionary mapping the subset's gene uniprot AC's to GO ID's.
    minGenes : int
        The minimum number of genes that has to be associated with a term,
        before the test will be performed.
    threshold: float
        The threshold of the hypergeometric test for which the GO term's
        parents will not be further recursively tested for enrichment.

    Returns
    -------
    dict
        A dictionary mapping GO id's to p-values. Only GO id's that
        were tested are returned.
    """

    # generate a list of all base GO id's to test
    # i.e. those of all genes in the subset of interest
    baseGOids = [GOid for gene, GOids in gafSubset.items()
                 for GOid in GOids if not GOdict[GOid].childs]

    # baseGOids = {gene:set() for gene in gafSubset}
    # for gene, GOids in gafSubset.items():
    #     for GOid in GOids:
    #         if not GOdict[GOid].childs:
    #             baseGOids[gene].add(GOid)
    # baseGOids = []
    # for gene, GOids in gafSubset.items():
    #     for GOid in GOids:
    #         if not GOdict[GOid].childs:
    #             baseGOids.append(GOid)

    pValues = {}

    backgroundTotal = len(background)
    subsetTotal = len(subset)

    # Perform a onesided enrichment test for each of the base GO id's,
    # Recurse to parents if not significant
    for GOid in baseGOids:

        recursiveTester(GOid, backgroundTotal, subsetTotal, GOdict,
                        gafDict, gafSubset, minGenes, threshold, pValues)

    print('Tested', len(pValues), 'GO categories.')
    sig = sum(i < threshold for i in pValues.values())
    print(sig, 'were significant at alpha =',threshold)
    return pValues


def recursiveTester(GOid, backgroundTotal, subsetTotal, GOdict, gafDict,
                    gafSubset, minGenes, threshold, pValues):
    """
    Implements the recursive enrichment tests for the enrichmentAnalysis() function
    by propagating through parent terms in case of an insignificant result or low
    gene count.

    NOTE: Does not return anything, but fills in the passed pValues dictionary.

    Parameters
    ----------
    GOid : str
        The GO id that is being tested for enrichment. 
    backgroundTotal : int
        The total number of genes in the background set.
    subsetTotal : int
        The total number of genes in the subset of interest.
    GOdict : dict
        A dictionary of GO objects generated by importOBO().
        Keys are of the format `GO-0000001` and map to OBO objects.
    gafDict : dict
        A dictionary mapping the background's gene uniprot AC's to GO ID's.        
    gafSubset : dict
        A dictionary mapping the subset's gene uniprot AC's to GO ID's.
    minGenes : int
        The minimum number of genes that has to be associated with
    threshold: float
        The threshold of the hypergeometric test for which the GO term's
        parents will not be further recursively tested for enrichment.
    pValues : dict
        An empty dictionary that gets passed through the recursion and
        filled with a GO id : p-value pair for every enrichment test.     
    """

    # If a certain GOid already has a p-value stored,
    # it can be skipped and so can its parents
    if GOid not in pValues:

        # While testing for a term, also test all terms that were associated
        # with one of its childs
        validTerms = set([GOid]) # https://stackoverflow.com/questions/36674083/why-is-it-possible-to-replace-set-with
        validTerms.update(GOdict[GOid].childs)

        # Count the number of genes in the background and subset that were
        # associated with the current terms
        backgroundGO = countGOassociations(validTerms, gafDict)
        subsetGO = countGOassociations(validTerms, gafSubset)

        # If the number of associated genes for the current GO category is too low,
        # skip and move up hierarchy to test the parents
        if backgroundGO < minGenes:
            for parent in GOdict[GOid].parents:
                recursiveTester(parent, backgroundTotal, subsetTotal,
                                GOdict, gafDict, gafSubset, minGenes,
                                threshold, pValues)

        else:
            # Map GOid to p-value
            pVal = enrichmentOneSided(
                subsetGO, backgroundTotal, backgroundGO, subsetTotal)
            pValues[GOid] = pVal

            # If test is not significant, move up the hierarchy to perform
            # additional tests on parent terms
            if pVal > threshold:
                for parent in GOdict[GOid].parents:
                    recursiveTester(parent, backgroundTotal, subsetTotal,
                                    GOdict, gafDict, gafSubset, minGenes,
                                    threshold, pValues)

            # Otherwise stop recursion and don't perform any higher up tests
            else:
                return

def multipleTestingCorrection(pValues, testType='fdr', threshold = 0.05):
    """
    Performs multiple testing correction for a list of supplied p-values.

    Parameters
    ----------
    pValues : dict
        A dictionary mapping GO id's to p-values. Only GO id's that
        were tested are returned.
    testType : str
        Specifies the type of multiple correction.
        Options include: `bonferroni` and `fdr` (Benjamini Hochberg).
    threshold : float
        The significance level to use.

    Returns
    -------
    array
        A numpy array containing uniprot AC's, p-values and corrected q-values.
    """

    # Convert uniprot AC's and associated p-values to np arrays
    keys = np.array(list(pValues.keys()))
    pvals = np.array(list(pValues.values()))

    # Perform multiple testing correction
    fdr = statsmodels.sandbox.stats.multicomp.multipletests(pvals, threshold)

    print(sum(fdr[0]),'GO categories out of',len(pvals),'significant after multiple testing correction.')

    # Create array with ID's, p-values and q-values
    outputArray = np.column_stack((keys, pvals, fdr[1]))

    outputArray = outputArray[outputArray[:,2].argsort()]

    return outputArray


# class goResults():
#
#     def __init__(self):
#         self.pValues = {}
#         self.qValues = {}
#         self.threshold = 0
#
#     # def multipleTestingCorrection(self, threshold):
