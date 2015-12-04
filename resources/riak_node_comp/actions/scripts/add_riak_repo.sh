#!/bin/bash

unknown_os ()
{
  echo "Unfortunately, your operating system distribution and version are not supported by this script."
  echo "Please email support@packagecloud.io and we will be happy to help."
  exit 1
}

curl_check ()
{
  echo "Checking for curl..."
  if command -v curl > /dev/null; then
    echo "Detected curl..."
  else
    echo "Installing curl..."
    apt-get install -q -y curl
  fi
}

os=
dist=
host=

get_hostname ()
{
  echo "Getting the hostname of this machine..."

  host=`hostname -f 2>/dev/null`
  if [ "$host" = "" ]; then
    host=`hostname 2>/dev/null`
    if [ "$host" = "" ]; then
      host=$HOSTNAME
    fi
  fi

  if [ "$host" = "" -o "$host" = "(none)" ]; then
    echo "Unable to determine the hostname of your system!"
    echo
    echo "Please consult the documentation for your system. The files you need "
    echo "to modify to do this vary between Linux distribution and version."
    echo
    exit 1
  fi

  echo "Found hostname: ${host}"
}


# some systems dont have lsb-release yet have the lsb_release binary and
# vice-versa
if [ -e /etc/lsb-release ]; then
  . /etc/lsb-release
  os=${DISTRIB_ID}
  dist=${DISTRIB_CODENAME}

  if [ -z "$dist" ]; then
    dist=${DISTRIB_RELEASE}
  fi

elif [ `which lsb_release 2>/dev/null` ]; then
  dist=`lsb_release -c | cut -f2`
  os=`lsb_release -i | cut -f2 | awk '{ print tolower($1) }'`

elif [ -e /etc/debian_version ]; then
  # some Debians have jessie/sid in their /etc/debian_version
  # while others have '6.0.7'
  os=`cat /etc/issue | head -1 | awk '{ print tolower($1) }'`
  if grep -q '/' /etc/debian_version; then
    dist=`cut --delimiter='/' -f1 /etc/debian_version`
  else
    dist=`cut --delimiter='.' -f1 /etc/debian_version`
  fi

else
  unknown_os
fi

if [ -z "$dist" ]; then
  unknown_os
fi

echo "Detected operating system as $os/$dist."

curl_check

echo -n "Installing apt-transport-https... "

# install apt-https-transport
apt-get install -y apt-transport-https &> /dev/null

echo "done."

get_hostname

apt_source_path="/etc/apt/sources.list.d/basho_riak.list"
apt_config_url="https://packagecloud.io/install/repositories/basho/riak/config_file.list?os=${os}&dist=${dist}&name=${host}&source=script"

echo -n "Installing $apt_source_path..."

# create an apt config file for this repository
curl -f "${apt_config_url}" > $apt_source_path
curl_exit_code=$?

if [ "$curl_exit_code" = "22" ]; then
  echo -n "Unable to download repo config from: "
  echo "${apt_config_url}"
  echo
  echo "Please contact support@packagecloud.io and report this."
  [ -e $apt_source_path ] && rm $apt_source_path
  exit 1
elif [ "$curl_exit_code" = "35" ]; then
  echo "curl is unable to connect to packagecloud.io over TLS when running: "
  echo "    curl ${apt_config_url}"
  echo "This is usually due to one of two things:"
  echo
  echo " 1.) Missing CA root certificates (make sure the ca-certificates package is installed)"
  echo " 2.) An old version of libssl. Try upgrading libssl on your system to a more recent version"
  echo
  echo "Contact support@packagecloud.io with information about your system for help."
  [ -e $apt_source_path ] && rm $apt_source_path
  exit 1
elif [ "$curl_exit_code" -gt "0" ]; then
  echo
  echo "Unable to run: "
  echo "    curl ${apt_config_url}"
  echo
  echo "Double check your curl installation and try again."
  [ -e $apt_source_path ] && rm $apt_source_path
  exit 1
else
  echo "done."
fi

echo -n "Importing packagecloud gpg key... "
# import the gpg key
curl https://packagecloud.io/gpg.key 2> /dev/null | apt-key add - &>/dev/null
echo "done."

echo -n "Running apt-get update... "
# update apt on this system
apt-get update &> /dev/null
echo "done."
