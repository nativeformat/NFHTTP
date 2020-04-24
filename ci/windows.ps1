param (
    [string]$build = "windows"
 )

Write-Host "NFHTTP build process starting..."
Write-Host $build

$ErrorActionPreference = "Stop"

try
{
	# Get python version
	$python_version = python --version
	Write-Host $python_version

	# Start virtualenv
	$virtualenv_vulcan_output = python tools/vulcan/bin/vulcan.py -v -f tools/virtualenv.vulcan -p virtualenv-15.1.0
	$virtualenv_bin = Join-Path $virtualenv_vulcan_output /virtualenv-15.1.0/virtualenv.py
	python $virtualenv_bin nfdriver_env

	& ./nfdriver_env/Scripts/activate.bat

	# Install Python Packages
	& nfdriver_env/Scripts/pip.exe install urllib3
	& nfdriver_env/Scripts/pip.exe install pyyaml
	& nfdriver_env/Scripts/pip.exe install flake8

	if($build -eq "android"){
		& nfdriver_env/Scripts/python.exe ci/androidwindows.py
	} else {
		& nfdriver_env/Scripts/python.exe ci/windows.py
	}

	if($LASTEXITCODE -ne 0){
		exit $LASTEXITCODE
	}

	& ./nfdriver_env/Scripts/deactivate.bat
}
catch
{
	echo $_.Exception|format-list -force
	exit 1
}
