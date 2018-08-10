
def parse_properties(*properties):
    props = {}
    for property in properties:
        index = property.find('=')
        if index == -1:
            name, value = property, ''
        else:
            name, value = property[:index], property[index+1:]
        props[name] = value
    return props
