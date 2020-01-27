try:
    from objgraph import *
    from pympler import *
    from pympler import asizeof
    from pympler import tracker
    from pympler import classtracker
except ImportError:
    print("please pip install objgraph and pympler first. `python3 -m pip install objgraph pympler`")


from Jumpscale import j


class MemProf:
    __jslocation__ = "j.tools.memprof"

    def __init__(self):
        self._tr = None

    def leak_check(self, limit=20):
        # JSX> show_most_common_types(limit=30, shortnames=False)
        # builtins.dict                                    49201
        # builtins.function                                35563
        # builtins.list                                    33720
        # builtins.tuple                                   26458
        # parso.python.tree.Operator                       15009
        # parso.python.tree.PythonNode                     10655
        # parso.python.tree.Name                           10132
        # builtins.weakref                                 8988
        # builtins.frozenset                               6933
        # Jumpscale.core.BASECLASSES.JSDict.JSDict         5908
        # parso.pgen2.generator.DFAPlan                    5205
        # builtins.type                                    4487
        # builtins.cell                                    4202
        # builtins.set                                     4165
        # builtins.getset_descriptor                       3984
        # capnp.lib.capnp._DynamicStructReader             3524
        # capnp.lib.capnp._PackedMessageReaderBytes        3524
        # builtins.property                                3394
        # prompt_toolkit.key_binding.key_bindings._Binding 3196
        # prompt_toolkit.styles.base.Attrs                 3086
        # builtins.builtin_function_or_method              2868
        # parso.python.tree.Newline                        2791
        # builtins.wrapper_descriptor                      2512
        # parso.pgen2.grammar_parser.NFAArc                2474
        # Jumpscale.data.types.List.ListObject             2280
        # parso.python.tree.Keyword                        2273
        # parso.pgen2.grammar_parser.NFAState              2180
        # parso.python.tree.Param                          2063
        # e952d0570a1f3d31c27fde7140987c9d.JSXObject2      2037
        # builtins.method_descriptor                       2020

        print("most common types in memory")
        show_most_common_types(limit=limit, shortnames=False)
        print("leaking objects stats:")
        roots = get_leaking_objects()
        print("#leaking objects: ", len(roots))  # doctest: +RANDOM_OUTPUT
        print(typestats(roots, shortnames=False))

    def refs_by_type(self, type_long_name):
        """
        JSX> roots = j.tools.memprof.refs_by_type("JSDict")
        """
        roots = by_type(type_long_name)
        return roots

    def show_roots(self, roots, filename="roots.png", **show_refs_opts):
        """
        JSX> roots = j.tools.memprof.refs_by_type("JSDict")
        JSX> j.tools.memprof.show_roots(roots[:5])
        Graph written to /tmp/objgraph-m6_fu8vm.dot (55 nodes)
        Image generated as /sandbox/code/github/roots.png.png
        """

        show_refs(
            roots,
            refcounts=True,
            shortnames=False,
            filename=f"{j.dirs.CODEDIR}/github/{filename}.png",
            **show_refs_opts,
        )

        # roots = by_type("Jumpscale.core.BASECLASSES.JSDict.JSDict")
        # show_refs(roots[:10], refcounts=True, shortnames=False, filename="/sandbox/code/github/rootsjsdict.png")

        # roots = by_type("Jumpscale.data.types.List.ListObject")
        # show_refs(roots[:10], refcounts=True, shortnames=False, filename="/sandbox/code/github/rootslistobject.png")

        # roots = by_type("JSXObject2")
        # show_refs(roots[:10], refcounts=True, shortnames=False, filename="/sandbox/code/github/rootsjsxobject2.png")

        # show_refs(roots[:6], refcounts=True, filename="/sandbox/code/github/roots.png")

    def size_of(self, obj):
        """Gets size of certain obj.

        Args:
            obj ([object])
        """
        return asizeof.asizeof(obj)

    def size_of_objs_of_type(self, type_name):
        """Gets size of objects by type_name 
        
        Args:
            type_name ([str])
        """
        return self.size_of(self.refs_by_type(type_name))

    def summary_tracker(self):
        """
        Gets a summary tracker.
        
        Example:

        JSX> st = j.tools.memprof.summary_tracker()                                                                                                                                                     
        JSX> #....                                                                                                                                                                                      
        JSX> st.print_diff()                                                                                                                                                                            
                                types |   # objects |   total size
        ============================== | =========== | ============
                                list |       19224 |      1.90 MB
                                str |       22126 |      1.51 MB
            parso.python.tree.Operator |        5731 |    537.28 KB
                                int |       13404 |    366.43 KB
        parso.python.tree.PythonNode |        5840 |    365.00 KB
                parso.python.tree.Name |        4594 |    358.91 KB
            parso.python.tree.Keyword |        1312 |    123.00 KB
            parso.python.tree.Newline |        1508 |    117.81 KB
            parso.python.tree.String |         428 |     33.44 KB
            parso.python.tree.Param |         422 |     29.67 KB
            parso.python.tree.ExprStmt |         525 |     28.71 KB
            parso.python.tree.IfStmt |         190 |     10.39 KB
            parso.python.tree.Number |         132 |     10.31 KB
            parso.python.tree.Function |         144 |     10.12 KB
                function (<lambda>) |          53 |      7.04 KB

        Returns:
            [type]: [description]
        """

        return tracker.SummaryTracker()

    def class_tracker(self):
        """Gets class tracker object.

        Example:
        >>> tr = j.tools.memprof.class_tracker()
        >>> tr.track_class(Document)
        >>> tr.create_snapshot()
        >>> create_documents()
        >>> tr.create_snapshot()
        >>> tr.stats.print_summary()
                    active      1.42 MB      average   pct
        Document     1000    195.38 KB    200     B   13%

        """

        return classtracker.ClassTracker()

    def check_schemas(self, count=1000):
        # FIXME: improve to use more complex/nested schemas
        for i in range(10):
            schema = f"""
            @url = test.jumpscale.objtest{i}
            field{i} = (I)
            field_string{i} = (S)
            """
            s = j.data.schema.get_from_text(schema_text=schema)
            for _ in range(1000):
                o = s.new()
        self.leak_check()

    def check_client_gedis(self, count=10000):
        rand_id = j.data.idgenerator.generateRandomInt(0, 100)
        for i in range(count):
            print(i)
            g = j.clients.gedis.get(name=f"_gedis_test{i}_{rand_id}")

        self.leak_check()

    def check_client_tcprouter_zos(self, count=10000):
        rand_id = j.data.idgenerator.generateRandomInt(0, 100)
        for i in range(count):
            print(i)
            tcl = j.clients.tcp_router.get(name=f"_tcl_test{rand_id}{i}")
            zos = j.clients.zos.get(name=f"_zos_test{rand_id}{i}")

        self.leak_check()

    def check_bcdb_objects(self, count=100000):
        rand_id = j.data.idgenerator.generateRandomInt(0, 100000)

        s = f"""
    @url = jumpscale.bcdb.test.house{rand_id}
    0 : name** = "" (S)
    1 : active** = "" (B)
    2 : cost** =  (N)

    """.lstrip()
        s = j.data.schema.get_from_text(schema_text=s)
        # check the right schema in meta stor
        model = j.data.bcdb.system.model_get(url=f"jumpscale.bcdb.test.house{rand_id}")
        for i in range(count):
            o = model.new()
            o.name = f"obj{i}"
            o.cost = 100
            o.active = False
        self.leak_check()
