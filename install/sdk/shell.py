import ast
import sys
import six
import pudb
import time
import inspect
import os

from . import __all__ as sdkall

from prompt_toolkit.application import get_app
from prompt_toolkit.keys import Keys
from prompt_toolkit.validation import ValidationError
from prompt_toolkit.shortcuts import print_formatted_text
from prompt_toolkit.formatted_text.utils import fragment_list_width
from prompt_toolkit.completion import Completion
from prompt_toolkit.formatted_text import (
    ANSI,
    FormattedText,
    merge_formatted_text,
)

from ptpython.prompt_style import PromptStyle

from . import __all__


__name__ = "<sdk>"


HIDDEN_PREFIXES = ("_", "__")


def filter_completions_on_prefix(completions, prefix=None, expert=False):
    for completion in completions:
        text = completion.text
        if prefix not in HIDDEN_PREFIXES and text.startswith(HIDDEN_PREFIXES):
            continue
        if not text.islower():
            continue
        if not expert and not text.startswith(tuple(sdkall)):
            continue
        yield completion


def get_rhs(line):
    """
    get the right-hand side from assignment statement
    will return the given line if it is not an assigment statement (e.g.an expression)

    :param line: line
    :type line: str
    """
    try:
        # remove the dot at the end to avoid syntax errors
        mod = ast.parse(line.rstrip("."))
    except SyntaxError:
        return line

    if mod.body:
        stmt = mod.body[0]
        # only assignment statements
        if type(stmt) in (ast.Assign, ast.AugAssign, ast.AnnAssign):
            return line[stmt.value.col_offset:].strip()
    return line


def get_current_line(document):
    tbc = document.current_line_before_cursor
    if tbc:
        line = get_rhs(tbc)
        parts = line.split(".")
        parent, member = ".".join(parts[:-1]), parts[-1]
        if member.startswith("__"):  # then we want to show private methods
            prefix = "__"
        elif member.startswith("_"):  # then we want to show private methods
            prefix = "_"
        else:
            prefix = ""
        return parent, member, prefix
    raise ValueError("nothing is written")


def eval_code(stmts, locals_=None, globals_=None):
    """
    a helper function to ignore incomplete syntax erros when evaluating code
    while typing incomplete lines, e.g.: j.clien...
    """
    if not stmts:
        return

    try:
        code = compile(stmts, filename=__name__, mode="eval")
    except SyntaxError:
        return

    try:
        return eval(code, globals_, locals_)
    except:
        return


def rewriteline(line, globals, locals):
    """
    Check if commands are entered in novice mode and rewrite them to python
    """
    def get_args_string(argslist):
        line = ""
        for arg in argslist:
            if arg in globals or arg in locals:
                line += f"{arg}, "
            elif arg.isdigit():
                line += f"{arg}, "
            elif ":" in arg:
                kwarg = arg.split(":")
                line += f"{kwarg[0]}="
                if kwarg[1].isdigt():
                    line += f"{kwarg[1]}, "
                else:
                    line += f"'{kwarg[1]}', "
            else:
                # let's assume its a string
                line += f"'{arg}', "
        return line

    parts = line.split()
    if parts[0] in sdkall + ["info"]:
        root = globals[parts[0]]
        if len(parts) >= 2:
            line = f"{parts[0]}.{parts[1]}("
            line += get_args_string(parts[2:])
            line += ")"
        elif inspect.isfunction(root):
            line = f"{parts[0]}("
            line += get_args_string(parts[1:])
            line += ")"
    return line


def patched_execute(self, line):
    """
    Evaluate the line and print the result.
    """
    output = self.app.output

    # WORKAROUND: Due to a bug in Jedi, the current directory is removed
    # from sys.path. See: https://github.com/davidhalter/jedi/issues/1148
    if "" not in sys.path:
        sys.path.insert(0, "")

    def compile_with_flags(code, mode):
        " Compile code with the right compiler flags. "
        return compile(code, "<stdin>", mode, flags=self.get_compiler_flags(), dont_inherit=True)

    line = rewriteline(line, self.get_globals(), self.get_locals())
    if line.lstrip().startswith("\x1a"):
        # When the input starts with Ctrl-Z, quit the REPL.
        self.app.exit()

    elif line.lstrip().startswith("!"):
        # Run as shell command
        os.system(line[1:])
    else:
        # Try eval first
        try:
            code = compile_with_flags(line, "eval")
            result = eval(code, self.get_globals(), self.get_locals())

            locals = self.get_locals()
            locals["_"] = locals["_%i" % self.current_statement_index] = result

            if result is not None:
                out_prompt = self.get_output_prompt()

                try:
                    result_str = "%r\n" % (result,)
                except UnicodeDecodeError:
                    # In Python 2: `__repr__` should return a bytestring,
                    # so to put it in a unicode context could raise an
                    # exception that the 'ascii' codec can't decode certain
                    # characters. Decode as utf-8 in that case.
                    result_str = "%s\n" % repr(result).decode("utf-8")

                # Align every line to the first one.
                line_sep = "\n" + " " * fragment_list_width(out_prompt)
                result_str = line_sep.join(result_str.splitlines()) + "\n"

                # Support ansi formatting (removed syntax higlighting)
                ansi_formatted = ANSI(result_str)._formatted_text
                formatted_output = merge_formatted_text([FormattedText(out_prompt) + ansi_formatted])

                print_formatted_text(
                    formatted_output,
                    style=self._current_style,
                    style_transformation=self.style_transformation,
                    include_default_pygments_style=False,
                )

        # If not a valid `eval` expression, run using `exec` instead.
        except SyntaxError:
            code = compile_with_flags(line, "exec")
            six.exec_(code, self.get_globals(), self.get_locals())

        output.flush()


def ptconfig(repl, expert=False):

    repl.exit_message = "We hope you had fun using our sdk shell"
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
    repl.complete_while_typing = True

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
    repl.enable_input_validation = True
    repl.default_buffer.validate_while_typing = lambda: True

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

            linecache.cache[__name__] = (len(statements), time.time(), statements.split("\n"), "<string>")
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

    class CustomPrompt(PromptStyle):
        """
        The classic Python prompt.
        """

        def in_prompt(self):
            return [("class:prompt", "3sdk> ")]

        def in2_prompt(self, width):
            return [("class:prompt.dots", "...")]

        def out_prompt(self):
            return []

    repl.all_prompt_styles["custom"] = CustomPrompt()
    repl.prompt_style = "custom"

    old_get_completions = repl._completer.__class__.get_completions

    def get_novice_completions(self, document, complete_event):
        line = document.current_line_before_cursor

        def complete_function(func):
            for arg in inspect.getargspec(func).args:
                field = arg + ":"
                if field not in line:
                    yield Completion(field, 0, display=field)

        parts = line.split()
        if len(parts) == 0:
            for rootitem in sdkall + ["info"]:
                yield Completion(rootitem, -len(line), display=rootitem)
        if parts[0] in sdkall:
            root = repl.get_globals()[parts[0]]
            if inspect.isfunction(root):
                yield from complete_function(root)
            if len(parts) == 1 and line.endswith(" "):
                rmembers = inspect.getmembers(root, inspect.isfunction)
                for rmember, _ in rmembers:
                    yield Completion(rmember, 0, display=rmember)
            elif len(parts) == 2 and not line.endswith(" "):
                root = repl.get_globals()[parts[0]]
                rmembers = inspect.getmembers(root, inspect.isfunction)
                for rmember, _ in rmembers:
                    if rmember.startswith(parts[1]):
                        yield Completion(rmember, -len(parts[1]), display=rmember)
            elif (len(parts) >= 3 or len(parts) == 2 and line.endswith(" ")) and hasattr(root, parts[1]):
                func = getattr(root, parts[1])
                yield from complete_function(func)

    def custom_get_completions(self, document, complete_event):
        try:
            _, _, prefix = get_current_line(document)
        except ValueError:
            return

        completions = get_novice_completions(self, document, complete_event)
        customcompletions = False
        for completion in completions:
            customcompletions = True
            yield completion
        if customcompletions:
            return True

        completions = old_get_completions(self, document, complete_event)
        yield from filter_completions_on_prefix(completions, prefix, expert)

    old_validator = repl._validator.__class__.validate

    def custom_validator(self, document):
        try:
            parent, _, _ = get_current_line(document)
        except ValueError:
            return

        try:
            eval_code(parent, repl.get_locals(), repl.get_globals())
        except (AttributeError, NameError) as e:
            raise ValidationError(message=str(e))
        except:
            old_validator(self, document)

    repl._completer.__class__.get_completions = custom_get_completions
    repl._validator.__class__.validate = custom_validator
    repl.__class__._execute = patched_execute
