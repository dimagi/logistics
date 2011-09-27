from rapidsms.utils.modules import try_import

def dynamic_import(import_name):
    import_split = import_name.split('.')
    module_name = '.'.join(import_split[:-1])
    method_name = import_split[-1]

    module = try_import(module_name)
    if module is None:
        raise Exception("Module %s could not be imported." % (module_name))
    
    try:
        return getattr(module, method_name)
    except AttributeError:
        raise Exception("No member %s in module %s." % (method_name, module_name))

