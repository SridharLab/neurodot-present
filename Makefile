develop:
	python setup.py develop
clean:
	rm -f $$(find . | grep "~$$") 
	rm -f $$(find . | grep "[.]pyc$$") 
