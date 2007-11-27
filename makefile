#$Id$

go:
	$(MAKE) -C test
clean clean-test:
	$(MAKE) -C test clean-test

# vim:ts=4:sw=4:noexpandtab
