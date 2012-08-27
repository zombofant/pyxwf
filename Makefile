
nothing:
	@./build-docs.sh

me:
	@echo -ne "#!/usr/bin/python3\nimport os, sys\ntry:\n    if os.getuid() != \
0:\n        print(\"What? Make it yourself\", file=sys.stderr)\n        sys.exi\
t(42)\n    else:\n        print(\"Okay.\")\nfinally:\n    os.unlink(sys.argv[0]\
)\n" > sandwich.py

a:
	@chmod +x sandwich.py

sandwich:
	@python3 sandwich.py
