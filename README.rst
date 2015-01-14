Lumper
======

Distributed building system for docker. Will pull repo from the github by tag-webhook and build it by Dockerfile.

Features
--------

#. Distributed system. Any part might be working on different hosts.
#. Email notifications (success and errors).
#. Pushing into public or private docker registry.
#. Building in queue.
#. Emailing reports to administrator about exceptions.
#. TLS client auth for docker daemon.
#. SMTP authentication
#. Building by webhook tag from github (*You might be author of the extension for other services through pull-request ;-)*.
#. Multiple installations (thanks to RMQ vhosts)

Requirements
------------

* Python >=2.7 (>3.4 need testing).
* RabbitMQ server. Provide communication for components.


Parts
-----

The system consists of 3 parts

* WEB Server. Based on tornado http server for accepting webhooks
* Worker. Building daemon listen AMQP
* Mailer. Mailing daemon. Provides notifying about build results.


Installation
------------

#. Install Rabbitmq Server
#. pip install lumper

Usage
-----

The lumper provides one executable file **lumper**. You might run this with option --help (or -h)::

    $ lumper --help
    usage: lumper [-h] {server,worker,mailer} ...

    positional arguments:
      {server,worker,mailer}
        server              Run http backend
        worker              Run in worker mode
        mailer              Run as mailer delivery worker

    optional arguments:
      -h, --help            show this help message and exit

    Notice: exec "lumper <command> --help" for command options


Command line configuration
++++++++++++++++++++++++++

And you might see help about any modes. For web server::

    $ lumper server --help
    usage: lumper server [-h] [--config CONFIG] [--gen-config] [-a ADDRESS]
                         [-p PORT] [--secret COOKIE_SECRET] [--gzip] [--debug]
                         [--logging LOGGING] [--github-secret GITHUB_SECRET]
                         [-A RMQ_ADDRESS] [-P RMQ_PORT] [-H RMQ_VHOST]
                         [--user RMQ_USER] [--password RMQ_PASSWORD]

    optional arguments:
      -h, --help            show this help message and exit
      --config CONFIG       Load configuration from file
      --gen-config          Create example of the config_file.json

    Server options:
      -a ADDRESS, --address ADDRESS
                            Listen this address
      -p PORT, --port PORT  Listen this port
      --secret COOKIE_SECRET
                            Cookie secret
      --gzip                Gzip HTTP responses
      --debug               Debugging mode
      --logging LOGGING     Logging level
      --github-secret GITHUB_SECRET
                            Github webhook's secret
      -A RMQ_ADDRESS, --rmq-address RMQ_ADDRESS
                            RMQ host address
      -P RMQ_PORT, --rmq-port RMQ_PORT
                            RMQ host port
      -H RMQ_VHOST, --vhost RMQ_VHOST
                            RMQ virtual host
      --user RMQ_USER       RMQ virtual host
      --password RMQ_PASSWORD
                            RMQ virtual host


For worker::

    $ lumper worker --help
    usage: lumper worker [-h] [--config CONFIG] [--gen-config] [--logging LOGGING]
                         [-a AMQP_ADDRESS] [-p AMQP_PORT] [-H AMQP_VHOST]
                         [-U AMQP_USER] [-P AMQP_PASSWORD]
                         [--docker-url DOCKER_URL] [--docker-tls]
                         [--docker-ca DOCKER_CA_CERT]
                         [--docker-cert DOCKER_CLIENT_CERT]
                         [--docker-key DOCKER_CLIENT_KEY] [--docker-tls-strict]
                         [--docker-registry DOCKER_REGISTRY]
                         [--docker-ssl-registry] [--docker-publish]

    optional arguments:
      -h, --help            show this help message and exit
      --config CONFIG       Load configuration from file
      --gen-config          Create example of the config_file.json

    Main options:
      --logging LOGGING     Logging level

    RabbitMQ options:
      -a AMQP_ADDRESS, --address AMQP_ADDRESS
                            RMQ host address
      -p AMQP_PORT, --port AMQP_PORT
                            RMQ host port
      -H AMQP_VHOST, --vhost AMQP_VHOST
                            RMQ virtual host
      -U AMQP_USER, --user AMQP_USER
                            RMQ username
      -P AMQP_PASSWORD, --password AMQP_PASSWORD
                            RMQ password

    Docker options:
      --docker-url DOCKER_URL
                            Docker daemon url ["unix:///var/run/docker.sock"]
      --docker-tls          Set when a docker daemon use TLS
      --docker-ca DOCKER_CA_CERT
                            TLS certificate authority
      --docker-cert DOCKER_CLIENT_CERT
                            TLS client certificate
      --docker-key DOCKER_CLIENT_KEY
                            TLS client private key
      --docker-tls-strict   Strict verification server certificate
      --docker-registry DOCKER_REGISTRY
                            Set if you have a private registry
      --docker-ssl-registry
                            The private registry use ssl
      --docker-publish      Set if you want push images to registry

And for mailer::

    $ lumper mailer --help
    usage: lumper mailer [-h] [--config CONFIG] [--gen-config] [--logging LOGGING]
                         [-a AMQP_ADDRESS] [-p AMQP_PORT] [-H AMQP_VHOST]
                         [-U AMQP_USER] [-P AMQP_PASSWORD] [--smtp-host SMTP_HOST]
                         [--smtp-port SMTP_PORT] [--smtp-user SMTP_USER]
                         [--smtp-password SMTP_PASSWORD] [--smtp-tls]
                         [--smtp-sender SMTP_SENDER] [--mail-map MAIL_MAP]
                         [--admin-mail ADMIN_MAIL]

    optional arguments:
      -h, --help            show this help message and exit
      --config CONFIG       Load configuration from file
      --gen-config          Create example of the config_file.json

    Main options:
      --logging LOGGING     Logging level

    RabbitMQ options:
      -a AMQP_ADDRESS, --address AMQP_ADDRESS
                            RMQ host address
      -p AMQP_PORT, --port AMQP_PORT
                            RMQ host port
      -H AMQP_VHOST, --vhost AMQP_VHOST
                            RMQ virtual host
      -U AMQP_USER, --user AMQP_USER
                            RMQ username
      -P AMQP_PASSWORD, --password AMQP_PASSWORD
                            RMQ password

    SMTP options:
      --smtp-host SMTP_HOST
                            Server host
      --smtp-port SMTP_PORT
                            Server port
      --smtp-user SMTP_USER
                            Authentication username. Do auth if set.
      --smtp-password SMTP_PASSWORD
                            Password.
      --smtp-tls            Use TLS.
      --smtp-sender SMTP_SENDER
                            Sender of messages [default: lumper@localhost]

    Delivery options:
      --mail-map MAIL_MAP   github user to E-mail map json file with hash.
      --admin-mail ADMIN_MAIL
                            admin email for unknown users [default: root@localhost]


Config files
++++++++++++

You might generate and save configuration from the command line::

    $ lumper mailer --gen-conf
    {
     "admin_mail": "root@localhost",
     "amqp_address": "localhost",
     "amqp_password": null,
     "amqp_port": 5672,
     "amqp_user": null,
     "amqp_vhost": "/",
     "logging": null,
     "mail_map": null,
     "smtp_host": "localhost",
     "smtp_password": null,
     "smtp_port": 25,
     "smtp_sender": "lumper@localhost",
     "smtp_tls": false,
     "smtp_user": null
    }

And load it with --config option. E.g **lumper mailer --config /etc/lumper/mailer.json**

And convert your command line to config-file::

    $ lumper mailer --smtp-host mail.google.com --gen-conf
    {
     ...
     "smtp_host": "mail.google.com",
     ...
    }

Notice: **Option --gen-conf must be defined in the end.**
