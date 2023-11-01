#!/usr/bin/env python3
"""
Main nmealogging command line daemon
Authors: Roelof Rietbroek
Nov 2022
"""

from gnssr_raspberry.gnssr import GNSSRconfig
import asyncio
import argparse
import sys
import signal

def main(argv):
    usage="GNSSR nmea logging and upload daemon"
    parser = argparse.ArgumentParser(description=usage)
    
    parser.add_argument('config',metavar="Configuration file",type=str,nargs="?",
            help="Specify configuration file to use (default ${HOME}/nmeaconfig.yml)")

    parser.add_argument('-s','--simulate',action='store_true',
            help="Simulate some nmea messages on a fake serial port (allows testing on non gnss-enabled platforms)")
    parser.add_argument('-n','--noupload',action='store_true',
            help="Don't attempt to upload any logs")
    args=parser.parse_args(argv[1:]) 



    gnssr=GNSSRconfig(args.config,args.simulate,args.noupload)
    # register graceful killing of logging routine
    signal.signal(signal.SIGINT, gnssr.stopLoggingDaemon)
    signal.signal(signal.SIGTERM, gnssr.stopLoggingDaemon)

    asyncio.run(gnssr.startLoggingDaemon())


if __name__ == "__main__":
    main(sys.argv)
