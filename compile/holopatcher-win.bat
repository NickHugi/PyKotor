pyinstaller ../toolset/__main__.py --workpath "./toolset-build" -n "HoloPatcher" -F -w -p "../scripts/holopatcher" --exclude-module numpy --exclude-module PyQt5 --exclude-module PIL --exclude-module matplotlib --exclude-module multiprocessing --exclude-module PyOpenGL --exclude-module PyGLM

rm *.spec