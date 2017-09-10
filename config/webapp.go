package config

import (
	parser "github.com/majestrate/configparser"
)

type WebappConfig struct {
	BindAddr string
}

func (cfg *WebappConfig) Load(s *parser.Section) error {
	cfg.BindAddr = s.Get("bind", "127.0.0.1:8080")
	return nil
}

func (cfg *WebappConfig) Save(s *parser.Section) {
	s.SetValueFor("bind", cfg.BindAddr)
}
