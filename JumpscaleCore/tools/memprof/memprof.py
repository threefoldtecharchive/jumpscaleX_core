try:
    from objgraph import *
except ImportError:
    print("please pip install objgraph first. `python3 -m pip install objgraph`")

from Jumpscale import j


class MemProf:
    __jslocation__ = "j.tools.memprof"

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
