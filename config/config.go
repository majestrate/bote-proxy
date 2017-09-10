package config

import (
	parser "github.com/majestrate/configparser"
)

type Configurable interface {
	Load(*parser.Section) error
	Save(*parser.Section)
}

type Config struct {
	SMTP SMTPConfig
	WebApp WebappConfig
}

func (cfg *Config) LoadFile(fname string) error {
	c, err := parser.Read(fname)
	if err != nil {
		return err
	}
	sects := map[string]Configurable{
		"smtp": &cfg.SMTP,
		"webapp" : &cfg.WebApp,
	}
	for name, sect := range sects {
		s, _ := c.Section(name)
		err = sect.Load(s)
		if err != nil {
			return err
		}
	}
	return nil
}
