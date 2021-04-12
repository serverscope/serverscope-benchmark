
DEB_PKGR='packaging/deb/build_deb.sh'
DEB_CHECKER='tests/general-test-deb.sh'
RPM_PKGR='packaging/rpm/build_rpm.sh'
RPM_CHECKER='tests/general-test-el7_el8.sh'

all:

rpm:
	$(RPM_PKGR)

deb:
	$(DEB_PKGR)
	cp deb_dist/python3-serverscope-benchmark*deb ./

check-rpm:
	$(RPM_CHECKER)

check-deb:
	$(DEB_CHECKER)

.PHONY: clean
clean:
	rm -rf deb_dist/ dist/ serverscope_benchmark.egg-info/ build/
	rm -f python3-serverscope-benchmark*.deb serverscope_benchmark*.tar.gz python*.noarch.rpm
