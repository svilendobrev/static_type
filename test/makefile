#$Id$

PY ?= python

ifndef TESTS1
TESTS1 += engine
TESTS1 += types
TESTS1 += atomary
TESTS1 += sequence
TESTS1 += forward
endif

TESTOUT ?= output
FILTERPATH ?= .
_PYTHONPATH ?= ../..

go: clean-test test

test: $(TESTS1:%=$(TESTOUT)/%.ok)
	@echo ok: $(TESTS1)
clean-test.%:
	-rm -f `find $(TESTOUT) -name \*.$*\*`

.PRECIOUS: $(TESTOUT)/%.result %.org %.tmp		#patterns same as in a rule!
#.DELETE_ON_ERROR:

$(TESTOUT)/%.result: ../types/%.py
	@[ -f $@ ] || ( mkdir -p $@ && rmdir $@ )
	PYTHONPATH=$(_PYTHONPATH) $(PY) $< > $@
#|| (rm $@ && false)
$(TESTOUT)/%.result: %.py
	@[ -f $@ ] || ( mkdir -p $@ && rmdir $@ )
	PYTHONPATH=$(_PYTHONPATH) $(PY) $< > $@
#|| (rm $@ && false)

%.org: %.result.tmp
	@[ -f $@ ] || ( read -p '$*.original inexisting. create?' -n 1 && [ "$$REPLY" = "y" ] && cp $< $@ && echo '' )
%.tmp: %
	@$(PY) $(FILTERPATH)/filter-output.py < $< >$@
#	echo -e '\n-------- test $*'
%.ok: %.result.tmp %.org
	diff -btw $+
	@touch $@
	@echo

clean-%: clean-%.ok clean-%.result
	@echo "cleaned"
rmpyc:
	find . -follow -name \*.pyc -exec rm {} \;

help:
	@echo "possible targets:"
	@echo " test"
	@echo " clean-test"
	@echo " clean-test.org: rm .org !!"
	@echo " rmpyc"

# vim:ts=4:sw=4:noexpandtab
