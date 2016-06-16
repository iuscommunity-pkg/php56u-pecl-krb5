# IUS spec file for php56u-pecl-krb5, forked from:
#
# spec file for php-pecl-krb5
#
# Copyright (c) 2014 Remi Collet
# License: CC-BY-SA
# http://creativecommons.org/licenses/by-sa/3.0/
#
# Please, preserve the changelog entries
#

%global pecl_name krb5
%global php_base  php56u
%global with_zts  0%{?__ztsphp:1}
%global ini_name  40-%{pecl_name}.ini

Summary:        Kerberos authentification extension
Name:           %{php_base}-pecl-%{pecl_name}
Version:        1.0.0
Release:        2.ius%{?dist}
License:        BSD
Group:          Development/Languages
URL:            http://pecl.php.net/package/%{pecl_name}
Source0:        http://pecl.php.net/get/%{pecl_name}-%{version}.tgz

# http://svn.php.net/viewvc?view=revision&revision=333127
Patch0:         krb5-build.patch

BuildRequires:  krb5-devel >= 1.8
BuildRequires:  pkgconfig(com_err)
BuildRequires:  %{php_base}-devel
BuildRequires:  %{php_base}-pear

Requires(post): %{php_base}-pear
Requires(postun): %{php_base}-pear
Requires:       %{php_base}(zend-abi) = %{php_zend_api}
Requires:       %{php_base}(api) = %{php_core_api}

# provide the stock and IUS names without pecl
Provides:       php-%{pecl_name} = %{version}-%{release}
Provides:       php-%{pecl_name}%{?_isa} = %{version}-%{release}
Provides:       %{php_base}-%{pecl_name} = %{version}-%{release}
Provides:       %{php_base}-%{pecl_name}%{?_isa} = %{version}-%{release}

# provide the stock and IUS names in pecl() format
Provides:       php-pecl(%{pecl_name}) = %{version}-%{release}
Provides:       php-pecl(%{pecl_name})%{?_isa} = %{version}-%{release}
Provides:       %{php_base}-pecl(%{pecl_name}) = %{version}-%{release}
Provides:       %{php_base}-pecl(%{pecl_name})%{?_isa} = %{version}-%{release}

# provide the stock name
Provides:       php-pecl-%{pecl_name} = %{version}-%{release}
Provides:       php-pecl-%{pecl_name}%{?_isa} = %{version}-%{release}

# conflict with the stock name
Conflicts:      php-pecl-%{pecl_name} < %{version}

# RPM 4.8
%{?filter_provides_in: %filter_provides_in %{_libdir}/.*\.so$}
%{?filter_provides_in: %filter_provides_in %{php_ztsextdir}/.*\.so$}
%{?filter_setup}


%description
Features:
+ An interface for maintaining credential caches (KRB5CCache),
  that can be used for authenticating against a kerberos5 realm
+ Bindings for nearly the complete GSSAPI (RFC2744)
+ The administrative interface (KADM5)
+ Support for HTTP Negotiate authentication via GSSAPI


%package devel
Summary:       Kerberos extension developer files (header)
Group:         Development/Libraries
Requires:      %{name}%{?_isa} = %{version}-%{release}
Requires:      %{php_base}-devel%{?_isa}
Conflicts:     php-pecl-%{pecl_name}-devel < %{version}
Provides:      php-pecl-%{pecl_name}-devel = %{version}-%{release}
Provides:      php-pecl-%{pecl_name}-devel%{?_isa} = %{version}-%{release}

%description devel
These are the files needed to compile programs using the Kerberos extension.


%prep
%setup -q -c
mv %{pecl_name}-%{version} NTS

cd NTS
%patch0 -p0 -b .build

# http://svn.php.net/viewvc?view=revision&revision=333126
chmod -x php_krb5_gssapi.h

# Sanity check, really often broken
extver=$(sed -n '/#define PHP_KRB5_EXT_VERSION/{s/.* "//;s/".*$//;p}' php_krb5.h)
if test "x${extver}" != "x%{version}"; then
   : Error: Upstream extension version is ${extver}, expecting %{version}.
   exit 1
fi
cd ..

%if %{with_zts}
# Duplicate source tree for NTS / ZTS build
cp -pr NTS ZTS
%endif

# Create configuration file
cat << 'EOF' | tee %{ini_name}
; Enable the '%{pecl_name}' extension module
extension=%{pecl_name}.so
EOF


%build
export CFLAGS="%{optflags} $(pkg-config --cflags com_err)"

peclbuild() {
%configure \
    --with-krb5 \
    --with-krb5config=%{_bindir}/krb5-config \
    --with-krb5kadm \
    --with-php-config=$1
%{__make} %{?_smp_mflags}
}

cd NTS
%{_bindir}/phpize
peclbuild %{_bindir}/php-config

%if %{with_zts}
cd ../ZTS
%{_bindir}/zts-phpize
peclbuild %{_bindir}/zts-php-config
%endif


%install
%{__make} -C NTS install INSTALL_ROOT=%{buildroot}
# install config file
%{__install} -D -m 644 %{ini_name} %{buildroot}%{php_inidir}/%{ini_name}

# Install XML package description
%{__install} -D -m 644 package.xml %{buildroot}%{pecl_xmldir}/%{name}.xml

%if %{with_zts}
%{__make} -C ZTS install INSTALL_ROOT=%{buildroot}
%{__install} -D -m 644 %{ini_name} %{buildroot}%{php_ztsinidir}/%{ini_name}
%endif

# Test & Documentation
for i in $(grep 'role="test"' package.xml | sed -e 's/^.*name="//;s/".*$//')
do %{__install} -Dpm 644 NTS/$i %{buildroot}%{pecl_testdir}/%{pecl_name}/$i
done
for i in $(grep 'role="doc"' package.xml | sed -e 's/^.*name="//;s/".*$//')
do %{__install} -Dpm 644 NTS/$i %{buildroot}%{pecl_docdir}/%{pecl_name}/$i
done


%check
cd NTS
: Minimal load test for NTS extension
%{__php} --no-php-ini \
    --define extension=%{buildroot}%{php_extdir}/%{pecl_name}.so \
    --modules | grep %{pecl_name}

%if %{with_zts}
cd ../ZTS
: Minimal load test for ZTS extension
%{__ztsphp} --no-php-ini \
    --define extension=%{buildroot}%{php_ztsextdir}/%{pecl_name}.so \
    --modules | grep %{pecl_name}
%endif


%post
%{pecl_install} %{pecl_xmldir}/%{name}.xml >/dev/null || :


%postun
if [ $1 -eq 0 ] ; then
    %{pecl_uninstall} %{pecl_name} >/dev/null || :
fi


%files
%doc %{pecl_docdir}/%{pecl_name}
%{pecl_xmldir}/%{name}.xml

%config(noreplace) %{php_inidir}/%{ini_name}
%{php_extdir}/%{pecl_name}.so

%if %{with_zts}
%config(noreplace) %{php_ztsinidir}/%{ini_name}
%{php_ztsextdir}/%{pecl_name}.so
%endif


%files devel
%doc %{pecl_testdir}/%{pecl_name}

%{php_incldir}/ext/%{pecl_name}

%if %{with_zts}
%{php_ztsincldir}/ext/%{pecl_name}
%endif


%changelog
* Thu Jun 16 2016 Ben Harper <ben.harper@rackspace.com> - 1.0.0-3.ius
- update filters to include zts

* Fri Oct 09 2015 Carl George <carl.george@rackspace.com> 1.0.0-2.ius
- Add provides for stock package names
- Add conflicts for the devel package
- Explictly require php56u-pear to get pecl

* Thu Oct 08 2015 Joshua M. Keyes <joshua.michael.keyes@gmail.com> 1.0.0-1.ius
- Port from Fedora to IUS

* Thu Jun 18 2015 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 1.0.0-7
- Rebuilt for https://fedoraproject.org/wiki/Fedora_23_Mass_Rebuild

* Sun Aug 17 2014 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 1.0.0-6
- Rebuilt for https://fedoraproject.org/wiki/Fedora_21_22_Mass_Rebuild

* Thu Jun 19 2014 Remi Collet <rcollet@redhat.com> - 1.0.0-5
- rebuild for https://fedoraproject.org/wiki/Changes/Php56

* Sat Jun 07 2014 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 1.0.0-4
- Rebuilt for https://fedoraproject.org/wiki/Fedora_21_Mass_Rebuild

* Wed Apr 23 2014 Remi Collet <rcollet@redhat.com> - 1.0.0-3
- add numerical prefix to extension configuration file

* Wed Mar 26 2014 Remi Collet <remi@fedoraproject.org> - 1.0.0-2
- upstream patch to fix SUCCESS definition
- enable --with-krb5kadm with all PHP versions

* Sat Mar  1 2014 Remi Collet <remi@fedoraproject.org> - 1.0.0-1
- initial package, version 1.0.0 (stable)
