#!/usr/bin/env python3.6

import email
import smtpd
import asyncore
import smtplib
import traceback
import configparser
import traceback
import sys
import os
import sqlalchemy

unquote = lambda s : s.replace('\'', '').replace('\"', '')

class FilterServer(smtpd.SMTPServer):

    filterMail = None
    
    def process_message(self, peer, mailfrom, rcpttos, data):
        """
        process a mail message
        """
        mailfrom = unquote(mailfrom)
        recips = list()
        for recip in rcpttos:
            recips.append(unquote(recip))

        try:
            msg = mail.message_from_bytes(data)
        except:
            print("failed to parse mail message")
            print(traceback.format_exc())
        else:
            if self.filterMail:
                msg = self.filterMail(msg)
            if msg:
                self.try_inject(mailfrom, recips, msg.as_bytes())
            else:
                print("message from {} dropped".format(mailfrom))
                

    def try_inject(self, mailfrom, rpttos, data):
        """
        try injecting mail back into postfix
        """
        try:
            mail = smtplib.SMTP("localhost", 10026)
            mail.sendmail(mailfrom, rpttos, data)
            mail.quit()
        except:
            print("try_inject(): {}".format(traceback.format_exc()))


def filterMail(msg):
    """
    do actual mail filtering
    """
    return msg

def main(args):
    fnames = ["/etc/bote-proxy.ini", "bote-proxy.ini"]
    if len(args) > 0:
        fnames = args
    fname = None
    for f in fnames:
        print("checking for config file: {}".format(f))
        if os.path.exists(f):
            fname = f
            break
    else:
        print("no config found, exiting")
        return
    cfg = configparser.ConfigParser()
    try:
        print("reading config file {}".format(fname))
        cfg.read(fname)
    except:
        print("failed to read config file {}: {}".format(fname, traceback.format_exc()))
        return
        
    print("filter server starting up")
    server = FilterServer(('127.0.0.1', 10025), None)
    asyncore.loop()
    
if __name__ == "__main__":
    main(sys.argv[1:])

