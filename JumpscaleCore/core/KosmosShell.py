import inspect
import pudb
import sys
import time
import traceback

from functools import partial
from prompt_toolkit.application import get_app
from prompt_toolkit.buffer import Buffer
from prompt_toolkit.document import Document
from prompt_toolkit.completion import Completion
from prompt_toolkit.filters import Condition, is_done
from prompt_toolkit.formatted_text import ANSI, to_formatted_text, fragment_list_to_text
from prompt_toolkit.keys import Keys
from prompt_toolkit.layout.containers import ConditionalContainer, Window
from prompt_toolkit.layout.controls import BufferControl
from prompt_toolkit.layout.dimension import Dimension
from prompt_toolkit.layout.processors import HighlightIncrementalSearchProcessor, Processor, Transformation
from prompt_toolkit.lexers import PygmentsLexer
from prompt_toolkit.shortcuts import print_formatted_text
from ptpython.filters import ShowDocstring, PythonInputFilter
from ptpython.prompt_style import PromptStyle
from pygments.lexers import PythonLexer


HIDDEN_PREFIXES = ("_", "__")


class KosmosShellConfig:
    pass


def eval_code(stmts, locals_=None, globals_=None):
    """
    a helper function to ignore incomplete syntax erros when evaluating code
    while typing incomplete lines, e.g.: j.clien...
    """
    if not stmts:
        return

    try:
        code = compile(stmts, filename="<kosmos>", mode="eval")
    except SyntaxError:
        return

    return eval(code, globals_, locals_)


def sort_children_key(name):
    """Sort members of an object

    :param name: name
    :type name: str
    :return: the order of sorting
    :rtype: int
    """
    if name.startswith("__"):
        return 3
    elif name.startswith("_"):
        return 2
    elif name.isupper():
        return 1
    else:
        return 0


def filter_completions_on_prefix(completions, prefix=None):
    for completion in completions:
        text = completion.text
        if prefix not in HIDDEN_PREFIXES and text.startswith(HIDDEN_PREFIXES):
            continue
        yield completion


def get_current_line(document):
    tbc = document.current_line_before_cursor
    if tbc:
        line = tbc.split(".")
        parent, member = ".".join(line[:-1]), line[-1]
        if member.startswith("__"):  # then we want to show private methods
            prefix = "__"
        elif member.startswith("_"):  # then we want to show private methods
            prefix = "_"
        else:
            prefix = ""
        return parent, member, prefix
    raise ValueError("nothing is written")


def get_completions(self, document, complete_event):
    """
    get completions for j objects (using _method_) and others (using dir)

    :rtype: `Completion` generator
    """
    j = KosmosShellConfig.j

    def colored_completions(names, color):
        for name in names:
            if not isinstance(name, str):
                raise j.exceptions.JSBUG("name need to be str")
            if not name:
                continue
            if name.startswith(member):
                completion = name[len(member) :]
                yield Completion(
                    completion, 0, display=name, style="bg:%s fg:ansiblack" % color, selected_style="bg:ansidarkgray"
                )

    try:
        parent, member, prefix = get_current_line(document)
    except ValueError:
        return

    obj = eval_code(parent, self.get_locals(), self.get_globals())
    if obj:
        if isinstance(obj, j.baseclasses.object):
            if not prefix.endswith("*"):
                prefix += "*"  # to make it a real prefix

            dataprops = obj._dataprops_names_get(filter=prefix)
            props = obj._properties_names_get(filter=prefix)
            yield from colored_completions(dataprops, "ansigray")
            yield from colored_completions(obj._children_names_get(filter=prefix), "ansiyellow")
            yield from colored_completions(props, "ansigreen")
            yield from colored_completions(obj._methods_names_get(filter=prefix), "ansired")
        elif isinstance(obj, j.baseclasses.dict):
            names = [i for i in obj._data.keys()]
            yield from colored_completions(names, "ansiyellow")
            # members = sorted(dir(obj), key=sort_children_key)
            # yield from colored_completions(members, "ansigray")
        else:
            # try dir()
            members = sorted(dir(obj), key=sort_children_key)
            yield from colored_completions(members, "ansigray")


def get_doc_string(tbc, locals_, globals_):
    # j = KosmosShellConfig.j

    obj = eval_code(tbc, locals_=locals_, globals_=globals_)
    if not obj:
        raise j.exceptions.Value("cannot get docstring of %s, not an object" % tbc)

    signature = ""
    try:
        signature = inspect.signature(obj)
        signature = obj.__name__ + str(signature)
    except (ValueError, TypeError):
        # no signature can be provided or it's not supported e.g.
        # a built-in functions or not a module/class/function...
        pass

    doc = inspect.getdoc(obj) or ""
    if not signature:
        return doc
    return "\n\n".join([signature, doc])


def patched_handle_exception(self, e):
    j = KosmosShellConfig.j

    # Instead of just calling ``traceback.format_exc``, we take the
    # traceback and skip the bottom calls of this framework.
    t, v, tb = sys.exc_info()

    output = self.app.output
    # Required for pdb.post_mortem() to work.
    sys.last_type, sys.last_value, sys.last_traceback = t, v, tb

    # loop until getting actual traceback (without internal ptpython part)
    last_stdin_tb = tb
    while tb:
        if tb.tb_frame.f_code.co_filename == "<stdin>":
            last_stdin_tb = tb
        tb = tb.tb_next

    logdict = j.core.tools.log(tb=last_stdin_tb, level=50, exception=e, stdout=False)
    formatted_tb = j.core.tools.log2str(logdict, data_show=True, replace=True)
    print_formatted_text(ANSI(formatted_tb))

    output.write("%s\n" % e)
    output.flush()


class LogPane:
    Buffer = Buffer(name="logging")
    Show = True


class HasDocString(PythonInputFilter):
    def __call__(self):
        return len(self.python_input.docstring_buffer.text) > 0


class FormatANSIText(Processor):
    """see https://github.com/prompt-toolkit/python-prompt-toolkit/issues/711"""

    def apply_transformation(self, ti):
        fragments = to_formatted_text(ANSI(fragment_list_to_text(ti.fragments)))
        return Transformation(fragments)


class HasLogs(PythonInputFilter):
    def __call__(self):
        j = KosmosShellConfig.j
        panel_enabled = bool(j.core.myenv.config.get("LOGGER_PANEL_NRLINES"))
        in_autocomplete = j.application._in_autocomplete
        return LogPane.Show and panel_enabled and not in_autocomplete


class IsInsideString(PythonInputFilter):
    def __call__(self):
        text = self.python_input.default_buffer.document.text_before_cursor
        grammer = self.python_input._completer._path_completer_grammar
        return bool(grammer.match(text))


def get_ptpython_parent_container(repl):
    # see ptpython.layout
    return repl.app.layout.container.children[0].children[0]


def setup_docstring_containers(repl):
    parent_container = get_ptpython_parent_container(repl)
    # the same as ptpython containers, but without signature checking
    parent_container.children.extend(
        [
            ConditionalContainer(
                content=Window(height=Dimension.exact(1), char="\u2500", style="class:separator"),
                filter=HasDocString(repl) & ShowDocstring(repl) & ~is_done,
            ),
            ConditionalContainer(
                content=Window(
                    BufferControl(buffer=repl.docstring_buffer, lexer=PygmentsLexer(PythonLexer)),
                    wrap_lines=True,
                    height=Dimension(max=12),
                ),
                filter=HasDocString(repl) & ShowDocstring(repl) & ~is_done,
            ),
        ]
    )


def add_logs_to_pane(msg):
    LogPane.Buffer.insert_text(data=msg, fire_event=False)
    LogPane.Buffer.newline()
    LogPane.Buffer.auto_down(count=LogPane.Buffer.document.line_count)


def setup_logging_containers(repl):
    j = KosmosShellConfig.j

    panel_line_count = j.core.myenv.config.get("LOGGER_PANEL_NRLINES", 12)
    parent_container = get_ptpython_parent_container(repl)
    parent_container.children.extend(
        [
            ConditionalContainer(
                content=Window(height=Dimension.exact(1), char="\u2500", style="class:separator"),
                filter=HasLogs(repl) & ~is_done,
            ),
            ConditionalContainer(
                content=Window(
                    BufferControl(
                        buffer=LogPane.Buffer,
                        input_processors=[FormatANSIText(), HighlightIncrementalSearchProcessor()],
                        focusable=False,
                        preview_search=True,
                    ),
                    wrap_lines=True,
                    height=Dimension.exact(panel_line_count),
                ),
                filter=HasLogs(repl) & ~is_done,
            ),
        ]
    )


def ptconfig(repl):
    j = KosmosShellConfig.j

    repl.exit_message = "We hope you had fun using te kosmos shell"
    repl.show_docstring = True

    # When CompletionVisualisation.POP_UP has been chosen, use this
    # scroll_offset in the completion menu.
    repl.completion_menu_scroll_offset = 0

    # Show line numbers (when the input contains multiple lines.)
    repl.show_line_numbers = True

    # Show status bar.
    repl.show_status_bar = False

    # When the sidebar is visible, also show the help text.
    # repl.show_sidebar_help = True

    # Highlight matching parethesis.
    repl.highlight_matching_parenthesis = True

    # Line wrapping. (Instead of horizontal scrolling.)
    repl.wrap_lines = True

    # Mouse support.
    repl.enable_mouse_support = True

    # Complete while typing. (Don't require tab before the
    # completion menu is shown.)
    # repl.complete_while_typing = True

    # Vi mode.
    repl.vi_mode = False

    # Paste mode. (When True, don't insert whitespace after new line.)
    repl.paste_mode = False

    # Use the classic prompt. (Display '>>>' instead of 'In [1]'.)
    repl.prompt_style = "classic"  # 'classic' or 'ipython'

    # Don't insert a blank line after the output.
    repl.insert_blank_line_after_output = False

    # History Search.
    # When True, going back in history will filter the history on the records
    # starting with the current input. (Like readline.)
    # Note: When enable, please disable the `complete_while_typing` option.
    #       otherwise, when there is a completion available, the arrows will
    #       browse through the available completions instead of the history.
    # repl.enable_history_search = False

    # Enable auto suggestions. (Pressing right arrow will complete the input,
    # based on the history.)
    repl.enable_auto_suggest = True

    # Enable open-in-editor. Pressing C-X C-E in emacs mode or 'v' in
    # Vi navigation mode will open the input in the current editor.
    # repl.enable_open_in_editor = True

    # Enable system prompt. Pressing meta-! will display the system prompt.
    # Also enables Control-Z suspend.
    repl.enable_system_bindings = False

    # Ask for confirmation on exit.
    repl.confirm_exit = False

    # Enable input validation. (Don't try to execute when the input contains
    # syntax errors.)
    # repl.enable_input_validation = True

    # Use this colorscheme for the code.
    repl.use_code_colorscheme("perldoc")

    # Set color depth (keep in mind that not all terminals support true color).
    repl.color_depth = "DEPTH_24_BIT"  # True color.

    repl.enable_syntax_highlighting = True

    repl.min_brightness = 0.3

    @repl.add_key_binding(Keys.ControlJ)
    def _debug_event(event):
        """
        custom binding for pudb, to allow debugging a statement and also
        post-mortem debugging in case of any exception
        """
        b = event.cli.current_buffer
        app = get_app()
        statements = b.document.text
        if statements:
            import linecache

            linecache.cache["<string>"] = (len(statements), time.time(), statements.split("\n"), "<string>")
            app.exit(pudb.runstatement(statements))
            app.pre_run_callables.append(b.reset)
        else:
            pudb.pm()

    # Custom key binding for some simple autocorrection while typing.

    corrections = {"impotr": "import", "pritn": "print", "pr": "print("}

    @repl.add_key_binding(" ")
    def _(event):
        " When a space is pressed. Check & correct word before cursor. "
        b = event.cli.current_buffer
        w = b.document.get_word_before_cursor()
        if w is not None:
            if w in corrections:
                b.delete_before_cursor(count=len(w))
                b.insert_text(corrections[w])
        b.insert_text(" ")

    @repl.add_key_binding("?", filter=~IsInsideString(repl))
    def _docevent(event):
        b = event.cli.current_buffer
        parent, member, _ = get_current_line(b.document)
        member = member.rstrip("(")

        try:
            d = None
            try:
                # try get the class member itself first
                d = get_doc_string(f"{parent}.__class__.{member}", repl.get_locals(), repl.get_globals())
            except:
                pass

            if not d:
                if parent:
                    d = get_doc_string(f"{parent}.{member}", repl.get_locals(), repl.get_globals())
                else:
                    d = get_doc_string(member, repl.get_locals(), repl.get_globals())
        except Exception as exc:
            j.tools.logger._log_error(str(exc))
            repl.docstring_buffer.reset()
            return

        if d:
            repl.docstring_buffer.reset(document=Document(d, cursor_position=0))

    sidebar_visible = Condition(lambda: repl.show_sidebar)

    @repl.add_key_binding("c-p", filter=~sidebar_visible)
    def _logevent(event):
        LogPane.Show = not LogPane.Show

    class CustomPrompt(PromptStyle):
        """
        The classic Python prompt.
        """

        def in_prompt(self):
            return [("class:prompt", "JSX> ")]

        def in2_prompt(self, width):
            return [("class:prompt.dots", "...")]

        def out_prompt(self):
            return []

    repl._handle_exception = partial(patched_handle_exception, repl)
    repl.all_prompt_styles["custom"] = CustomPrompt()
    repl.prompt_style = "custom"

    old_get_completions = repl._completer.__class__.get_completions

    def custom_get_completions(self, document, complete_event):
        j.application._in_autocomplete = True

        try:
            _, _, prefix = get_current_line(document)
        except ValueError:
            return

        completions = []
        try:
            completions = list(get_completions(self, document, complete_event))
        except Exception:
            j.tools.logger._log_error("Error while getting completions\n" + traceback.format_exc())

        # j.tools.logger._log_error(completions)

        if not completions:
            completions = old_get_completions(self, document, complete_event)

        j.application._in_autocomplete = False
        yield from filter_completions_on_prefix(completions, prefix)

    repl._completer.__class__.get_completions = custom_get_completions
    j.core.tools.custom_log_printer = add_logs_to_pane

    parent_container = get_ptpython_parent_container(repl)
    # remove ptpython docstring containers, we have ours now
    parent_container.children = parent_container.children[:-2]
    # setup docstring and logging containers
    setup_docstring_containers(repl)
    setup_logging_containers(repl)
