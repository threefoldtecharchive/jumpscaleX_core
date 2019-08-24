from Jumpscale import j
import pygments


class Lexers:
    def __init__(self):
        self._lexers = {}

    @property
    def _items(self):
        res = [item.lower().replace("lexer", "") for item in pygments.lexers.__all__ if item[0].upper() == item[0]]
        # res.append("toml")
        return res

    def __getattr__(self, key):
        if key.startswith("_"):
            return self.__dict__[key]
        return self.get(key)

    def get(self, key):
        key2 = key.lower().replace("lexer", "")
        if key2 not in self._lexers:

            # if key=="toml":
            #     cl=lexers.find_lexer_class('TOML')
            #     cl
            #     j.shell()

            self._lexers[key2] = pygments.lexers.get_lexer_by_name(key2)
            # for lexer in  pygments.lexers.get_all_lexers():
            #     j.shell()
            #     w
            #     if lexer[0]==key:
            #         j.shell()
            #         self._lexers[lexer[0]]=lexer[1]()
        return self._lexers[key2]

    def __dir__(self):
        return self._items

    def __setattr__(self, key, value):
        if key.startswith("_"):
            self.__dict__[key] = value
            return
        raise j.exceptions.Base("readonly")

    def __str__(self):
        out = j.core.tools.text_replace("{RED}Pygment Lexers:\n\n", colors=True)
        for item in self._items:
            out += j.core.tools.text_replace("{RED}-{RESET} %s\n" % item, colors=True)
        return out

    __repr__ = __str__


class Formatters:
    def __init__(self):
        self._formatters = {}

    @property
    def _items(self):
        return [
            item.lower().replace("formatter", "") for item in pygments.formatters.__all__ if item[0].upper() == item[0]
        ]

    def __getattr__(self, key):
        if key.startswith("_"):
            return self.__dict__[key]
        return self.get(key)

    def get(self, key):
        key2 = key.lower().replace("formatter", "")
        if key2 not in self._formatters:
            self._formatters[key2] = pygments.formatters.get_formatter_by_name(key2)
        return self._formatters[key2]

    def __dir__(self):
        return self._items

    def __setattr__(self, key, value):
        if key.startswith("_"):
            self.__dict__[key] = value
            return
        raise j.exceptions.Base("readonly")

    def __str__(self):
        out = j.core.tools.text_replace("{RED}Pygment Formatters:\n\n", colors=True)
        for item in self._items:
            out += j.core.tools.text_replace("{RED}-{RESET} %s\n" % item, colors=True)
        return out

    __repr__ = __str__


class FormattersFactory(j.baseclasses.object):
    """
    """

    __jslocation__ = "j.tools.formatters"

    def _init(self, **kwargs):
        self.lexers = Lexers()
        self.formatters = Formatters()

    def print_python(self, text, formatter="terminal"):
        C = j.core.tools.text_replace(text)
        print(pygments.highlight(C, self.lexers.get("python"), self.formatters.get(formatter)))

    def print_toml(self, text, formatter="terminal"):
        C = j.core.tools.text_replace(text)
        print(pygments.highlight(C, self.lexers.get("toml"), self.formatters.get(formatter)))

    def test(self):
        """
        kosmos 'j.tools.formatters.test()'
        :return:
        """

        j.tools.formatters.lexers.bash
        j.tools.formatters.lexers.python3
        j.tools.formatters.formatters.terminal

        C = """
        def _init(self,**kwargs):
            self.lexers = Lexers()
            self.formatters = Formatters()
            
    
        def print_python(self,text,formatter="terminal"):
            C=Tools.text_replace(text)
            print(pygments.highlight(C,self.lexers.get("python"), self.formatters.get(formatter)))
    

        """

        j.tools.formatters.print_python(C)

        print("####TOML EXAMPLE####")

        C = """
        
        title = "TOML Example"

        [owner]
        name = "Tom Preston-Werner"
        organization = "GitHub"
        bio = "GitHub Cofounder & CEO"
        dob = 1979-05-27T07:32:00Z # First class dates? Why not?
        
        [database]
        server = "192.168.1.1"
        ports = [ 8001, 8001, 8002 ]
        connection_max = 5000
        enabled = true
                
        """

        j.tools.formatters.print_toml(C)
