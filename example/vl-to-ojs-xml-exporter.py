from VisualLibrary import VisualLibrary
from ojs.xmlgenerator import OjsXmlGenerator, Journal
from configuration.Configurator import Configurator


def main():
    configurator = Configurator()
    configurator.parse_configuration()

    ojs_xml_generator = OjsXmlGenerator(configurator)

    vl = VisualLibrary()
    items_to_process = configurator.items
    for item_id in items_to_process:
        vl_obj = vl.get_element_for_id(item_id)
        if isinstance(vl_obj, Journal):
            for volume in vl_obj.volumes:
                generate_xml(volume, ojs_xml_generator)
        else:
            generate_xml(vl_obj, ojs_xml_generator)


def generate_xml(vl_obj, ojs_xml_generator):
    print('Generating XML')
    print('Type: {vl_type}\tID: {id}'.format(vl_type=vl_obj.__class__.__name__, id=vl_obj.id))
    item_xml_generator = ojs_xml_generator.convert_vl_objecto_to_ojs_object(vl_obj)
    ojs_xml_string = item_xml_generator.generate_xml()
    print('Store to file!')
    output_file_path = './xml/{item_id}.xml'.format(item_id=vl_obj.id)
    save_xml_to_file_path(ojs_xml_string, output_file_path)


def save_xml_to_file_path(xml_string: str, file_path: str):
    with open(file_path, 'w') as ofile:
        ofile.write(xml_string)


if __name__ == '__main__':
    main()


