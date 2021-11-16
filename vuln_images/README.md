## Image builder

This tools builds DigitalOcean's images for each service
with respect of its deployment config (aka `deploy.yaml`).

## How it works

Basically, this scripts just runs the packer tool (https://packer.io/) with DigitalOcean builder,
which launches a VM (aka Droplet) in DigitalOcean, installs updates, deploys your service,
shutdowns it and creates a snapshot for further copying.

## Example of deploy.yaml

Write your own `deploy.yaml` and put it to the service folder (in `services/<service-name>`).

```yaml
# Just a version of the file format. For now, it's always equal to 1.
version: 1

# Name of the service. Required field. Available as $SERVICE in some places below.
service: test

# Name of the user. Specify it if you want to create a user and a home directory for him.
# Most probably, you want.
# Available as $USERNAME in some places below.
username: test

# Scripts/commands for running on different build stages.
# If you build instructions are complicated, extract them into a separate file, and
# run it from this field, i.e.:
#
# scripts:
#   build_outside_vm: ./build.sh
# 
# Moreover, you should run your build inside prepared docker environment, because
# there we don't guarantee that compilers or other tools will be installed on the 
# building environment.
#
# All paths here are relative to the folder contains deploy.yaml, so you can write 
# ./build.sh, and it will be 
scripts:
  # First command: build_outside_vm
  # This command will be run outside the target VM. Here you can compile you code, 
  # if you don't want to deploy source codes to participants.
  build_outside_vm: make -j4
  # Second command: build_inside_vm
  # This command will be run inside the target VM. DON'T RUN YOUR SERVICE HERE,
  # only build it. Most probably, it will be single `docker-compose build --pull` command here.
  build_inside_vm: docker-compose -f /home/$USERNAME/docker-compose.yaml build --pull
  # Third command: start_one
  # As far as your docker containers should be restarted by docker daemon itself 
  # (don't forget to specify "restart: unless-stopped" in your docker-compose.yaml!),
  # here we need a command which will be run only once, at first boot of team's VM.
  start_once: docker-compose -f /home/$USERNAME/docker-compose.yaml up -d
  
# Here you have to specify files which we need to deliver to the VM.
# You can upload a single file or a complete directory. 
files:
  # Will copy all files from ./deploy/ folder to /home/$SERVICE/.
  - source: ./deploy/
    destination: /home/$USERNAME
  # Will copy all files from ./deploy/ folder to /home/$SERVICE/deploy/
  # (because there is no trailing slash in source! See https://www.packer.io/docs/provisioners/file#directory-uploads
  # for details).
  - source: ./deploy
    destination: /home/$USERNAME
  # Will copy different files into one destination.
  - sources:
      - docker-compose.yaml
      - Dockerfile
      - service.py
    destination: /home/$USERNAME
```

## How to run

1. Install packer 1.7.0 or higher: https://learn.hashicorp.com/tutorials/packer/get-started-install-cli#
2. Install Python 3.8 or higher
3. Install requirements: `pip install -Ur requirements.txt`
4. Get the API Token for Digital Ocean: https://cloud.digitalocean.com/settings/applications
5. Run `DO_API_TOKEN=<...> python build_image.py ../services/<service-name>/deploy.yaml`

You can also put you `DO_API_TOKEN` into `.env` file in following format:
```dotenv
DO_API_TOKEN=<...>
```

The tool will also update file with id's of snaphots for cloud infrastructure 
(`ansible/roles/cloud_master/files/api_srv/do_vulnimages.json`),
don't forget to commit and deploy it.