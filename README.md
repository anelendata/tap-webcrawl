# tap-webcrawl

Crawl web with Selenium to download a data file containing tables then
output singer.io tap compatible format.

This is a [Singer](https://singer.io) tap that produces JSON-formatted data
following the [Singer
spec](https://github.com/singer-io/getting-started/blob/master/SPEC.md).

This tap:

- Crawls the web to download a data file
- Outputs the schema for each resource
- Currently only supports Excel (.xls) file to singer tap conversion

Usage:

It's rather complicated right now. Here is an [example project](https://github.com/anelendata/edu_research_webcrawl_etl)
that you can learn from.

1. Create the spec for config file:

Example:

```
{
    "application": "Crawl some ancient web server to get the data files",
    "args": {
        "id":
        {
            "type": "string",
            "default": "01",
            "help": "This will fill the URL as https://www.example.com/some_resource/{id}"
        },
        "format":
        {
            "type": "string",
            "default": "xls",
            "help": "This will fill the URL as https://www.example.com/some_resource/01?format={format}"
        }
    }
}
```

Note: Currently, you need to create this file even if you don't want to modify the default config specs.
In such cases, please provide an empty object:

```
{}
```

The args that are reserved default can be found [default_spec.json](./tap_webcrawl/default_spec.json)

2. Generate Selenium IDE Python script

1. Install [Selenium IDE](https://www.selenium.dev/selenium-ide/) as a browswer plugin.
2. Browse web manually to complete one task
3. Export Python test script and save somewhere (keep things untitled so the class name is the default "TestDefaultSuit" and the test function is "test_untitled")
4. Edit the script to parameterize so tap can replay with different params

Hint: Refer to [the example Python](https://github.com/anelendata/edu_research_webcrawl_etl/blob/master/selenium_ide_export/nces_schools.py). This example passes URL parameter via kwargs. It also inserts with_retry() method to patiently wait for the slow web server.

3. Create Config file based on the spec:

Example:
```
{
  "datetime_key": "last_modified_at",
  "schema_dir": <path_to_schema_dir>
  "selenium_ide_script": "./selenium_ide_export/default.py"  // This Python script is from the previous step
  "id": "01" // a user defined config value to be used as a parameter for the Selenium script
}
```

4. Create schema and catalog files

```
$ tap_webcrawl spec.json --infer_schema --config config.json --schema_dir ./schema
```

4.Run the tap

```
$ tap_webcrawl spec.json --config config.json --catalog catalog.json
```

---

Copyright &copy; 2019~ Anelen Co., LLC
