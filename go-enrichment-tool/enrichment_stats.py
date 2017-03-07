#!/usr/bin/env python3
# -*- coding: utf-8 -*-
'''
@author: Pieter Moris
'''

import numpy as np
import pandas as pd
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
#     validTerms.update(GOdict['GOid'].children)

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
         A set of GO terms. Should include the GO id of interest and all of its children.
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
    using a one-sided hypergeometric test.

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
    dict of dicts
        A dictionary of dictionaries mapping GO id's to p-values and frequencies.
        Only GO id's that were tested are returned.
    """

    # generate a list of all base GO terms to test
    # i.e. the terms of all the genes in the subset of interest
    # but starting at the most specific child terms since the function
    # will propagate upwards.
    subsetGOids = {GOid for gene, GOids in gafSubset.items() for GOid in GOids}
    subsetGOidsParents = {parent for GOid in subsetGOids for parent in GOdict[GOid].parents}
    baseGOids = [GOid for GOid in subsetGOids if not GOid in subsetGOidsParents]

    # baseGOids = {gene:set() for gene in gafSubset}
    # for gene, GOids in gafSubset.items():
    #     for GOid in GOids:
    #         if not GOdict[GOid].children:
    #             baseGOids[gene].add(GOid)
    # baseGOids = []
    # for gene, GOids in gafSubset.items():
    #     for GOid in GOids:
    #         if not GOdict[GOid].children:
    #             baseGOids.append(GOid)

    enrichmentTestResults = { 'pValues' : {}, 'interestCount' : {}, 'backgroundCount' : {}}

    backgroundTotal = len(background)
    subsetTotal = len(subset)

    # Perform a onesided enrichment test for each of the base GO id's,
    # Recurse to parents if not significant
    for GOid in baseGOids:
        recursiveTester(GOid, backgroundTotal, subsetTotal, GOdict,
                        gafDict, gafSubset, minGenes, threshold, enrichmentTestResults)

    print('Tested', len(enrichmentTestResults['pValues']), 'GO categories.\n')
    sig = sum(i < threshold for i in enrichmentTestResults['pValues'].values())
    print(sig, 'were significant at alpha =', threshold, '\n')

    return enrichmentTestResults


def recursiveTester(GOid, backgroundTotal, subsetTotal, GOdict, gafDict,
                    gafSubset, minGenes, threshold, enrichmentTestResults):
    """
    Implements the recursive enrichment tests for the enrichmentAnalysis() function
    by propagating through parent terms in case of an insignificant result or low
    gene count.

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
    enrichmentTestResults : dict of dicts
        An dictionary of dictionaries that gets passed through the recursion and
        filled with mappings of GO id's to p-values and frequencies for every enrichment test.

    Returns
    -------
    Does not return anything, but fills in the passed pValues dictionary (which
    is nested in the enrichmentTestResults dictionary).
    """

    # If a certain GOid already has a p-value stored,
    # it can be skipped and so can its parents
    if GOid not in enrichmentTestResults['pValues']:

        # While testing for a term, also count all of its child terms
        validTerms = set([GOid]) # https://stackoverflow.com/questions/36674083/why-is-it-possible-to-replace-set-with
        validTerms.update(GOdict[GOid].children)

        # Count the number of genes in the background and subset that were
        # associated with the current terms
        backgroundGO = countGOassociations(validTerms, gafDict)
        subsetGO = countGOassociations(validTerms, gafSubset)

        # if GOid == 'GO:0032993':
        #     print('bg Count', backgroundGO, 'interestCount', subsetGO, 'pval', pVal)
        #     print('bgTotal', backgroundTotal, 'subsetTotal', subsetTotal)

        # If the number of associated genes for the current GO category is too low,
        # skip and move up hierarchy to test the parents
        if backgroundGO < minGenes:
            for parent in GOdict[GOid].parents:
                recursiveTester(parent, backgroundTotal, subsetTotal,
                                GOdict, gafDict, gafSubset, minGenes,
                                threshold, enrichmentTestResults)

        else:
            # Map GOid to p-value and the number of associated genes in the interest and background set
            pVal = enrichmentOneSided(
                subsetGO, backgroundTotal, backgroundGO, subsetTotal)
            enrichmentTestResults['pValues'][GOid] = pVal
            enrichmentTestResults['interestCount'][GOid] = subsetGO
            enrichmentTestResults['backgroundCount'][GOid] = backgroundGO

            # If test is not significant, move up the hierarchy to perform
            # additional tests on parent terms
            if pVal > threshold:
                for parent in GOdict[GOid].parents:
                    recursiveTester(parent, backgroundTotal, subsetTotal,
                                    GOdict, gafDict, gafSubset, minGenes,
                                    threshold, enrichmentTestResults)

            # Otherwise stop recursion and don't perform any higher up tests
            else:
                return

def multipleTestingCorrection(enrichmentTestResults, testType='fdr', threshold = 0.05):
    """
    Updates the original enrichmentTestResults dictionary of dictionaries by appending
    an additional dictionary mapping GO id's to corrected p-values.

    Parameters
    ----------
    enrichmentTestResults : dict of dicts
        An dictionary of dictionaries mapping GO id's to p-values and counts.
    testType : str
        Specifies the type of multiple correction.
        Options include: `bonferroni` and `fdr` (Benjamini Hochberg).
    threshold : float
        The significance level to use.

    Returns
    -------
    None
        Modifies the provided enrichmenTestResults dictionary in-place.
    """

    # Convert uniprot AC's and associated p-values to np arrays
    pValues = enrichmentTestResults['pValues'].values()
    ids = enrichmentTestResults['pValues'].keys()

    # Perform multiple testing correction
    if testType == 'bonferroni':
        print('Performing multiple testing correction using the Bonferroni FWER method.\n')
        corr = statsmodels.sandbox.stats.multicomp.multipletests(list(pValues), alpha=threshold, method='bonferroni')
        print(np.sum(corr[0]),'GO categories out of', len(corr[0]), 'were significant after bonferroni multiple testing correction.\n')
    else:
        print('Performing multiple testing correction using the Benjamini-Hochberg FDR method.\n')
        corr = statsmodels.sandbox.stats.multicomp.multipletests(list(pValues), alpha=threshold, method='fdr_bh')
        print(np.sum(corr[0]),'GO categories out of', len(corr[0]), 'were significant after FDR multiple testing correction.\n')

    # Append corrected p-values as a new dictionary
    enrichmentTestResults['corr'] = { id : corrValue for id, corrValue in zip(ids, corr[1]) }

    return None

def annotateOutput(enrichmentTestResults, GOdict, background, subset):
    """
    Adds the GO id names to the array with enrichment results.

    Parameters
    ----------
    enrichmentTestResults : dict of dicts
        A dictionary containing dictionaries mapping the GO id's to their frequency counts
        for both the interest and background set.
    GOdict : dict
        A dictionary of GO objects generated by importOBO().
        Keys are of the format `GO-0000001` and map to OBO objects.
    background : set
        A set of background gene uniprot AC's.
    subset : set
        A subset of gene uniprot AC's of interest.

    Returns
    -------
    DataFrame
        A pandas DataFrame containing GO id's, descriptions, frequency counts and p-values and corrected p-values.
    """

    # Convert dictionary to dataframe with level 1 dictionary keys as columns
    # https://stackoverflow.com/questions/37839136/convert-dictionary-of-dictionaries-into-dataframe-python
    outputDataFrame = pd.DataFrame.from_records(enrichmentTestResults).reset_index().rename(columns=dict(index='GO id',
                                                                                                         backgroundCount='background freq',
                                                                                                         interestCount='cluster freq',
                                                                                                         corr='corrected p-value',
                                                                                                         pValues='p-value'))

    # Retrieve GO id names and namespaces
    outputDataFrame['GO name'] = [GOdict[id].name for id in outputDataFrame['GO id']]
    outputDataFrame['GO namespace'] = [GOdict[id].namespace for id in outputDataFrame['GO id']]

    # Retrieve GO id counts in background and interest set
    backgroundTotal = len(background)
    subsetTotal = len(subset)
    outputDataFrame['cluster freq'] = outputDataFrame['cluster freq'].apply(lambda x: '{0}/{1} ({2}%)'.format(str(x), str(subsetTotal), "{0:.2f}".format(100*x/subsetTotal)))
    outputDataFrame['background freq'] = outputDataFrame['background freq'].apply(lambda x: '{0}/{1} ({2}%)'.format(str(x), str(backgroundTotal), "{0:.2f}".format(100*x/backgroundTotal)))
    # https://stackoverflow.com/questions/34859135/find-key-from-value-for-pandas-series
    # outputDataFrame['background freq'] = pd.Series(['{0}/{1} ({2}%)'.format(str(outputDataFrame[outputDataFrame['GO id'] == id]['background freq']), str(backgroundTotal),
    #                                                   str(outputDataFrame[outputDataFrame['GO id'] == id]['background freq'] / backgroundTotal)) for id in outputDataFrame['GO id']])
    # outputDataFrame['GO namespace'] = GOdict[outputDataFrame['GO id']].namespace

    # Sort on corrected p-values
    outputDataFrame = outputDataFrame.sort_values(by=['corrected p-value', 'p-value']).reset_index(drop=True)

    # Re-arrange columns
    outputDataFrame = outputDataFrame[['GO id', 'GO name', 'GO namespace', 'p-value', 'corrected p-value', 'cluster freq', 'background freq']]

    return outputDataFrame

    # Deprecated code

    # goidNames = np.array([GOdict[id].name for id in pValuesArray[:,0]])
    # goidNamespaces = np.array([GOdict[id].namespace for id in pValuesArray[:,0]])

    # # Retrieve GO id counts in background and interest set
    # backgroundTotal = len(background)
    # subsetTotal = len(subset)
    # interestCounts = pd.Series(['{0}/{1} ({2}%)'.format(str(enrichmentTestResults['interestCount'][id]), str(subsetTotal),
    #                                                   str(enrichmentTestResults['interestCount'][id] / subsetTotal)) for id in pValuesArray[:, 0]])
    # backgroundCounts = pd.Series(['{0}/{1} ({2}%)'.format(str(enrichmentTestResults['backgroundCount'][id]), str(backgroundTotal),
    #                                                   str(enrichmentTestResults['backgroundCount'][id] / backgroundTotal)) for id in pValuesArray[:, 0]])

    # # Append names and namespaces to array
    # outputArray = np.hstack((pValuesArray, goidNames[:,None], goidNamespaces[:,None], interestCounts[:,None], backgroundCounts[:,None]))
    # # requires [:,] because otherwise 1d array is passed)
    #
    # # Convert array to DataFrame and re-arrange columns
    # outputDataFrame = pd.DataFrame(outputArray, columns=['GO id', 'p-value', 'fdr-corrected p-value', 'GO name', 'GO namespace', 'cluster freq', 'background freq'])
    # outputDataFrame = outputDataFrame[['GO id', 'GO name', 'GO namespace', 'p-value', 'fdr-corrected p-value', 'cluster freq', 'background freq']]
