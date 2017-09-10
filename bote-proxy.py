#!/usr/bin/env python3.6

import email
from email.message import EmailMessage, MIMEPart
import smtpd
import asyncore
import smtplib
import traceback
import configparser
import traceback
import sys
import os
import sqlalchemy as SA
from sqlalchemy.sql import select

unquote = lambda s : s.replace('\'', '').replace('\"', '')

log = lambda s : sys.stdout.write("{}\n".format(s)) and sys.stdout.flush()

class DB:

    def __init__(self, url):
        self._engine = SA.create_engine(url)
        self._metadata = SA.MetaData()
        self._boteusers = SA.Table('boteusers', self._metadata, 
                                   SA.Column('uid', SA.Integer, primary_key=True, autoincrement=True),
                                   SA.Column('email', SA.String(100), nullable=False),
                                   SA.Column('bote_address', SA.String(512), nullable=False))
        
        self._v_domains = SA.Table('virtual_domains', self._metadata,
                                   SA.Column('id', SA.Integer, primary_key=True, autoincrement=True),
                                   SA.Column('name', SA.String(50), nullable=False))
        
        self._v_users = SA.Table('virtual_users', self._metadata,
                                 SA.Column('id', SA.Integer, primary_key=True, autoincrement=True),
                                 SA.Column('domain_id', SA.Integer, SA.ForeignKey('virtual_domains.id'), nullable=False),
                                 SA.Column('password', SA.String(106), nullable=False),
                                 SA.Column('email', SA.String(100), nullable=False))

        self._v_aliases = SA.Table('virtual_aliases', self._metadata,
                                   SA.Column('id', SA.Integer, primary_key=True, autoincrement=True),
                                   SA.Column('domain_id', SA.Integer, SA.ForeignKey('virtual_domains.id'), nullable=False),
                                   SA.Column('source', SA.String(100), nullable=False),
                                   SA.Column('destination', SA.String(100), nullable=False))

        self._metadata.create_all(self._engine)
        
    def getBoteUsers(self, recips):
        yield from select([self._boteusers.c.bote_address]).where(self._boteusers.c.email in recips).execute()

    def getLocalusers(self, recips):
        yield from select([self._v_aliases.c.destination.label('email')]).where(self._v_aliases.c.source in recips).execute()
        yield from select([self._v_users.c.email]).where(self._v_users.c.email in recips).execute()        

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
            log("processing mail from {}".format(mailfrom))
            msg = email.message_from_string(data + "\n")
            log("got message {}".format(msg))
        except:
            log("failed to parse mail message")
            log(traceback.format_exc())
            return
        
        if self.filterMail:
            newmsg = self.filterMail(msg, mailfrom, recips)
            if newmsg:
                self.try_inject(mailfrom, recips, newmsg.as_bytes())
            else:
                log("message filtered from {}".format(mailfrom))
        elif msg:
            self.try_inject(mailfrom, recips, msg.as_bytes())
        else:
            log("message from {} dropped".format(mailfrom))
                

    def try_inject(self, mailfrom, rpttos, data):
        """
        try injecting mail back into postfix
        """
        try:
            log("try injecting mail for {}".format(mailfrom))
            mail = smtplib.SMTP("localhost", 10026)
            mail.sendmail(mailfrom, rpttos, data)
            mail.quit()
        except:
            log("try_inject(): {}".format(traceback.format_exc()))

class BoteSender:

    _acceptedMimeTypes = ['multipart/encrypted']
    _filteringMimeTypes = ['text/plain']

    _bote_host = None
    _bote_port = None
    _bote_user = None
    _bote_passwd = None
    
    def __init__(self, db, cfg=None):
        self._db = db
        if cfg:
            self._bote_host = cfg['smtp_host']
            self._bote_port = cfg['smtp_port']
            self._bote_user = cfg['smtp_user']
            self._bote_passwd = cfg['smtp_password']
    
    def filterMail(self, msg, mailfrom, recips):
        """
        do actual mail filtering
        """
        botes = self.getBoteRecips(recips)
        if botes:
            localUsers = self.getLocalUsers(recips)
            newmsg = self.stripMessage(msg)
            if newmsg:
                for recip in botes:
                    self.forwardToBote(recip, newmsg)
            if localUsers:
                return msg
        else:
            log("no bote recipiants")
            # no bote recipiants
            return msg

    def getLocalUsers(self, recips):
        found = list()
        for recip in self._db.getLocalUsers(recips):
            found.append(recip[0])
        if len(found) > 0:
            return found
        
    def getBoteRecips(self, recips):
        found = list()
        for recip in self._db.getBoteUsers(recips):
            found.append(recip[0])
        if len(found) > 0:
            return found


    def stripMessage(self, msg):
        """
        strip email message of anything not encrypted
        """
        log("filtering message....")
        newmsg = EmailMessage()
        for k in msg.keys():
            newmsg[k] = msg[k]

        addedParts = 0
            
        for part in msg.walk():
            contentType = part.get_content_type().lower()
            if contentType in self._acceptedMimeTypes or (contentType in self._filteringMimeTypes and self.partIsEncrypted(part)):
                newmsg.attach(part)
                addedParts += 1

        if addedParts > 0:
            log("attached {} encrypted parts".format(addedParts))
            return newmsg
        else:
            log("no encrypted parts found in message, dropping")
        
    def forwardToBote(self, recip, msg):
        """
        forward message to i2pbote
        """
        if self._bote_host and self._bote_port:
            log("forwarding bote message to {}:{}".format(self._bote_host, self._bote_port))
        else:
            log("no bote forwarding configured, not forwarding to {}".format(recip))

        

def main(args):
    fnames = ["/etc/bote-proxy.ini", "bote-proxy.ini"]
    if len(args) > 0:
        fnames = args
    fname = None
    for f in fnames:
        log("checking for config file: {}".format(f))
        if os.path.exists(f):
            fname = f
            break
    else:
        log("no config found, exiting")
        return
    cfg = configparser.ConfigParser()
    try:
        log("reading config file {}".format(fname))
        cfg.read(fname)
    except:
        log("failed to read config file {}: {}".format(fname, traceback.format_exc()))
        return
    if "database" not in cfg:
        log("no database section in configuration file. Bailing!")
        return
    if 'url' not in cfg["database"]:
        log("no database configured, set url in database section. Bailing!")
        return
    
    log("setting up database...")
    db = DB(cfg["database"]['url'])
    log("preparing bote sender...")
    sender = BoteSender(db)
    log("filter server starting up")
    server = FilterServer(('127.0.0.1', 10025), None)
    server.filterMail = sender.filterMail
    asyncore.loop()
    
if __name__ == "__main__":
    main(sys.argv[1:])

