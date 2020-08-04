# Visual Library to OJS XML Exporter 
This package allows to call for data from the Visual Library and converts it into OJS XML. The tool can be run on any scale, i.e. journal, volume, issue, or article. The user only has to provide some basic settings and give a list of Visual Library IDs to convert.

Be aware that currently this package only takes VisualLibraryExportElements from the [visual-library](https://dev.git.ub.uni-frankfurt.de/apachzelt/visual-library) package. If you want to convert data from another source, you made need to make some changes to the code.

## Usage

```python
from VlToOjsExporter.configuration.Configurator import Configurator
from VlToOjsExporter.ojs.xmlgeneration import OjsXmlGenerator

vl = VisualLibrary()
vl_issue = vl.get_element_for_id('4177381')

configurator = Configurator()
configurator.parse_configuration('/path/to/your/config.ini')

ojs_xml_generator = OjsXmlGenerator(configurator)
ojs_issue = ojs_xml_generator.convert_vl_objecto_to_ojs_object(vl_issue)

ojs_export_xml_string = ojs_issue.generate_xml()
```

If you have a `config.ini` in your main package folder, you do not have to give the path to this file. Just call `configurator.parse_configuration()`.

Your configuration file should look like this:

```ini
[General]
# If there is a file called items.txt in the package folder, it will be taken as a list of items to process.
# If in the Process section a list in the items is given, this will have precedence.
# The given items in the file, can be comma seperated or on a single line each.
# So, this is fine:
    # item1, item2, item3
# And this is fine too:
    # item1
    # item2
    # item3
# Please, without the hashes! Only the IDs to download!
itemFile = items.txt

# This should give the languages of the OJS journal, where the final XML is read to!
# Watch out that you use double quotes (") for quoting, because single quotes cause an error...
languages = ["de_DE", "en_US"]

[Templates]
# Here are some OJS default labels. You may change them as needed. Please note, that you do not need quotations for strings, only for strings in lists! 
user_group_reference_label = Autor/in
article_text_genre_label = Artikeltext
file_uploading_ojs_user = ojs_admin
article_reference_label = ART
dummy_mail_address = dummy@mail.com

# This allows to switch between the old XML schema (pre OJS 3.2) and the new XML schema
use_pre_3_2_schema = False

# If you need to split the file (e.g. due to size), you can configure for every issue to have it's own <issues> tag.
root_every_issue_in_issues_tag = False

[Process]
# Please double quote the given IDs!
items = [
            "10812612",
            "10773114"
        ]
```

Currently you cannot iterate a journal, because a journal may contain Volumes and volumes can contain Issues. This is a nesting concept not supported by OJS. However, there are Volumes containing articles. Hence, if a Volume does not contain articles, it will throw an error.

The generated issues are set to be NOT published by default to enable metadata corrections in OJS without versioning. If you would like to do so, you have to set `published="1"` in the XML for each issue that should be published.

## Installation
To install the package call:

```shell script
source {path_to_your_virtual_environment}/bin/activate

cd vl-to-ojs-exporter
pip3 install -r requierements.txt
```

## Tests
The tests will run and also make a check against the OJS native.xsd format (with local files as of 2020-07-23 in `OJS 3.2.1.4`) to guarantee perfect OJS compatibility.

To run the tests, install the requirements and simply call:

`pytest tests/*py`

## Import to OJS
### Post-processing Data
It may occur that the produced file is too large for OJS to import it. Hence, there is the possibility to set the parameter `root_every_issue_in_issues_tag` true. Subsequently, you can split the file with `xml_split` like so:

```shell script
xml_split -c issues your-file.xml
```

This splits the given file in multiple smaller files, separated at every `issues` node.

### Import Process
#### Command-line
When importing the data into OJS, go into the directory of the journal of choice and call:

```shell script
php tools/importExport.php import path/to/your/file.xml journal-short-name ojs_admin
```

The `journal-short-name` is mostly given in the journal URL. E.g. in `https://ojs.ub.uni-frankfurt.de/decheniana/index.php/beihefte` it would be `beihefte`. The `ojs_admin` is the user uploading the file. I would make sure that the given user exists, but I don't know what happens, if not.

Additionally, you may have to check if the given file size is accepted by PHP. If not, you may have to edit the `memory_limit` parameter in the `/etc/php7/cli/php.ini`. 

#### Web-GUI
Of course, you can also upload the file via the OJS backend. Here also the `memory_limit` of PHP may stand in your way. However, in this case you need to edit `/etc/php7/apache2/php.ini`.
