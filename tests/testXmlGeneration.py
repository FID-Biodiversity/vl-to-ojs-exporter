from configuration.Configurator import Configurator
from VisualLibary import VisualLibrary
from ojs.xmlgenerator import OjsXmlGenerator


class TestXmlGeneration:
    def test_issue_xml_generation(self):
        configurator = Configurator()
        vl = VisualLibrary()

        item_id = '10802368'
        vl_item = vl.get_element_for_id(item_id)

        ojs_xml_generator = OjsXmlGenerator()
        issue_xml = ojs_xml_generator.get_xml_from_vl_object(vl_item)


