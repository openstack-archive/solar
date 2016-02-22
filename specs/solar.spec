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
Requires:    python-click >= 6
Requires:    python-dictdiffer >= 0.4.0
Requires:    python-enum34 >= 1.0.4
Requires:    python-gevent >= 1.0
Requires:    python-jinja2 >= 2.7.3
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
Requires:    PyYAML
Requires:    python-psycogreen
Requires:    python-pydotplus
Requires:    python-semantic_version >= 2.3.1
Requires:    python-pyzmq
Requires:    python-zerorpc >= 0.5.2


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

