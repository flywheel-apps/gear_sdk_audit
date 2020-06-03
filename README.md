# gear_sdk_audit

Make sure you have a decent amount of free space (~50Gb), as large docker images will likely need to be pulled onto your machine temporarily.


This code performs a gear audit on a set of instances, or on the flywheel gear exchange. 
The audit looks at docker images and records information about the gear such as version, sdk-enabled, python versions, and any pip-installed packages for each python version. 

First, the gears in a site/exchange directory are identified.  One by one, each gear is audited. 
The manifest is examined to see if an api-key is being used (indicating SDK-enabled gear). 
Then the docker image is pulled, and the environment PATH is searched for any pips.  If none are found, a generic
"pip","pip2", and "pip3" are tried, mostly for shits and giggles, but it never works
I don't think.

Then the code looks for all python versions in that image's PATH , and matches them
by version to previously mentioned pips also found in the docker image.  If a
python does not have a matching pip, then the python is skipped and no information
is stored on it.  Only pythons with pips are used so that "pip freeze" can be
called.  If there are multiple pips that match a python, all possible matches are
listed.

The python version, pip version, and pip freeze are documented along with other pieces of information. 
The resulting json file follows the following format:

```json
{
	"<Instance Name>": {
		"(gear name)": {
			"gear-name": (gear name),
			"gear-label": (gear label),
			"custom-docker-image": (Docker Image),
			"gear-version": "",
			"site": "<Instance Name>",
			"api-enabled": (True / False),
			"found-manifest": "",
			"Python_Dirs": [(List of all python directories)],
			"Pip_Dirs": [(List of all pip directories)],
			"Pythons": {
				"<Python_1>": {
					"python_dir": (Directory this python is in ),
					"python_version": (Full version of this python),
					"pips": {
						"<Pip1 associated with this python>": {
							"freeze": {
								"<package1>": "<version>",
								"<package2>": "<version>",
								...
							},
							"pip_dir": (directory this pip is at),
							"pip_version": (version of this pip
						}
								...(may be multiple pips associated with this python)
					}
				}
					...(may be multiple pythons associated with this docker image)
			}
		},
		...(may be multiple gears at this site)
	}
	...(may be multiple sites in this run)
}
```

# How to run

This gear is not fully automatic.  First decide if you want to run on instances or on the exchange.

For starters, both the instance and exchange run need a specified working directory.  
This is set using the `pwd = ` variable at the top of the code, just after the imports.  


If there is already a `exchange_master_json.json` or `instance_master_json.json` file in your working directory,
the code will attempt to load this file, and pick up where you left off.  This means that if the .json file already
has a key for the instance or exchange folder you're running on, it will skip that entirely.  This assumes that 
your .json file is up to date, and re-running would not add anything new.  If you would like to refresh the .json,
and double check all instances for any changes, set `refresh = True` in the main() function of the [instance/exchange]_audit_gears.py file.  

  
**Note:** setting `refresh = True` will overwrite any master_json.json file in the working directory (set by `pwd`).  
It's recommended that if you need to refresh your audit, move the old .json file to an archive first.


## Instance:
for instances, you must supply a "site_list.py" file.  Place this file in the same directory as your main "instance_audit_gears.py" file.file
Within this file, define a function "get_site_list", that returns a python dictionary.
This dictionary should have the names of sites you want to query, with the following format:

```python
def get_site_list():
    site_list = {'<Instance Name 1>':
                     ['<URL To Instance>',
                      '<Username On Instance>',
                      '<API Key For Instance>>'],
                 
                 '<Instance Name 2>':
                     ['<URL To Instance>',
                      '<Username On Instance>',
                      '<API Key For Instance>>'],
                 
                 '<Instance Name 3>':
                     ['<URL To Instance>',
                      '<Username On Instance>',
                      '<API Key For Instance>>']}
                      
    return(site_list)
                      
```

In this example, there are three instances.  You can list as many or as few as you want.  Each instance is given a human friendly name (<Instance Name 1,2,3>) which will be used in the json file as the key for that instance.  This name does not have to match anything from flywheel, you can use any name you'd like, as long as it will help you identify the different sites later.  
Each instance name is a key in the site_list dictionary.  The value with each key must be a list with three elements, in this order:
1. The instance url
1. Your username exactly as it appears on that instance
1. Your api key specific to that instance.  

This file is imported and called in "instance_audit_gears.py".  


## Exchange:
For the exchange, you only need to verify that the exchange repo wed address is correct (set at the top of the exchange_audit_gears.py file, just after the imports.)
This repo will automatically be downloaded to the working directory.  This one is actually fairly automatic, and as long as the directory structure of the exchange repo doesn't change, it should pretty much just work automatically. 

## Support:
Contact davidparker@flywheel.io for support issues.  Sometimes this thing feels like it's held together with duct tape and bubble gum, so there are probably some issues. 


