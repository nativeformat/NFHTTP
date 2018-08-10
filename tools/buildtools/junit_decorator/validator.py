from lxml import etree

def main():
    # validate('testsuite-feature-mapping.xsd', 'testsuite-feature-mapping.xml')
    # validate('feature-squad-mapping.xsd', 'feature-squad-mapping.xml')
    validate('xsd/feature-squad-mapping.xsd', 'decorated-junit.xml')

def validate(schema_file_path, xml_file_path):
    schema_tree = None
    testfile_tree = None

    with open(schema_file_path, 'r') as schema_file:
        schema_tree = etree.parse(schema_file)

    schema = etree.XMLSchema(schema_tree)
    parser = etree.XMLParser(schema=schema)
    with open(xml_file_path, 'r') as testfile_file:
        try:
            testfile_tree = etree.parse(testfile_file, parser)
        except etree.XMLSyntaxError as e:
            print('[FAILURE] {} IS INVALID towards schema {}! Error was: {}'.format(xml_file_path, schema_file_path, e))
            return

    print('[OK] {} is VALID towards schema {}!'.format(xml_file_path, schema_file_path))

if __name__ == "__main__":
    main()
