package config

import (
	parser "github.com/majestrate/configparser"
)

type SMTPConfig struct {
	BindAddr string
	HostName string
	TempMailDir string
}

func (cfg *SMTPConfig) Load(s *parser.Section) error {
	return nil
}

func (cfg *SMTPConfig) Save(s *parser.Section) {
	
}

