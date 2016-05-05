import xml.etree.ElementTree as ET


class IOC(object):
    def __init__(self):
        self.file_name = 'data/ioc.xml'
        self.tree = ET.parse(self.file_name)
        self.root = self.tree.getroot()
        self.root_list = self.root.find('./list')

    def get_orders(self):
        orders = self.root_list.findall('./order')
        return [o.find('latin_name').text for o in orders]

    def get_families(self, order=None):
        if order is None or order == 'ALL':
            families = self.root_list.findall('./order/family')
        else:
            families = self.root_list.findall(
                './order[latin_name="{}"]/family'.format(order))
        return [f.find('latin_name').text for f in families]

    def get_species(self, order=None, family=None):
        result = []
        xpath = '.'
        if order is None or order == 'ALL':
            xpath += '/order'
        else:
            xpath += '/order[latin_name="{}"]'.format(order)
        if family is None or family == 'ALL':
            xpath += '/family'
        else:
            xpath += '/family[latin_name="{}"]'.format(family)
        xpath += '/genus'
        genera = self.root_list.findall(xpath)
        for genus in genera:
            genus_name = genus.find('latin_name').text
            species = genus.findall('./species')
            for sp in species:
                sp_lat_name = sp.find('latin_name').text
                sp_eng_name = sp.find('english_name').text
                result.append(
                    ('{} {}'.format(genus_name, sp_lat_name), sp_eng_name))
        return result

    def get_subspecies(self, species):
        return ['foo', 'bar']
