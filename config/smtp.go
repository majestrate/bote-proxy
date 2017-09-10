package config

import (
	parser "github.com/majestrate/configparser"
)

type SMTPConfig struct {
	BindAddr    string
	HostName    string
	TempMailDir string
}

func (cfg *SMTPConfig) Load(s *parser.Section) error {
	cfg.BindAddr = s.Get("bind", "127.0.0.1:2525")
	cfg.HostName = s.Get("hostname", "bote-proxy.i2p.rocks")
	cfg.TempMailDir = s.Get("maildir", "/tmp/bote-proxy")
	return nil
}

func (cfg *SMTPConfig) Save(s *parser.Section) {
	s.SetValueFor("bind", cfg.BindAddr)
	s.SetValueFor("hostname", cfg.HostName)
	s.SetValueFor("maildir", cfg.TempMailDir)
}
