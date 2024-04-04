PHONY: windows_dist, mac_dist, pre-commit, run

windows_dist:
	pipenv run pyinstaller --onefile --noconsole src/division_generator.py
	rmdir /Q /S build
	del /Q /F division_generator.spec

mac_dist:
	pipenv run pyinstaller --onefile --noconsole src/division_generator.py
	rmdir build
	rm -f division_generator.spec

pre-commit:
	pipenv run pre-commit install
	pipenv run pre-commit run --all-files

run:
	pipenv run python src/division_generator.py
