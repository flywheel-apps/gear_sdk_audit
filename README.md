# gear_sdk_audit

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
                      
```

In this example, there are three instances.  Each instance is given a human friendly name (<Instance Name 1,2,3>) which will be used in the json file as the key for that instance.  This name does not have to match anything from flywheel, you can use any name you'd like, as long as it will help you identify the different sites later.  
Each instance name is a key in the site_list dictionary.  The value with each key must be a list with three elements, in this order:
1. The instance url
1. Your username exactly as it appears on that instance
1. Your api key specific to that instance.  

This file is imported and called in "instance_audit_gears.py".  


## Exchange:
For the exchange, you only need to verify 


