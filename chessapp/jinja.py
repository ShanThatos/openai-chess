from jinja2 import Environment, FileSystemLoader, select_autoescape

jinja_env = Environment(loader=FileSystemLoader("templates"), autoescape=select_autoescape())


def get_template(name: str):
    return jinja_env.get_template(name)


def get_macro(name: str):
    name, macro = name.split(":", 1)
    return getattr(get_template(name).module, macro)


def render_template(name: str, **kwargs):
    return get_template(name).render(**kwargs)


def render_macro(name: str, *args, **kwargs):
    return get_macro(name)(*args, **kwargs)
