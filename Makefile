
DEB_PKGR='packaging/deb/build_deb.sh'
DEB_CHECKER='tests/general-test-deb.sh'

all:

deb:
	$(DEB_PKGR)
	cp deb_dist/python3-serverscope-benchmark*deb ./

check-deb:
	$(DEB_CHECKER)

.PHONY: clean
clean:
	rm -rf deb_dist/ dist/ serverscope_benchmark.egg-info/
	rm -f python3-serverscope-benchmark*.deb serverscope_benchmark*.tar.gz
