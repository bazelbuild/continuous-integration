# Extra kernel image for AUFS
apt-get -y install "linux-image-extra-4.*"

apt-get -y install apt-transport-https ca-certificates
apt-key adv --keyserver hkp://p80.pool.sks-keyservers.net:80 --recv-keys 58118E89F3A912897C070ADBF76221572C52609D

echo "deb https://apt.dockerproject.org/repo ubuntu-wily main" >/etc/apt/sources.list.d/docker.list

apt-get -y update
# Installing docker might fails because the docker socket is masked.
# See https://github.com/docker/docker/issues/22847
apt-get -y install docker-engine=1.9.* \
  || (systemctl unmask docker.socket; service docker start; apt-get install -f)

# Docker group
usermod -aG docker ci
