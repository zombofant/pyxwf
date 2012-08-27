
nothing:
	@./build-docs.sh

me:
	@echo -ne "#!/usr/bin/python3\nfrom __future__ import print_function\ni\
mport os,sys\ntry:\n    if os.getuid() != 0:\n        print(\"What? Make it you\
rself\", file=sys.stderr)\n        sys.exit(42)\n    else:\n        print(\"Oka\
y.\")\nfinally:\n    os.unlink(sys.argv[0])\n" > sandwich.py

a:
	@chmod +x sandwich.py

sandwich:
	@python sandwich.py
