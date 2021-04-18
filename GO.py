from __future__ import print_function
import csv
import goatools
from goatools.anno.genetogo_reader import Gene2GoReader
from goatools.obo_parser import GODag
from goatools.base import download_ncbi_associations
from goatools.base import download_go_basic_obo
import genes_NCBI_9606_ProteinCoding
from goatools.goea.go_enrichment_ns import GOEnrichmentStudyNS
import os

# Name: pullGOenrichment
# Summary: from a list of differentially expressed geneids,
#           find the enriched GO terms as compared to a population
#           of possible genes (all protein coding human genes)
# Parameters: inputFile - the file containg the geneids + gene symbols
#             project - the name of the project for labeling purposes.
# Return: NA - writes output to a .csv and .txt file.
def pullGOenrichment(inputFile, project):
    GeneID2nt_hum = genes_NCBI_9606_ProteinCoding.GENEID2NT

    obo_fname = download_go_basic_obo()

    fin_gene2go = download_ncbi_associations()

    obodag = GODag("go-basic.obo")

    # Read NCBI's gene2go. Store annotations in a list of namedtuples
    objanno = Gene2GoReader(fin_gene2go, taxids=[9606])

    # Get namespace2association where:
    #    namespace is:
    #        BP: biological_process
    #        MF: molecular_function
    #        CC: cellular_component
    #    assocation is a dict:
    #        key: NCBI GeneID
    #        value: A set of GO IDs associated with that gene
    ns2assoc = objanno.get_ns2assc()

    for nspc, id2gos in ns2assoc.items():
        print("{NS} {N:,} annotated human genes".format(NS=nspc, N=len(id2gos)))

    print(len(GeneID2nt_hum))



    goeaobj = GOEnrichmentStudyNS(
        GeneID2nt_hum.keys(),  # List of human protein-coding genes
        ns2assoc,  # geneid/GO associations
        obodag,  # Ontologies
        propagate_counts=False,
        alpha=0.05,  # default significance cut-off
        methods=['fdr_bh'])  # defult multipletest correction method

    geneid2symbol = {}
    with open(inputFile, 'r') as infile:
        input_genes = csv.reader(infile)
        for line in input_genes:
            geneid = line[0]
            symbol = line[1]
            if geneid:
                geneid2symbol[int(geneid)] = symbol

    infile.close()
    print(len(geneid))


    geneids_study = geneid2symbol.keys()
    goea_results_all = goeaobj.run_study(geneids_study)
    goea_results_sig = [r for r in goea_results_all if r.p_fdr_bh < 0.05]

    import collections as cx
    ctr = cx.Counter([r.NS for r in goea_results_sig])
    print('Significant results[{TOTAL}] = {BP} BP + {MF} MF + {CC} CC'.format(
        TOTAL=len(goea_results_sig),
        BP=ctr['BP'],  # biological_process
        MF=ctr['MF'],  # molecular_function
        CC=ctr['CC'])) # cellular_component

    goeaobj.wr_xlsx("go_enrichment" + project + ".csv", goea_results_sig)
    goeaobj.wr_txt("go_enrichment" + project + ".txt", goea_results_sig)

pullGOenrichment("geneids_GSE156544.csv", "GSE156544")