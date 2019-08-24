from Jumpscale import j
import pytoml

# import toml

from .SerializerBase import SerializerBase

testtemplate = """
name = ''

multiline = ''

nr = 0
nr2 = 0
nr3 = 0
nr4 = 0.0
nr5 = 0.0

bbool = true
bbool2 = true
bbool3 = true

list1 = [ ]
list2 = [ ]
list3 = [ ]
list4 = [ ]
list5 = [ ]

"""

testtoml = """
name = 'something'

multiline = '''
    these are multiple lines
    next line
    '''

nr = 87
nr2 = ""
nr3 = "1"
nr4 = "34.4"
nr5 = 34.4

bbool = 1
bbool2 = true
bbool3 = 0

list1 = "4,1,2,3"
list2 = [ 3, 1, 2, 3 ]
list3 = [ "a", " b ", "   c  " ]
list4 = [ "ab" ]
list5 = "d,a,a,b,c"

"""


class SerializerTOML(SerializerBase):
    def __init__(self):
        SerializerBase.__init__(self)

    def fancydumps(self, obj, secure=False):
        """
        if secure then will look for key's ending with _ and will use your secret key to encrypt (see nacl client)
        """

        if not j.data.types.dict.check(obj):
            raise j.exceptions.Input("need to be dict")

        keys = [item for item in obj.keys()]
        keys.sort()

        out = ""
        prefix = ""
        lastprefix = ""
        for key in keys:

            val = obj[key]

            # get some vertical spaces between groups which are not equal
            if "." in key:
                prefix, key.split(".", 1)
            # elif "_" in key:
            #     prefix, key.split("_", 1)
            else:
                prefix = key[0:6]

            if prefix != lastprefix:
                out += "\n"
                # print("PREFIXCHANGE:%s:%s" % (prefix, lastprefix))
                lastprefix = prefix
            # else:
            # print("PREFIXNOCHANGE:%s:%s" % (prefix, lastprefix))

            ttype = j.data.types.type_detect(val)
            if secure and key.endswith("_") and ttype.BASETYPE == "string":
                val = j.data.nacl.default.encryptSymmetric(val, hex=True, salt=val)

            out += "%s\n" % (ttype.toml_string_get(val, key=key))

            # else:
            #     raise j.exceptions.Base("error in fancydumps for %s in %s"%(key,obj))

        out = out.replace("\n\n\n", "\n\n")

        return j.core.text.strip(out)

    def dumps(self, obj):
        try:
            return pytoml.dumps(obj, sort_keys=True)
        except Exception as e:
            raise j.exceptions.Value("Toml serialization failed", data=obj, exception=e)

    def loads(self, s, secure=False):
        if isinstance(s, bytes):
            s = s.decode("utf-8")
        if not isinstance(s, str):
            raise j.exceptions.Value("Toml deserialization failed, input needs to be str or bytes", data=s)
        try:
            val = pytoml.loads(s)
        except Exception as e:
            raise j.exceptions.Value("Toml deserialization failed", data=s, exception=e)
        if secure and j.data.types.dict.check(val):
            res = {}
            for key, item in val.items():
                if key.endswith("_"):
                    res[key] = j.data.nacl.default.decryptSymmetric(item, hex=True).decode()
            val = res
        return val

    def merge(
        self,
        tomlsource,
        tomlupdate,
        keys_replace={},
        add_non_exist=False,
        die=True,
        errors=[],
        listunique=False,
        listsort=True,
        liststrip=True,
    ):
        """
        the values of the tomlupdate will be applied on tomlsource (are strings or dicts)

        @param add_non_exist, if False then will die if there is a value in the dictupdate which is not in the dictsource
        @param keys_replace, key = key to replace with value in the dictsource (which will be the result)
        @param if die=False then will return errors, the list has the keys which were in dictupdate but not in dictsource

        listsort means that items in list will be sorted (list at level 1 under dict)

        @return dict,errors

        """
        if j.data.types.string.check(tomlsource):
            try:
                dictsource = self.loads(tomlsource)
            except Exception:
                raise j.exceptions.Value("toml file source is not properly formatted.", data=tomlsource)
        else:
            dictsource = tomlsource
        if j.data.types.string.check(tomlupdate):
            try:
                dictupdate = self.loads(tomlupdate)
            except Exception:
                raise j.exceptions.Value("toml file source is not properly formatted.", data=tomlupdate)
        else:
            dictupdate = tomlupdate

        return j.data.serializers.dict.merge(
            dictsource,
            dictupdate,
            keys_replace=keys_replace,
            add_non_exist=add_non_exist,
            die=die,
            errors=errors,
            listunique=listunique,
            listsort=listsort,
            liststrip=liststrip,
        )

    def test(self):
        """
        kosmos 'j.data.serializers.toml.test()'
        """

        ddict = self.loads(testtoml)
        template = self.loads(testtemplate)

        ddictout, errors = self.merge(template, ddict, listunique=True)

        ddicttest = {
            "name": "something",
            "multiline": "these are multiple lines\nnext line\n",
            "nr": 87,
            "nr2": 0,
            "nr3": 1,
            "nr4": 34.4,
            "nr5": 34.4,
            "bbool": True,
            "bbool2": True,
            "bbool3": False,
            "list1": ["1", "2", "3", "4"],
            "list2": [1, 2, 3],
            "list3": ["a", "b", "c"],
            "list4": ["ab"],
            "list5": ["a", "b", "c", "d"],
        }

        self._log_debug(ddictout)

        assert ddictout == ddicttest

        ddictmerge = {"nr": 88}

        # start from previous one, update
        ddictout, errors = self.merge(ddicttest, ddictmerge, listunique=True)

        ddicttest = {
            "name": "something",
            "multiline": "these are multiple lines\nnext line\n",
            "nr": 88,
            "nr2": 0,
            "nr3": 1,
            "nr4": 34.4,
            "nr5": 34.4,
            "bbool": True,
            "bbool2": True,
            "bbool3": False,
            "list1": ["1", "2", "3", "4"],
            "list2": [1, 2, 3],
            "list3": ["a", "b", "c"],
            "list4": ["ab"],
            "list5": ["a", "b", "c", "d"],
        }

        assert ddictout == ddicttest

        ddictmerge = {"nr_nonexist": 88}

        # needs to throw error
        try:
            error = 0
            ddictout, errors = self.merge(ddicttest, ddictmerge, listunique=True)
        except:
            error = 1
        assert 1

        ddictmerge = {}
        ddictmerge["list1"] = []
        for i in range(20):
            ddictmerge["list1"].append("this is a test %s" % i)
        ddictout, errors = self.merge(ddicttest, ddictmerge, listunique=True)

        yyaml = self.fancydumps(ddictout)
        self._log_debug(yyaml)

        compare = {
            "bbool": True,
            "bbool2": True,
            "bbool3": False,
            "list1": [
                "this is a test 0",
                "this is a test 1",
                "this is a test 10",
                "this is a test 11",
                "this is a test 12",
                "this is a test 13",
                "this is a test 14",
                "this is a test 15",
                "this is a test 16",
                "this is a test 17",
                "this is a test 18",
                "this is a test 19",
                "this is a test 2",
                "this is a test 3",
                "this is a test 4",
                "this is a test 5",
                "this is a test 6",
                "this is a test 7",
                "this is a test 8",
                "this is a test 9",
            ],
            "list2": [1, 2, 3],
            "list3": ["a", "b", "c"],
            "list4": ["ab"],
            "list5": ["a", "b", "c", "d"],
            "multiline": "    these are multiple lines\n    next line\n    ",
            "name": "something",
            "nr": 88,
            "nr2": 0,
            "nr3": 1,
            "nr4": 34.4,
            "nr5": 34.4,
        }

        res = self.loads(yyaml)

        assert res == compare

        template = {
            "login": "",
            "first_name": "",
            "last_name": "",
            "locations": [],
            "companies": [],
            "departments": [],
            "languageCode": "en-us",
            "title": [],
            "description_internal": "",
            "description_public_friendly": "",
            "description_public_formal": "",
            "experience": "",
            "hobbies": "",
            "pub_ssh_key": "",
            "skype": "",
            "telegram": "",
            "itsyou_online": "",
            "reports_into": "",
            "mobile": [],
            "email": [],
            "github": "",
            "linkedin": "",
            "links": [],
        }
        toupdate = {
            "companies": ["threefold"],
            "company_id": [2],
            "departments": ["threefold:engineering", "threefold:varia"],
            "description_internal": "Researcher who develops new ideas for Threefold and creates concise explanations of difficult concepts",
            "description_public_formal": "Develops new ideas for Threefold and creates concise explanations of difficult concepts.",
            "description_public_friendly": "Virgil is a researcher and innovator who is always looking to improve the world around him both on a macro and micro scale.\n\nFor the past 11 years he has been working with new technologies, helping organizations integrate them into their existing services and create their new products.  \nHe holds a PhD in autonomous robotics, artificial intelligence and reliability.\n\nVirgil also lectures at a technical university and an academy.\n\n",
            "email": ["ilian.virgil@gmail.com", "ilian@threefold.tech"],
            "name": "virgil",
            "github": "Virgil3",
            "hobbies": "generative coding, movies, diving, languages",
            "itsyou_online": "ilian@threefold.tech",
            "languageCode": "en-us",
            "last_name": "ilian",
            "linkedin": "https://www.linkedin.com/in/ilian-virgil-342b8471",
            "links": [],
            "locations": ["bucharest"],
            "login": "",
            "mobile": ["+40721543908"],
            "pub_ssh_key": "",
            "reports_into": "Kristof",
            "skype": "ilian.virgil",
            "telegram": "@virgil_ilian",
            "title": ["Researcher"],
        }

        result, errors = self.merge(
            template, toupdate, keys_replace={"name": "first_name"}, add_non_exist=False, die=False, errors=[]
        )

        assert [("company_id", [2])] == errors
        assert "bucharest" in result["locations"]
        assert "ilian.virgil@gmail.com" in result["email"]
        assert "company_id" not in result  # should not be in
