.PHONY: srpm

srpm:
	dnf -y install git
	sed -i "1s/^/\%global commit $$(git rev-parse HEAD)\n/" $(spec)
	git archive --prefix=osbuild-$$(git rev-parse HEAD)/ --format=tar.gz HEAD > osbuild-$$(git rev-parse HEAD).tar.gz
	/usr/bin/rpmbuild -bs \
	  --define "_sourcedir $(CURDIR)" \
	  --define "_srcrpmdir $(outdir)" \
	  $(spec)
