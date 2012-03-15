PYTHON=`which python`
DESTDIR=/
PROJECT=eventbrain

all:
	@echo "make test - Run tests"
	@echo "make source - Create source package"
	@echo "make install - Install on local system"
	@echo "make buildrpm - Generate a rpm package"
	@echo "make clean - Get rid of scratch and byte files"

source:
	$(PYTHON) setup.py sdist $(COMPILE)

install:
	$(PYTHON) setup.py install --root $(DESTDIR) $(COMPILE)

buildrpm:
	$(PYTHON) setup.py bdist_rpm --post-install=rpm/postinstall --pre-uninstall=rpm/preuninstall

test:
	$(PYTHON) setup.py nosetests

clean:
	$(PYTHON) setup.py clean
	rm -rf build/ MANIFEST
	find . -name '*.py[oc]' -delete

