package config

import (
	parser "github.com/majestrate/configparser"
)

type WebappConfig struct {

}

func (cfg *WebappConfig) Load(s *parser.Section) error {
	return nil
}

func (cfg *WebappConfig) Save(s *parser.Section) {
	
}
