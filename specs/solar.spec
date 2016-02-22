%define name solar
%{!?version: %define version 0.3.0}
%{!?release: %define release 1}

Name: %{name}
Version: %{version}
Release: %{release}
Source0: %{name}-%{version}.tar.gz
Summary: Solar package
URL:     http://mirantis.com
License: Apache
Group: Development/Libraries
BuildRoot: %{_tmppath}/%{name}-%{version}-buildroot
Prefix: %{_prefix}
BuildRequires:  git
BuildRequires: python-setuptools
BuildRequires: python-pbr
BuildArch: noarch

Requires:    ansible
Requires:    fabric >= 1.10.2
Requires:    python
Requires:    python-bunch
# XXX to old, can raise errors!
#Requires:    python-click >= 6.2
Requires:    python-click >= 3.3
Requires:    python-dictdiffer >= 0.4.0
Requires:    python-enum34 >= 1.0.4
#Requires:    python-gevent>=1.0.2
Requires:    python-gevent >= 1.0
Requires:    python-jinja2 >= 2.7.3
#Requires:    python-jsonschema >= 2.4
Requires:    python-jsonschema >= 2.3
Requires:    python-mock
Requires:    python-networkx >= 1.10
Requires:    python-pbr
Requires:    python-ply
Requires:    python-psycopg2 >= 2.5
Requires:    python-requests
Requires:    python-six >= 1.9.0
Requires:    python-stevedore
Requires:    python-wrapt
Requires:    python-yaml
# XXX not exist in centos repos!
#Requires:    python-psycogreen
# XXX not exist in centos repos!
#Requires:    python-inflection
# XXX not exist in centos repos!
#Requires:    python-tabulate==0.7.5
# XXX not exist in centos repos!
#Requires:    python-multipledispatch==0.4.8
# XXX not exist in centos repos!
#Requires:    python-pydotplus
# XXX not exist in centos repos!
#Requires:    python-semver
# XXX not exist in centos repos!
# zerorpc doesnt consume messages with >13.0.2, need to debug
#Requires:    pyzmq==13.0.2
# XXX not exist in centos repos!
#Requires:    python-zerorpc>=0.5.2


%description
Solar is a resource manager and orchestration engine for distributed systems.

%prep
%setup -cq -n %{name}-%{version}

%build
cd %{_builddir}/%{name}-%{version} && PBR_VERSION=%{version} python setup.py build

%install
cd %{_builddir}/%{name}-%{version} && PBR_VERSION=%{version} python setup.py install --single-version-externally-managed -O1 --root=$RPM_BUILD_ROOT --record=%{_builddir}/%{name}-%{version}/INSTALLED_FILES

%clean
rm -rf $RPM_BUILD_ROOT

%files -f %{_builddir}/%{name}-%{version}/INSTALLED_FILES

