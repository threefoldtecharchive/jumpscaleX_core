# memprof


## leak_check

```
JSX> j.tools.memprof.leak_check(limit=50)
most common types in memory
builtins.dict                                    24207
builtins.function                                20069
builtins.tuple                                   16448
builtins.list                                    11483
parso.pgen2.generator.DFAPlan                    5205
builtins.weakref                                 4880
builtins.frozenset                               3602
builtins.set                                     2904
builtins.cell                                    2881
builtins.type                                    2626
parso.pgen2.grammar_parser.NFAArc                2474
builtins.getset_descriptor                       2354
parso.pgen2.grammar_parser.NFAState              2180
builtins.property                                1686
prompt_toolkit.styles.base.Attrs                 1682
builtins.method_descriptor                       1602
prompt_toolkit.key_binding.key_bindings._Binding 1602
builtins.wrapper_descriptor                      1575
builtins.builtin_function_or_method              1460
builtins.module                                  870
_frozen_importlib.ModuleSpec                     852
_weakrefset.WeakSet                              787
parso.pgen2.generator.DFAState                   774
_frozen_importlib_external.SourceFileLoader      761
builtins.member_descriptor                       659
operator.itemgetter                              407
builtins.staticmethod                            340
builtins.classmethod                             330
abc.ABCMeta                                      261
collections.deque                                259
prompt_toolkit.cache.SimpleCache                 241
prompt_toolkit.filters.base._AndList             193
pygments.lexer.include                           192
inspect.Parameter                                192
builtins.cython_function_or_method               186
pkg_resources.PathMetadata                       178
pkg_resources.DistInfoDistribution               169
pkg_resources._vendor.six.MovedAttribute         166
parso.pgen2.generator.ReservedString             166
collections.OrderedDict                          162
builtins.method                                  148
collections.defaultdict                          142
builtins.mappingproxy                            138
pkg_resources.EntryPoint                         138
inspect.Signature                                136
Jumpscale.core.BASECLASSES.JSDict.JSDict         134
fakeredis._server.Signature                      134
fakeredis._server.Key                            129
_frozen_importlib_external.FileFinder            126
prompt_toolkit.layout.screen.Char                113
leaking objects stats:
#leaking objects:  1779
{'builtins.dict': 1279, 'builtins.list': 376, 'builtins.tuple': 30, 'gevent.__hub_local._Threadlocal': 1, '_ast.Load': 1, '_ast.Store': 1, '_ast.Del': 1, '_ast.AugLoad': 1, '_ast.AugStore': 1, '_ast.Param': 1, '_ast.And': 1, '_ast.Or': 1, '_ast.Add': 1, '_ast.Sub': 1, '_ast.Mult': 1, '_ast.MatMult': 1, '_ast.Div': 1, '_ast.Mod': 1, '_ast.Pow': 1, '_ast.LShift': 1, '_ast.RShift': 1, '_ast.BitOr': 1, '_ast.BitXor': 1, '_ast.BitAnd': 1, '_ast.FloorDiv': 1, '_ast.Invert': 1, '_ast.Not': 1, '_ast.UAdd': 1, '_ast.USub': 1, '_ast.Eq': 1, '_ast.NotEq': 1, '_ast.Lt': 1, '_ast.LtE': 1, '_ast.Gt': 1, '_ast.GtE': 1, '_ast.Is': 1, '_ast.IsNot': 1, '_ast.In': 1, '_ast.NotIn': 1, 'builtins.weakref': 1, 'builtins.set': 1, 'builtins.method': 21, 'builtins.frame': 8, 'builtins.builtin_function_or_method': 8, 'greenlet.greenlet': 1, 'abc.SignalDict': 6, '_cffi_backend.CTypeDescr': 5, 'psycopg2._psycopg.type': 1, '_weakrefset.WeakSet': 1, 'builtins.slice': 3, 'builtins.function': 1, 'gevent.libev.corecext.callback': 1}
JSX>


```

## generating graphs

- get references of the objects you want to graph by type using `refs_by_type`

- pass these references (or a slice of them) to `show_roots`

e.g

```
    JSX> roots = j.tools.memprof.refs_by_type("JSDict")
    JSX> j.tools.memprof.show_roots(roots[:5])
    Graph written to /tmp/objgraph-m6_fu8vm.dot (55 nodes)
    Image generated as /sandbox/code/github/roots.png.png
```

## other helpers
- `check_schemas(count=...)` creates `count` of schema objects
- `check_bcdb_objects(count=...)` creates `count` of bcdb objects
- `check_client_gedis(count=...)` creates `count` of gedis client objects
- `check_client_tcprouter(count=...)` creates `count` of tcprouter client


## to profile one of the calls
e.g
```
import cProfile

cProfile.run('j.tools.memprof.check_schemas(5000)', filename=None)
```
