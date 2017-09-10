package config

import (
	parser "github.com/majestrate/configparser"
)

type DatabaseConfig struct {
	Dialect string
	Server  string
}

func (cfg *DatabaseConfig) Load(s *parser.Section) error {
	cfg.Dialect = s.Get("dialect", "mysql")
	cfg.Server = s.Get("server", "mailuser@/mailserver")
	return nil
}

func (cfg *DatabaseConfig) Save(s *parser.Section) {
	s.SetValueFor("dialect", cfg.Dialect)
	s.SetValueFor("server", cfg.Server)
}
