%define _disable_lto 1
%define _disable_ld_no_undefined 1

%define _libexecdir %_prefix/libexec
%global _localstatedir %_var
#define _userunitdir /usr/lib/systemd/user/

Name: zfs
Version: 0.8.3
Release: 1
Summary: ZFS on Linux
License: CDDL
Group: System/Kernel and hardware
URL: http://zfsonlinux.org/
Source0: https://github.com/zfsonlinux/zfs/releases/download/%{name}-%{version}/%{name}-%{version}.tar.gz
Patch1: zfs-0.7.13-import-by-disk-id.patch

BuildRequires: pkgconfig(blkid)
BuildRequires: pkgconfig(libssl)
BuildRequires: pkgconfig(udev) 
BuildRequires: pkgconfig(uuid)
BuildRequires: pkgconfig(python)
BuildRequires: python3dist(setuptools)
BuildRequires: pkgconfig(zlib)
BuildRequires: pkgconfig(libtirpc)
BuildRequires: pkgconfig(libsystemd)

Conflicts: fuse-zfs

%description
This package contains the ZFS command line utilities

%package utils
Summary: Native OpenZFS management utilities for Linux
Group: System/Kernel and hardware
Provides: spl-utils = %version-%release splat = %version-%release
Obsoletes: spl-utils < %version-%release

%description utils
This package provides the zpool and zfs commands that are used to
manage OpenZFS filesystems.

%package zed
Summary: OpenZFS Event Daemon
Group: System/Kernel and hardware

%description zed
This package adds OpenZFS to the system initramfs with a hook
for the initramfs-tools infrastructure.

%package -n lib%name
Summary: ZFS shared libraries
Group: System/Libraries

%description -n lib%name
This package contains ZFS shared libraries.

%package -n lib%name-devel
Summary: ZFS development files
Group: Development/C

%description -n lib%name-devel
This package contains ZFS development files.

%package -n kernel-source-%name
Summary: ZFS modules sources for Linux kernel
Group: Development/Kernel
BuildArch: noarch
Provides: kernel-src-%name = %version-%release

%description -n kernel-source-%name
This package contains ZFS modules sources for Linux kernel.

%prep
%setup -q
%patch1 -p1
sed -i 's|datarootdir|libdir|' lib/libzfs/Makefile.am

%build
export CC=gcc
export CXX=g++
#autoreconf
%configure \
	--sbindir=/sbin \
	--libexecdir=%_libexecdir \
	--with-config=user \
	--with-udevdir=/lib/udev \
	--with-udevruledir=%_udevrulesdir \
	--enable-systemd \
	--with-systemdunitdir=%_unitdir \
	--with-systemdpresetdir=%_unitdir-preset \
	--disable-sysvinit \
	--with-gnu-ld \
	--disable-static
%make_build

%install
%make DESTDIR=%buildroot pkgdatadir=%_datadir/doc/%name-utils-%version/examples modulesloaddir=%_sysconfdir/modules-load.d install
install -pDm0644 %SOURCE0 %kernel_srcdir/%name-%version.tar
gzip %kernel_srcdir/%name-%version.tar
mkdir -p %buildroot/%_lib
for f in %buildroot%_libdir/lib*.so; do
	t=$(readlink "$f")
	ln -sf ../../%_lib/"$t" "$f"
done
mv %buildroot%_libdir/lib*.so.* %buildroot/%_lib/

install -m0644 COPYRIGHT LICENSE %buildroot%_datadir/doc/%name-utils-%version/

touch %buildroot%_sysconfdir/%name/zpool.cache
mkdir -p %buildroot%_sysconfdir/{modprobe.d,dfs}
touch %buildroot%_sysconfdir/dfs/sharetab
cat << __EOF__ > %buildroot%_sysconfdir/modprobe.d/zfs.conf
#options zfs zfs_autoimport_disable=0
__EOF__

rm -fr %buildroot%_datadir/zfs

%post utils
if [ $1 -eq 1 ] ; then
	/sbin/systemctl preset \
		zfs-import-cache.service \
		zfs-import-scan.service \
		zfs-mount.service \
		zfs-import.target \
		zfs.target \
		>/dev/null 2>&1 || :
fi

%preun utils
if [ $1 -eq 0 ] ; then
	/sbin/systemctl disable \
		zfs-import-cache.service \
		zfs-import-scan.service \
		zfs-mount.service \
		zfs-import.target \
		zfs.target \
		>/dev/null 2>&1 || :
fi

%post zed
if [ $1 -eq 1 ] ; then
	/sbin/systemctl preset \
		zfs-zed.service \
		>/dev/null 2>&1 || :
fi

%preun zed
if [ $1 -eq 0 ] ; then
	/sbin/systemctl disable \
		zfs-zed.service \
		>/dev/null 2>&1 || :
fi

%files utils
%{_datadir}/doc/%name-utils-%version
%dir %{_sysconfdir}/%name
%{_sysconfdir}/sudoers.d/zfs
%{_sysconfdir}/sysconfig/zfs
%{_sysconfdir}/zfs/vdev_id.conf*
%ghost %{_sysconfdir}/%name/zpool.cache
%dir %{_sysconfdir}/dfs
%ghost %{_sysconfdir}/dfs/sharetab
%exclude %{_unitdir}/zfs-zed.service
%config(noreplace) %{_sysconfdir}/modprobe.d/zfs.conf
%{_sysconfdir}/modules-load.d/%name.conf
%{_sysconfdir}/zfs/zfs-functions
%{_sysconfdir}/zfs/zpool.d*
%{_unitdir}/*.service
%{_unitdir}/*.target
/lib/systemd/system-preset/50-zfs.preset
/lib/udev/*_id
%{_udevrulesdir}/*.rules
/usr/lib/dracut/modules.d/*
 /usr/lib/systemd/system-generators/zfs-mount-generator
%exclude /sbin/zed
/sbin/*
%{_bindir}/*
%{_datadir}/initramfs-tools/*
%{_mandir}/man1/*
%{_mandir}/man5/*
%{_mandir}/man8/*

#_man1dir/*.1*
#_man5dir/*.5*
#_man8dir/*.8*
%exclude %{_mandir}/man8/zed.8.*

%files zed
%dir %{_sysconfdir}/%name/zed.d
%{_sysconfdir}/%name/zed.d*
%{_unitdir}/zfs-zed.service
/sbin/zed
%{_libexecdir}/zfs
%{_mandir}/man8/zed.8*

%files -n lib%name
/%{_lib}/*.so.*

%files -n lib%name-devel
%{_includedir}/*
%{_libdir}/pkgconfig/libzfs.pc
%{_libdir}/pkgconfig/libzfs_core.pc
%{_libdir}/*.so

%files -n kernel-source-%name
#_usrsrc/kernel
