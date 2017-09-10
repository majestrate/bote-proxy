package main

import (
	"github.com/majestrate/bote-proxy/config"
	"github.com/majestrate/bote-proxy/maildir"
	"github.com/majestrate/bote-proxy/smtp"
	"net"
	"os"
)

func main() {
	var conf config.Config
	fname := "bote-proxy.ini"
	if len(os.Args) == 2 {
		fname = os.Args[1]
	}
	err := conf.LoadFile(fname)

	if err != nil {
		panic(err.Error())
	}

	server := smtp.Server{
		Appname:  "bote-proxy",
		Hostname: conf.SMTP.HostName,
		MailDir:  maildir.MailDir(conf.SMTP.TempMailDir),
	}
	l, err := net.Listen("tcp", conf.SMTP.BindAddr)
	if err != nil {
		panic(err.Error())
	}
	server.Serve(l)
}
