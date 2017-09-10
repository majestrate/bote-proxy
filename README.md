# bote proxy

i2pbote mail proxy/filter for postfix


main.cf: 

    content_filter = scan:localhost:10025 receive_override_options = no_address_mappings

master.cf: 

     scan unix - - n - 10 smtp -o smtp_send_xforward_command=yes -o disable_mime_output_conversion=yes
         localhost:10026 inet n - n - 10 smtpd -o content_filter= -o receive_override_options=no_unknown_recipient_checks,no_header_body_checks,no_milters -o smtpd_authorized_xforward_hosts=127.0.0.0/8


