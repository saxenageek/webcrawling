"""Batch Job for all Websites."""
import os
import sys
from datetime import datetime
from bd.src.crawler_mp import run

def main(argv):
    start_time = datetime.now()
    demo_flag = False
    ingressfilename = "files/Demo-Sourcing-PilotItems-10252021.xlsx"

    manufacturer_id = argv[1]
    if ingressfilename and os.path.isfile(ingressfilename):
        print("Crawling Started..")
        egressfoldername = run(ingressfilename, manufacturer_id)

        if egressfoldername:
            print("Crawling End..")
            current_timestamp = datetime.now()
            print('Crawl Time taken in minutes : ' + str(
                round((current_timestamp - start_time).total_seconds() / 60.0, 2)))
        else:
            print("No data crawled")

        current_timestamp = datetime.now()
        print('Total Processing Time taken in minutes : ' + str(
            round((current_timestamp - start_time).total_seconds() / 60.0, 2)))
    else:
        print("File doesn't exists")

if __name__=="__main__":
    main(sys.argv)
