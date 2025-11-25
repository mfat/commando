Name:           commando
Version:        0.1.0
Release:        1%{?dist}
Summary:        A GNOME application for saving and running user-defined Linux commands
License:        GPL-3.0-or-later
URL:            https://github.com/commando/commando
Source0:        %{name}-%{version}.tar.gz

BuildArch:      noarch
BuildRequires:  python3-devel
BuildRequires:  python3-setuptools
BuildRequires:  python3-gobject
BuildRequires:  gtk4-devel
BuildRequires:  libadwaita-devel
BuildRequires:  vte291-devel
BuildRequires:  webkitgtk6-devel

Requires:       python3-gobject
Requires:       gtk4
Requires:       libadwaita
Requires:       vte291
Requires:       webkitgtk6

%description
Commando allows you to save and quickly execute your frequently used
Linux commands. Organize commands with customizable cards featuring
icons, colors, tags, and categories.

%prep
%setup -q

%build
python3 setup.py build

%install
python3 setup.py install --root=%{buildroot} --optimize=1

%files
%{python3_sitelib}/commando
%{_bindir}/commando
%{_datadir}/applications/com.github.commando.desktop
%{_datadir}/metainfo/com.github.commando.metainfo.xml

%changelog
* Mon Jan 01 2024 Commando Developers <dev@commando.example> - 0.1.0-1
- Initial release

